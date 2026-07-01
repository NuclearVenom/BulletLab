<h1>
  <img src="https://raw.githubusercontent.com/NuclearVenom/BulletLab/main/docs/assets/logo.png" width="40" align="center" alt="[logo]">
  BulletLab
</h1>

Developed by [Ranasurya Ghosh](https://github.com/NuclearVenom)


>**A robotics experimentation framework that transforms PyBullet robots into intuitive Python objects, with modern ImGui-based controls, telemetry, visualization, and reinforcement learning workflows.**

[![Python 3.10](https://img.shields.io/badge/Python-3.10-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-2B9348?style=flat)](LICENSE)
[![BulletLab Arsenal](https://img.shields.io/badge/Registry-BulletLab_Arsenal-239281?style=plastic)](https://github.com/NuclearVenom/BulletLab-Arsenal)

**Install BulletLab library:** `pip install bulletlab`<br><br>
[![Read Documentation](https://img.shields.io/badge/Read_The_Documentation-2094F3?style=for-the-badge)](https://nuclearvenom.github.io/BulletLab/)
<br><br>

![BulletLab example UI](https://raw.githubusercontent.com/NuclearVenom/BulletLab/main/assets/bulletlab_ui.png)

---

## What is BulletLab?

BulletLab provides a high-level object-oriented interface to [PyBullet](https://pybullet.org/wordpress/) that simplifies robotics experimentation by exposing joints, links, sensors, and environments as intuitive Python objects instead of raw physics engine IDs. It combines real-time simulation with a [ImGui](https://www.dearimgui.com/)-powered modern interface for interactive control, parameter tuning, telemetry visualization, and experiment management, while also offering reinforcement learning integration for training and evaluating autonomous robotic systems within a unified workflow.

**Instead of this:**
```python
p.setJointMotorControl2(
    robot_id, joint_index,
    controlMode=p.VELOCITY_CONTROL,
    targetVelocity=15,
    force=100
)
```

**You write this:**
```python
robot.joints["motor"].velocity = 15
```

### BulletLab Arsenal: The Official Package Registry

Just as Python has PyPI for software packages, BulletLab has **[Arsenal](https://github.com/NuclearVenom/BulletLab-Arsenal)** for verified robotics assets. 

Arsenal is the official registry of the BulletLab ecosystem. It solves the long-standing problem of hunting down compatible URDFs and manually fixing missing meshes. Arsenal provides:

* **Verified Robot Packages:** Curated, community-contributed models guaranteed to load correctly.
* **One-Line Installation:** Permanently download assets to your local machine (`Robot.install()`).
* **Direct Loading:** Stream assets directly into your session cache without permanently modifying your filesystem (`Robot.load("arsenal:...")`).
* **Standardized Package Format:** Powered by machine-readable manifests (`metadata.json`) for automated validation.

Whether you are conducting reproducible research or building quick demos, Arsenal ensures you spend less time configuring assets and more time writing robotics code.

---

## Architecture

BulletLab uses a **two-window architecture**:

| Window | Purpose |
|--------|---------|
| PyBullet Native Window | Physics simulation, 3D rendering, camera |
| BulletLab ImGui Window | Control panels, telemetry, live plots, console |

These windows communicate through Python objects. BulletLab does **not** attempt to replace PyBullet's renderer or embed ImGui inside the simulation viewport.

---

## Quick Start

### Installation

**Install from PyPI**
```bash
pip install bulletlab
```

**Developer Installation**
```bash
git clone https://github.com/NuclearVenom/BulletLab.git
cd BulletLab
pip install -e .
```

### Basic Example

```python
from bulletlab import Simulation, Robot
from bulletlab.ui import BulletLabUI

# Create simulation
sim = Simulation()
sim.start()

# Load robot
robot = Robot.load("path/to/robot.urdf", sim=sim)

# Control joints by name
robot.joints["wheel_left"].velocity = 10
robot.joints["wheel_right"].velocity = 10

# Modify physics parameters
robot.links["chassis"].mass = 5.0
robot.links["wheel_fl"].friction = 1.2

# Get robot state
state = robot.get_state()
print(f"Position: {robot.base_position}")
print(f"Roll: {robot.roll:.2f}°")

# Build UI
ui = BulletLabUI(sim=sim)
ui.register_panel(...)
ui.run()
```

### Telemetry & Logging

```python
from bulletlab.telemetry import TelemetryManager
from bulletlab.logging import DataLogger

telemetry = TelemetryManager()
telemetry.watch("Speed", lambda: robot.base_velocity[0])
telemetry.watch("Roll",  lambda: robot.roll)

logger = DataLogger()
logger.watch("speed", lambda: robot.base_velocity[0])
logger.start("run1.csv")

for _ in range(1000):
    sim.step()
    telemetry.update()
    logger.step()

logger.stop()
```

### Live Plotting

```python
from bulletlab.plotting import LivePlot

plot = LivePlot(title="Robot Speed")
plot.watch("Speed", lambda: robot.base_velocity[0], color="#00ff88")
plot.start()

for _ in range(1000):
    sim.step()
    plot.update()
```

### Camera Follow

```python
from bulletlab import Simulation, Robot, CameraFollow

sim = Simulation(mode="gui").start()
robot = Robot.load("husky/husky.urdf", sim=sim, position=(0, 0, 0.3))

# One line — camera glides after the robot (smooth mode by default)
cam = CameraFollow(robot, sim)

# Or pick a mode:
cam = CameraFollow(robot, sim, mode="snap")    # locks instantly
cam = CameraFollow(robot, sim, mode="smooth")  # cinematic glide
cam = CameraFollow(robot, sim, mode="chase")   # always behind the robot

while sim.is_connected:
    sim.step()
    cam.update()   # ← one call keeps the camera centred on the robot
```

### Hover Highlighting

```python
from bulletlab import Simulation, Robot, RobotHighlighter
from bulletlab.ui import BulletLabUI

sim = Simulation(mode="gui").start()
robot = Robot.load("kuka_iiwa/model.urdf", sim=sim)

# One line — hover any joint/link in the UI to see it glow in 3D
hl = RobotHighlighter(robot, sim)
app = BulletLabUI(sim=sim, robots=[robot], highlighter=hl)
app.run()
```

Hovering over an Explorer row or a Properties slider instantly highlights
the matching 3D part in the PyBullet window with an orange pulsing glow.

### BulletLab Arsenal

[BulletLab Arsenal](https://github.com/NuclearVenom/BulletLab-Arsenal) is the official
robot asset registry — load community robots with a single line, no manual download required.

```python
from bulletlab import Simulation, Robot
from bulletlab.core.world import World

sim = Simulation(mode="gui").start()
World(sim).load_plane()

# Install permanently to ~/.bulletlab/packages/
Robot.install("reference_bot")

# Load directly from Arsenal into a session cache (cleaned up on exit)
robot = Robot.load("arsenal:reference_bot", sim=sim, position=(0, 0, 0.3))

# Load a specific model
robot = Robot.load("arsenal:reference_bot/BLem1", sim=sim)
```

All standard `Robot.load()` parameters — `position`, `fixed_base`, `tilt`, etc. — work
identically with Arsenal sources.

### ImGui Control Panel

```python
from bulletlab.ui import BulletLabUI
from bulletlab.ui import widgets as ui

app = BulletLabUI(sim=sim, robots=[robot])

@app.custom_panel("My Controls")
def my_panel():
    ui.button("Reset", robot.reset)
    ui.slider("Wheel Mass", robot.links["wheel"].mass, 0.1, 20,
              setter=lambda v: setattr(robot.links["wheel"], "mass", v))
    ui.checkbox("Motors Enabled", lambda: motors_on,
                setter=lambda v: toggle_motors(v))

app.run()
```

### Virtual Joystick

Add an interactive 2D joystick to any custom panel for intuitive, gamepad-style robot control.

```python
@app.custom_panel("Drive")
def drive_panel():
    ui.joystick(
        "Rover Drive",
        on_y=lambda v: [setattr(robot.joints["wheel_left"],  "velocity", v * 10),
                        setattr(robot.joints["wheel_right"], "velocity", v * 10)],
        on_x=lambda v: [setattr(robot.joints["wheel_left"],  "velocity", -v * 5),
                        setattr(robot.joints["wheel_right"], "velocity",  v * 5)],
        snap=True,                       # Handle snaps to center on release
        size=80,                         # Joystick circle radius (pixels)
        handle_color=(0.2, 0.8, 0.4, 1.0),
    )
```

- **`snap=True`** — robot stops when you release (default)
- **`snap=False`** — handle latches; robot keeps driving at the last commanded speed
- Drop multiple joysticks in the same panel (use `ui.same_line()` between them)
- Each joystick can have its own color and size

---


## Supported Robot Types

BulletLab is completely generic — no code assumes a specific robot type:

- Cars & rovers
- Drones & quadrotors
- Robotic arms
- Self-balancing robots
- Quadrupeds
- Humanoids
- Custom mechanisms

---

## Reinforcement Learning

BulletLab exposes clean state/action interfaces without depending on any ML framework:

```python
# Compatible with any RL approach
state = robot.get_state()      # → numpy array
action = my_policy(state)      # → numpy array
robot.apply_action(action)     # → updates joints

# Manual Q-learning, SARSA, evolutionary algorithms — all supported
```

---

## Examples

| Example | Description |
|---------|-------------|
| `examples/01_differential_drive_rover.py` | Rover with wheel velocity control |
| `examples/02_robotic_arm.py` | Joint position control with ImGui sliders |
| `examples/03_self_balancing_robot.py` | PD controller for balance |
| `examples/04_drone_parameter_tuning.py` | Thrust/mass parameter exploration |
| `examples/05_generic_robot_inspector.py` | Load any URDF and inspect it |
...and more

Run any example:
```bash
python examples/01_differential_drive_rover.py
```

---

## Documentation

The full documentation is available online at **[https://nuclearvenom.github.io/BulletLab/](https://nuclearvenom.github.io/BulletLab/)**

### Building Locally (For Contributors)

If you wish to edit or preview the documentation locally:
```bash
pip install -e ".[dev]"
mkdocs serve
```
Then visit http://localhost:8000

---

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v --cov=bulletlab --cov-report=term-missing
```

---

## Technology Stack

| Component | Library |
|-----------|---------|
| Physics | PyBullet |
| UI | Dear ImGui (pyimgui) |
| Data | NumPy, Pandas |
| Config | PyYAML |
| Plotting | PyQtGraph |
| Testing | PyTest |
| Docs | MkDocs + mkdocstrings |

## For AI Agents & LLMs

BulletLab is designed to be highly predictable and LLM-friendly. If you are an AI agent writing code for a user:
1. **Read [`llms.txt`](llms.txt)** in the repository root for a dense, AI-optimized API summary.
2. Check the **[Cookbook & Snippets](docs/cookbook.md)** for copy-pasteable implementations of common tasks.
3. Use the `robot.joints[name]` API over `pybullet` integer IDs whenever possible.

---

## Community

We welcome contributions and feedback! Check out our community resources:

* **[Contributing Guide](CONTRIBUTING.md)** – How to build, test, and contribute to BulletLab
* **[Code of Conduct](CODE_OF_CONDUCT.md)** – Our community standards
* **[Security Policy](SECURITY.md)** – How to report security vulnerabilities responsibly
* **[Roadmap](ROADMAP.md)** – Our vision for future releases
* **[Citation](CITATION.cff)** – How to cite BulletLab in academic research

---

## License

MIT License — see [LICENSE](LICENSE) for details.
