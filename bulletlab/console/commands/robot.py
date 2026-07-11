"""
Robot manipulation console commands.
"""

from bulletlab.console.decorators import command
from bulletlab.console.context import get_context
from bulletlab.console.exceptions import CommandError


def _get_robot(name: str):
    ctx = get_context()
    if not ctx.sim:
        raise CommandError("No active simulation found.")
    
    # Assume sim has a robots dict or similar.
    # We will try a few common patterns.
    if hasattr(ctx.sim, "robots"):
        if name in ctx.sim.robots:
            return ctx.sim.robots[name]
        
        # In bulletlab, maybe it's a list?
        if isinstance(ctx.sim.robots, list):
            for r in ctx.sim.robots:
                if getattr(r, "name", None) == name:
                    return r
                    
    # Check if the name is just bound in the namespace itself? No, they specify 'name'
    raise CommandError(f"Robot '{name}' not found.")


@command(
    name="robot.reset",
    description="Restore a robot's initial position and joint states.",
    category="Robot"
)
def robot_reset(name: str) -> None:
    """Restores position, orientation, joint positions, velocities."""
    if not isinstance(name, str):
        raise CommandError("robot.reset() requires a string name.")
        
    robot = _get_robot(name)
    if hasattr(robot, "reset"):
        robot.reset()
    else:
        raise CommandError(f"Robot '{name}' does not support reset().")


@command(
    name="robot.scale",
    description="Uniformly scales a robot.",
    category="Robot"
)
def robot_scale(name: str, factor: float | int) -> None:
    """Uniformly scales the robot."""
    if not isinstance(name, str):
        raise CommandError("robot.scale() requires a string name.")
    if not isinstance(factor, (int, float)):
        raise CommandError("robot.scale() factor must be numeric.")
    if factor <= 0:
        raise CommandError("robot.scale() factor must be > 0.")
        
    robot = _get_robot(name)
    if hasattr(robot, "scale"):
        try:
            robot.scale(float(factor))
        except Exception as e:
            raise CommandError(f"Failed to scale robot '{name}': {e}")
    else:
        raise CommandError(f"Robot '{name}' does not support scale().")


@command(
    name="robot.tilt",
    description="Rotates a robot around a specific axis.",
    category="Robot"
)
def robot_tilt(name: str, axis: str, degrees: float | int) -> None:
    """Rotates the robot around 'x', 'y', or 'z' axis."""
    if not isinstance(name, str):
        raise CommandError("robot.tilt() requires a string name.")
    if not isinstance(axis, str) or axis.lower() not in ('x', 'y', 'z'):
        raise CommandError("robot.tilt() axis must be 'x', 'y', or 'z'.")
    if not isinstance(degrees, (int, float)):
        raise CommandError("robot.tilt() degrees must be numeric.")
        
    robot = _get_robot(name)
    if hasattr(robot, "tilt"):
        robot.tilt(axis.lower(), float(degrees))
    else:
        raise CommandError(f"Robot '{name}' does not support tilt().")


@command(
    name="robot.delete",
    description="Removes a robot from the simulation.",
    category="Robot"
)
def robot_delete(name: str) -> None:
    """Removes a robot and frees resources."""
    if not isinstance(name, str):
        raise CommandError("robot.delete() requires a string name.")
        
    ctx = get_context()
    robot = _get_robot(name)
    
    if hasattr(ctx.sim, "delete_robot"):
        ctx.sim.delete_robot(name)
    elif hasattr(robot, "delete"):
        robot.delete()
    else:
        raise CommandError(f"Could not delete robot '{name}': operation unsupported.")
