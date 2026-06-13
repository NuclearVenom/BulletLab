# Telemetry Guide

The telemetry system lets you watch any callable data source and accumulate a rolling history.

## Basic Usage

```python
from bulletlab.telemetry import TelemetryManager

telemetry = TelemetryManager()
telemetry.watch("Speed",  lambda: robot.speed, unit="m/s")
telemetry.watch("Roll",   lambda: robot.roll,  unit="rad")
telemetry.watch("Height", lambda: robot.base_position[2], unit="m")

# In the simulation loop:
for _ in range(1000):
    sim.step()
    telemetry.update(t=sim.elapsed_time)

# Get the latest values
print(telemetry.snapshot())
# → {"Speed": 2.4, "Roll": 0.02, "Height": 0.31}

# Get a specific channel
speed = telemetry.get("Speed")
```

## Watching Joint States

```python
for joint in robot.controllable_joints[:4]:
    telemetry.watch(
        f"joint_{joint.name}",
        (lambda j: lambda: j.position)(joint),   # closure over joint
        unit="rad",
    )
```

## Accessing History

```python
# Full history for a channel: [(t0, v0), (t1, v1), ...]
history = telemetry.history("Speed")

# Just values: [v0, v1, v2, ...]
values = telemetry.values_array("Speed")
```

## Clearing Data

```python
telemetry.clear_history()   # clear all history buffers
telemetry.unwatch("Speed")  # remove a specific channel
telemetry.clear_all()       # remove all channels
```

## Channel Properties

```python
ch = telemetry.channels["Speed"]
print(ch.name)       # "Speed"
print(ch.unit)       # "m/s"
print(ch.latest)     # most recent value
print(ch.history)    # deque of (timestamp, value)
print(ch.timestamps) # list of timestamps
print(ch.values)     # list of values
```
