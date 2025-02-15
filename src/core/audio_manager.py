"""Core audio resource manager for voice functionality"""
import logging
from typing import Dict, Optional
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class AudioManager:
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._audio_states: Dict[int, discord.VoiceClient] = {}
        self._bass_levels: Dict[int, int] = {}

    def set_bass_level(self, guild_id: int, level: int) -> None:
        """Set bass boost level for a guild (0-100)"""
        self._bass_levels[guild_id] = max(0, min(100, level))

    def get_bass_level(self, guild_id: int) -> int:
        """Get current bass boost level for a guild"""
        return self._bass_levels.get(guild_id, 0)

    async def cleanup_guild(self, guild_id: int) -> None:
        """Clean up voice resources for a guild"""
        try:
            voice: Optional[discord.VoiceClient] = self._audio_states.get(guild_id)
            if voice:
                try:
                    if voice.is_playing():
                        voice.stop()
                    if voice.is_connected():
                        await voice.disconnect(force=True)
                except Exception as e:
                    logger.error("Error cleaning up voice in guild %s: %s", guild_id, e)
                finally:
                    self._audio_states.pop(guild_id, None)
                    self._bass_levels.pop(guild_id, None)
        except Exception as e:
            logger.error("Failed to cleanup guild %s: %s", guild_id, e)

    # ... rest of existing methods ...
