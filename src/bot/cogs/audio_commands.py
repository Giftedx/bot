"""Compatibility module for audio commands.

This module re-exports MediaCommands to maintain backward compatibility.
All audio functionality has been merged into media_commands.py.
"""

from src.bot.cogs.media_commands import MediaCommands as _MediaCommands

# Re-export with original name
MediaCommands = _MediaCommands

__all__ = ["MediaCommands"]
