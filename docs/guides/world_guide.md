# World Guide

The `World` class populates your simulation with environments, obstacles, and terrain.
You never need `import pybullet as p` for standard environment setup.

```python
from bulletlab import Simulation
from bulletlab.core.world import World

sim = Simulation().start()
world = World(sim)
```

## Flat Ground Plane

```python
world.load_plane()
```

## Loading URDFs & SDFs

```python
# Any URDF from pybullet_data or an absolute path
world.load_urdf("table/table.urdf", position=(1, 0, 0))

# Dynamic (not fixed) URDF
world.load_urdf("cube_small.urdf", position=(0, 0, 1), fixed=False)

# SDF file
world.load_sdf("stadium.sdf")
```

## Primitive Shapes

All factory methods return a body ID and register the body with the world for cleanup.

### Box

```python
# Static box obstacle (mass=0)
world.create_box(
    size=(1.0, 0.5, 0.4),        # full width, depth, height in metres
    position=(2, 0, 0.2),
    color=(0.7, 0.4, 0.2, 1.0),
)

# Dynamic box that falls under gravity
world.create_box((0.3, 0.3, 0.3), position=(0, 0, 2), mass=1.0)
```

### Sphere

```python
world.create_sphere(radius=0.25, position=(0, 2, 0.25), color=(0.2, 0.8, 0.2, 1))
```

### Capsule

```python
world.create_capsule(radius=0.1, height=0.6, position=(1, 1, 0.5))
```

## Heightfield Terrain

Build procedural terrain from any 2-D numpy array (or a flat list):

```python
import numpy as np, math

n = 256
xs = np.linspace(0, 6 * math.pi, n)
heights = np.outer(np.sin(xs), np.cos(xs))   # 2-D sine hills

world.load_heightfield(
    heights,
    xy_scale=0.08,            # metres per grid cell
    z_scale=0.4,              # vertical exaggeration
    color=(0.55, 0.45, 0.35, 1.0),   # dirt brown
)
```

**Multi-octave noise example** (as used in `examples/06_irregular_terrain.py`):

```python
import numpy as np, math

n = 256
np.random.seed(42)
h = np.zeros((n, n))
for amp, freq in [(0.6, 0.05), (0.3, 0.12), (0.1, 0.3)]:
    for i in range(n):
        for j in range(n):
            h[i, j] += amp * math.sin(freq * i) * math.cos(freq * j)
h += np.random.uniform(-0.15, 0.15, (n, n))

# Flat spawn zone at centre
cx, cy = n // 2, n // 2
h[cx-8:cx+8, cy-8:cy+8] = 0.0

world.load_heightfield(h, xy_scale=0.1, z_scale=0.25)
```

> **Tip:** Pass a flat `list[float]` plus explicit `rows=` and `cols=` if you generate
> heights outside numpy.

## Scattering Obstacles

Randomly place obstacles across a rectangular region:

```python
# 30 random boxes in a 20×20 m area
world.scatter_obstacles(
    count=30,
    kind="box",               # "box" | "sphere" | "capsule"
    size_range=(0.2, 0.6),   # random size range (metres)
    region=(-10, -10, 10, 10),
    color=(0.4, 0.4, 0.4, 1),
    seed=42,                  # for reproducibility
)

# Mix spheres as rolling hazards
world.scatter_obstacles(10, kind="sphere", size_range=(0.15, 0.4),
                        region=(-5, -5, 5, 5), mass=1.0)
```

## Removing Bodies

```python
rock = world.create_box((0.3, 0.3, 0.3), position=(1, 0, 0.15))
# ... later ...
world.remove_body(rock)   # removes from sim and tracking list
```

## Clearing Everything

```python
world.clear()   # removes all bodies this World instance created
```

## Gravity

```python
world.set_gravity(gz=-1.62)    # Moon
world.set_gravity(gz=-3.72)    # Mars
world.set_gravity(gz=-9.81)    # Earth (default)
```

## Tracking Body IDs

```python
print(world.body_ids)   # list of all body IDs this World created
```
