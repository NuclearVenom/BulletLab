# BulletLab Cookbook

This cookbook provides short, copy-pasteable snippets for common tasks in BulletLab. 

## 1. Minimal Simulation Loop
The most basic setup to get a physics world running with a plane and a robot.

```python
from bulletlab import Simulation, Robot
from bulletlab.core.world import World

sim = Simulation(mode="gui").start()
World(sim).load_plane()
robot = Robot.load("r2d2.urdf", sim=sim, position=(0, 0, 0.5))

while sim.is_connected:
    sim.step()
```

## 2. Moving a Robot (Velocity Control)
Use the `velocity` property on a `Joint` object to command a target speed.

```python
# Drive two wheels forward at 10 rad/s
robot.joints['left_wheel_joint'].velocity = 10.0
robot.joints['right_wheel_joint'].velocity = 10.0
```

## 3. Moving a Robot (Position Control)
Use the `position` property to command a joint to a specific angle (in radians).

```python
import math
# Move a robotic arm joint to 90 degrees
robot.joints['shoulder_pan_joint'].position = math.pi / 2
```

## 4. Reading Robot State
Access the robot's base or specific links to read live physical states.

```python
# Base position (x, y, z)
x, y, z = robot.base_position

# Base orientation (quaternion: x, y, z, w)
qx, qy, qz, qw = robot.base_orientation

# Get the world position of a specific link (e.g. end effector)
end_effector_pos = robot.links['gripper_link'].position
```

## 5. Setting up Telemetry and Live Plots
Use `TelemetryManager` to track variables, and `LivePlot` to graph them dynamically.

```python
from bulletlab.telemetry import TelemetryManager
from bulletlab.plotting import LivePlot

telemetry = TelemetryManager()
# Watch the robot's speed (magnitude of base velocity)
telemetry.watch("Speed", lambda: robot.speed, unit="m/s")

# Plot it
plot = LivePlot(title="Rover Telemetry")
plot.watch("Speed", lambda: robot.speed, color="#00ff88")
plot.start()

# Inside your loop:
# telemetry.update(t=sim.elapsed_time)
# plot.update()
```

## 6. Changing Physics Properties
You can alter physics parameters on the fly via the `sim` or `link` objects.

```python
# Change gravity to Moon gravity
sim.gravity = (0, 0, -1.62)

# Make a specific link heavier
robot.links['base_link'].mass = 50.0

# Change lateral friction
robot.links['wheel_link'].lateral_friction = 1.2
```

## 7. Attaching the BulletLab UI
Add a complete ImGui dashboard with an Explorer, Properties panel, and Console with just two lines of code.

```python
from bulletlab.ui import BulletLabUI

ui = BulletLabUI(sim=sim, robots=[robot], telemetry=telemetry).start()

# Inside your loop:
# ui.step()
```

## 8. Virtual Joystick Control

Add an interactive 2D joystick to your custom panel for intuitive robot control.
The joystick calls your callbacks **every frame**, so wheels keep spinning while you hold it.

```python
from bulletlab import Simulation, Robot
from bulletlab.core.world import World
from bulletlab.ui import BulletLabUI
from bulletlab.ui import widgets as ui

sim = Simulation(mode="gui").start()
World(sim).load_plane()
robot = Robot.load("husky/husky.urdf", sim=sim)

app = BulletLabUI(sim=sim, robots=[robot])

@app.custom_panel("Drive")
def drive_panel():
    # Single joystick: Y=forward/back, X=turn
    ui.joystick(
        "Rover Drive",
        on_y=lambda v: [
            setattr(robot.joints["front_left_wheel"],  "velocity", v * 10),
            setattr(robot.joints["front_right_wheel"], "velocity", v * 10),
            setattr(robot.joints["rear_left_wheel"],   "velocity", v * 10),
            setattr(robot.joints["rear_right_wheel"],  "velocity", v * 10),
        ],
        on_x=lambda v: [
            setattr(robot.joints["front_left_wheel"],  "velocity", -v * 5),
            setattr(robot.joints["front_right_wheel"], "velocity",  v * 5),
            setattr(robot.joints["rear_left_wheel"],   "velocity", -v * 5),
            setattr(robot.joints["rear_right_wheel"],  "velocity",  v * 5),
        ],
        snap=True,                        # Release = stop
        size=80,                          # Larger joystick circle
        handle_color=(0.2, 0.8, 0.4, 1.0),
    )

app.start()
while sim.is_connected:
    sim.step()
    app.step()
    if app.should_close:
        break
app.stop()
sim.stop()
```

**Tip:** Set `snap=False` for a latching mode where the robot keeps driving at the last
commanded speed after you release. Set it back to `snap=True` if you want the robot to stop
immediately when you let go.

## 9. Loading a Robot at a Custom Tilt Angle

Use the `tilt` parameter on `Robot.load()` to set an initial orientation using an intuitive
**axis + angle** shorthand instead of computing quaternions by hand.

```python
from bulletlab import Simulation, Robot
from bulletlab.core.world import World

sim = Simulation(mode="gui").start()
World(sim).load_plane()

# Tilt 30° around the Y axis (nose-down / forward lean)
robot = Robot.load("laikago/laikago.urdf", sim=sim,
                   position=(0, 0, 0.5),
                   tilt=((0, 1, 0), 30))

# Tilt 45° around the X axis (lean left / roll)
robot = Robot.load("laikago/laikago.urdf", sim=sim,
                   position=(2, 0, 0.5),
                   tilt=((1, 0, 0), 45))

# Diagonal axis — vector is normalised automatically
robot = Robot.load("laikago/laikago.urdf", sim=sim,
                   position=(4, 0, 0.5),
                   tilt=((1, 1, 0), 60))

# Combine with an explicit orientation (heading) + tilt
# The tilt is applied on top of the base orientation
import pybullet as p, math
heading = p.getQuaternionFromEuler([0, 0, math.radians(90)])  # face East
robot = Robot.load("laikago/laikago.urdf", sim=sim,
                   position=(6, 0, 0.5),
                   orientation=heading,
                   tilt=((0, 1, 0), 15))   # also pitch forward 15°

while sim.is_connected:
    sim.step()
```

**Axis reference:**

| Axis | Effect |
|------|--------|
| `(1, 0, 0)` | Roll — lean left / right |
| `(0, 1, 0)` | Pitch — nose up / down |
| `(0, 0, 1)` | Yaw — spin on the spot |
| `(1, 1, 0)` | Diagonal — normalised automatically |

The angle is always in **degrees**. The axis does not need to be a unit vector.

## 10. Custom Terrain & Obstacles

No raw PyBullet needed — the `World` class handles everything.

```python
import numpy as np, math
from bulletlab import Simulation
from bulletlab.core.world import World

sim = Simulation(mode="gui").start()
world = World(sim)

# ── Flat ground (standard) ───────────────────────────────────────────
world.load_plane()

# ── Primitive obstacles ──────────────────────────────────────────────
world.create_box((1.0, 0.5, 0.3), position=(2, 0, 0.15), color=(0.8, 0.4, 0.1, 1))
world.create_sphere(radius=0.25, position=(0, 2, 0.25), color=(0.2, 0.8, 0.2, 1))
world.create_capsule(radius=0.1, height=0.6, position=(-1, 1, 0.5))

# ── Heightfield terrain ──────────────────────────────────────────────
n = 128
xs = np.linspace(0, 4 * math.pi, n)
heights = np.outer(np.sin(xs), np.cos(xs))   # 2-D sine wave hills
world.load_heightfield(heights, xy_scale=0.08, z_scale=0.3,
                       color=(0.55, 0.45, 0.35, 1.0))

# ── Scatter 20 rock-like boxes across a 20×20 m area ────────────────
world.scatter_obstacles(20, kind="box", size_range=(0.2, 0.5),
                        region=(-10, -10, 10, 10), seed=42)

# ── Remove one body, clear all ───────────────────────────────────────
rock = world.create_box((0.3, 0.3, 0.3), position=(5, 0, 0.15))
world.remove_body(rock)
# world.clear()  ← removes everything this World created

while sim.is_connected:
    sim.step()
```

## 11. Applying Forces, Torques & Runtime Dynamics

```python
from bulletlab import Simulation, Robot
from bulletlab.core.world import World

sim = Simulation(mode="gui").start()
World(sim).load_plane()
robot = Robot.load("laikago/laikago.urdf", sim=sim, position=(0, 0, 0.6))

# ── External forces (must be called every step) ──────────────────────
while sim.is_connected:
    # Continuous upward thrust (like a drone rotor)
    robot.apply_force((0, 0, 15.0))

    # Air drag proportional to speed
    vx, vy, vz = robot.base_velocity
    robot.apply_force((-0.2 * vx, -0.2 * vy, -0.2 * vz))

    # Apply force to a specific link (in the link's own frame)
    robot.apply_force((1.0, 0, 0), link="trunk", frame="local")

    # Spin torque around Z axis
    robot.apply_torque((0, 0, 2.0))

    sim.step()

# ── Runtime physics parameters (call once, takes effect immediately) ─
robot.set_dynamics(mass=20.0)                        # change body mass
robot.set_dynamics("FR_hip", lateral_friction=2.0)  # grippier foot
robot.set_dynamics(linear_damping=0.0, angular_damping=0.0)  # slippery

# Bump restitution on all links
for name in robot.links:
    robot.set_dynamics(name, restitution=0.5)
```

**Key rule:** `apply_force()` and `apply_torque()` are **single-step** — PyBullet clears
them after every `sim.step()`. Call them inside your loop for continuous effects.
`set_dynamics()` is **persistent** — call it once to change a property permanently.
