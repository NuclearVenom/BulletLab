<div><span class="hero-section">
<h1>
  <img src="https://raw.githubusercontent.com/NuclearVenom/BulletLab/main/docs/assets/logo.png" width="80" align="bottom" alt="[logo]"> 
  <span class="hero-title">
  BulletLab 
  </span>
</h1>

<div>Developed  by  <a href="https://www.linkedin.com/in/ranasuryaghosh/" target="_blank" class="author-name">Ranasurya Ghosh</a></div>
</span></div>

---

**A high-level robotics simulation and experimentation framework built on PyBullet.**

BulletLab provides a high-level object-oriented interface to [PyBullet](https://pybullet.org/wordpress/) that simplifies robotics experimentation by exposing joints, links, sensors, and environments as intuitive Python objects instead of raw physics engine IDs. It combines real-time simulation with a [Dear ImGui](https://www.dearimgui.com/)-powered modern interface for interactive control, parameter tuning, telemetry visualization, and experiment management, while also offering reinforcement learning integration for training and evaluating autonomous robotic systems within a unified workflow.

## Why BulletLab?

| <h3>Without BulletLab</h3> | <h3>With BulletLab</h3> |
|---|---|
| `p.setJointMotorControl2(robot_id, i, p.VELOCITY_CONTROL, ...)` | `robot.joints["motor"].velocity = 15` |
| `p.changeDynamics(robot_id, i, mass=5)` | `robot.links["wheel"].mass = 5` |
| `p.getBasePositionAndOrientation(...)` | `robot.base_position` |
| **Complex IDs everywhere** | **Named Python objects** |


## Key Features
- **⚡ One-Line Model Deployment (`quickLaunch`)** — deploy and inspect any model (local URDF or [Arsenal package](guides/arsenal_guide.md)) with a single line of code, complete with interactive 3-mode joint controls, telemetry, and camera tracking
- **Object-oriented robot interface** — joints and links as Python objects
- **Dear ImGui control window** — modern interface, separate from PyBullet visualization
- **Interactive UI Console** — live test API calls, script sequential movements, and register custom [commands](guides/console_guide.md#built-in-commands)
- **[BulletLab Arsenal](guides/arsenal_guide.md)** — built-in model registry to seamlessly download and spawn high-quality robots on the fly
- **Live telemetry** — watch any robot state variable
- **Data logging** — CSV and JSON output
- **Live plots** — ImPlot-powered real-time charts
- **RL-ready** — clean state/action interface, no ML framework required
- **Generic** — works with any URDF or MJCF robot

## Quick Start

### Instant Deployment (`quickLaunch`)

Deploy any robot model in a full interactive simulation with rich UI controls in **just one line**:

```python
import bulletlab

# Deploy a built-in URDF or local file
bulletlab.quickLaunch("kuka_iiwa/model.urdf")

# Or deploy directly from BulletLab Arsenal
bulletlab.quickLaunch("arsenal:reference_bot")
```

### Custom Simulation Script

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

> **Requirements:** Python 3.11–3.13, 64-bit. The BulletLab GUI dependencies use prebuilt binary wheels on supported Windows Python versions, so no C++ compiler is required for the normal Windows installation.

```bash
pip install bulletlab
```

Or from source:

```bash
git clone https://github.com/NuclearVenom/BulletLab.git
cd BulletLab
pip install -e ".[dev]"
```
