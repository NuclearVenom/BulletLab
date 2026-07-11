"""
Global context for console commands to access engine and simulation state.
"""

from typing import Any


class ConsoleContext:
    """Holds the active context for console commands.
    
    This allows globally registered commands (like `wait`, `sim.start`) 
    to interact with the currently running engine or simulation instance.
    """
    
    def __init__(self) -> None:
        self.sim: Any = None
        self.engine: Any = None


_active_context = ConsoleContext()


def get_context() -> ConsoleContext:
    """Retrieve the active console context."""
    return _active_context
