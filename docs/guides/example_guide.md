# Examples Guide

BulletLab ships with 9 comprehensive, ready-to-run examples demonstrating real use cases.

## Running the Examples

```bash
cd BulletLab
python examples/01_differential_drive_rover.py
python examples/02_robotic_arm.py
python examples/03_self_balancing_robot.py
python examples/04_drone_parameter_tuning.py
python examples/05_generic_robot_inspector.py
python examples/06_irregular_terrain.py
python examples/07_arsenal_loading.py
python examples/08_loading_humanoid.py
python examples/09_quick_launch.py
```

## Example 01 – Differential Drive Rover

**File**: `examples/01_differential_drive_rover.py`

Loads the Husky rover (falls back to racecar or R2D2) and drives it through
a sequence of forward and turning maneuvers. Logs speed, position, and roll
to `rover_run.csv`.

**Demonstrates**:
- Wheel velocity control
- Phase-based motion planning
- Telemetry + CSV logging
- BulletLabUI control window

## Example 02 – Robotic Arm

**File**: `examples/02_robotic_arm.py`

Loads the Kuka iiwa arm (fixed to ground) and provides per-joint slider
controls in the BulletLab UI. Falls back to animated sinusoidal motion
if the UI is not available.

**Demonstrates**:
- Fixed-base arm loading
- Position control
- Dynamic UI slider generation
- Joint limit reading

## Example 03 – Self-Balancing Robot

**File**: `examples/03_self_balancing_robot.py`

Implements a PD controller to keep a robot upright. The cartpole URDF is
preferred; R2D2 is used as a fallback. Gain values (Kp, Kd) are editable
in the UI at runtime.

**Demonstrates**:
- PD control loop
- Reading roll/pitch from `robot.roll`/`robot.pitch`
- Adjustable gains via Dear ImGui sliders
- Controller data logging

## Example 04 – Drone Parameter Tuning

**File**: `examples/04_drone_parameter_tuning.py`

Generates a custom quadrotor URDF and applies `pybullet.applyExternalForce`
to simulate thrust. Parameters (thrust, mass, drag, rotor speed) are exposed
as Dear ImGui sliders and can be changed live during flight.

**Demonstrates**:
- Custom URDF generation at runtime
- `applyExternalForce` for direct physics manipulation
- Live mass modification via `robot.links["base_link"].mass`
- Multi-parameter exploration

## Example 05 – Generic Robot Inspector

**File**: `examples/05_generic_robot_inspector.py`

Load any URDF by name or path and inspect it:

```bash
python examples/05_generic_robot_inspector.py kuka_iiwa/model.urdf
python examples/05_generic_robot_inspector.py r2d2.urdf
python examples/05_generic_robot_inspector.py /path/to/custom/robot.urdf
```

**Demonstrates**:
- Generic robot discovery
- Dynamic joint/link panel generation
- RL state vector inspection
- Universal telemetry

## Example 06 – Irregular Terrain

**File**: `examples/06_irregular_terrain.py`

Demonstrates loading custom procedural heightfields and scattering random obstacle geometries for off-road navigation.

**Demonstrates**:
- `World.load_heightfield()` procedural terrain
- `World.scatter_obstacles()` for rock/box fields
- Rover mobility on uneven geometry

## Example 07 – Arsenal Loading

**File**: `examples/07_arsenal_loading.py`

Demonstrates loading community robot packages directly from the official [BulletLab Arsenal](https://github.com/NuclearVenom/BulletLab-Arsenal) registry using session caching.

**Demonstrates**:
- `Robot.load("arsenal:reference_bot/BLem1")`
- Seamless asset downloading and caching
- Interactive virtual joystick drive panel

## Example 08 – Humanoid Robot Loading

**File**: `examples/08_loading_humanoid.py`

Loads a multi-DOF humanoid robot, sets up joint limits, and monitors high-dimensional telemetry.

**Demonstrates**:
- High-DOF kinematic tree handling
- Complex joint hierarchy inspection
- Multi-joint telemetry tracking

## Example 09 – Instant Deployment (`quickLaunch`)

**File**: `examples/09_quick_launch.py`

Demonstrates BulletLab's signature one-line deployment feature with built-in, local, and Arsenal models.

**Demonstrates**:
- `bulletlab.quickLaunch("arsenal:reference_bot")`
- 3-mode joint controls (Position, Velocity, Torque)
- Dynamic camera tracking with capsule toggle switch
- Zero-configuration interactive inspection
