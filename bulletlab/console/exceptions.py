"""
Exceptions used by the BulletLab Console system.
"""

from bulletlab.arsenal.exceptions import ArsenalError

class ConsoleError(ArsenalError):
    """Base class for all console-related errors."""
    pass

class CommandError(ConsoleError):
    """Raised when a command encounters a validation or execution error.
    These errors are displayed in the console cleanly.
    """
    pass

class CommandNotFoundError(ConsoleError):
    """Raised when a requested command does not exist."""
    pass
