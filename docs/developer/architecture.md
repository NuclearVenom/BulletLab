# Architecture

## Overview

BulletLab is designed around a **two-window, shared-state** architecture.

```
┌──────────────────────────────────────────────────────────────┐
│                     Python Process                           │
│                                                              │
│  ┌─────────────────┐    Python objects    ┌───────────────┐ │
│  │ PyBullet Server │ ←──────────────────→ │ BulletLabUI   │ │
│  │ (physics + 3D)  │    Robot, Joint,     │ (ImGui window)│ │
│  └─────────────────┘    Link, Sim         └───────────────┘ │
│         ↑                                         ↑          │
│   pybullet.so                               GLFW + OpenGL   │
└──────────────────────────────────────────────────────────────┘
```

## Module Dependency Graph

```
bulletlab/
├── core/
│   ├── simulation.py    ← depends on pybullet
│   └── world.py         ← depends on simulation
│
├── robot/
│   ├── robot.py         ← depends on simulation, joint, link, math_utils
│   ├── joint.py         ← depends on simulation
│   └── link.py          ← depends on simulation
│
├── telemetry/
│   ├── manager.py       ← depends on channel
│   └── channel.py       ← no BulletLab dependencies
│
├── logging/
│   ├── logger.py        ← depends on csv_writer, json_writer
│   ├── csv_writer.py    ← stdlib only
│   └── json_writer.py   ← stdlib only
│
├── plotting/
│   └── live_plot.py     ← depends on pyqtgraph (optional)
│
├── ui/
│   ├── app.py           ← depends on all panels, imgui, glfw
│   ├── widgets.py       ← depends on imgui (optional)
│   └── panels/
│       ├── explorer.py  ← depends on robot types
│       ├── properties.py← depends on robot types
│       ├── telemetry.py ← depends on TelemetryManager
│       ├── console.py   ← stdlib only
│       └── plots.py     ← depends on TelemetryManager
│
└── utils/
    ├── math_utils.py    ← numpy only
    ├── urdf_utils.py    ← pybullet_data
    └── timer.py         ← stdlib only
```

## Key Design Principles

### 1. Object-first Interface
All interactions go through Python objects. PyBullet body IDs and joint indices are never exposed to the user.

### 2. Property Propagation
Setting a property on a Python object immediately propagates to PyBullet:
```python
robot.links["wheel"].mass = 5.0
# → p.changeDynamics(body_id, link_idx, mass=5.0, ...)
```

### 3. Optional Dependencies
All UI and plotting dependencies are optional. BulletLab degrades gracefully:
- No ImGui → UI panels are no-ops
- No PyQtGraph → LivePlot prints a warning and does nothing
- No GLFW → BulletLabUI prints a message and returns

### 4. Separation of Concerns
- PyBullet handles **physics + 3D rendering**
- BulletLab handles **object abstraction + UI + telemetry + logging**
- No attempt to combine or replace either

### 5. RL Agnostic
BulletLab doesn't depend on or recommend any specific ML framework. The `get_state()` / `apply_action()` interface is compatible with anything that operates on NumPy arrays.
