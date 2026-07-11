"""
Asset loading console commands.
"""

from bulletlab.console.decorators import command
from bulletlab.console.context import get_context
from bulletlab.console.exceptions import CommandError
import os
from typing import Any


def _require_sim():
    ctx = get_context()
    if not ctx.sim:
        raise CommandError("No active simulation found.")
    return ctx.sim


@command(
    name="load",
    description="Load a robot or asset into the simulation.",
    category="Loading"
)
def load(path: str, position: tuple[float, float, float] | None = None) -> Any:
    """Accepts a robot directory, URDF file, or registered asset."""
    if not isinstance(path, str):
        raise CommandError("load() requires a string path as its first argument.")
        
    sim = _require_sim()
    pos = position or (0.0, 0.0, 0.0)
    
    if position is not None:
        if not isinstance(position, (list, tuple)) or len(position) != 3:
            raise CommandError("load() position must be a tuple of 3 numbers (x, y, z).")
    
    # We delegate to the simulation's loading logic
    if hasattr(sim, "load"):
        try:
            return sim.load(path, pos)
        except Exception as e:
            raise CommandError(f"Failed to load '{path}': {e}")
    else:
        raise CommandError("Active simulation does not support load().")
