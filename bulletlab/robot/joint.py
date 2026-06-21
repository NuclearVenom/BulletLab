"""
Joint – a single degree-of-freedom actuator in a robot model.

The Joint class wraps a single PyBullet joint and exposes its properties
(position, velocity, torque, limits, max_force, max_velocity) as Python
attributes. Setting any property automatically propagates to PyBullet.

Example::

    joint = robot.joints["motor"]
    print(joint.position)         # read current angle
    joint.velocity = 15.0         # apply velocity control
    joint.torque = 20.0           # apply torque control
    joint.reset(pos=0.0)          # reset to zero position
"""

from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

import pybullet as p

if TYPE_CHECKING:
    from bulletlab.core.simulation import Simulation


class JointType(IntEnum):
    """Enumeration of PyBullet joint types."""

    REVOLUTE = p.JOINT_REVOLUTE
    PRISMATIC = p.JOINT_PRISMATIC
    SPHERICAL = p.JOINT_SPHERICAL
    PLANAR = p.JOINT_PLANAR
    FIXED = p.JOINT_FIXED


class Joint:
    """A single joint in a robot model.

    Joints are typically not instantiated directly — they are created by
    :class:`~bulletlab.robot.robot.Robot` when loading a URDF/MJCF file.
    Access them via ``robot.joints["joint_name"]``.

    Args:
        name: Joint name (from URDF).
        index: PyBullet joint index.
        body_id: PyBullet body ID of the parent robot.
        sim: The :class:`~bulletlab.core.simulation.Simulation` instance.

    Example::

        joint = robot.joints["wheel_left"]
        joint.velocity = 10.0
        joint.max_force = 50.0
        print(joint.position)
    """

    def __init__(
        self,
        name: str,
        index: int,
        body_id: int,
        sim: "Simulation",
    ) -> None:
        self._name = name
        self._index = index
        self._body_id = body_id
        self._sim = sim
        self._max_force: float = 100.0
        self._max_velocity: float = 10.0
        self._control_mode: int = p.VELOCITY_CONTROL
        self._enabled: bool = True

        # Read limits and joint type from PyBullet
        info = p.getJointInfo(
            self._body_id,
            self._index,
            physicsClientId=self._sim.client_id,
        )
        self._joint_type = JointType(info[2]) if info[2] in [t.value for t in JointType] else info[2]
        self._lower_limit: float = float(info[8])
        self._upper_limit: float = float(info[9])
        self._max_force = float(info[10]) if info[10] > 0 else 100.0
        self._max_velocity = float(info[11]) if info[11] > 0 else 10.0

    # ------------------------------------------------------------------
    # Safety guard
    # ------------------------------------------------------------------

    def _check_connected(self) -> bool:
        """Return True if the physics server is still live.

        Uses ``p.isConnected()`` to query the actual PyBullet runtime rather
        than BulletLab's internal flag, which only updates on explicit
        ``sim.stop()`` calls and misses cases where the 3D window is closed
        by the user independently.
        """
        try:
            return bool(p.isConnected(physicsClientId=self._sim.client_id))
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Joint name as defined in the URDF."""
        return self._name

    @property
    def index(self) -> int:
        """PyBullet joint index (internal identifier)."""
        return self._index

    @property
    def joint_type(self) -> JointType | int:
        """Type of this joint (revolute, prismatic, fixed, etc.)."""
        return self._joint_type

    @property
    def is_fixed(self) -> bool:
        """``True`` if this is a fixed (non-actuated) joint."""
        return self._joint_type == JointType.FIXED

    # ------------------------------------------------------------------
    # State reads
    # ------------------------------------------------------------------

    @property
    def position(self) -> float:
        """Current joint position (angle in radians or displacement in meters).

        Read-only. Use :meth:`reset` to set position directly.

        Example::

            print(robot.joints["elbow"].position)
        """
        if not self._check_connected():
            return 0.0
        state = p.getJointState(
            self._body_id,
            self._index,
            physicsClientId=self._sim.client_id,
        )
        return float(state[0])

    @position.setter
    def position(self, target: float) -> None:
        """Apply position control to move the joint to a target angle/displacement.

        This is a convenience alias for :meth:`set_position` using the default max force.
        """
        self.set_position(target)

    @property
    def velocity(self) -> float:
        """Current joint velocity (rad/s or m/s).

        Setting this applies velocity control via PyBullet.

        Example::

            robot.joints["wheel"].velocity = 10.0
        """
        if not self._check_connected():
            return 0.0
        state = p.getJointState(
            self._body_id,
            self._index,
            physicsClientId=self._sim.client_id,
        )
        return float(state[1])

    @velocity.setter
    def velocity(self, value: float) -> None:
        if not self._check_connected():
            return
        self._control_mode = p.VELOCITY_CONTROL
        p.setJointMotorControl2(
            self._body_id,
            self._index,
            controlMode=p.VELOCITY_CONTROL,
            targetVelocity=float(value),
            force=self._max_force,
            physicsClientId=self._sim.client_id,
        )

    @property
    def torque(self) -> float:
        """Current joint applied torque (N·m or N).

        Setting this applies torque control via PyBullet.

        Example::

            robot.joints["hip"].torque = 20.0
        """
        if not self._check_connected():
            return 0.0
        state = p.getJointState(
            self._body_id,
            self._index,
            physicsClientId=self._sim.client_id,
        )
        return float(state[3])

    @torque.setter
    def torque(self, value: float) -> None:
        if not self._check_connected():
            return
        self._control_mode = p.TORQUE_CONTROL
        # Disable velocity motor first so torque control can take over
        p.setJointMotorControl2(
            self._body_id,
            self._index,
            controlMode=p.VELOCITY_CONTROL,
            targetVelocity=0,
            force=0,
            physicsClientId=self._sim.client_id,
        )
        p.setJointMotorControl2(
            self._body_id,
            self._index,
            controlMode=p.TORQUE_CONTROL,
            force=float(value),
            physicsClientId=self._sim.client_id,
        )

    # ------------------------------------------------------------------
    # Position control
    # ------------------------------------------------------------------

    def set_position(self, target: float, max_force: float | None = None) -> None:
        """Apply position control to move the joint to a target angle/displacement.

        Args:
            target: Target position (radians or meters).
            max_force: Maximum force/torque. Defaults to :attr:`max_force`.

        Example::

            robot.joints["shoulder"].set_position(1.57)   # 90°
        """
        if not self._check_connected():
            return
        force = float(max_force) if max_force is not None else self._max_force
        self._control_mode = p.POSITION_CONTROL
        p.setJointMotorControl2(
            self._body_id,
            self._index,
            controlMode=p.POSITION_CONTROL,
            targetPosition=float(target),
            force=force,
            physicsClientId=self._sim.client_id,
        )

    # ------------------------------------------------------------------
    # Limits and tuning
    # ------------------------------------------------------------------

    @property
    def limits(self) -> tuple[float, float]:
        """Joint position limits as ``(lower, upper)`` in radians or meters.

        Returns ``(0.0, 0.0)`` for fixed joints or joints with no limits.

        Example::

            lo, hi = robot.joints["elbow"].limits
        """
        return (self._lower_limit, self._upper_limit)

    @property
    def max_force(self) -> float:
        """Maximum motor force / torque in N or N·m.

        Example::

            robot.joints["motor"].max_force = 150.0
        """
        return self._max_force

    @max_force.setter
    def max_force(self, value: float) -> None:
        self._max_force = float(value)

    @property
    def max_velocity(self) -> float:
        """Maximum joint velocity in rad/s or m/s.

        Example::

            robot.joints["wheel"].max_velocity = 20.0
        """
        return self._max_velocity

    @max_velocity.setter
    def max_velocity(self, value: float) -> None:
        self._max_velocity = float(value)

    # ------------------------------------------------------------------
    # Enable / disable
    # ------------------------------------------------------------------

    def enable(self) -> None:
        """Enable the joint motor (default state).

        Example::

            robot.joints["motor"].enable()
        """
        self._enabled = True
        if not self._check_connected():
            return
        p.setJointMotorControl2(
            self._body_id,
            self._index,
            controlMode=p.VELOCITY_CONTROL,
            targetVelocity=0,
            force=self._max_force,
            physicsClientId=self._sim.client_id,
        )

    def disable(self) -> None:
        """Disable the joint motor (free-spinning / passive joint).

        Example::

            robot.joints["motor"].disable()
        """
        self._enabled = False
        if not self._check_connected():
            return
        p.setJointMotorControl2(
            self._body_id,
            self._index,
            controlMode=p.VELOCITY_CONTROL,
            targetVelocity=0,
            force=0,
            physicsClientId=self._sim.client_id,
        )

    @property
    def is_enabled(self) -> bool:
        """``True`` if the joint motor is enabled."""
        return self._enabled

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self, pos: float = 0.0, vel: float = 0.0) -> None:
        """Teleport the joint to a specific state.

        This bypasses physics and directly sets joint position and velocity.
        Useful for initializing a robot pose.

        Args:
            pos: Target position in radians or meters.
            vel: Target velocity in rad/s or m/s.

        Example::

            robot.joints["shoulder"].reset(pos=1.0, vel=0.0)
        """
        if not self._check_connected():
            return
        p.resetJointState(
            self._body_id,
            self._index,
            targetValue=float(pos),
            targetVelocity=float(vel),
            physicsClientId=self._sim.client_id,
        )

    # ------------------------------------------------------------------
    # Reaction forces
    # ------------------------------------------------------------------

    @property
    def reaction_forces(self) -> tuple[float, ...]:
        """Joint reaction forces and torques as a 6-element tuple ``(Fx, Fy, Fz, Mx, My, Mz)``.

        Note:
            Requires enabling joint force sensors via PyBullet first.
        """
        if not self._check_connected():
            return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        state = p.getJointState(
            self._body_id,
            self._index,
            physicsClientId=self._sim.client_id,
        )
        return tuple(float(v) for v in state[2])

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        if self._check_connected():
            return (
                f"Joint({self._name!r}, type={self._joint_type}, "
                f"pos={self.position:.3f}, vel={self.velocity:.3f})"
            )
        return f"Joint({self._name!r}, type={self._joint_type}, disconnected)"
