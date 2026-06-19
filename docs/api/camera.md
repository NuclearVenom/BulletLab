# Camera Follow

BulletLab's `CameraFollow` keeps the PyBullet 3D camera locked on a moving
robot with a single `update()` call per step. Three modes are available.

## Quickstart

```python
from bulletlab import Simulation, Robot, CameraFollow

sim = Simulation(mode="gui").start()
robot = Robot.load("husky/husky.urdf", sim=sim, position=(0, 0, 0.3))

cam = CameraFollow(robot, sim)          # defaults: smooth mode, 4 m back

while sim.is_connected:
    sim.step()
    cam.update()                        # ← one call per step
```

---

## Modes

| Mode | Constant | Behaviour |
|------|----------|-----------|
| **Snap** | `"snap"` | Camera target locks to the robot instantly every frame |
| **Smooth** | `"smooth"` | Camera target glides toward the robot (lerp). Cinematic feel |
| **Chase** | `"chase"` | Camera yaw rotates with the robot's heading — always behind it |

```python
# Snap – no lag
cam = CameraFollow(robot, sim, mode="snap")

# Smooth – gliding (default)
cam = CameraFollow(robot, sim, mode="smooth", lerp=0.08)

# Chase – 3rd-person, always behind the robot
cam = CameraFollow(robot, sim, mode="chase", distance=5.0, pitch=-20)
```

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `robot` | `Robot` | required | Robot to follow |
| `sim` | `Simulation` | required | Simulation instance |
| `mode` | `str` | `"smooth"` | `"snap"`, `"smooth"`, or `"chase"` |
| `distance` | `float` | `4.0` | Camera distance from robot (metres) |
| `pitch` | `float` | `-25.0` | Vertical camera angle (degrees, negative = looking down) |
| `yaw` | `float` | `45.0` | Horizontal angle (snap/smooth only, degrees) |
| `lerp` | `float` | `0.08` | Smooth/chase glide speed (0 = frozen, 1 = instant) |
| `height_offset` | `float` | `0.2` | Extra height above robot base (metres) |

---

## Runtime Control

All parameters are writable at any time — change mode or settings on the fly:

```python
cam.mode     = "chase"   # switch mode mid-run
cam.distance = 6.0       # zoom out
cam.pitch    = -35.0     # look more steeply down
cam.lerp     = 0.15      # glide faster
```

---

## API Reference

::: bulletlab.core.camera.CameraFollow
    options:
      show_source: true
