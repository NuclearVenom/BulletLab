"""
Robot – the primary interface to a simulated robot in BulletLab.

The Robot class loads a URDF or MJCF model into PyBullet and exposes all
its joints and links as named Python objects. You never need to work with
raw PyBullet body IDs or joint indices.

Example::

    from bulletlab import Simulation, Robot

    sim = Simulation().start()
    robot = Robot.load("kuka_iiwa/model.urdf", sim=sim)

    # Access joints and links by name
    robot.joints["iiwa_joint_1"].set_position(1.0)
    robot.links["iiwa_link_0"].mass = 5.0

    # State inspection
    print(robot.base_position)
    print(robot.roll, robot.pitch, robot.yaw)

    # RL-style interface
    state = robot.get_state()
    robot.apply_action(action)
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import numpy as np
import pybullet as p

from bulletlab.robot.joint import Joint, JointType
from bulletlab.robot.link import Link
from bulletlab.utils.math_utils import quaternion_to_euler

if TYPE_CHECKING:
    from bulletlab.core.simulation import Simulation


class Robot:
    """A simulated robot loaded from a URDF or MJCF file.

    Provides structured access to all joints and links by name, along with
    base-link state properties, RL-compatible state/action interfaces,
    and reset functionality.

    Do not instantiate directly — use the :meth:`load` class method.

    Args:
        body_id: PyBullet body ID.
        sim: The parent :class:`~bulletlab.core.simulation.Simulation`.
        name: Human-readable robot name.
        initial_position: Initial base position.
        initial_orientation: Initial base orientation (quaternion).

    Example::

        robot = Robot.load("car.urdf", sim=sim, position=(0, 0, 0.5))
        robot.joints["steering"].set_position(0.3)
        robot.links["chassis"].mass = 10.0
    """

    def __init__(
        self,
        body_id: int,
        sim: "Simulation",
        name: str = "Robot",
        initial_position: tuple[float, float, float] = (0.0, 0.0, 0.0),
        initial_orientation: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
    ) -> None:
        self._body_id = body_id
        self._sim = sim
        self._name = name
        self._initial_position = initial_position
        self._initial_orientation = initial_orientation
        self._joints: dict[str, Joint] = {}
        self._links: dict[str, Link] = {}
        self._joint_indices: list[int] = []  # controllable joint indices

        self._discover_joints_and_links()

    # ------------------------------------------------------------------
    # Factory / classmethod
    # ------------------------------------------------------------------

    @classmethod
    def load(
        cls,
        path: str | Path,
        sim: "Simulation",
        position: tuple[float, float, float] = (0.0, 0.0, 0.0),
        orientation: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
        name: str | None = None,
        fixed_base: bool = False,
        scale: float = 1.0,
        flags: int = 0,
    ) -> "Robot":
        """Load a robot from a URDF or MJCF file.

        Automatically discovers all joints and links and exposes them by name.

        Args:
            path: Path to the URDF/MJCF file. Can be an absolute path or a
                filename resolvable from the pybullet_data search path.
            sim: The :class:`~bulletlab.core.simulation.Simulation` instance.
            position: Initial base position ``(x, y, z)`` in meters.
            orientation: Initial base orientation as a quaternion ``(x, y, z, w)``.
            name: Human-readable robot name. Defaults to the filename stem.
            fixed_base: If ``True``, the robot's base is fixed to the world.
            scale: Global scale factor for the loaded model.
            flags: Additional PyBullet load flags.

        Returns:
            A new :class:`Robot` instance.

        Raises:
            FileNotFoundError: If the URDF/MJCF file cannot be found.
            RuntimeError: If PyBullet fails to load the model.

        Example::

            robot = Robot.load("kuka_iiwa/model.urdf", sim=sim, position=(0, 0, 0))
        """
        path_str = str(path)
        robot_name = name or Path(path_str).stem

        path_obj = Path(path_str)
        ext = path_obj.suffix.lower()

        if ext in (".urdf",):
            body_id = p.loadURDF(
                path_str,
                basePosition=list(position),
                baseOrientation=list(orientation),
                useFixedBase=fixed_base,
                globalScaling=scale,
                flags=flags,
                physicsClientId=sim.client_id,
            )
        elif ext in (".xml", ".mjcf"):
            # MJCF: position/orientation not directly supported at load time
            body_ids = p.loadMJCF(
                path_str,
                physicsClientId=sim.client_id,
            )
            body_id = body_ids[0] if isinstance(body_ids, (list, tuple)) else body_ids
        else:
            # Try URDF by default
            body_id = p.loadURDF(
                path_str,
                basePosition=list(position),
                baseOrientation=list(orientation),
                useFixedBase=fixed_base,
                globalScaling=scale,
                flags=flags,
                physicsClientId=sim.client_id,
            )

        robot = cls(
            body_id=body_id,
            sim=sim,
            name=robot_name,
            initial_position=position,
            initial_orientation=orientation,
        )
        sim.add_robot(robot)
        return robot

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _discover_joints_and_links(self) -> None:
        """Scan PyBullet body and populate joints and links dictionaries."""
        num_joints = p.getNumJoints(self._body_id, physicsClientId=self._sim.client_id)

        # Base link (index -1)
        base_name = p.getBodyInfo(self._body_id, physicsClientId=self._sim.client_id)
        base_link_name = base_name[0].decode("utf-8") if isinstance(base_name[0], bytes) else str(base_name[0])
        self._links[base_link_name] = Link(
            name=base_link_name,
            index=-1,
            body_id=self._body_id,
            sim=self._sim,
        )
        # Also expose as "base"
        self._links["base"] = self._links[base_link_name]

        for i in range(num_joints):
            info = p.getJointInfo(self._body_id, i, physicsClientId=self._sim.client_id)
            joint_name_raw = info[1]
            link_name_raw = info[12]

            joint_name = joint_name_raw.decode("utf-8") if isinstance(joint_name_raw, bytes) else str(joint_name_raw)
            link_name = link_name_raw.decode("utf-8") if isinstance(link_name_raw, bytes) else str(link_name_raw)
            joint_type = info[2]

            # Build Joint object
            joint = Joint(
                name=joint_name,
                index=i,
                body_id=self._body_id,
                sim=self._sim,
            )
            self._joints[joint_name] = joint

            # Build Link object for this joint's child link
            link = Link(
                name=link_name,
                index=i,
                body_id=self._body_id,
                sim=self._sim,
            )
            self._links[link_name] = link

            # Track controllable joints (non-fixed)
            if joint_type != p.JOINT_FIXED:
                self._joint_indices.append(i)

    # ------------------------------------------------------------------
    # Joints and Links access
    # ------------------------------------------------------------------

    @property
    def joints(self) -> dict[str, Joint]:
        """Dictionary of all joints indexed by name.

        Example::

            robot.joints["wheel_left"].velocity = 10
        """
        return self._joints

    @property
    def links(self) -> dict[str, Link]:
        """Dictionary of all links indexed by name.

        Example::

            robot.links["chassis"].mass = 5.0
        """
        return self._links

    @property
    def controllable_joints(self) -> list[Joint]:
        """List of all non-fixed joints (those that can be actuated)."""
        return [j for j in self._joints.values() if not j.is_fixed]

    # ------------------------------------------------------------------
    # Base state
    # ------------------------------------------------------------------

    @property
    def base_position(self) -> tuple[float, float, float]:
        """World-frame base position ``(x, y, z)`` in meters.

        Example::

            x, y, z = robot.base_position
        """
        pos, _ = p.getBasePositionAndOrientation(
            self._body_id,
            physicsClientId=self._sim.client_id,
        )
        return tuple(float(v) for v in pos)  # type: ignore[return-value]

    @property
    def base_orientation(self) -> tuple[float, float, float, float]:
        """World-frame base orientation as quaternion ``(x, y, z, w)``.

        Example::

            q = robot.base_orientation
        """
        _, orn = p.getBasePositionAndOrientation(
            self._body_id,
            physicsClientId=self._sim.client_id,
        )
        return tuple(float(v) for v in orn)  # type: ignore[return-value]

    @property
    def base_velocity(self) -> tuple[float, float, float]:
        """World-frame linear velocity ``(vx, vy, vz)`` in m/s.

        Example::

            speed = robot.base_velocity[0]
        """
        vel, _ = p.getBaseVelocity(
            self._body_id,
            physicsClientId=self._sim.client_id,
        )
        return tuple(float(v) for v in vel)  # type: ignore[return-value]

    @property
    def base_angular_velocity(self) -> tuple[float, float, float]:
        """World-frame angular velocity ``(wx, wy, wz)`` in rad/s.

        Example::

            wx, wy, wz = robot.base_angular_velocity
        """
        _, avel = p.getBaseVelocity(
            self._body_id,
            physicsClientId=self._sim.client_id,
        )
        return tuple(float(v) for v in avel)  # type: ignore[return-value]

    @property
    def roll(self) -> float:
        """Base roll angle in radians (rotation around X axis).

        Example::

            print(f"Roll: {math.degrees(robot.roll):.1f}°")
        """
        return quaternion_to_euler(self.base_orientation)[0]

    @property
    def pitch(self) -> float:
        """Base pitch angle in radians (rotation around Y axis)."""
        return quaternion_to_euler(self.base_orientation)[1]

    @property
    def yaw(self) -> float:
        """Base yaw angle in radians (rotation around Z axis)."""
        return quaternion_to_euler(self.base_orientation)[2]

    @property
    def speed(self) -> float:
        """Scalar speed (magnitude of base linear velocity) in m/s.

        Example::

            print(f"Speed: {robot.speed:.2f} m/s")
        """
        v = self.base_velocity
        return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(
        self,
        position: tuple[float, float, float] | None = None,
        orientation: tuple[float, float, float, float] | None = None,
    ) -> None:
        """Reset the robot to its initial (or specified) pose.

        Also resets all joint positions and velocities to zero.

        Args:
            position: Target base position. Defaults to initial load position.
            orientation: Target base orientation. Defaults to initial load orientation.

        Example::

            robot.reset()
            robot.reset(position=(0, 0, 1), orientation=(0, 0, 0, 1))
        """
        pos = position if position is not None else self._initial_position
        orn = orientation if orientation is not None else self._initial_orientation

        p.resetBasePositionAndOrientation(
            self._body_id,
            list(pos),
            list(orn),
            physicsClientId=self._sim.client_id,
        )
        p.resetBaseVelocity(
            self._body_id,
            [0, 0, 0],
            [0, 0, 0],
            physicsClientId=self._sim.client_id,
        )
        for joint in self._joints.values():
            if not joint.is_fixed:
                joint.reset(pos=0.0, vel=0.0)

    # ------------------------------------------------------------------
    # RL interface
    # ------------------------------------------------------------------

    def get_state(self) -> np.ndarray:
        """Return the full observable state as a flat NumPy array.

        State vector layout::

            [base_x, base_y, base_z,       # base position (3)
             base_qx, base_qy, base_qz, base_qw,  # base orientation quaternion (4)
             base_vx, base_vy, base_vz,   # base linear velocity (3)
             base_wx, base_wy, base_wz,   # base angular velocity (3)
             joint_pos_0, ...,            # controllable joint positions (N)
             joint_vel_0, ...]            # controllable joint velocities (N)

        Returns:
            1D NumPy float64 array of shape ``(13 + 2*N,)`` where N is the
            number of controllable joints.

        Example::

            state = robot.get_state()
            action = my_policy(state)
        """
        pos = list(self.base_position)
        orn = list(self.base_orientation)
        vel = list(self.base_velocity)
        avel = list(self.base_angular_velocity)

        joint_positions = []
        joint_velocities = []
        for idx in self._joint_indices:
            js = p.getJointState(self._body_id, idx, physicsClientId=self._sim.client_id)
            joint_positions.append(float(js[0]))
            joint_velocities.append(float(js[1]))

        return np.array(
            pos + orn + vel + avel + joint_positions + joint_velocities,
            dtype=np.float64,
        )

    def apply_action(self, action: np.ndarray) -> None:
        """Apply a NumPy action array to all controllable joints.

        The action array must have the same length as the number of
        controllable joints. Each value is interpreted as a target velocity.

        Args:
            action: 1D NumPy array of target velocities for each controllable joint.

        Raises:
            ValueError: If ``action`` length doesn't match controllable joint count.

        Example::

            action = np.array([10.0, 10.0, -5.0])
            robot.apply_action(action)
        """
        if len(action) != len(self._joint_indices):
            raise ValueError(
                f"Action length {len(action)} does not match "
                f"controllable joint count {len(self._joint_indices)}"
            )
        for idx, act_val in zip(self._joint_indices, action):
            p.setJointMotorControl2(
                self._body_id,
                idx,
                controlMode=p.VELOCITY_CONTROL,
                targetVelocity=float(act_val),
                force=100.0,
                physicsClientId=self._sim.client_id,
            )

    def apply_torques(self, torques: np.ndarray) -> None:
        """Apply torque control to all controllable joints.

        Args:
            torques: 1D NumPy array of torques for each controllable joint (N·m).

        Raises:
            ValueError: If ``torques`` length doesn't match controllable joint count.

        Example::

            robot.apply_torques(np.array([5.0, -5.0, 0.0]))
        """
        if len(torques) != len(self._joint_indices):
            raise ValueError(
                f"Torques length {len(torques)} does not match "
                f"controllable joint count {len(self._joint_indices)}"
            )
        # Disable velocity motors first
        for idx in self._joint_indices:
            p.setJointMotorControl2(
                self._body_id,
                idx,
                controlMode=p.VELOCITY_CONTROL,
                targetVelocity=0,
                force=0,
                physicsClientId=self._sim.client_id,
            )
        for idx, torque_val in zip(self._joint_indices, torques):
            p.setJointMotorControl2(
                self._body_id,
                idx,
                controlMode=p.TORQUE_CONTROL,
                force=float(torque_val),
                physicsClientId=self._sim.client_id,
            )

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Human-readable robot name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = str(value)

    @property
    def body_id(self) -> int:
        """PyBullet body ID (internal identifier). Prefer using named properties."""
        return self._body_id

    @property
    def num_joints(self) -> int:
        """Total number of joints (including fixed joints)."""
        return len(self._joints)

    @property
    def num_controllable_joints(self) -> int:
        """Number of non-fixed, actuatable joints."""
        return len(self._joint_indices)

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Robot({self._name!r}, body_id={self._body_id}, "
            f"joints={len(self._joints)}, links={len(self._links)})"
        )
