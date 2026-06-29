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

---

## Joystick Widget

BulletLab includes a built-in 2D virtual joystick that you can drop into any custom panel.
It renders a draggable handle inside a circular ring and calls your callbacks **every frame**
for smooth, continuous control — exactly like a hardware joystick.

### Basic Usage

```python
from bulletlab.ui import BulletLabUI
from bulletlab.ui import widgets as ui

app = BulletLabUI(sim=sim, robots=[robot])

@app.custom_panel("Drive")
def drive_panel():
    ui.joystick(
        "Rover Drive",
        on_y=lambda v: [
            setattr(robot.joints["wheel_left"],  "velocity", v * 10),
            setattr(robot.joints["wheel_right"], "velocity", v * 10),
        ],
        on_x=lambda v: [
            setattr(robot.joints["wheel_left"],  "velocity", (-v) * 5),
            setattr(robot.joints["wheel_right"], "velocity",   v  * 5),
        ],
    )

app.run()
```

**Axis convention:**
- `on_y`: positive = handle dragged **up** = "forward"
- `on_x`: positive = handle dragged **right** = "right"

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `label` | `str` | *(required)* | Unique name shown above the widget |
| `on_x` | `Callable[[float], None]` | `None` | Called every frame with X value in `[-1, 1]` |
| `on_y` | `Callable[[float], None]` | `None` | Called every frame with Y value in `[-1, 1]` |
| `snap` | `bool` | `True` | If `True`, handle returns to center on mouse release |
| `size` | `int` | `60` | Radius of the outer ring in pixels |
| `handle_color` | `tuple[float,float,float,float]` | `(0.2, 0.6, 1.0, 1.0)` | RGBA color of the draggable handle |

### `snap=True` vs `snap=False`

```python
# snap=True (default) — robot stops when you release the joystick
ui.joystick("Drive", on_y=lambda v: setattr(robot.joints["drive"], "velocity", v * 10))

# snap=False — handle latches in place; robot keeps driving after release
ui.joystick("Cruise", on_y=lambda v: setattr(robot.joints["drive"], "velocity", v * 10),
            snap=False, handle_color=(0.2, 0.9, 0.4, 1.0))
```

### Multiple Joysticks

You can include as many joysticks as you like in a single panel.
Use `ui.same_line()` between them to place them side-by-side.
Each joystick must have a **unique label**.

```python
@app.custom_panel("Arm Control")
def arm_panel():
    # Left joystick: shoulder
    ui.joystick(
        "Shoulder",
        on_y=lambda v: setattr(robot.joints["shoulder_joint"], "velocity", v * 5),
        handle_color=(0.2, 0.6, 1.0, 1.0),
    )

    ui.same_line()

    # Right joystick: elbow — different color
    ui.joystick(
        "Elbow",
        on_y=lambda v: setattr(robot.joints["elbow_joint"], "velocity", v * 5),
        handle_color=(1.0, 0.5, 0.1, 1.0),
    )
```

### Custom Functions

The callbacks accept any Python callable, so you can use full multi-line functions:

```python
def drive_forward(v):
    speed = v * 15.0
    robot.joints["wheel_left"].velocity  = speed
    robot.joints["wheel_right"].velocity = speed

def turn(v):
    robot.joints["wheel_left"].velocity  += -v * 5.0
    robot.joints["wheel_right"].velocity +=  v * 5.0

@app.custom_panel("Rover")
def rover_panel():
    ui.joystick("Drive", on_y=drive_forward, on_x=turn, size=80)
```

---

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
| `ui.toggle_switch(label, getter, setter, color_on, color_off, width, height)` | Capsule toggle switch |
| `ui.joystick(label, on_x, on_y, snap, size, handle_color)` | 2D virtual joystick |

