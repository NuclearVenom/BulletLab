"""
Example 01: Differential Drive Rover
=====================================
Demonstrates basic wheel velocity control using the Husky robot from pybullet_data.

What this shows:
- Loading a robot by name using pybullet_data
- Setting joint velocities by name
- Monitoring base telemetry (position, speed, roll)
- Logging data to CSV
- Simple BulletLabUI control window

Run::

    python examples/01_differential_drive_rover.py
"""

import math
import time
import sys
from pathlib import Path

# Ensure bulletlab is importable from the repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from bulletlab import Simulation, Robot
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
    # 4. Set up telemetry
    # ──────────────────────────────────────────────
    telemetry = TelemetryManager()
    telemetry.watch("x",       lambda: robot.base_position[0], unit="m")
    telemetry.watch("y",       lambda: robot.base_position[1], unit="m")
    telemetry.watch("z",       lambda: robot.base_position[2], unit="m")
    telemetry.watch("speed",   lambda: robot.speed,            unit="m/s")
    telemetry.watch("roll",    lambda: math.degrees(robot.roll),  unit="°")
    telemetry.watch("pitch",   lambda: math.degrees(robot.pitch), unit="°")

    # ──────────────────────────────────────────────
    # 5. Set up data logger
    # ──────────────────────────────────────────────
    logger = DataLogger()
    logger.watch("speed",   lambda: robot.speed)
    logger.watch("x",       lambda: robot.base_position[0])
    logger.watch("y",       lambda: robot.base_position[1])
    logger.watch("roll",    lambda: math.degrees(robot.roll))
    logger.start("rover_run.csv")
    print("Logging to: rover_run.csv\n")

    # ──────────────────────────────────────────────
    # 6. Try to launch UI (optional)
    # ──────────────────────────────────────────────
    ui = None
    try:
        from bulletlab.ui import BulletLabUI
        ui = BulletLabUI(sim=sim, robots=[robot], telemetry=telemetry)
        ui.start()
        print("BulletLab control window opened.\n")
    except Exception as exc:
        print(f"UI not available ({exc}). Running headless.\n")

    # ──────────────────────────────────────────────
    # 7. Simulation loop
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
        while True:
            # Simple phase-based motion: forward → turn → forward → turn
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

            # Apply velocities (split by left/right side)
            for i, joint in enumerate(wheel_joints):
                if i % 2 == 0:
                    joint.velocity = left_vel
                else:
                    joint.velocity = right_vel

            sim.step()
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

    finally:
        logger.stop()
        print(f"\nLogged {logger.step_count} steps to rover_run.csv")
        if ui is not None:
            ui.stop()
        sim.stop()
        print("Done.")


if __name__ == "__main__":
    main()
