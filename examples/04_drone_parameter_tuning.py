"""
Example 04: Drone Parameter Tuning
=====================================
Demonstrates live physics parameter tuning on a quadrotor.
Uses the drone URDF from pybullet_data if available, otherwise uses a
simple box as a stand-in.

What this shows:
- Modifying link mass at runtime via robot.links["body"].mass
- Modifying friction at runtime
- Applying upward forces to simulate thrust (via joint torques)
- Exposing parameter sliders in BulletLabUI
- Real-time observation of how parameter changes affect flight

Run::

    python examples/04_drone_parameter_tuning.py
"""

import math
import sys
from pathlib import Path
from bulletlab import Simulation, Robot
from bulletlab.core.world import World
from bulletlab.telemetry import TelemetryManager
from bulletlab.logging import DataLogger
from bulletlab.utils.urdf_utils import find_urdf


def create_drone_urdf(output_path: Path) -> None:
    """Generate a minimal quadrotor URDF on disk if none exists."""
    urdf_content = """<?xml version="1.0"?>
<robot name="quadrotor">
  <link name="base_link">
    <visual>
      <geometry><box size="0.4 0.4 0.1"/></geometry>
    </visual>
    <collision>
      <geometry><box size="0.4 0.4 0.1"/></geometry>
    </collision>
    <inertial>
      <mass value="1.0"/>
      <inertia ixx="0.01" iyy="0.01" izz="0.02" ixy="0" ixz="0" iyz="0"/>
    </inertial>
  </link>

  <link name="rotor_fl">
    <visual><geometry><cylinder radius="0.08" length="0.02"/></geometry></visual>
    <collision><geometry><cylinder radius="0.08" length="0.02"/></geometry></collision>
    <inertial><mass value="0.05"/>
      <inertia ixx="0.0001" iyy="0.0001" izz="0.0001" ixy="0" ixz="0" iyz="0"/>
    </inertial>
  </link>
  <joint name="rotor_fl_joint" type="continuous">
    <parent link="base_link"/>
    <child link="rotor_fl"/>
    <origin xyz="0.15 0.15 0.06"/>
    <axis xyz="0 0 1"/>
  </joint>

  <link name="rotor_fr">
    <visual><geometry><cylinder radius="0.08" length="0.02"/></geometry></visual>
    <collision><geometry><cylinder radius="0.08" length="0.02"/></geometry></collision>
    <inertial><mass value="0.05"/>
      <inertia ixx="0.0001" iyy="0.0001" izz="0.0001" ixy="0" ixz="0" iyz="0"/>
    </inertial>
  </link>
  <joint name="rotor_fr_joint" type="continuous">
    <parent link="base_link"/>
    <child link="rotor_fr"/>
    <origin xyz="0.15 -0.15 0.06"/>
    <axis xyz="0 0 1"/>
  </joint>

  <link name="rotor_rl">
    <visual><geometry><cylinder radius="0.08" length="0.02"/></geometry></visual>
    <collision><geometry><cylinder radius="0.08" length="0.02"/></geometry></collision>
    <inertial><mass value="0.05"/>
      <inertia ixx="0.0001" iyy="0.0001" izz="0.0001" ixy="0" ixz="0" iyz="0"/>
    </inertial>
  </link>
  <joint name="rotor_rl_joint" type="continuous">
    <parent link="base_link"/>
    <child link="rotor_rl"/>
    <origin xyz="-0.15 0.15 0.06"/>
    <axis xyz="0 0 1"/>
  </joint>

  <link name="rotor_rr">
    <visual><geometry><cylinder radius="0.08" length="0.02"/></geometry></visual>
    <collision><geometry><cylinder radius="0.08" length="0.02"/></geometry></collision>
    <inertial><mass value="0.05"/>
      <inertia ixx="0.0001" iyy="0.0001" izz="0.0001" ixy="0" ixz="0" iyz="0"/>
    </inertial>
  </link>
  <joint name="rotor_rr_joint" type="continuous">
    <parent link="base_link"/>
    <child link="rotor_rr"/>
    <origin xyz="-0.15 -0.15 0.06"/>
    <axis xyz="0 0 1"/>
  </joint>
</robot>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(urdf_content)


def main() -> None:
    print("=== BulletLab Example 04: Drone Parameter Tuning ===\n")

    # ──────────────────────────────────────────────
    # Simulation
    # ──────────────────────────────────────────────
    sim = Simulation(mode="gui", gravity=(0, 0, -9.81))
    sim.start()
    sim.set_camera(distance=3.0, yaw=45.0, pitch=-20.0, target=(0, 0, 1.0))

    world = World(sim)
    world.load_plane()

    # ──────────────────────────────────────────────
    # Load drone URDF
    # ──────────────────────────────────────────────
    drone_urdf = Path(__file__).parent / "assets" / "quadrotor.urdf"
    if not drone_urdf.exists():
        print("Generating quadrotor URDF...")
        create_drone_urdf(drone_urdf)

    robot = Robot.load(str(drone_urdf), sim=sim, position=(0, 0, 0.5), name="Drone")
    print(f"Loaded: {robot}")
    print(f"Joints: {list(robot.joints.keys())}")
    print(f"Links:  {list(robot.links.keys())}\n")

    # ──────────────────────────────────────────────
    # Parameters (mutable via UI)
    # ──────────────────────────────────────────────
    params = {
        "thrust": 12.0,    # total thrust force (N)
        "mass": 1.0,       # body mass (kg)
        "drag": 0.1,       # artificial drag coefficient
        "rotor_speed": 100.0,  # rotor spin speed (rad/s)
    }

    # ──────────────────────────────────────────────
    # Telemetry
    # ──────────────────────────────────────────────
    telemetry = TelemetryManager()
    telemetry.watch("height",  lambda: robot.base_position[2], unit="m")
    telemetry.watch("vz",      lambda: robot.base_velocity[2], unit="m/s")
    telemetry.watch("roll",    lambda: math.degrees(robot.roll), unit="°")
    telemetry.watch("pitch",   lambda: math.degrees(robot.pitch), unit="°")

    # ──────────────────────────────────────────────
    # Logger
    # ──────────────────────────────────────────────
    logger = DataLogger()
    logger.watch("height", lambda: robot.base_position[2])
    logger.watch("thrust", lambda: params["thrust"])
    logger.watch("mass",   lambda: params["mass"])
    logger.start("drone_tuning.csv")

    # ──────────────────────────────────────────────
    # UI
    # ──────────────────────────────────────────────
    ui = None
    try:
        from bulletlab.ui import BulletLabUI
        import bulletlab.ui.widgets as ui_widgets

        ui = BulletLabUI(sim=sim, robots=[robot], telemetry=telemetry)
        ui.start()

        @ui.custom_panel("Drone Parameters")
        def drone_panel() -> None:
            ui_widgets.text("Drone", "Quadrotor Tuner")
            ui_widgets.separator()

            params["thrust"] = ui_widgets.slider(
                "Total Thrust (N)", lambda: params["thrust"], 0.0, 50.0,
                setter=lambda v: params.update({"thrust": v}),
            )
            params["mass"] = ui_widgets.slider(
                "Body Mass (kg)", lambda: params["mass"], 0.1, 10.0,
                setter=lambda v: (params.update({"mass": v}),
                                  robot.set_dynamics("base_link", mass=v)),
            )
            params["drag"] = ui_widgets.slider(
                "Drag Coefficient", lambda: params["drag"], 0.0, 2.0,
                setter=lambda v: params.update({"drag": v}),
            )
            params["rotor_speed"] = ui_widgets.slider(
                "Rotor Speed (rad/s)", lambda: params["rotor_speed"], 0.0, 500.0,
                setter=lambda v: params.update({"rotor_speed": v}),
            )

            ui_widgets.separator()
            ui_widgets.text("Height",   f"{robot.base_position[2]:.3f} m")
            ui_widgets.text("Vertical Vel", f"{robot.base_velocity[2]:.3f} m/s")

            if ui_widgets.button("Reset Drone"):
                robot.reset(position=(0, 0, 0.5))

        print("BulletLab drone tuning window opened.\n")
    except Exception as exc:
        print(f"UI not available ({exc}). Running headless.\n")

    # ──────────────────────────────────────────────
    # Simulation loop
    # ──────────────────────────────────────────────
    print("Running. Press Ctrl+C to stop.\n")
    step = 0
    rotor_joints = list(robot.joints.values())

    try:
        while True:
            # Apply upward thrust force (world frame, at the robot's centre)
            robot.apply_force((0, 0, params["thrust"]))

            # Apply simple drag (opposite to velocity, world frame)
            vel = robot.base_velocity
            drag_force = tuple(-params["drag"] * v for v in vel)
            robot.apply_force(drag_force)

            # Spin rotors
            for joint in rotor_joints:
                if not joint.is_fixed:
                    joint.velocity = params["rotor_speed"]

            sim.step()
            telemetry.update(t=sim.elapsed_time)
            logger.step(t=sim.elapsed_time)

            if ui is not None:
                ui.step()
                if ui.should_close:
                    break

            step += 1
            if step % 240 == 0:
                h = robot.base_position[2]
                vz = robot.base_velocity[2]
                print(f"  t={sim.elapsed_time:.1f}s | height={h:.2f}m | vz={vz:.2f}m/s | thrust={params['thrust']:.1f}N")

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        logger.stop()
        print(f"\nLogged {logger.step_count} steps to drone_tuning.csv")
        if ui is not None:
            ui.stop()
        sim.stop()
        print("Done.")


if __name__ == "__main__":
    main()
