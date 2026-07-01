"""
Example 07: BulletLab Arsenal — Direct Loading Demo
=====================================================
Loads the BLem1 rover directly from the BulletLab Arsenal registry into a
temporary session cache.  No installation or manual download is required —
the URDF and meshes are fetched on-the-fly and cleaned up on exit.

After loading, the full BulletLabUI opens with:
  - A joystick panel to drive the rover with all four wheel pairs
  - Live telemetry (position, speed, orientation)
  - Camera follow in smooth mode
  - Joint / link hover highlighting

Internet access is required on the first run to fetch assets from the registry.

Run::

    python examples/07_arsenal_loading.py
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bulletlab import Simulation, Robot, CameraFollow, RobotHighlighter
from bulletlab.core.world import World
from bulletlab.telemetry import TelemetryManager


def main() -> None:
    print("=" * 60)
    print("BulletLab Arsenal — BLem1 Rover")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 1. Simulation
    # ------------------------------------------------------------------
    sim = Simulation(mode="gui", gravity=(0, 0, -9.81), timestep=1.0 / 240.0)
    sim.start()
    sim.set_camera(distance=3.5, yaw=45.0, pitch=-25.0, target=(0, 0, 0.3))

    # ------------------------------------------------------------------
    # 2. World
    # ------------------------------------------------------------------
    world = World(sim)
    world.load_plane()

    # ------------------------------------------------------------------
    # 3. Load BLem1 directly from Arsenal (session cache, no install)
    # ------------------------------------------------------------------
    print("\nFetching 'reference_bot/BLem1' from Arsenal registry...")
    robot = Robot.load(
        "arsenal:reference_bot/BLem1",
        sim=sim,
        position=(0, 0, 0.3),
        name="BLem1",
    )
    print(f"Loaded: {robot}")
    print(f"  Joints: {list(robot.joints.keys())}")
    print()

    # ------------------------------------------------------------------
    # 4. Camera follow
    # ------------------------------------------------------------------
    cam = CameraFollow(
        robot, sim,
        mode="smooth",
        distance=3.5,
        pitch=-25.0,
        yaw=45.0,
        lerp=0.06,
        height_offset=0.3,
    )

    # ------------------------------------------------------------------
    # 5. Hover highlighting
    # ------------------------------------------------------------------
    hl = RobotHighlighter(robot, sim)

    # ------------------------------------------------------------------
    # 6. Telemetry
    # ------------------------------------------------------------------
    telemetry = TelemetryManager()
    telemetry.watch("x",     lambda: robot.base_position[0], unit="m")
    telemetry.watch("y",     lambda: robot.base_position[1], unit="m")
    telemetry.watch("z",     lambda: robot.base_position[2], unit="m")
    telemetry.watch("speed", lambda: robot.speed,            unit="m/s")
    telemetry.watch("roll",  lambda: math.degrees(robot.roll),  unit="°")
    telemetry.watch("pitch", lambda: math.degrees(robot.pitch), unit="°")
    telemetry.watch("yaw",   lambda: math.degrees(robot.yaw),   unit="°")

    # ------------------------------------------------------------------
    # 7. Identify wheel joints
    # BLem1 wheels: rear_right_wheel, front_right_wheel,
    #               rear_left_wheel,  front_left_wheel
    # Left-side wheels spin one direction; right-side the other for steering.
    # ------------------------------------------------------------------
    left_wheels  = [j for name, j in robot.joints.items() if "left_wheel"  in name]
    right_wheels = [j for name, j in robot.joints.items() if "right_wheel" in name]

    # Fallback: use all wheel joints if naming differs
    if not left_wheels or not right_wheels:
        all_wheels = [j for name, j in robot.joints.items() if "wheel" in name]
        half = len(all_wheels) // 2
        left_wheels  = all_wheels[:half]
        right_wheels = all_wheels[half:]

    for j in left_wheels + right_wheels:
        j.max_force = 150.0

    print(f"  Left  wheels: {[j.name for j in left_wheels]}")
    print(f"  Right wheels: {[j.name for j in right_wheels]}")
    print()

    # ------------------------------------------------------------------
    # 8. UI
    # ------------------------------------------------------------------
    ui = None
    manual_vel = [0.0, 0.0]    # [left_vel, right_vel]

    try:
        from bulletlab.ui import BulletLabUI
        from bulletlab.ui import widgets as ui_widgets
        import imgui

        ui = BulletLabUI(
            sim=sim,
            robots=[robot],
            telemetry=telemetry,
            camera=cam,
            highlighter=hl,
        )
        ui.start()

        snap_on = [True]

        def on_joy_y(v: float) -> None:
            """Forward (+) / backward (-)."""
            spd = v * 12.0
            manual_vel[0] += spd
            manual_vel[1] += spd

        def on_joy_x(v: float) -> None:
            """Steer right (+) / left (-)."""
            turn = v * 6.0
            manual_vel[0] += turn
            manual_vel[1] -= turn

        @ui.custom_panel("Drive — BLem1")
        def drive_panel() -> None:
            # Reset each frame so callbacks accumulate cleanly
            manual_vel[0] = 0.0
            manual_vel[1] = 0.0

            ui_widgets.toggle_switch(
                "Snap joystick to zero",
                getter=lambda: snap_on[0],
                setter=lambda v: snap_on.__setitem__(0, v),
                color_on=(0.2, 0.9, 0.4, 1.0),
            )
            imgui.separator()
            ui_widgets.joystick(
                "BLem1 Drive",
                on_y=on_joy_y,
                on_x=on_joy_x,
                snap=snap_on[0],
                size=80,
                handle_color=(0.2, 0.75, 1.0, 1.0),
            )
            imgui.separator()
            ui_widgets.text("Left  vel", f"{manual_vel[0]:+.1f} rad/s")
            ui_widgets.text("Right vel", f"{manual_vel[1]:+.1f} rad/s")

        # Leg controls — continuous revolute joints, no position limits
        leg_joints = [j for name, j in robot.joints.items() if "leg" in name]

        if leg_joints:
            leg_vel = [0.0]

            @ui.custom_panel("Legs")
            def legs_panel() -> None:
                changed, v = imgui.slider_float(
                    "Leg fold speed", leg_vel[0], -3.0, 3.0
                )
                if changed:
                    leg_vel[0] = v
                for j in leg_joints:
                    j.velocity = leg_vel[0]

        print("BulletLab UI opened.\n")
    except Exception as exc:
        print(f"UI not available ({exc}). Running headless.\n")

    # ------------------------------------------------------------------
    # 9. Simulation loop
    # ------------------------------------------------------------------
    print("Running simulation. Close the UI window or press Ctrl+C to stop.\n")

    try:
        while sim.is_connected:
            # Apply wheel velocities (updated by joystick callbacks)
            for j in left_wheels:
                j.velocity = manual_vel[0]
            for j in right_wheels:
                j.velocity = manual_vel[1]

            sim.step()
            telemetry.update(t=sim.elapsed_time)
            cam.update()

            if ui is not None:
                ui.step()
                if ui.should_close:
                    break

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        if ui is not None:
            ui.stop()
        sim.stop()
        print("Done. Session cache cleaned up automatically.")


if __name__ == "__main__":
    main()
