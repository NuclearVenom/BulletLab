"""
Decorator for registering console commands.
"""

from typing import Callable, Any
from bulletlab.console.registry import registry


def command(name: str, description: str = "", category: str = "", aliases: list[str] | None = None) -> Callable:
    """Decorator to register a function as a console command.

    Args:
        name: The name of the command (can use dot notation like 'sim.start').
        description: A brief description of what the command does.
        category: The category this command belongs to.
        aliases: Alternative names for the command.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        registry.register(
            name=name,
            func=func,
            description=description,
            category=category,
            aliases=aliases,
        )
        return func
    return decorator
