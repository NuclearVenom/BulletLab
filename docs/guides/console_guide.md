# Console Guide

The **BulletLab Console** is a built-in, interactive Python execution environment embedded directly within the BulletLab UI. 

It allows you to inspect the simulation, test out API calls on the fly, and even execute long-running scripts sequentially without freezing the physics or the UI.

---

## Why Use the Console?

1. **Live Debugging**: Inspect the state of your robots (e.g., `robot.joints['motor'].position`) instantly without adding print statements and restarting the simulation.
2. **Interactive Tuning**: Adjust PID gains, mass, friction, or other properties interactively to see their physical effects in real-time.
3. **Scripting Motions**: Write small multi-line scripts to sequence robot movements and delays without writing separate control loop threads.

---

## How to Use the Console

The console panel appears at the bottom-right of the BulletLab UI by default. It has two modes of operation:

### Single-Line Mode (REPL)
When you type a single Python statement or expression, it acts exactly like a standard Python REPL. It evaluates immediately and prints the output.

```python
>>> robot.links['wheel'].mass
    2.5
>>> robot.tilt('y', 45)
```

### Multi-Line Mode (Sequential Scripting)
When you expand the console (using the **Expand** button) or type a multi-line script (like a `for` loop), BulletLab hands the code to the **ConsoleEngine**.

The engine executes your script in a background thread, running **one statement per simulation frame**. This allows you to write sequential control logic without freezing the UI or the physics engine!

**Example:**
```python
# The loop will execute smoothly, holding the joint for 500ms on each iteration.
for i in range(5):
    robot.joints['arm_joint'].position = 1.0
    wait(500)
    robot.joints['arm_joint'].position = -1.0
    wait(500)
```

---

## Accessing the Namespace

Code executed in the console doesn't run in a vacuum. By default, the `BulletLabUI` injects key objects from your active script into the console's namespace.

If you initialized your UI like this:
```python
ui = BulletLabUI(sim=sim, robots=[my_robot], telemetry=telemetry)
```
Then the console will automatically have access to `sim`, `my_robot`, and `telemetry`. You can interact with these variables directly:
```python
>>> sim.timestep = 1/480
>>> my_robot.reset()
```

---

## Built-in Commands

BulletLab's latest version provides **12 built-in commands** out of the box to make console usage faster and more intuitive. Because of the dynamic namespace engine, you don't need to import anything to use them—they are always available.

### Utility Commands
* `wait(ms)`: Pause your script for `ms` milliseconds. The simulation and UI continue to run normally in the background.
* `step(n=1)`: Instantly force the simulation to advance by `n` physics steps.

### Simulation Commands
* `sim.start()`: Start the physics clock.
* `sim.pause()`: Freeze physics and the simulation clock.
* `sim.resume()`: Unfreeze physics.
* `sim.reset()`: Clear the physics state and restore objects to their spawn points.

### World Commands
* `gravity(x, y, z)`: Set the global gravity vector for the PyBullet world.
* `timescale(factor)`: Speed up or slow down the simulation execution speed (1.0 = real-time) without changing the underlying physics timestep.

### Robot Commands
* `robot.reset(name)`: Restore a specific robot to its initial spawn position, orientation, and joint states.
* `robot.scale(name, factor)`: Uniformly scale a robot.
* `robot.tilt(name, axis, degrees)`: Rotate a robot around the `x`, `y`, or `z` axis.
* `robot.delete(name)`: Remove a robot from the simulation.

> **Tip:** If the variable `robot` is already in your namespace as a `Robot` object (e.g. `robots=[robot]`), the built-in commands `robot.reset` and `robot.delete` are safely hidden in favor of the actual object-oriented methods on your `Robot` instance! This means you can just type `robot.delete()` without needing to pass the name.

### Loading Commands
* `load(path, position=(0,0,0))`: Load a URDF file, robot directory, or Arsenal asset dynamically.

---

## Creating Your Own Commands

You are not limited to the default commands. You can easily create your own custom console commands using the `@command` decorator!

Just import the decorator, define your function, and it will automatically be registered and available in the console namespace (complete with autocomplete and help text).

### Example: Custom Reset Sequence

```python
from bulletlab import Simulation, Robot, command

sim = Simulation(mode="gui").start()
robot = Robot.load("husky.urdf", sim=sim)

@command(
    name="dance", 
    description="Make the robot do a little dance.", 
    category="Custom"
)
def make_robot_dance():
    """Wiggles the wheels back and forth."""
    # Note: custom commands can import and use global variables or context.
    robot.joints['front_left'].velocity = 10
    robot.joints['front_right'].velocity = -10

# Start your UI
from bulletlab.ui import BulletLabUI
ui = BulletLabUI(sim=sim, robots=[robot])
ui.start()
```

Now, in the BulletLab UI console, you can simply type:
```python
>>> dance()
```
And your custom logic will execute!

### Nesting Custom Commands

The ConsoleEngine supports nested proxy objects natively. If you want your command to feel like an object-oriented method, simply use dot-notation in the name!

```python
@command(name="camera.orbit", description="Orbit the camera around the origin.")
def orbit_cam(speed: float = 1.0):
    # logic here...
    pass
```
In the console, you would call this using `camera.orbit(1.5)`.
