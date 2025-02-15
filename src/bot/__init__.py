"""
Plex Discord Selfbot package.
This package provides functionality for streaming Plex media in Discord voice channels.
"""

from .media_player import MediaPlayer
from .plex_selfbot import PlexSelfBot, run_selfbot

__all__ = ["MediaPlayer", "PlexSelfBot", "run_selfbot"]
