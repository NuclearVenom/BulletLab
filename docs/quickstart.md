# Quick Start

Get up and running with BulletLab in 5 minutes.

## Installation

> **Requirements:** Python 3.11–3.13, 64-bit. Windows, Linux, and macOS are supported.

```bash
pip install bulletlab

# Or for development (from source):
pip install -e ".[dev]"
```

## ⚡ One-Line Model Deployment (`quickLaunch`)

The absolute fastest way to get started with BulletLab is `quickLaunch()`. Just pass a robot model path or an Arsenal URI, and your model is immediately deployed into an interactive simulation with real-time joint controls, telemetry, and camera follow:

```python
import bulletlab

# Deploy a built-in model or local URDF/MJCF file
bulletlab.quickLaunch("kuka_iiwa/model.urdf")

# Or deploy directly from BulletLab Arsenal
bulletlab.quickLaunch("arsenal:reference_bot")
```

`quickLaunch()` automatically configures:
- **Joint Control Panel:** Instant Position, Velocity, and Torque control sliders per joint
- **Dynamic Camera Follow:** Smooth tracking with an interactive capsule toggle switch
- **Real-Time Telemetry:** Position, velocity, speed, roll/pitch/yaw angles, and joint positions
- **Interactive Python Console:** Live script and interact with your simulation
- **Arsenal Pre-Fetching:** Downloads model assets before window creation so you never see an empty viewport

---

## Building a Custom Simulation

For granular control over the simulation loop, world geometry, controllers, and custom UI dashboards:

```python
from bulletlab import Simulation, Robot
from bulletlab.core.world import World

# 1. Create and start simulation
sim = Simulation(mode="gui")   # "gui" shows PyBullet window
sim.start()

# 2. Set up the world
world = World(sim)
world.load_plane()             # flat ground

# 3. Load a robot (any URDF from pybullet_data)
robot = Robot.load("kuka_iiwa/model.urdf", sim=sim, position=(0, 0, 0), fixed_base=True)

# 4. Inspect what was loaded
print(robot)
print("Joints:", list(robot.joints.keys()))
print("Links:",  list(robot.links.keys()))

# 5. Control the robot
robot.joints["iiwa_joint_1"].set_position(1.0)   # move to 1 rad
robot.links["iiwa_link_0"].mass = 5.0             # change mass

# 6. Run the simulation loop
for _ in range(1000):
    sim.step()

sim.stop()
```

## Adding Telemetry

```python
from bulletlab.telemetry import TelemetryManager

telemetry = TelemetryManager()
telemetry.watch("speed",  lambda: robot.speed, unit="m/s")
telemetry.watch("height", lambda: robot.base_position[2], unit="m")
telemetry.watch("roll",   lambda: robot.roll, unit="rad")

for _ in range(1000):
    sim.step()
    telemetry.update(t=sim.elapsed_time)

print(telemetry.snapshot())
```

## Logging Data

```python
from bulletlab.logging import DataLogger

logger = DataLogger()
logger.watch("speed",  lambda: robot.speed)
logger.watch("height", lambda: robot.base_position[2])
logger.start("my_experiment.csv")

for _ in range(1000):
    sim.step()
    logger.step(t=sim.elapsed_time)

logger.stop()
```

## Live Plots

```python
from bulletlab.plotting import LivePlot

plot = LivePlot(title="Robot Speed")
plot.watch("Speed", lambda: robot.speed, color="#00ff88")
plot.start()

for _ in range(5000):
    sim.step()
    plot.update()

plot.stop()
```

## The BulletLab Control Window

```python
from bulletlab.ui import BulletLabUI
from bulletlab.telemetry import TelemetryManager

telemetry = TelemetryManager()
telemetry.watch("speed", lambda: robot.speed)

app = BulletLabUI(sim=sim, robots=[robot], telemetry=telemetry)

# Add a custom control panel
@app.custom_panel("My Controls")
def my_panel():
    from bulletlab.ui import widgets as ui
    ui.button("Reset", robot.reset)
    ui.slider("Joint 1", lambda: robot.joints["iiwa_joint_1"].position, -3.14, 3.14,
              setter=lambda v: robot.joints["iiwa_joint_1"].set_position(v))

app.run()   # blocking — opens the ImGui window
```

## Next Steps

- [Robot Guide](guides/robot_guide.md) — detailed robot loading and control
- [Telemetry Guide](guides/telemetry_guide.md) — monitoring robot state
- [UI Guide](guides/ui_guide.md) — building custom panels
- [Examples Guide](guides/example_guide.md) — running the example scripts
- [RL Guide](guides/rl_guide.md) — implementing reinforcement learning
