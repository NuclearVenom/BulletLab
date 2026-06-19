"""
Example 05: Generic Robot Inspector
=====================================
Load any URDF by name or path and automatically inspect all joints,
links, and telemetry in the BulletLab UI.

This is the most versatile example — it works with any robot.

Usage::

    python examples/05_generic_robot_inspector.py
    python examples/05_generic_robot_inspector.py kuka_iiwa/model.urdf
    python examples/05_generic_robot_inspector.py r2d2.urdf
    python examples/05_generic_robot_inspector.py /absolute/path/to/robot.urdf

What this shows:
- Auto-discovery of all joints and links
- Dynamically building a full inspector UI
- RL-compatible state inspection
- Generic telemetry without knowing the robot type in advance
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bulletlab import Simulation, Robot
from bulletlab.core.world import World
from bulletlab.telemetry import TelemetryManager
from bulletlab.logging import DataLogger
from bulletlab.utils.urdf_utils import find_urdf, list_available_urdfs


def pick_robot(arg: str | None) -> str:
    """Determine which URDF to load based on CLI argument."""
    if arg is not None:
        try:
            return str(find_urdf(arg))
        except FileNotFoundError:
            print(f"Could not find: {arg}")
            print("Available URDFs in pybullet_data:")
            for u in list_available_urdfs(30):
                print(f"  {u}")
            sys.exit(1)

    # Default priority list
    defaults = [
        "kuka_iiwa/model.urdf",
        "husky/husky.urdf",
        "franka_panda/panda.urdf",
        "r2d2.urdf",
        "cartpole.urdf",
    ]
    for d in defaults:
        try:
            return str(find_urdf(d))
        except FileNotFoundError:
            continue

    print("No default URDF found. Available URDFs:")
    for u in list_available_urdfs(20):
        print(f"  {u}")
    sys.exit(1)


def main() -> None:
    print("=== BulletLab Example 05: Generic Robot Inspector ===\n")

    urdf_path = pick_robot(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"Loading: {urdf_path}\n")

    # ──────────────────────────────────────────────
    # Simulation
    # ──────────────────────────────────────────────
    sim = Simulation(mode="gui", gravity=(0, 0, -9.81))
    sim.start()
    sim.set_camera(distance=3.0, yaw=45.0, pitch=-20.0, target=(0, 0, 0.3))

    world = World(sim)
    world.load_plane()

    robot = Robot.load(urdf_path, sim=sim, position=(0, 0, 0.2), name="InspectedRobot")

    print(f"Robot: {robot}")
    print(f"  Joints ({len(robot.joints)}):")
    for name, j in robot.joints.items():
        lo, hi = j.limits
        jtype = j.joint_type.name if hasattr(j.joint_type, "name") else str(j.joint_type)
        print(f"    [{name}] type={jtype} limits=[{lo:.2f}, {hi:.2f}]")
    print(f"  Links ({len(robot.links)}):")
    for name, l in robot.links.items():
        print(f"    [{name}] mass={l.mass:.3f}kg")
    print(f"  State dim: {len(robot.get_state())}\n")

    # ──────────────────────────────────────────────
    # Telemetry – auto-discover
    # ──────────────────────────────────────────────
    telemetry = TelemetryManager()
    telemetry.watch("x",     lambda: robot.base_position[0], unit="m")
    telemetry.watch("y",     lambda: robot.base_position[1], unit="m")
    telemetry.watch("z",     lambda: robot.base_position[2], unit="m")
    telemetry.watch("speed", lambda: robot.speed,             unit="m/s")
    telemetry.watch("roll",  lambda: math.degrees(robot.roll),  unit="°")
    telemetry.watch("pitch", lambda: math.degrees(robot.pitch), unit="°")
    telemetry.watch("yaw",   lambda: math.degrees(robot.yaw),   unit="°")

    # Add joint positions for first 4 controllable joints
    for joint in robot.controllable_joints[:4]:
        telemetry.watch(
            f"j_{joint.name[:12]}",
            (lambda j: lambda: j.position)(joint),
            unit="rad",
        )

    # ──────────────────────────────────────────────
    # Logger
    # ──────────────────────────────────────────────
    logger = DataLogger()
    logger.watch("x",     lambda: robot.base_position[0])
    logger.watch("y",     lambda: robot.base_position[1])
    logger.watch("z",     lambda: robot.base_position[2])
    logger.watch("speed", lambda: robot.speed)
    logger.start("inspector_run.csv")

    # ──────────────────────────────────────────────
    # UI
    # ──────────────────────────────────────────────
    ui = None
    try:
        from bulletlab.ui import BulletLabUI
        import bulletlab.ui.widgets as ui_widgets

        ui = BulletLabUI(sim=sim, robots=[robot], telemetry=telemetry)
        ui.start()

        @ui.custom_panel("Joint Inspector")
        def joint_inspector() -> None:
            ui_widgets.text("Robot", robot.name)
            ui_widgets.text("State dim", str(len(robot.get_state())))
            ui_widgets.separator("Controllable Joints")
            for joint in robot.controllable_joints[:8]:
                lo, hi = joint.limits
                lo2 = lo if lo != 0 or hi != 0 else -math.pi
                hi2 = hi if lo != 0 or hi != 0 else math.pi
                ui_widgets.slider(
                    joint.name[:20],
                    lambda j=joint: j.position,
                    lo2, hi2,
                    setter=lambda v, j=joint: j.set_position(v),
                )

        @ui.custom_panel("Link Inspector")
        def link_inspector() -> None:
            ui_widgets.text("Link count", str(len(robot.links)))
            ui_widgets.separator("Editable Properties")
            for link in list(robot.links.values())[:6]:
                if ui_widgets.collapsing_header(link.name[:20], default_open=False):
                    ui_widgets.drag_float(
                        f"mass##{link.name}", lambda l=link: l.mass,
                        setter=lambda v, l=link: setattr(l, "mass", v),
                        speed=0.01, min_val=0.0001, max_val=100.0,
                    )
                    ui_widgets.drag_float(
                        f"friction##{link.name}", lambda l=link: l.friction,
                        setter=lambda v, l=link: setattr(l, "friction", v),
                        speed=0.01, min_val=0.0, max_val=10.0,
                    )

        print("BulletLab inspector window opened.\n")
    except Exception as exc:
        print(f"UI not available ({exc}). Running headless.\n")

    # ──────────────────────────────────────────────
    # Simulation loop
    # ──────────────────────────────────────────────
    print("Running inspector. Press Ctrl+C to stop.\n")
    step = 0

    try:
        while sim.is_connected:
            sim.step()
            telemetry.update(t=sim.elapsed_time)
            logger.step(t=sim.elapsed_time)

            if ui is not None:
                ui.step()
                if ui.should_close:
                    break

            step += 1
            if step % 480 == 0:
                snap = telemetry.snapshot()
                pos = (snap.get("x", 0), snap.get("y", 0), snap.get("z", 0))
                print(
                    f"  t={sim.elapsed_time:.1f}s | "
                    f"pos=({pos[0]:.2f},{pos[1]:.2f},{pos[2]:.2f}) | "
                    f"speed={snap.get('speed', 0):.2f}m/s"
                )

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        logger.stop()
        print(f"\nLogged {logger.step_count} steps to inspector_run.csv")
        if ui is not None:
            ui.stop()
        sim.stop()
        print("Done.")


if __name__ == "__main__":
    main()
