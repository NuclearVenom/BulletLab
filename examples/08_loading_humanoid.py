"""
Example 08: Loading Humanoid from Arsenal
=========================================
Loads the Unitree G1 humanoid from BulletLab Arsenal and auto-generates
a UI panel with sliders for all its controllable joints.

Run::

    python examples/08_loading_humanoid.py
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bulletlab import Simulation, Robot, CameraFollow
from bulletlab.core.world import World

def main() -> None:
    print("=== BulletLab Example 08: Loading Humanoid ===\n")

    # 1. Setup Simulation
    # Note: We do not call sim.start() immediately. This ensures the PyBullet
    # GUI window only pops up *after* the heavy model download completes.
    sim = Simulation(mode="gui", gravity=(0, 0, -9.81), timestep=1.0 / 240.0)

    # 2. Load Humanoid from Arsenal
    print("Fetching 'unitree/g1_description/g1_29dof' from Arsenal registry...")
    try:
        robot = Robot.load(
            "arsenal:unitree/g1_description/g1_29dof",
            sim=sim,
            position=(0, 0, 0.8),  # Spawn slightly above ground
            name="UnitreeG1",
        )
    except Exception as exc:
        print(f"Failed to load robot from arsenal: {exc}")
        sys.exit(1)

    print(f"Loaded: {robot.name} with {len(robot.controllable_joints)} controllable joints.")

    # 3. World and Camera setup
    sim.set_camera(distance=2.5, yaw=45.0, pitch=-20.0, target=(0, 0, 0.5))
    world = World(sim)
    world.load_plane()

    # 4. Camera Follow
    cam = CameraFollow(
        robot, sim,
        mode="smooth",
        distance=2.5,
        pitch=-20.0,
        yaw=45.0,
        lerp=0.1,
        height_offset=0.5,
    )

    # 5. UI Setup
    ui = None
    try:
        from bulletlab.ui import BulletLabUI
        import bulletlab.ui.widgets as ui_widgets

        ui = BulletLabUI(sim=sim, robots=[robot], camera=cam)
        ui.start()

        @ui.custom_panel("Joint Controls")
        def joint_controls() -> None:
            ui_widgets.text("Robot", robot.name)
            ui_widgets.text("Total Joints", str(len(robot.controllable_joints)))
            ui_widgets.separator()
            
            for joint in robot.controllable_joints:
                lo, hi = joint.limits
                # If limits are not defined, provide a reasonable default range
                lo2 = lo if lo != 0 or hi != 0 else -math.pi
                hi2 = hi if lo != 0 or hi != 0 else math.pi
                ui_widgets.slider(
                    joint.name[:25],
                    lambda j=joint: j.position,
                    lo2, hi2,
                    setter=lambda v, j=joint: j.set_position(v),
                )

        print("BulletLab UI opened.\n")
    except Exception as exc:
        print(f"UI not available ({exc}). Running headless.\n")

    # 6. Simulation loop
    print("Running simulation. Close the UI window or press Ctrl+C to stop.\n")

    try:
        while sim.is_connected:
            sim.step()
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
        print("Done.")

if __name__ == "__main__":
    main()
