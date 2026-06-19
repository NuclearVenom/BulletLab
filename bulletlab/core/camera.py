"""
CameraFollow – robot-tracking camera controller for BulletLab.

Attaches a virtual camera to a robot and keeps it centred in the
PyBullet 3D window every simulation step.  Three tracking modes are
supported:

* ``SNAP``   – target locks to the robot instantly (no lag).
* ``SMOOTH`` – target glides toward the robot with configurable lerp
               speed (cinematic, good for fast-moving robots).
* ``CHASE``  – always stays behind the robot; the camera yaw rotates
               with the robot's heading (3rd-person game camera).

One-liner usage::

    cam = CameraFollow(robot, sim)
    # or with options:
    cam = CameraFollow(robot, sim, mode="smooth", distance=5.0, lerp=0.1)

In your loop::

    while sim.is_connected:
        sim.step()
        cam.update()           # ← one call, camera follows robot

Developed by Ranasurya Ghosh – https://github.com/NuclearVenom/BulletLab
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bulletlab.core.simulation import Simulation
    from bulletlab.robot.robot import Robot


class CameraFollow:
    """Robot-tracking camera controller.

    Wraps ``sim.set_camera()`` and updates the PyBullet debug camera every
    time :meth:`update` is called — typically once per simulation step.

    Args:
        robot: The robot to follow.
        sim: The :class:`~bulletlab.core.simulation.Simulation` instance.
        mode: Tracking mode – ``"snap"``, ``"smooth"``, or ``"chase"``.
        distance: Camera distance from the robot in metres. Default ``4.0``.
        pitch: Camera pitch angle in degrees (negative = looking down).
              Default ``-25.0``.
        yaw: Initial yaw angle in degrees.  Only used in ``snap`` and
             ``smooth`` modes (in ``chase`` mode yaw is automatic).
             Default ``45.0``.
        lerp: Lerp factor used in ``smooth`` mode – fraction of the
              remaining gap closed per step (0 < lerp ≤ 1).  Default
              ``0.08`` (≈ 8 % per step ≈ ~2 s settling at 240 Hz).
        height_offset: Extra height added to the camera target above the
                       robot's base position (metres). Default ``0.2``.

    Modes:
        * ``"snap"``   – target snaps to the robot instantly each step.
        * ``"smooth"`` – target slides toward the robot using *lerp*.
        * ``"chase"``  – camera yaw tracks the robot's heading so the
                         camera always looks at the robot from behind.

    Example::

        from bulletlab import Simulation, Robot
        from bulletlab.core.camera import CameraFollow

        sim = Simulation(mode="gui").start()
        robot = Robot.load("husky/husky.urdf", sim=sim)

        # One-liner: camera that smoothly follows the robot
        cam = CameraFollow(robot, sim, mode="smooth")

        while sim.is_connected:
            sim.step()
            cam.update()
    """

    SNAP   = "snap"
    SMOOTH = "smooth"
    CHASE  = "chase"

    _VALID_MODES = {SNAP, SMOOTH, CHASE}

    def __init__(
        self,
        robot: "Robot",
        sim: "Simulation",
        *,
        mode: str = "smooth",
        distance: float = 4.0,
        pitch: float = -25.0,
        yaw: float = 45.0,
        lerp: float = 0.08,
        height_offset: float = 0.2,
    ) -> None:
        mode = mode.lower()
        if mode not in self._VALID_MODES:
            raise ValueError(
                f"Unknown camera mode {mode!r}. "
                f"Choose from: {sorted(self._VALID_MODES)}"
            )

        self._robot   = robot
        self._sim     = sim
        self._mode    = mode
        self._dist    = float(distance)
        self._pitch   = float(pitch)
        self._yaw     = float(yaw)
        self._lerp    = float(max(1e-4, min(1.0, lerp)))
        self._h_off   = float(height_offset)
        self._enabled = True   # toggle on/off without destroying the object

        # Smoothed target (initialised to robot spawn position)
        pos = robot.base_position
        self._target  = [pos[0], pos[1], pos[2] + self._h_off]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self) -> None:
        """Update the camera for the current simulation frame.

        Call once per simulation step in your main loop.  When
        :attr:`enabled` is ``False`` the call is a no-op and the camera
        stays fixed at its last position.

        Example::

            while sim.is_connected:
                sim.step()
                cam.update()
        """
        if not self._enabled:
            return
        pos = self._robot.base_position

        if self._mode == self.SNAP:
            self._update_snap(pos)
        elif self._mode == self.SMOOTH:
            self._update_smooth(pos)
        elif self._mode == self.CHASE:
            self._update_chase(pos)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def enabled(self) -> bool:
        """Whether the camera follow is active.

        Set to ``False`` to freeze the camera at its current position.
        Set to ``True`` to resume tracking.

        Example::

            cam.enabled = False   # freeze
            cam.enabled = True    # resume
        """
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = bool(value)

    @property
    def mode(self) -> str:
        """Current tracking mode (``"snap"``, ``"smooth"``, or ``"chase"``)."""
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        value = value.lower()
        if value not in self._VALID_MODES:
            raise ValueError(f"Unknown mode {value!r}.")
        self._mode = value

    @property
    def distance(self) -> float:
        """Camera distance from the robot in metres."""
        return self._dist

    @distance.setter
    def distance(self, value: float) -> None:
        self._dist = float(value)

    @property
    def pitch(self) -> float:
        """Camera pitch in degrees."""
        return self._pitch

    @pitch.setter
    def pitch(self, value: float) -> None:
        self._pitch = float(value)

    @property
    def yaw(self) -> float:
        """Camera yaw in degrees (snap/smooth modes only)."""
        return self._yaw

    @yaw.setter
    def yaw(self, value: float) -> None:
        self._yaw = float(value)

    @property
    def lerp(self) -> float:
        """Lerp factor used in smooth mode (0 < lerp ≤ 1)."""
        return self._lerp

    @lerp.setter
    def lerp(self, value: float) -> None:
        self._lerp = float(max(1e-4, min(1.0, value)))

    # ------------------------------------------------------------------
    # Internal per-mode updaters
    # ------------------------------------------------------------------

    def _update_snap(self, pos: tuple) -> None:
        """Snap: target locks instantly to robot position."""
        target = (pos[0], pos[1], pos[2] + self._h_off)
        self._sim.set_camera(
            distance=self._dist,
            yaw=self._yaw,
            pitch=self._pitch,
            target=target,
        )
        self._target = list(target)

    def _update_smooth(self, pos: tuple) -> None:
        """Smooth: lerp camera target toward robot each frame."""
        lp = self._lerp
        self._target[0] += (pos[0]                  - self._target[0]) * lp
        self._target[1] += (pos[1]                  - self._target[1]) * lp
        self._target[2] += (pos[2] + self._h_off    - self._target[2]) * lp
        self._sim.set_camera(
            distance=self._dist,
            yaw=self._yaw,
            pitch=self._pitch,
            target=tuple(self._target),
        )

    def _update_chase(self, pos: tuple) -> None:
        """Chase: camera yaw mirrors the robot's heading (always behind)."""
        heading_deg = math.degrees(self._robot.yaw)
        # Place camera 180° behind the robot's current heading
        chase_yaw = heading_deg + 180.0

        lp = self._lerp
        self._target[0] += (pos[0]                  - self._target[0]) * lp
        self._target[1] += (pos[1]                  - self._target[1]) * lp
        self._target[2] += (pos[2] + self._h_off    - self._target[2]) * lp

        self._sim.set_camera(
            distance=self._dist,
            yaw=chase_yaw,
            pitch=self._pitch,
            target=tuple(self._target),
        )

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"CameraFollow(robot={self._robot.name!r}, mode={self._mode!r}, "
            f"dist={self._dist}, pitch={self._pitch}°)"
        )
