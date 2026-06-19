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
