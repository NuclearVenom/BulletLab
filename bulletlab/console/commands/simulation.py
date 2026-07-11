"""
Simulation control console commands.
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
    name="sim.start",
    description="Start physics stepping and the simulation clock.",
    category="Simulation"
)
def sim_start() -> None:
    """Starts physics stepping."""
    sim = _require_sim()
    if hasattr(sim, "start"):
        sim.start()
    else:
        # Fallback if sim doesn't have a start method directly
        if hasattr(sim, "resume"):
            sim.resume()


@command(
    name="sim.stop",
    description="Stop physics stepping and background tasks.",
    category="Simulation"
)
def sim_stop() -> None:
    """Stops physics stepping."""
    sim = _require_sim()
    if hasattr(sim, "stop"):
        sim.stop()
    else:
        # Fallback
        if hasattr(sim, "pause"):
            sim.pause()


@command(
    name="sim.pause",
    description="Freeze physics and simulation time.",
    category="Simulation"
)
def sim_pause() -> None:
    """Freezes physics and simulation time."""
    sim = _require_sim()
    if hasattr(sim, "pause"):
        sim.pause()


@command(
    name="sim.resume",
    description="Resume a paused simulation.",
    category="Simulation"
)
def sim_resume() -> None:
    """Resumes a paused simulation."""
    sim = _require_sim()
    if hasattr(sim, "resume"):
        sim.resume()


@command(
    name="sim.reset",
    description="Clear physics state and restore objects to initial spawn state.",
    category="Simulation"
)
def sim_reset() -> None:
    """Resets the simulation."""
    sim = _require_sim()
    if hasattr(sim, "reset"):
        sim.reset()
