"""Utility functions for text formatting."""
from typing import Any
from discord.ext import commands

def format_error(error: Any) -> str:
    """Format an error message for user display."""
    if isinstance(error, commands.MissingPermissions):
        return f"You don't have permission to use this command! Missing: {', '.join(error.missing_permissions)}"
    
    elif isinstance(error, commands.BotMissingPermissions):
        return f"I need the following permissions: {', '.join(error.missing_permissions)}"
    
    elif isinstance(error, commands.MissingRole):
        return f"You need the {error.missing_role} role to use this command!"
    
    elif isinstance(error, commands.NoPrivateMessage):
        return "This command can't be used in private messages!"
    
    elif isinstance(error, commands.CommandOnCooldown):
        return f"This command is on cooldown. Try again in {error.retry_after:.1f}s"
    
    elif isinstance(error, commands.MissingRequiredArgument):
        return f"Missing required argument: {error.param.name}"
    
    elif isinstance(error, commands.BadArgument):
        return "Invalid argument provided!"
    
    elif isinstance(error, commands.CheckFailure):
        return str(error) or "You can't use this command!"
    
    # Generic error message for unknown errors
    return "An error occurred while executing the command."

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable string."""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)

def format_size(size: int) -> str:
    """Format size in bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}PB"

def truncate(text: str, length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix

def format_list(items: list, separator: str = ", ", last_separator: str = " and ") -> str:
    """Format a list of items into a human readable string."""
    if not items:
        return ""
    if len(items) == 1:
        return str(items[0])
    
    *rest, last = items
    return f"{separator.join(map(str, rest))}{last_separator}{last}" 