# UI Guide

The BulletLab UI is a separate Dear ImGui window that runs alongside the PyBullet simulation window.

## Architecture

```
┌─────────────────────────┐  ┌──────────────────────────────┐
│   PyBullet Window       │  │   BulletLab ImGui Window     │
│  • Physics simulation   │  │  • Explorer Panel            │
│  • 3D rendering         │  │  • Properties Panel          │
│  • Camera controls      │  │  • Telemetry Panel           │
│                         │  │  • Console Panel             │
│                         │  │  • Plots Panel               │
│                         │  │  • Custom Panels             │
└─────────────────────────┘  └──────────────────────────────┘
         communicate via Python objects
```

## Basic Usage

```python
from bulletlab.ui import BulletLabUI
from bulletlab.telemetry import TelemetryManager

telemetry = TelemetryManager()
telemetry.watch("Speed", lambda: robot.speed)

app = BulletLabUI(sim=sim, robots=[robot], telemetry=telemetry)
app.run()    # blocking
```

## Non-Blocking Usage

```python
app = BulletLabUI(sim=sim, robots=[robot])
app.start()

while True:
    sim.step()
    telemetry.update(t=sim.elapsed_time)
    app.step()
    if app.should_close:
        break

app.stop()
```

## Built-in Panels

| Panel | Purpose |
|-------|---------|
| **Explorer** | Scene tree: Simulation → Robots → Joints/Links |
| **Properties** | Editable properties for selected object |
| **Telemetry** | Live key-value table |
| **Plots** | Inline sparkline charts |
| **Console** | Interactive Python REPL |

## Custom Panels

### Using the decorator

```python
from bulletlab.ui import BulletLabUI
from bulletlab.ui import widgets as ui

app = BulletLabUI(sim=sim, robots=[robot])

@app.custom_panel("Motor Control")
def motor_panel():
    ui.text("Robot", robot.name)
    ui.separator()
    ui.slider("Left Wheel",  lambda: robot.joints["wheel_l"].velocity, -20, 20,
              setter=lambda v: setattr(robot.joints["wheel_l"], "velocity", v))
    ui.slider("Right Wheel", lambda: robot.joints["wheel_r"].velocity, -20, 20,
              setter=lambda v: setattr(robot.joints["wheel_r"], "velocity", v))
    ui.separator()
    ui.button("Stop All", lambda: [setattr(j, "velocity", 0) for j in robot.controllable_joints])

app.run()
```

### Using register_panel

```python
app.register_panel("My Panel", my_render_function)
```

## Widget Reference

| Function | Description |
|----------|-------------|
| `ui.button(label, callback)` | Clickable button |
| `ui.text(label, value)` | Read-only text field |
| `ui.slider(label, getter, min, max, setter)` | Float slider |
| `ui.drag_float(label, getter, setter, speed)` | Drag-to-edit field |
| `ui.input_float(label, getter, setter)` | Float input box |
| `ui.checkbox(label, getter, setter)` | Boolean toggle |
| `ui.color_edit(label, getter, setter)` | RGB color picker |
| `ui.combo(label, items, getter, setter)` | Dropdown list |
| `ui.collapsing_header(label)` | Collapsible section |
| `ui.separator(label)` | Horizontal divider |
| `ui.tooltip(text)` | Hover tooltip |

## Console Panel

The console provides an interactive Python REPL inside the UI:

```python
# Example commands you can type in the console:
robot.links["wheel"].mass = 10
robot.joints["motor"].velocity = 15
print(robot.base_position)
sim.pause()
```

The console namespace includes `sim`, `robot` (first robot), and `telemetry` by default.
