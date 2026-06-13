# Plotting Guide

BulletLab provides two plotting options:

1. **LivePlot** — a full PyQtGraph window with zoom/pan
2. **PlotsPanel** — lightweight ImGui sparklines inside the BulletLab UI

## LivePlot (PyQtGraph)

```python
from bulletlab.plotting import LivePlot

plot = LivePlot(
    title="Robot Telemetry",
    max_points=500,            # rolling buffer size
    update_interval_ms=33,     # ~30 fps refresh
    y_label="Value",
    x_label="Time (s)",
)

# Register data series
plot.watch("Speed",  lambda: robot.speed, color="#00ff88")
plot.watch("Roll",   lambda: robot.roll,  color="#ff4488")
plot.watch("Height", lambda: robot.base_position[2], color="#44aaff")

# Open window
plot.start()

# Update in simulation loop
for _ in range(5000):
    sim.step()
    plot.update(t=sim.elapsed_time)

# Controls
plot.pause()    # freeze updates
plot.resume()   # unfreeze
plot.clear()    # clear all data

# Export
plot.export("speed_chart.png")

plot.stop()
```

## Inline Plots Panel (ImGui)

When using `BulletLabUI`, a **Plots Panel** is automatically shown with sparklines for all telemetry channels.

No extra code needed — just register channels in `TelemetryManager` and the sparklines appear automatically.

## Color Strings

Colors for `LivePlot.watch()` accept CSS hex strings:

| Color | Code |
|-------|------|
| Bright green | `"#00ff88"` |
| Hot pink | `"#ff4488"` |
| Sky blue | `"#44aaff"` |
| Orange | `"#ff8844"` |
| Yellow | `"#ffdd44"` |
| White | `"#ffffff"` |
