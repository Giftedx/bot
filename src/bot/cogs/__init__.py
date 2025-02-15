"""Bot cogs package initialization."""
from typing import List


def get_cogs() -> List[str]:
    """Return list of cogs to load"""
    return [
        'src.bot.cogs.osrs_commands',  # OSRS game commands
        'src.bot.cogs.media_commands',  # Media playback commands
        'src.bot.cogs.error_handler',   # Error handling
    ]
