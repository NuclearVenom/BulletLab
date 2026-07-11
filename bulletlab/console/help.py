"""
Help generation and command listing for the console.
"""

from bulletlab.console.registry import registry

def get_help(command_name: str | None = None) -> str:
    """Generate help text for a specific command or all commands."""
    if command_name:
        cmd = registry.get(command_name)
        return f"{cmd.name}: {cmd.description}"
    
    lines = ["Available Commands:"]
    for name, cmd in registry.get_all().items():
        lines.append(f"  {name} - {cmd.description}")
    return "\n".join(lines)
