# BulletLab

**A fast, lightweight, research-oriented robotics experimentation workbench built on PyBullet.**

BulletLab provides a high-level Python API over PyBullet, making robotics experimentation significantly easier. Rather than working with raw physics engine IDs and low-level calls, you interact with structured Python objects.

## Why BulletLab?

| Without BulletLab | With BulletLab |
|---|---|
| `p.setJointMotorControl2(robot_id, i, p.VELOCITY_CONTROL, ...)` | `robot.joints["motor"].velocity = 15` |
| `p.changeDynamics(robot_id, i, mass=5)` | `robot.links["wheel"].mass = 5` |
| `p.getBasePositionAndOrientation(...)` | `robot.base_position` |
| Complex IDs everywhere | Named Python objects |

## Key Features

- 🤖 **Object-oriented robot interface** — joints and links as Python objects
- 🎮 **ImGui control window** — separate from PyBullet visualization
- 📊 **Live telemetry** — watch any robot state variable
- 📁 **Data logging** — CSV and JSON output
- 📈 **Live plots** — PyQtGraph-powered real-time charts
- 🧮 **RL-ready** — clean state/action interface, no ML framework required
- 🔧 **Generic** — works with any URDF or MJCF robot

## Quick Start

```python
from bulletlab import Simulation, Robot

sim = Simulation()
sim.start()

robot = Robot.load("kuka_iiwa/model.urdf", sim=sim)

# Control by name
robot.joints["iiwa_joint_1"].set_position(1.0)
robot.links["iiwa_link_0"].mass = 5.0

while True:
    sim.step()
```

## Installation

```bash
pip install bulletlab
```

Or from source:

```bash
git clone https://github.com/bulletlab/bulletlab
cd bulletlab
pip install -e ".[dev]"
```
