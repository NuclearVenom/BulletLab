"""
BulletLab Console system.

A modular architecture for registering and executing interactive Python commands.
"""

from bulletlab.console.decorators import command
from bulletlab.console.registry import registry
from bulletlab.console.engine import ConsoleEngine, get_current_stop_event
from bulletlab.console.exceptions import ConsoleError, CommandError, CommandNotFoundError
from bulletlab.console.context import get_context

# Auto-import all built-in commands so they register themselves
import bulletlab.console.commands

__all__ = [
    "command",
    "registry",
    "ConsoleEngine",
    "get_current_stop_event",
    "ConsoleError",
    "CommandError",
    "CommandNotFoundError",
    "get_context",
]
