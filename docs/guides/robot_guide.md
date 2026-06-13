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
