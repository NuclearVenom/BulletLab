"""
Example 01: Differential Drive Rover
=====================================
Demonstrates basic wheel velocity control using the Husky robot from pybullet_data.

What this shows:
- Loading a robot by name using pybullet_data
- Setting joint velocities by name
- Smooth camera that follows the robot (CameraFollow)
- Joint/link highlighting on hover (RobotHighlighter)
- Monitoring base telemetry (position, speed, roll)
- Logging data to CSV
- Autopilot toggle with manual joystick override
- BulletLabUI joystick widget for gamepad-style control

Run::

    python examples/01_differential_drive_rover.py
"""

import math
import time
import sys
from pathlib import Path

# Ensure bulletlab is importable from the repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from bulletlab import Simulation, Robot, CameraFollow, RobotHighlighter
from bulletlab.core.world import World
from bulletlab.telemetry import TelemetryManager
from bulletlab.logging import DataLogger
from bulletlab.utils.urdf_utils import find_urdf


def main() -> None:
    print("=== BulletLab Example 01: Differential Drive Rover ===\n")

    # ──────────────────────────────────────────────
    # 1. Create simulation
    # ──────────────────────────────────────────────
    sim = Simulation(mode="gui", gravity=(0, 0, -9.81), timestep=1.0 / 240.0)
    sim.start()
    # Initial camera — CameraFollow will take over once the robot is loaded
    sim.set_camera(distance=4.0, yaw=50.0, pitch=-30.0, target=(0, 0, 0.5))

    # ──────────────────────────────────────────────
    # 2. Build world
    # ──────────────────────────────────────────────
    world = World(sim)
    world.load_plane()

    # ──────────────────────────────────────────────
    # 3. Load robot
    # ──────────────────────────────────────────────
    # husky.urdf is bundled with pybullet_data
    try:
        urdf_path = find_urdf("husky/husky.urdf")
    except FileNotFoundError:
        # Fallback: use racecar
        try:
            urdf_path = find_urdf("racecar/racecar.urdf")
        except FileNotFoundError:
            print("Could not find husky or racecar URDF. Trying r2d2...")
            urdf_path = find_urdf("r2d2.urdf")

    robot = Robot.load(str(urdf_path), sim=sim, position=(0, 0, 0.3), name="Rover")
    print(f"Loaded robot: {robot}")
    print(f"  Joints:  {list(robot.joints.keys())[:6]}{'...' if len(robot.joints) > 6 else ''}")
    print(f"  Links:   {list(robot.links.keys())[:6]}{'...' if len(robot.links) > 6 else ''}")
    print(f"  State dim: {len(robot.get_state())}\n")

    # ──────────────────────────────────────────────
    # 4. Smooth camera follow
    # ──────────────────────────────────────────────
    cam = CameraFollow(
        robot, sim,
        mode="smooth",
        distance=4.0,
        pitch=-30.0,
        yaw=50.0,
        lerp=0.06,        # gentle glide — lower = slower/smoother
        height_offset=0.3,
    )

    # ──────────────────────────────────────────────
    # 5. Joint / link hover highlighting
    # ──────────────────────────────────────────────
    hl = RobotHighlighter(robot, sim)

    # ──────────────────────────────────────────────
    # 6. Set up telemetry
    # ──────────────────────────────────────────────
    telemetry = TelemetryManager()
    telemetry.watch("x",       lambda: robot.base_position[0], unit="m")
    telemetry.watch("y",       lambda: robot.base_position[1], unit="m")
    telemetry.watch("z",       lambda: robot.base_position[2], unit="m")
    telemetry.watch("speed",   lambda: robot.speed,            unit="m/s")
    telemetry.watch("roll",    lambda: math.degrees(robot.roll),  unit="°")
    telemetry.watch("pitch",   lambda: math.degrees(robot.pitch), unit="°")

    # ──────────────────────────────────────────────
    # 7. Set up data logger
    # ──────────────────────────────────────────────
    logger = DataLogger()
    logger.watch("speed",   lambda: robot.speed)
    logger.watch("x",       lambda: robot.base_position[0])
    logger.watch("y",       lambda: robot.base_position[1])
    logger.watch("roll",    lambda: math.degrees(robot.roll))
    logger.start("rover_run.csv")
    print("Logging to: rover_run.csv\n")

    # ──────────────────────────────────────────────
    # 8. Try to launch UI (optional)
    # ──────────────────────────────────────────────
    ui = None
    try:
        from bulletlab.ui import BulletLabUI
        from bulletlab.ui import widgets as ui_widgets
        import imgui

        ui = BulletLabUI(sim=sim, robots=[robot], telemetry=telemetry, camera=cam, highlighter=hl)
        ui.start()

        # ── Shared state (mutable containers so lambdas can write to them) ──
        autopilot_on   = [True]   # Autopilot active by default
        joystick_snap  = [True]   # Snap-to-center on release

        # Store current manual velocities so the joystick callbacks can
        # write them from inside the UI frame without a direct joint reference.
        manual_vel     = [0.0, 0.0]   # [left_side_vel, right_side_vel]

        def on_joy_y(v):
            """Y axis: +1 = forward, -1 = backward."""
            spd = v * 10.0
            manual_vel[0] += spd   # additive so X-axis turn is preserved
            manual_vel[1] += spd

        def on_joy_x(v):
            """X axis: +1 = turn right, -1 = turn left."""
            turn = v * 5.0
            manual_vel[0] += turn   # left wheels speed up → turns right
            manual_vel[1] -= turn   # right wheels slow down → turns right

        @ui.custom_panel("Drive")
        def drive_panel() -> None:
            # ── Autopilot toggle switch ───────────────────────────────────────
            prev = autopilot_on[0]
            ui_widgets.toggle_switch(
                "Autopilot",
                getter=lambda: autopilot_on[0],
                setter=lambda v: autopilot_on.__setitem__(0, v),
                color_on=(0.2, 0.75, 1.0, 1.0),
            )
            # When switching back ON, zero manual velocity so robot stops
            if not prev and autopilot_on[0]:
                manual_vel[0] = 0.0
                manual_vel[1] = 0.0

            imgui.separator()

            # ── Manual controls (grayed out when autopilot is ON) ────────────
            if autopilot_on[0]:
                imgui.push_style_var(imgui.STYLE_ALPHA, 0.35)

            # Snap toggle switch
            ui_widgets.toggle_switch(
                "Snap joystick to zero",
                getter=lambda: joystick_snap[0],
                setter=lambda v: (None if autopilot_on[0]
                                  else joystick_snap.__setitem__(0, v)),
                color_on=(0.2, 0.9, 0.4, 1.0),
            )

            # Reset manual_vel to zero every frame so joystick callbacks
            # accumulate cleanly from the base speed on each frame
            if not autopilot_on[0]:
                manual_vel[0] = 0.0
                manual_vel[1] = 0.0

            # Joystick (callbacks only do work when autopilot is off)
            ui_widgets.joystick(
                "Rover Drive",
                on_y=on_joy_y if not autopilot_on[0] else None,
                on_x=on_joy_x if not autopilot_on[0] else None,
                snap=joystick_snap[0],
                size=75,
                handle_color=(0.2, 0.75, 1.0, 1.0),
            )

            if autopilot_on[0]:
                imgui.pop_style_var()

        print("BulletLab control window opened.\n")
    except Exception as exc:
        autopilot_on  = [True]
        joystick_snap = [True]
        manual_vel    = [0.0, 0.0]
        print(f"UI not available ({exc}). Running headless.\n")

    # ──────────────────────────────────────────────
    # 9. Simulation loop
    # ──────────────────────────────────────────────
    print("Running simulation. Press Ctrl+C to stop.\n")

    # Identify wheel joints (try common naming patterns)
    wheel_joints = []
    for name, joint in robot.joints.items():
        if any(kw in name.lower() for kw in ("wheel", "drive", "motor", "rear", "front")):
            if not joint.is_fixed:
                wheel_joints.append(joint)

    if not wheel_joints:
        # Fall back to all controllable joints
        wheel_joints = robot.controllable_joints[:4]

    print(f"Controlling joints: {[j.name for j in wheel_joints]}\n")

    # Set max force for all wheel joints
    for joint in wheel_joints:
        joint.max_force = 100.0

    phase = 0
    step = 0
    try:
        while sim.is_connected:
            if autopilot_on[0]:
                # ── Autopilot phase-based motion ──────────────────────────────
                phase_steps = 480  # 2 seconds at 240Hz
                t = step % (phase_steps * 4)

                if t < phase_steps:
                    left_vel, right_vel = 8.0, 8.0    # forward
                elif t < phase_steps * 2:
                    left_vel, right_vel = 8.0, -2.0   # turn right
                elif t < phase_steps * 3:
                    left_vel, right_vel = 8.0, 8.0    # forward again
                else:
                    left_vel, right_vel = -2.0, 8.0   # turn left

                for i, joint in enumerate(wheel_joints):
                    if i % 2 == 0:
                        joint.velocity = left_vel
                    else:
                        joint.velocity = right_vel
            else:
                # ── Manual / joystick control ─────────────────────────────────
                # manual_vel is written by the joystick callbacks inside ui.step()
                for i, joint in enumerate(wheel_joints):
                    if i % 2 == 0:
                        joint.velocity = manual_vel[0]
                    else:
                        joint.velocity = manual_vel[1]

            sim.step()
            cam.update()                        # smooth camera follows the rover
            telemetry.update(t=sim.elapsed_time)
            logger.step(t=sim.elapsed_time)

            if ui is not None:
                ui.step()
                if ui.should_close:
                    break

            step += 1

            # Print telemetry every 2 seconds
            if step % 480 == 0:
                snap = telemetry.snapshot()
                print(
                    f"  t={sim.elapsed_time:.1f}s | "
                    f"speed={snap.get('speed', 0):.2f} m/s | "
                    f"pos=({snap.get('x', 0):.2f}, {snap.get('y', 0):.2f}) | "
                    f"roll={snap.get('roll', 0):.1f}°"
                )

    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")

    except Exception as e:
        # Catches pybullet.error when the 3D window is closed externally
        if "isConnected" in str(e) or "Joint index" in str(e) or "connect" in str(e).lower():
            print("\nSimulation window closed.")
        else:
            raise

    finally:
        logger.stop()
        print(f"\nLogged {logger.step_count} steps to rover_run.csv")
        if ui is not None:
            ui.stop()
        sim.stop()
        print("Done.")


if __name__ == "__main__":
    main()
