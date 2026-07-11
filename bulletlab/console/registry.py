"""
Registry for console commands.
"""

from dataclasses import dataclass, field
from typing import Callable, Any

from bulletlab.console.exceptions import CommandNotFoundError


@dataclass
class CommandMeta:
    name: str
    func: Callable[..., Any]
    description: str = ""
    category: str = "Uncategorized"
    aliases: list[str] = field(default_factory=list)


class CommandRegistry:
    """Stores all registered console commands."""

    def __init__(self) -> None:
        self._commands: dict[str, CommandMeta] = {}

    def register(self, name: str, func: Callable[..., Any], description: str = "", category: str = "", aliases: list[str] | None = None) -> None:
        """Register a command with the given metadata."""
        meta = CommandMeta(
            name=name,
            func=func,
            description=description,
            category=category,
            aliases=aliases or [],
        )
        self._commands[name] = meta
        for alias in meta.aliases:
            self._commands[alias] = meta

    def get(self, name: str) -> CommandMeta:
        """Retrieve a command by name."""
        if name not in self._commands:
            raise CommandNotFoundError(f"Command '{name}' not found.")
        return self._commands[name]

    def get_all(self) -> dict[str, CommandMeta]:
        """Return all registered commands."""
        return self._commands.copy()

    def clear(self) -> None:
        """Clear all registered commands (useful for testing)."""
        self._commands.clear()


# Global singleton registry used by the @command decorator
registry = CommandRegistry()
