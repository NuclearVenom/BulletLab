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

import weakref
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


# Global registry of all instantiated joints.
_ALL_JOINTS = weakref.WeakSet()


class _UnpinCommand:
    """Helper to support both `joint.unpin()` and console `joint.unpin` (no parens)."""
    def __init__(self, joint: "Joint"):
        self.joint = joint

    def __call__(self) -> str:
        self.joint._pinned = False
        return self.joint.name

    def __repr__(self) -> str:
        self.joint._pinned = False
        return f"'{self.joint.name}'"


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

        # Live target value ────────────────────────────────────────────────────
        # This is the value sliders read and write.  It is updated by the
        # property setters (joint.position = X) and by the slider widget
        # (via joint.target = X).  apply_targets()-style loops read it via
        # j.target and pass it to set_position(j.target) etc.
        self._target: float = 0.0

        # Console pin ──────────────────────────────────────────────────────
        # Set via  joint.pin_position = X  (or pin_velocity / pin_torque).
        # While pinned, set_position() / set_velocity() / set_torque() ignore
        # their argument and re-apply the pin value instead.  A 📌 icon is
        # shown next to the slider in the UI.  Call  joint.unpin()  to release.
        self._pinned: bool = False
        self._pin_value: float = 0.0
        self._pin_mode: str = "position"   # "position" | "velocity" | "torque"
        
        _ALL_JOINTS.add(self)

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
        """Move to *target*, sync the slider, and leave the slider **free**.

        Updates :attr:`target` (so sliders follow) and applies position control
        immediately.  If the joint was previously pinned, the pin is released so
        that ``apply_targets()`` loops and sliders can take over again.

        Use :attr:`pin_position` if you want to lock the slider as well.

        Example (in the BulletLab console)::

            robot.joints["left_knee_joint"].position = 1.0
            # Joint moves to 1.0; slider syncs to 1.0; slider is still free.
        """
        self._target = float(target)
        self._pinned = False              # release any previous pin
        if not self._check_connected():
            return
        self._control_mode = p.POSITION_CONTROL
        p.setJointMotorControl2(
            self._body_id,
            self._index,
            controlMode=p.POSITION_CONTROL,
            targetPosition=float(target),
            force=self._max_force,
            physicsClientId=self._sim.client_id,
        )

    @property
    def pin_position(self) -> float | None:
        """Read the current pinned position value, or ``None`` if not pinned."""
        return self._pin_value if (self._pinned and self._pin_mode == "position") else None

    @pin_position.setter
    def pin_position(self, target: float) -> None:
        """Move to *target*, sync the slider, and **lock** the slider (📌).

        ``apply_targets()`` loops calling :meth:`set_position` will be overridden
        with this value until :meth:`unpin` is called.

        Example (in the BulletLab console)::

            robot.joints["left_knee_joint"].pin_position = 1.0
            # Joint moves to 1.0; slider shows 📌 and is locked.
            robot.joints["left_knee_joint"].unpin()   # release
        """
        self._target = float(target)
        self._pinned = True
        self._pin_value = float(target)
        self._pin_mode = "position"
        if not self._check_connected():
            return
        self._control_mode = p.POSITION_CONTROL
        p.setJointMotorControl2(
            self._body_id,
            self._index,
            controlMode=p.POSITION_CONTROL,
            targetPosition=float(target),
            force=self._max_force,
            physicsClientId=self._sim.client_id,
        )

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
        """Apply velocity control immediately, sync slider, leave slider **free**.

        Use :attr:`pin_velocity` to lock the slider as well.

        Example::

            robot.joints["wheel"].velocity = 10.0
        """
        self._target = float(value)
        self._pinned = False
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
    def pin_velocity(self) -> float | None:
        """Read the current pinned velocity value, or ``None`` if not pinned."""
        return self._pin_value if (self._pinned and self._pin_mode == "velocity") else None

    @pin_velocity.setter
    def pin_velocity(self, value: float) -> None:
        """Apply velocity control, sync slider, and **lock** the slider (📌).

        Example (in the BulletLab console)::

            robot.joints["wheel"].pin_velocity = 10.0
            robot.joints["wheel"].unpin()   # release
        """
        self._target = float(value)
        self._pinned = True
        self._pin_value = float(value)
        self._pin_mode = "velocity"
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
        """Apply torque control immediately, sync slider, leave slider **free**.

        Use :attr:`pin_torque` to lock the slider as well.

        Example::

            robot.joints["hip"].torque = 20.0
        """
        self._target = float(value)
        self._pinned = False
        if not self._check_connected():
            return
        self._control_mode = p.TORQUE_CONTROL
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

    @property
    def pin_torque(self) -> float | None:
        """Read the current pinned torque value, or ``None`` if not pinned."""
        return self._pin_value if (self._pinned and self._pin_mode == "torque") else None

    @pin_torque.setter
    def pin_torque(self, value: float) -> None:
        """Apply torque control, sync slider, and **lock** the slider (📌).

        Example (in the BulletLab console)::

            robot.joints["hip"].pin_torque = 20.0
            robot.joints["hip"].unpin()   # release
        """
        self._target = float(value)
        self._pinned = True
        self._pin_value = float(value)
        self._pin_mode = "torque"
        if not self._check_connected():
            return
        self._control_mode = p.TORQUE_CONTROL
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
    # Programmatic control (respects console pin)
    # ------------------------------------------------------------------

    def set_position(self, target: float, max_force: float | None = None) -> None:
        """Programmatic position control — respects any active console pin.

        If the joint has been pinned via ``joint.position = X``, the *pinned*
        value is applied instead of *target*.  Use :meth:`unpin` to release.

        Args:
            target: Desired position (radians or meters).
            max_force: Maximum force/torque. Defaults to :attr:`max_force`.

        Example::

            robot.joints["shoulder"].set_position(1.57)   # 90°
        """
        if not self._check_connected():
            return
        force = float(max_force) if max_force is not None else self._max_force
        effective = (
            self._pin_value
            if self._pinned and self._pin_mode == "position"
            else float(target)
        )
        self._control_mode = p.POSITION_CONTROL
        p.setJointMotorControl2(
            self._body_id,
            self._index,
            controlMode=p.POSITION_CONTROL,
            targetPosition=effective,
            force=force,
            physicsClientId=self._sim.client_id,
        )

    def set_velocity(self, value: float) -> None:
        """Programmatic velocity control — respects any active console pin.

        If the joint has been pinned via ``joint.velocity = X``, the *pinned*
        value is applied instead of *value*.  Use :meth:`unpin` to release.

        Args:
            value: Desired velocity (rad/s or m/s).

        Example::

            robot.joints["wheel"].set_velocity(10.0)
        """
        if not self._check_connected():
            return
        effective = (
            self._pin_value
            if self._pinned and self._pin_mode == "velocity"
            else float(value)
        )
        self._control_mode = p.VELOCITY_CONTROL
        p.setJointMotorControl2(
            self._body_id,
            self._index,
            controlMode=p.VELOCITY_CONTROL,
            targetVelocity=effective,
            force=self._max_force,
            physicsClientId=self._sim.client_id,
        )

    def set_torque(self, value: float) -> None:
        """Programmatic torque control — respects any active console pin.

        If the joint has been pinned via ``joint.torque = X``, the *pinned*
        value is applied instead of *value*.  Use :meth:`unpin` to release.

        Args:
            value: Desired torque (N·m or N).

        Example::

            robot.joints["hip"].set_torque(20.0)
        """
        if not self._check_connected():
            return
        effective = (
            self._pin_value
            if self._pinned and self._pin_mode == "torque"
            else float(value)
        )
        self._control_mode = p.TORQUE_CONTROL
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
            force=effective,
            physicsClientId=self._sim.client_id,
        )

    # ------------------------------------------------------------------
    # Target (slider-readable value)
    # ------------------------------------------------------------------

    @property
    def target(self) -> float:
        """The live target value for this joint, shared with sliders.

        Sliders read and write this value.  The property setters
        (``joint.position = X``, etc.) also update it so that sliders
        visually follow console commands.

        Example::

            j.target = 0.5   # move slider without immediate PyBullet call
            print(j.target)  # read what the slider is currently set to
        """
        if self._pinned:
            return self._pin_value
        return self._target

    @target.setter
    def target(self, value: float) -> None:
        """Update the target value (slider write path — no immediate PyBullet call)."""
        if self._pinned:
            return  # Locked! Prevents slider from drifting, causes "snap back"
        self._target = float(value)

    # ------------------------------------------------------------------
    # Pin control
    # ------------------------------------------------------------------

    @property
    def unpin(self) -> _UnpinCommand:
        """Release the console/manual pin.  Returns the joint name.

        Supports both method call ``j.unpin()`` in scripts, and property
        access ``j.unpin`` in the interactive console.

        After calling this, :meth:`set_position` / :meth:`set_velocity` /
        :meth:`set_torque` will use the caller's argument again, and the
        slider unlocks.

        Example (in the BulletLab console)::

            robot.joints["left_knee_joint"].unpin
            # Unpin all:
            [j.unpin() for j in robot.controllable_joints]
        """
        return _UnpinCommand(self)

    @property
    def is_pinned(self) -> bool:
        """``True`` if this joint is currently locked by :attr:`pin_position`,
        :attr:`pin_velocity`, or :attr:`pin_torque`.

        Example::

            if robot.joints["elbow"].is_pinned:
                print("elbow locked — call .unpin() to release")
        """
        return self._pinned

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
