"""
Example 02: Robotic Arm (Kuka iiwa)
=====================================
Demonstrates joint position control on the Kuka iiwa arm with an ImGui
slider control panel for each joint.

What this shows:
- Loading the Kuka iiwa arm from pybullet_data
- Individual joint position control
- Reading joint limits and building dynamic UI sliders
- Monitoring joint state in real-time

Run::

    python examples/02_robotic_arm.py
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bulletlab import Simulation, Robot
from bulletlab.core.world import World
from bulletlab.telemetry import TelemetryManager
from bulletlab.utils.urdf_utils import find_urdf


def main() -> None:
    print("=== BulletLab Example 02: Robotic Arm (Kuka iiwa) ===\n")

    # ──────────────────────────────────────────────
    # Simulation setup
    # ──────────────────────────────────────────────
    sim = Simulation(mode="gui", gravity=(0, 0, -9.81))
    sim.start()
    sim.set_camera(distance=2.0, yaw=45.0, pitch=-20.0, target=(0, 0, 0.5))

    world = World(sim)
    world.load_plane()

    # ──────────────────────────────────────────────
    # Load Kuka arm
    # ──────────────────────────────────────────────
    try:
        urdf_path = find_urdf("kuka_iiwa/model.urdf")
    except FileNotFoundError:
        try:
            urdf_path = find_urdf("kuka_lwr/kuka.urdf")
        except FileNotFoundError:
            urdf_path = find_urdf("franka_panda/panda.urdf")

    robot = Robot.load(
        str(urdf_path),
        sim=sim,
        position=(0, 0, 0),
        fixed_base=True,
        name="KukaArm",
    )
    print(f"Loaded: {robot}")

    controllable = robot.controllable_joints
    print(f"Controllable joints ({len(controllable)}):")
    for j in controllable:
        lo, hi = j.limits
        print(f"  {j.name}: [{lo:.2f}, {hi:.2f}] rad")
    print()

    # ──────────────────────────────────────────────
    # Initial pose (all zeros)
    # ──────────────────────────────────────────────
    for joint in controllable:
        joint.set_position(0.0)

    # ──────────────────────────────────────────────
    # Telemetry
    # ──────────────────────────────────────────────
    telemetry = TelemetryManager()
    for joint in controllable:
        telemetry.watch(
            f"{joint.name}_pos",
            (lambda j: lambda: j.position)(joint),
            unit="rad",
        )
        telemetry.watch(
            f"{joint.name}_vel",
            (lambda j: lambda: j.velocity)(joint),
            unit="rad/s",
        )

    # ──────────────────────────────────────────────
    # UI setup
    # ──────────────────────────────────────────────
    ui = None
    try:
        from bulletlab.ui import BulletLabUI
        import bulletlab.ui.widgets as ui_widgets

        ui = BulletLabUI(sim=sim, robots=[robot], telemetry=telemetry)
        ui.start()

        # Custom panel: arm joint sliders
        target_positions = {j.name: 0.0 for j in controllable}

        @ui.custom_panel("Arm Control")
        def arm_control_panel() -> None:
            for joint in controllable:
                lo, hi = joint.limits
                lo2 = lo if lo != 0 or hi != 0 else -math.pi
                hi2 = hi if lo != 0 or hi != 0 else math.pi

                new_pos = ui_widgets.slider(
                    f"{joint.name}",
                    lambda j=joint: j.position,
                    lo2, hi2,
                    setter=lambda v, j=joint: j.set_position(v),
                )
                target_positions[joint.name] = new_pos

        print("BulletLab arm control window opened.\n")
    except Exception as exc:
        print(f"UI not available ({exc}). Running automated demo.\n")

    # ──────────────────────────────────────────────
    # Simulation loop
    # ──────────────────────────────────────────────
    print("Running simulation. Press Ctrl+C to stop.\n")

    step = 0
    period = 480  # 2 seconds per motion cycle

    try:
        while True:
            if ui is None:
                # Automated sinusoidal joint motion for headless mode
                t = step / 240.0
                for i, joint in enumerate(controllable):
                    lo, hi = joint.limits
                    lo2 = lo if lo != 0 or hi != 0 else -math.pi
                    hi2 = hi if lo != 0 or hi != 0 else math.pi
                    mid = (lo2 + hi2) / 2.0
                    amp = (hi2 - lo2) * 0.3
                    target = mid + amp * math.sin(t * 0.5 + i * 0.8)
                    joint.set_position(target)

            sim.step()
            telemetry.update(t=sim.elapsed_time)

            if ui is not None:
                ui.step()
                if ui.should_close:
                    break

            step += 1
            if step % 240 == 0:
                print(f"  t={sim.elapsed_time:.1f}s | joints: " +
                      ", ".join(f"{j.name}={j.position:.2f}" for j in controllable[:3]))

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        if ui is not None:
            ui.stop()
        sim.stop()
        print("Done.")


if __name__ == "__main__":
    main()
