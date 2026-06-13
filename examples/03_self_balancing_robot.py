"""
Example 03: Self-Balancing Robot
=================================
Demonstrates a PD controller keeping a two-wheeled robot upright.
Uses R2D2 as a stand-in for demonstration (roll/pitch balancing).

What this shows:
- Reading roll and pitch from base_orientation
- Implementing a simple PD control loop manually
- Monitoring control effort in real-time via telemetry
- Logging controller data

Run::

    python examples/03_self_balancing_robot.py
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bulletlab import Simulation, Robot
from bulletlab.core.world import World
from bulletlab.telemetry import TelemetryManager
from bulletlab.logging import DataLogger
from bulletlab.utils.urdf_utils import find_urdf
from bulletlab.utils.math_utils import clamp


def main() -> None:
    print("=== BulletLab Example 03: Self-Balancing Robot ===\n")

    # ──────────────────────────────────────────────
    # Simulation
    # ──────────────────────────────────────────────
    sim = Simulation(mode="gui", gravity=(0, 0, -9.81))
    sim.start()
    sim.set_camera(distance=2.5, yaw=45.0, pitch=-15.0, target=(0, 0, 0.5))

    world = World(sim)
    world.load_plane()

    # ──────────────────────────────────────────────
    # Load robot – try r2d2 or cartpole-like URDF
    # ──────────────────────────────────────────────
    try:
        urdf_path = find_urdf("cartpole.urdf")
        robot = Robot.load(str(urdf_path), sim=sim, position=(0, 0, 0.1), name="CartPole")
        is_cartpole = True
    except FileNotFoundError:
        urdf_path = find_urdf("r2d2.urdf")
        robot = Robot.load(str(urdf_path), sim=sim, position=(0, 0, 0.3), name="R2D2")
        is_cartpole = False

    print(f"Loaded: {robot}")
    print(f"Controllable joints: {[j.name for j in robot.controllable_joints]}\n")

    # ──────────────────────────────────────────────
    # PD Controller parameters
    # ──────────────────────────────────────────────
    Kp = 50.0   # proportional gain (roll error → wheel torque)
    Kd = 5.0    # derivative gain (angular velocity damping)
    target_angle = 0.0  # desired pitch/roll angle (upright)

    prev_error = 0.0
    dt = sim.timestep

    print(f"PD Controller: Kp={Kp}, Kd={Kd}")
    print(f"Timestep: {dt:.4f}s\n")

    # ──────────────────────────────────────────────
    # Telemetry
    # ──────────────────────────────────────────────
    control_effort = [0.0]

    telemetry = TelemetryManager()
    telemetry.watch("pitch",    lambda: math.degrees(robot.pitch), unit="°")
    telemetry.watch("roll",     lambda: math.degrees(robot.roll),  unit="°")
    telemetry.watch("control",  lambda: control_effort[0],        unit="N·m")
    telemetry.watch("speed",    lambda: robot.speed,               unit="m/s")

    # ──────────────────────────────────────────────
    # Logger
    # ──────────────────────────────────────────────
    logger = DataLogger()
    logger.watch("pitch",   lambda: math.degrees(robot.pitch))
    logger.watch("roll",    lambda: math.degrees(robot.roll))
    logger.watch("control", lambda: control_effort[0])
    logger.start("balancing_run.csv")

    # ──────────────────────────────────────────────
    # UI (optional)
    # ──────────────────────────────────────────────
    ui = None
    try:
        from bulletlab.ui import BulletLabUI
        import bulletlab.ui.widgets as ui_widgets

        ui = BulletLabUI(sim=sim, robots=[robot], telemetry=telemetry)
        ui.start()

        gains = [Kp, Kd]

        @ui.custom_panel("PD Controller")
        def controller_panel() -> None:
            ui_widgets.text("Controller", "PD Balance")
            gains[0] = ui_widgets.drag_float(
                "Kp (Proportional)", lambda: gains[0], setter=lambda v: gains.__setitem__(0, v),
                speed=0.5, min_val=0.0, max_val=500.0,
            )
            gains[1] = ui_widgets.drag_float(
                "Kd (Derivative)", lambda: gains[1], setter=lambda v: gains.__setitem__(1, v),
                speed=0.1, min_val=0.0, max_val=50.0,
            )
            ui_widgets.separator()
            ui_widgets.text("Control effort", f"{control_effort[0]:.2f} N·m")
            ui_widgets.text("Pitch", f"{math.degrees(robot.pitch):.2f}°")
            ui_widgets.text("Roll",  f"{math.degrees(robot.roll):.2f}°")
            ui_widgets.separator()
            if ui_widgets.button("Reset Robot"):
                robot.reset()

        print("BulletLab control window opened.\n")
    except Exception as exc:
        print(f"UI not available ({exc}). Running headless.\n")
        gains = [Kp, Kd]

    # ──────────────────────────────────────────────
    # Simulation loop
    # ──────────────────────────────────────────────
    print("Running. Press Ctrl+C to stop.\n")
    step = 0

    try:
        while True:
            # Read current angle
            if is_cartpole:
                # Cartpole: use first joint angle as pole angle
                controllable = robot.controllable_joints
                if controllable:
                    pole_angle = controllable[-1].position
                    error = target_angle - pole_angle
                    d_error = -controllable[-1].velocity
                else:
                    error, d_error = 0.0, 0.0
            else:
                # General: use pitch for balance
                error = target_angle - robot.pitch
                d_error = (error - prev_error) / dt

            # PD control
            u = clamp(gains[0] * error + gains[1] * d_error, -100.0, 100.0)
            control_effort[0] = u
            prev_error = error

            # Apply control to wheel/drive joints
            controllable_joints = robot.controllable_joints
            if is_cartpole and controllable_joints:
                # Apply force to cart (prismatic joint)
                controllable_joints[0].torque = u
            else:
                # Apply to drive wheels
                for joint in controllable_joints[:4]:
                    joint.velocity = clamp(u * 0.5, -20.0, 20.0)

            sim.step()
            telemetry.update(t=sim.elapsed_time)
            logger.step(t=sim.elapsed_time)

            if ui is not None:
                ui.step()
                if ui.should_close:
                    break

            step += 1
            if step % 480 == 0:
                print(
                    f"  t={sim.elapsed_time:.1f}s | "
                    f"pitch={math.degrees(robot.pitch):.2f}° | "
                    f"roll={math.degrees(robot.roll):.2f}° | "
                    f"u={control_effort[0]:.2f}"
                )

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        logger.stop()
        print(f"\nLogged {logger.step_count} steps to balancing_run.csv")
        if ui is not None:
            ui.stop()
        sim.stop()
        print("Done.")


if __name__ == "__main__":
    main()
