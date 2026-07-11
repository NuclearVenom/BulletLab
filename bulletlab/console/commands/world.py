"""
World and physics console commands.
"""

from bulletlab.console.decorators import command
from bulletlab.console.context import get_context
from bulletlab.console.exceptions import CommandError


def _require_sim():
    ctx = get_context()
    if not ctx.sim:
        raise CommandError("No active simulation found.")
    return ctx.sim


@command(
    name="gravity",
    description="Set the world gravity vector.",
    category="World"
)
def gravity(x: float | int, y: float | int, z: float | int) -> None:
    """Sets world gravity. Applies to every physics object."""
    if not all(isinstance(v, (int, float)) for v in (x, y, z)):
        raise CommandError("gravity() requires three numeric arguments (x, y, z).")
        
    sim = _require_sim()
    if hasattr(sim, "world") and hasattr(sim.world, "set_gravity"):
        sim.world.set_gravity(float(x), float(y), float(z))
    elif hasattr(sim, "set_gravity"):
        sim.set_gravity(float(x), float(y), float(z))
    else:
        raise CommandError("Active simulation does not support setting gravity.")


@command(
    name="timescale",
    description="Set the simulation execution speed (1.0 = real-time).",
    category="World"
)
def timescale(factor: float | int) -> None:
    """Changes simulation execution speed without changing the physics timestep."""
    if not isinstance(factor, (int, float)):
        raise CommandError("timescale() requires a numeric argument.")
    if factor <= 0:
        raise CommandError("timescale() factor must be > 0.")
        
    sim = _require_sim()
    if hasattr(sim, "timescale"):
        sim.timescale = float(factor)
    elif hasattr(sim, "set_timescale"):
        sim.set_timescale(float(factor))
    else:
        raise CommandError("Active simulation does not support setting timescale.")
