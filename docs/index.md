<h1>
  <img src="https://raw.githubusercontent.com/NuclearVenom/BulletLab/main/docs/assets/logo.png" width="60" align="center" alt="[logo]">
  BulletLab
</h1>

<div>Developed  by  <span class="author-name">Ranasurya Ghosh</span></div>


---

**A high-level robotics simulation and experimentation framework built on PyBullet.**

BulletLab provides a high-level object-oriented interface to [PyBullet](https://pybullet.org/wordpress/) that simplifies robotics experimentation by exposing joints, links, sensors, and environments as intuitive Python objects instead of raw physics engine IDs. It combines real-time simulation with a [ImGui](https://www.dearimgui.com/)-powered modern interface for interactive control, parameter tuning, telemetry visualization, and experiment management, while also offering reinforcement learning integration for training and evaluating autonomous robotic systems within a unified workflow.

## Why BulletLab?

| Without BulletLab | With BulletLab |
|---|---|
| `p.setJointMotorControl2(robot_id, i, p.VELOCITY_CONTROL, ...)` | `robot.joints["motor"].velocity = 15` |
| `p.changeDynamics(robot_id, i, mass=5)` | `robot.links["wheel"].mass = 5` |
| `p.getBasePositionAndOrientation(...)` | `robot.base_position` |
| **Complex IDs everywhere** | **Named Python objects** |


## Key Features
- **Object-oriented robot interface** — joints and links as Python objects
- **ImGui control window** — separate from PyBullet visualization
- **Live telemetry** — watch any robot state variable
- **Data logging** — CSV and JSON output
- **Live plots** — PyQtGraph-powered real-time charts
- **RL-ready** — clean state/action interface, no ML framework required
- **Generic** — works with any URDF or MJCF robot

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
git clone https://github.com/NuclearVenom/BulletLab.git
cd BulletLab
pip install -e ".[dev]"
```
