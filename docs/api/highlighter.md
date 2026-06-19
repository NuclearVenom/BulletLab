# Robot Highlighter

`RobotHighlighter` lights up joints and links in the PyBullet 3D viewport
the moment the user moves their mouse over any related element in the UI —
Explorer rows, Properties sliders, buttons, or custom widgets.

## Quickstart

```python
from bulletlab import Simulation, Robot, RobotHighlighter
from bulletlab.ui import BulletLabUI

sim = Simulation(mode="gui").start()
robot = Robot.load("kuka_iiwa/model.urdf", sim=sim)

# One-liner — pass to BulletLabUI and it works automatically
hl = RobotHighlighter(robot, sim)
app = BulletLabUI(sim=sim, robots=[robot], highlighter=hl)
app.run()
```

No other code required. The UI wires up the hover detection and 3D colour
changes internally.

---

## What triggers a highlight?

| Where you hover | What lights up |
|---|---|
| Joint name in the **Explorer** tree | The joint's child link in 3D |
| Link name in the **Explorer** tree | That link in 3D |
| Any slider/drag in the **Properties** panel for a Joint | Same joint's 3D link |
| Any slider/drag in the **Properties** panel for a Link | That link in 3D |

As soon as the mouse leaves the element, the colour is instantly restored.

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `robot` | `Robot` | required | Robot whose parts will be highlighted |
| `sim` | `Simulation` | required | Simulation instance |
| `color` | `tuple[float,float,float,float]` | `(1.0, 0.55, 0.05, 1.0)` | RGBA highlight colour (orange) |
| `pulse` | `bool` | `True` | Whether the glow breathes/pulses |

---

## Custom colours and pulse

```python
# Blue highlight, no pulse
hl = RobotHighlighter(robot, sim, color=(0.2, 0.6, 1.0, 1.0), pulse=False)

# Change colour at runtime
hl.color = (0.0, 1.0, 0.4, 1.0)   # green
hl.pulse = True
```

---

## Manual API (custom panels)

Call `set_hover()` in your own panel after any ImGui widget:

```python
@app.custom_panel("Joint Control")
def my_panel():
    changed, val = imgui.slider_float("Speed", speed, -20, 20)
    if imgui.is_item_hovered():
        hl.set_hover(robot.joints["wheel_left"])   # highlight that joint

    if imgui.button("Reset"):
        robot.reset()
    if imgui.is_item_hovered():
        hl.set_hover(robot.links["base_link"])     # highlight base
```

To clear all highlights immediately:

```python
hl.clear()
```

---

## API Reference

::: bulletlab.core.highlighter.RobotHighlighter
    options:
      show_source: true
