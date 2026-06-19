"""
Simulation – the central controller for a BulletLab physics session.

The Simulation class manages the PyBullet physics server connection, controls
the simulation time step, gravity, stepping, pausing, and tracks all robots
loaded into the scene.

Example::

    from bulletlab import Simulation

    sim = Simulation()
    sim.start()                # connects to PyBullet GUI
    sim.gravity = (0, 0, -9.81)
    sim.timestep = 1.0 / 240.0

    while True:
        sim.step()

    sim.stop()
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Optional

import pybullet as p
import pybullet_data

from bulletlab.utils.silencer import SuppressOutput

if TYPE_CHECKING:
    from bulletlab.robot.robot import Robot


class Simulation:
    """Central controller for a BulletLab physics simulation session.

    Wraps the PyBullet physics server and provides a high-level interface
    for connecting, stepping, pausing, resetting, and configuring the
    simulation environment.

    Args:
        mode: PyBullet connection mode. Use ``"gui"`` for an interactive
            window or ``"direct"`` for headless (testing/RL) mode.
        gravity: Initial gravity vector as ``(gx, gy, gz)``.
            Defaults to ``(0, 0, -9.81)``.
        timestep: Physics timestep in seconds. Defaults to ``1/240``.
        real_time: If ``True``, enable real-time simulation in GUI mode.

    Example::

        sim = Simulation(mode="gui")
        sim.start()
        sim.gravity = (0, 0, -9.81)

        for _ in range(1000):
            sim.step()

        sim.stop()
    """

    GUI = p.GUI
    DIRECT = p.DIRECT

    def __init__(
        self,
        mode: str = "gui",
        gravity: tuple[float, float, float] = (0.0, 0.0, -9.81),
        timestep: float = 1.0 / 240.0,
        real_time: bool = False,
        hide_gui: bool = True,
    ) -> None:
        self._mode_str = mode.lower()
        self._mode = p.GUI if self._mode_str == "gui" else p.DIRECT
        self._gravity = gravity
        self._timestep = timestep
        self._real_time = real_time
        self._hide_gui = hide_gui
        self._client_id: int = -1
        self._paused: bool = False
        self._step_count: int = 0
        self._robots: list["Robot"] = []
        self._connected: bool = False

    @property
    def is_connected(self) -> bool:
        """``True`` if connected to the PyBullet physics server and the window is open."""
        if not self._connected or self._client_id < 0:
            return False
        try:
            info = p.getConnectionInfo(physicsClientId=self._client_id)
            connected = info.get("isConnected", 0) == 1
            if not connected:
                self._connected = False
            return connected
        except Exception:  # includes pybullet.error
            self._connected = False
            return False

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def start(self) -> "Simulation":
        """Connect to the PyBullet server and configure the environment.

        Returns:
            self, for method chaining.

        Example::

            sim = Simulation().start()
        """
        if self.is_connected:
            return self

        with SuppressOutput():
            self._client_id = p.connect(self._mode)
            p.setAdditionalSearchPath(pybullet_data.getDataPath(), physicsClientId=self._client_id)
            p.setGravity(*self._gravity, physicsClientId=self._client_id)
            p.setTimeStep(self._timestep, physicsClientId=self._client_id)

        if self._mode == p.GUI:
            if self._hide_gui:
                # Remove all PyBullet built-in sidebar panels, sliders,
                # and debug widgets. BulletLab provides its own ImGui UI.
                p.configureDebugVisualizer(
                    p.COV_ENABLE_GUI, 0, physicsClientId=self._client_id
                )
            if self._real_time:
                p.setRealTimeSimulation(1, physicsClientId=self._client_id)

        self._connected = True
        return self


    def stop(self) -> None:
        """Disconnect from the PyBullet server.

        Example::

            sim.stop()
        """
        if self._connected:
            try:
                with SuppressOutput():
                    p.disconnect(physicsClientId=self._client_id)
            except Exception:
                pass
            self._connected = False
            self._client_id = -1

    # Alias for stop()
    disconnect = stop

    def reset(self) -> None:
        """Reset the simulation to a clean state.

        Removes all objects from the world, resets the step counter,
        and reloads the data search path. Robot references in
        ``self.robots`` are cleared.

        Example::

            sim.reset()
        """
        if not self.is_connected:
            return
        p.resetSimulation(physicsClientId=self._client_id)
        p.setAdditionalSearchPath(pybullet_data.getDataPath(), physicsClientId=self._client_id)
        p.setGravity(*self._gravity, physicsClientId=self._client_id)
        p.setTimeStep(self._timestep, physicsClientId=self._client_id)
        self._robots.clear()
        self._step_count = 0
        self._paused = False

    # ------------------------------------------------------------------
    # Stepping
    # ------------------------------------------------------------------

    def step(self) -> None:
        """Advance the simulation by one timestep.

        Does nothing if the simulation is paused or not connected.

        Example::

            for _ in range(1000):
                sim.step()
        """
        if not self.is_connected or self._paused:
            return
        try:
            p.stepSimulation(physicsClientId=self._client_id)
            self._step_count += 1
        except Exception:
            # Physics server closed externally (e.g. user closed the PyBullet window)
            self._connected = False

    def pause(self) -> None:
        """Pause the simulation. Calls to :meth:`step` are no-ops while paused.

        Example::

            sim.pause()
        """
        self._paused = True

    def resume(self) -> None:
        """Resume a paused simulation.

        Example::

            sim.resume()
        """
        self._paused = False

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def gravity(self) -> tuple[float, float, float]:
        """Gravity vector ``(gx, gy, gz)`` in m/s².

        Example::

            sim.gravity = (0, 0, -9.81)   # Earth gravity
            sim.gravity = (0, 0, -1.62)   # Moon gravity
        """
        return self._gravity

    @gravity.setter
    def gravity(self, value: tuple[float, float, float]) -> None:
        self._gravity = tuple(float(v) for v in value)  # type: ignore[assignment]
        if self._connected:
            p.setGravity(*self._gravity, physicsClientId=self._client_id)

    @property
    def timestep(self) -> float:
        """Physics timestep in seconds.

        Example::

            sim.timestep = 1.0 / 480.0   # higher resolution
        """
        return self._timestep

    @timestep.setter
    def timestep(self, value: float) -> None:
        self._timestep = float(value)
        if self._connected:
            p.setTimeStep(self._timestep, physicsClientId=self._client_id)

    @property
    def is_paused(self) -> bool:
        """``True`` if the simulation is currently paused."""
        return self._paused

    @property
    def is_connected(self) -> bool:
        """``True`` if connected to a PyBullet physics server."""
        return self._connected

    @property
    def client_id(self) -> int:
        """The PyBullet physics server client ID.

        This is an internal identifier. Most users should not need it.
        """
        return self._client_id

    @property
    def step_count(self) -> int:
        """Total number of simulation steps taken since last reset."""
        return self._step_count

    @property
    def elapsed_time(self) -> float:
        """Simulated time elapsed in seconds since last reset."""
        return self._step_count * self._timestep

    @property
    def robots(self) -> list["Robot"]:
        """List of all robots currently registered in this simulation."""
        return list(self._robots)

    # ------------------------------------------------------------------
    # Robot management
    # ------------------------------------------------------------------

    def add_robot(self, robot: "Robot") -> None:
        """Register a robot with this simulation.

        This is called automatically by :meth:`Robot.load` when ``sim`` is
        provided, so you rarely need to call this directly.

        Args:
            robot: A :class:`~bulletlab.robot.robot.Robot` instance.

        Example::

            sim.add_robot(robot)
        """
        if robot not in self._robots:
            self._robots.append(robot)

    def remove_robot(self, robot: "Robot") -> None:
        """Unregister a robot from this simulation.

        Args:
            robot: The robot to remove.
        """
        if robot in self._robots:
            self._robots.remove(robot)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def add_debug_text(
        self,
        text: str,
        position: tuple[float, float, float],
        color: tuple[float, float, float] = (1.0, 1.0, 1.0),
        size: float = 1.5,
    ) -> int:
        """Add a text label to the PyBullet debug visualizer.

        Args:
            text: Text to display.
            position: 3D world position ``(x, y, z)``.
            color: RGB color normalized to [0, 1].
            size: Text size multiplier.

        Returns:
            Debug item ID (can be used to remove later).
        """
        if not self._connected:
            return -1
        return p.addUserDebugText(
            text,
            list(position),
            textColorRGB=list(color),
            textSize=size,
            physicsClientId=self._client_id,
        )

    def remove_debug_item(self, item_id: int) -> None:
        """Remove a debug visualizer item by ID.

        Args:
            item_id: ID returned by :meth:`add_debug_text` or similar.
        """
        if self._connected:
            p.removeUserDebugItem(item_id, physicsClientId=self._client_id)

    def set_camera(
        self,
        distance: float = 3.0,
        yaw: float = 50.0,
        pitch: float = -35.0,
        target: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> None:
        """Set the PyBullet debug camera position.

        Args:
            distance: Camera distance from target.
            yaw: Camera yaw angle in degrees.
            pitch: Camera pitch angle in degrees.
            target: Camera target position ``(x, y, z)``.
        """
        if self._connected and self._mode == p.GUI:
            p.resetDebugVisualizerCamera(
                cameraDistance=distance,
                cameraYaw=yaw,
                cameraPitch=pitch,
                cameraTargetPosition=list(target),
                physicsClientId=self._client_id,
            )

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "Simulation":
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()

    def __repr__(self) -> str:
        status = "connected" if self._connected else "disconnected"
        return (
            f"Simulation(mode={self._mode_str!r}, {status}, "
            f"step={self._step_count}, t={self.elapsed_time:.3f}s)"
        )
