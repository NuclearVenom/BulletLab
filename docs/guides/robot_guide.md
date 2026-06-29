# Robot Guide

This guide covers everything about loading and controlling robots in BulletLab.

## Loading Robots

BulletLab supports URDF and MJCF formats. Use `Robot.load()`:

```python
from bulletlab import Simulation, Robot

sim = Simulation().start()

# Load from pybullet_data (by relative path)
robot = Robot.load("kuka_iiwa/model.urdf", sim=sim)

# Load with custom position and orientation
robot = Robot.load(
    "my_robot.urdf",
    sim=sim,
    position=(0, 0, 0.5),
    orientation=(0, 0, 0, 1),   # quaternion (x, y, z, w)
    fixed_base=False,
    scale=1.0,
    name="MyRobot",
)
```

### Loading with a Custom Tilt

Use the `tilt` parameter for an easy axis-angle shorthand — no quaternion maths required.
Pass `tilt=((ax, ay, az), angle_deg)` and BulletLab handles the rest.

```python
# Tilt 30° around the Y axis (nose-down / forward lean)
robot = Robot.load("laikago/laikago.urdf", sim=sim, tilt=((0, 1, 0), 30))

# Tilt 45° around the X axis (lean left / roll)
robot = Robot.load("laikago/laikago.urdf", sim=sim, tilt=((1, 0, 0), 45))

# Diagonal axis — automatically normalised
robot = Robot.load("laikago/laikago.urdf", sim=sim, tilt=((1, 1, 0), 60))

# Combine tilt with an explicit heading orientation
import pybullet as p, math
heading = p.getQuaternionFromEuler([0, 0, math.radians(90)])  # face East
robot = Robot.load("laikago/laikago.urdf", sim=sim,
                   orientation=heading, tilt=((0, 1, 0), 15))
```

| Axis | Effect |
|------|--------|
| `(1, 0, 0)` | Roll — lean left / right |
| `(0, 1, 0)` | Pitch — nose up / down |
| `(0, 0, 1)` | Yaw — spin on the spot |
| any direction | Normalised automatically |

The angle is always in **degrees**. When both `orientation` and `tilt` are given, the tilt
is applied *on top of* the base orientation (quaternion composition).


## Accessing Joints

Joints are accessible by name via `robot.joints`:

```python
# List all joints
print(list(robot.joints.keys()))

# Access a specific joint
joint = robot.joints["iiwa_joint_1"]
print(joint.position)    # current angle (rad)
print(joint.velocity)    # current velocity (rad/s)
print(joint.torque)      # applied torque (N·m)
print(joint.limits)      # (lower, upper) in rad
print(joint.is_fixed)    # True for fixed joints
```

## Controlling Joints

### Velocity Control
```python
robot.joints["wheel_left"].velocity = 10.0    # rad/s
```

### Position Control
```python
robot.joints["shoulder"].set_position(1.57)   # 90°
```

### Torque Control
```python
robot.joints["hip"].torque = 20.0             # N·m
```

### Resetting
```python
robot.joints["shoulder"].reset(pos=0.0, vel=0.0)
```

## Accessing Links

Links are accessible by name via `robot.links`:

```python
# List all links
print(list(robot.links.keys()))

# Access the base link
base = robot.links["base"]
print(base.mass)           # mass in kg
print(base.position)       # world position (x, y, z)
print(base.velocity)       # linear velocity (vx, vy, vz)
```

## Modifying Link Properties

All property setters call `pybullet.changeDynamics` immediately:

```python
robot.links["chassis"].mass = 5.0
robot.links["wheel_fl"].friction = 1.2
robot.links["bumper"].restitution = 0.5
robot.links["chassis"].linear_damping = 0.1
robot.links["chassis"].angular_damping = 0.05
```

## Base State

```python
robot.base_position          # (x, y, z) in meters
robot.base_orientation       # (x, y, z, w) quaternion
robot.base_velocity          # (vx, vy, vz) m/s
robot.base_angular_velocity  # (wx, wy, wz) rad/s
robot.roll                   # roll angle in rad
robot.pitch                  # pitch angle in rad
robot.yaw                    # yaw angle in rad
robot.speed                  # scalar speed in m/s
```

## Resetting the Robot

```python
# Reset to original load position
robot.reset()

# Reset to a specific pose
robot.reset(position=(0, 0, 1), orientation=(0, 0, 0, 1))
```

## RL-Compatible Interface

```python
# Get flat state vector (numpy array)
state = robot.get_state()
# [x, y, z, qx, qy, qz, qw, vx, vy, vz, wx, wy, wz, j0_pos, j1_pos, ..., j0_vel, j1_vel, ...]

# Apply velocity actions
action = my_policy(state)    # → numpy array of velocities
robot.apply_action(action)   # applies to all controllable joints

# Apply torque actions
robot.apply_torques(torques)
```

## Finding URDFs

```python
from bulletlab.utils.urdf_utils import find_urdf, list_available_urdfs

# Find a URDF by name
path = find_urdf("kuka_iiwa/model.urdf")

# List all available URDFs in pybullet_data
for urdf in list_available_urdfs():
    print(urdf)
```

## Applying External Forces & Torques

Use `robot.apply_force()` and `robot.apply_torque()` to push/spin the robot from outside
without needing `import pybullet as p`.

> **Important:** PyBullet clears external forces after every `sim.step()` call.
> Call `apply_force()` **inside your loop** every step for a continuous effect.

```python
# Upward thrust — simulate a drone motor every step
while sim.is_connected:
    robot.apply_force((0, 0, 20.0))   # 20 N upward (world frame)
    sim.step()

# Wind gust in world X direction
robot.apply_force((5.0, 0, 0))

# Apply force in the robot's own body frame
robot.apply_force((0, 0, 10.0), frame="local")

# Apply force to a specific link
robot.apply_force((2.0, 0, 0), link="gripper")

# Spin the base around the Z axis (world frame)
robot.apply_torque((0, 0, 3.0))

# Apply drag proportional to velocity (call every step)
vel = robot.base_velocity
robot.apply_force((-0.1 * vel[0], -0.1 * vel[1], -0.1 * vel[2]))
```

## Changing Physics Parameters

`robot.set_dynamics()` wraps PyBullet's `changeDynamics` — call it any time to adjust
mass, friction, restitution, and damping without touching raw PyBullet.

```python
# Change body mass at runtime
robot.set_dynamics(mass=5.0)            # base link

# Make wheels grippier
robot.set_dynamics("wheel_fl", lateral_friction=1.5)
robot.set_dynamics("wheel_fr", lateral_friction=1.5)

# Add bounciness to an end-effector
robot.set_dynamics("gripper", restitution=0.6)

# Reduce linear/angular damping for a drone-like feel
robot.set_dynamics(linear_damping=0.0, angular_damping=0.0)

# Multiple parameters at once
robot.set_dynamics("chassis",
                   mass=10.0,
                   lateral_friction=0.5,
                   restitution=0.1)

# Apply same dynamics to every link
for link_name in robot.links:
    robot.set_dynamics(link_name, rolling_friction=0.01)
```
