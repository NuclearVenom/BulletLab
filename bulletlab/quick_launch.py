"""
quickLaunch – one-liner robot inspector for BulletLab.

Spin up a complete simulation + GUI from a single line of Python code::

    import bulletlab
    bulletlab.quickLaunch("r2d2.urdf")

    # Arsenal model
    bulletlab.quickLaunch("arsenal:reference_bot")

    # Absolute / relative local path
    bulletlab.quickLaunch(r"C:/robots/my_arm/arm.urdf")

The function:

* Opens a PyBullet GUI window **only after** the model file is resolved
  (so arsenal downloads never leave an empty white window behind).
* Sets sensible defaults (gravity, timestep, camera, ground plane).
* Loads the robot model (local URDF/MJCF **or** ``arsenal:…`` URI).
* Auto-generates a full BulletLab UI with:
    - Joint Control panel with **Position / Velocity / Torque** mode tabs
      per joint and appropriate slider ranges.
    - Telemetry readouts for position, orientation, speed, and joint angles.
    - Dynamic camera follow with a **capsule toggle switch** (same style as
      example 01) instead of a plain checkbox.
    - The full console panel (interact via code during the session).
* Runs the blocking simulation loop until the window is closed.

Developed by Ranasurya Ghosh – https://github.com/NuclearVenom/BulletLab
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Defaults that feel "good" for a generic inspection session
# ---------------------------------------------------------------------------
_DEFAULT_GRAVITY    = (0.0, 0.0, -9.81)
_DEFAULT_TIMESTEP   = 1.0 / 240.0
_DEFAULT_CAM_DIST   = 2.5
_DEFAULT_CAM_YAW    = 45.0
_DEFAULT_CAM_PITCH  = -20.0
_DEFAULT_CAM_TARGET = (0.0, 0.0, 0.3)
_DEFAULT_SPAWN_POS  = (0.0, 0.0, 0.0)

# Control mode names cycling order
_MODES = ("Position", "Velocity", "Torque")


def quickLaunch(
    path: str,
    *,
    gravity: tuple[float, float, float] = _DEFAULT_GRAVITY,
    timestep: float = _DEFAULT_TIMESTEP,
    spawn_position: tuple[float, float, float] | None = None,
    camera_distance: float = _DEFAULT_CAM_DIST,
    camera_yaw: float = _DEFAULT_CAM_YAW,
    camera_pitch: float = _DEFAULT_CAM_PITCH,
    camera_mode: str = "smooth",
    ground_plane: bool = True,
    realtime: bool = False,
    title: str | None = None,
    max_joints_in_ui: int = 16,
) -> None:
    """Launch an interactive GUI session for any robot model.

    Accepts the same path formats as :func:`~bulletlab.robot.robot.Robot.load`
    — a local file path **or** an Arsenal URI such as
    ``"arsenal:reference_bot"`` / ``"arsenal:reference_bot/BLem1"``.

    Arsenal models are fully downloaded **before** the PyBullet window opens,
    so you never see an empty simulation window during the download.

    Args:
        path: Path to a URDF/MJCF file, or an ``arsenal:…`` URI.
        gravity: Gravity vector ``(gx, gy, gz)`` in m/s².
                 Default: ``(0, 0, -9.81)``.
        timestep: Physics timestep in seconds. Default: ``1/240``.
        spawn_position: Robot spawn position ``(x, y, z)``.
                        Defaults to ``None`` (automatically placed just above the ground plane).
        camera_distance: Initial camera distance from the robot in metres.
        camera_yaw: Initial camera yaw in degrees.
        camera_pitch: Initial camera pitch in degrees (negative = looking down).
        camera_mode: CameraFollow tracking mode: ``"snap"``, ``"smooth"``
                     (default), or ``"chase"``.
        ground_plane: If ``True`` (default), load a flat ground plane.
        realtime: If ``True``, enable PyBullet real-time simulation.
        title: Custom window title. Defaults to the model filename / package.
        max_joints_in_ui: Maximum controllable joints to display sliders for.
                          Default: 16.

    Example::

        import bulletlab

        # From pybullet_data
        bulletlab.quickLaunch("r2d2.urdf")

        # Arsenal model (window opens *after* download completes)
        bulletlab.quickLaunch("arsenal:reference_bot")

        # Absolute local path
        bulletlab.quickLaunch(r"C:\\robots\\my_arm\\arm.urdf")

        # Custom camera
        bulletlab.quickLaunch(
            "arsenal:reference_bot/BLem1",
            camera_distance=3.0,
            camera_mode="chase",
        )

    Raises:
        FileNotFoundError: If the local model file cannot be found.
        bulletlab.ArsenalError: If the Arsenal URI cannot be resolved or downloaded.
        ImportError: If ``imgui-bundle`` / ``glfw`` / ``PyOpenGL`` are not installed
                     (the simulation will still run headless in that case).
    """
    from bulletlab.core.simulation import Simulation
    from bulletlab.core.world import World
    from bulletlab.core.camera import CameraFollow
    from bulletlab.robot.robot import Robot
    from bulletlab.telemetry.manager import TelemetryManager
    from bulletlab.ui import BulletLabUI
    import bulletlab.ui.widgets as ui_widgets

    path_str = str(path).strip()
    pos = spawn_position if spawn_position is not None else _DEFAULT_SPAWN_POS

    # ── Derive a friendly display name ─────────────────────────────────────
    if path_str.startswith("arsenal:"):
        _raw = path_str[len("arsenal:"):]
        display_name = _raw.split("/")[0].replace("_", " ").title()
    else:
        display_name = Path(path_str).stem

    window_title = title or f"BulletLab — {display_name}"

    print(f"\n{'='*60}")
    print(f"  BulletLab quickLaunch")
    print(f"  Model : {path_str}")
    print(f"  Press Ctrl+C or close the window to stop.")
    print(f"{'='*60}\n")

    # ── FIX 1: Pre-resolve arsenal paths BEFORE opening the GUI window ──────
    # For arsenal: URIs, download the model to the local session cache now.
    # This means the PyBullet window only opens once the file is ready,
    # so the user never sees an empty white simulation window.
    resolved_path = path_str
    if path_str.startswith("arsenal:"):
        arsenal_source = path_str[len("arsenal:"):]
        print(f"[quickLaunch] Resolving Arsenal model '{arsenal_source}' …")
        try:
            resolved_path = Robot._load_from_arsenal(arsenal_source)
            print(f"[quickLaunch] Model ready: {resolved_path}\n")
        except Exception as exc:
            print(f"[quickLaunch] ERROR resolving Arsenal model: {exc}", file=sys.stderr)
            raise

    # ── Physics setup (GUI opens here — model already on disk) ─────────────
    sim = Simulation(
        mode="gui",
        gravity=gravity,
        timestep=timestep,
        real_time=realtime,
    )
    sim.start()
    sim.set_camera(
        distance=camera_distance,
        yaw=camera_yaw,
        pitch=camera_pitch,
        target=_DEFAULT_CAM_TARGET,
    )

    if ground_plane:
        world = World(sim)
        world.load_plane()

    # ── Load robot ──────────────────────────────────────────────────────────
    try:
        # Pass resolved_path (already a local .urdf) so Robot.load skips the
        # arsenal download it would otherwise do a second time.
        robot = Robot.load(
            resolved_path,
            sim=sim,
            position=pos,
            name=display_name,
        )
        if spawn_position is None:
            robot.auto_ground(clearance=0.02)
    except Exception as exc:
        print(f"[quickLaunch] ERROR loading model: {exc}", file=sys.stderr)
        sim.stop()
        raise

    _print_robot_summary(robot)

    # ── Telemetry – base pose + joint angles ────────────────────────────────
    telemetry = TelemetryManager()
    telemetry.watch("x",     lambda: robot.base_position[0], unit="m")
    telemetry.watch("y",     lambda: robot.base_position[1], unit="m")
    telemetry.watch("z",     lambda: robot.base_position[2], unit="m")
    telemetry.watch("speed", lambda: robot.speed,             unit="m/s")
    telemetry.watch("roll",  lambda: math.degrees(robot.roll),  unit="°")
    telemetry.watch("pitch", lambda: math.degrees(robot.pitch), unit="°")
    telemetry.watch("yaw",   lambda: math.degrees(robot.yaw),   unit="°")

    for joint in robot.controllable_joints[:max_joints_in_ui]:
        telemetry.watch(
            f"j_{joint.name[:10]}",
            (lambda j: lambda: j.position)(joint),
            unit="rad",
        )

    # ── Dynamic camera follow ────────────────────────────────────────────────
    camera = CameraFollow(
        robot,
        sim,
        mode=camera_mode,
        distance=camera_distance,
        pitch=camera_pitch,
        yaw=camera_yaw,
    )
    # Start disabled — user can toggle it on in the Camera panel
    camera.enabled = False

    # ── UI ───────────────────────────────────────────────────────────────────
    ui: BulletLabUI | None = None
    try:
        ui = BulletLabUI(
            sim=sim,
            robots=[robot],
            telemetry=telemetry,
            camera=camera,
            title=window_title,
        )
        ui.start()

        # ── FIX 2: Joint Control panel with Position / Velocity / Torque ─────
        # Per-joint mode state stored in a dict so the closure captures it.
        # 0 = Position, 1 = Velocity, 2 = Torque
        _joint_modes: dict[str, int] = {
            j.name: 0 for j in robot.controllable_joints[:max_joints_in_ui]
        }

        # Pre-compute reasonable slider ranges for each mode:
        #   Position → joint limits (or [-π, π] if unspecified)
        #   Velocity → [-max_velocity, +max_velocity]
        #   Torque   → [-max_force,    +max_force]
        def _ranges(joint: Any) -> tuple[
            tuple[float, float],   # position range
            tuple[float, float],   # velocity range
            tuple[float, float],   # torque range
        ]:
            lo, hi = joint.limits
            if lo == 0.0 and hi == 0.0:
                lo, hi = -math.pi, math.pi
            max_v = getattr(joint, "_max_velocity", 10.0) or 10.0
            max_f = getattr(joint, "_max_force",    100.0) or 100.0
            return (lo, hi), (-max_v, max_v), (-max_f, max_f)

        @ui.custom_panel("Joint Control")
        def _joint_control_panel() -> None:
            try:
                from imgui_bundle import imgui as _imgui
                _has_imgui = True
            except ImportError:
                _has_imgui = False

            ctrl_joints = robot.controllable_joints[:max_joints_in_ui]
            if not ctrl_joints:
                ui_widgets.text("Info", "No controllable joints found.")
                return

            ui_widgets.text("Robot",  robot.name)
            ui_widgets.text("Joints", f"{len(robot.controllable_joints)} controllable")

            for joint in ctrl_joints:
                jname = joint.name
                mode_idx = _joint_modes.get(jname, 0)
                pos_range, vel_range, tor_range = _ranges(joint)

                # ── Section header with joint name ─────────────────────────
                if _has_imgui:
                    _imgui.spacing()
                    _imgui.separator()
                    _imgui.text(f"  {jname[:28]}")
                    _imgui.same_line(0, 12)

                    # ── Mode selector: three small radio-style buttons ─────
                    for i, mode_label in enumerate(_MODES):
                        is_active = (mode_idx == i)
                        if is_active:
                            _imgui.push_style_color(
                                _imgui.Col_.button,
                                _imgui.ImVec4(0.20, 0.50, 0.80, 1.0)
                            )
                            _imgui.push_style_color(
                                _imgui.Col_.button_hovered,
                                _imgui.ImVec4(0.25, 0.60, 0.95, 1.0)
                            )
                        btn_label = f"{mode_label}##{jname}"
                        if _imgui.button(btn_label, _imgui.ImVec2(66, 18)):
                            _joint_modes[jname] = i
                            mode_idx = i
                        if is_active:
                            _imgui.pop_style_color(2)
                        if i < len(_MODES) - 1:
                            _imgui.same_line(0, 3)
                else:
                    # Fallback — no imgui available
                    pass

                # ── Slider for the active mode ─────────────────────────────
                if mode_idx == 0:  # Position
                    lo, hi = pos_range
                    ui_widgets.slider(
                        f"pos##{jname}",
                        getter=lambda j=joint: j.position,
                        min_val=lo,
                        max_val=hi,
                        setter=lambda v, j=joint: j.set_position(v),
                    )
                elif mode_idx == 1:  # Velocity
                    lo, hi = vel_range
                    ui_widgets.slider(
                        f"vel##{jname}",
                        getter=lambda j=joint: j.velocity,
                        min_val=lo,
                        max_val=hi,
                        setter=lambda v, j=joint: setattr(j, "velocity", v),
                    )
                else:  # Torque
                    lo, hi = tor_range
                    ui_widgets.slider(
                        f"tor##{jname}",
                        getter=lambda j=joint: j.torque,
                        min_val=lo,
                        max_val=hi,
                        setter=lambda v, j=joint: setattr(j, "torque", v),
                    )

        print(f"[quickLaunch] UI window opened: '{window_title}'")
        print("[quickLaunch] Camera panel: use the toggle switch to enable dynamic follow.\n")

    except ImportError as exc:
        print(
            f"[quickLaunch] UI unavailable — running headless.\n"
            f"  Install: pip install imgui-bundle glfw PyOpenGL\n"
            f"  Error  : {exc}",
            file=sys.stderr,
        )
        ui = None

    # ── Main loop ────────────────────────────────────────────────────────────
    step_count = 0
    try:
        while sim.is_connected:
            sim.step()
            telemetry.update(t=sim.elapsed_time)

            # Dynamic camera update (only when enabled)
            if camera.enabled:
                camera.update()

            if ui is not None:
                ui.step()
                if ui.should_close:
                    break

            step_count += 1
            # Periodic console status (every 5 simulated seconds at 240 Hz)
            if step_count % 1200 == 0:
                snap = telemetry.snapshot()
                px, py, pz = snap.get("x", 0), snap.get("y", 0), snap.get("z", 0)
                spd = snap.get("speed", 0)
                print(
                    f"  t={sim.elapsed_time:.1f}s | "
                    f"pos=({px:.2f}, {py:.2f}, {pz:.2f}) | "
                    f"speed={spd:.3f} m/s"
                )

    except KeyboardInterrupt:
        print("\n[quickLaunch] Interrupted by user.")
    finally:
        if ui is not None:
            ui.stop()
        sim.stop()
        print(
            f"\n[quickLaunch] Session ended. "
            f"Ran {step_count} steps "
            f"({sim.elapsed_time:.2f}s simulated time)."
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_robot_summary(robot: Any) -> None:
    """Print a short summary of the loaded robot to the console."""
    print(f"  Robot     : {robot.name}")
    print(f"  Joints    : {len(robot.joints)} total, "
          f"{len(robot.controllable_joints)} controllable")
    print(f"  Links     : {len(robot.links)}")
    print(f"  State dim : {len(robot.get_state())}")
    if robot.controllable_joints:
        names = ", ".join(j.name for j in robot.controllable_joints[:6])
        suffix = " …" if len(robot.controllable_joints) > 6 else ""
        print(f"  Controls  : {names}{suffix}")
    print()
