"""Discord activity client for voice channel media playback."""

import json
import asyncio
from typing import Dict, Optional
import discord
from discord import Activity, ActivityType
from .plex_client import PlexClient


class DiscordPlexActivity:
    """Manages Discord voice channel activity for Plex media playback."""

    def __init__(self, bot: discord.Client):
        """Initialize the Discord Plex activity.

        Args:
            bot: The Discord bot instance.
        """
        self.bot = bot
        self.plex = PlexClient()
        self.current_media: Optional[Dict] = None
        self.voice_client: Optional[discord.VoiceClient] = None

    async def create_activity(self, channel_id: int, media_key: str):
        """Create a Discord activity for media playback.

        Args:
            channel_id: The voice channel ID.
            media_key: The Plex media key.

        Raises:
            ValueError: If media not found or activity creation fails.
        """
        try:
            # Get media info from Plex
            media_info = self.plex.get_media_info(media_key)
            stream_url = media_info["stream_url"]

            # Create activity payload
            activity_data = {
                "type": 2,  # Activity type for "Watching"
                "name": "Plex",
                "details": media_info["title"],
                "state": f"via {self.bot.user.name}",
                "assets": {"large_image": media_info["thumb"], "large_text": media_info["title"]},
                "metadata": {"video_url": stream_url, "duration": media_info["duration"]},
            }

            # Join voice channel if not already in one
            channel = self.bot.get_channel(channel_id)
            if not self.voice_client or not self.voice_client.is_connected():
                self.voice_client = await channel.connect()

            # Set bot activity
            activity = Activity(
                type=ActivityType.watching,
                name=media_info["title"],
                details=json.dumps(activity_data),
            )
            await self.bot.change_presence(activity=activity)

            # Store current media info
            self.current_media = media_info

        except Exception as e:
            raise ValueError(f"Failed to create activity: {str(e)}")

    async def update_activity_progress(self, progress: float):
        """Update the activity progress.

        Args:
            progress: Current playback progress (0-1).
        """
        if not self.current_media:
            return

        activity_data = {
            "type": 2,
            "name": "Plex",
            "details": self.current_media["title"],
            "state": f"via {self.bot.user.name}",
            "assets": {
                "large_image": self.current_media["thumb"],
                "large_text": self.current_media["title"],
            },
            "metadata": {
                "video_url": self.current_media["stream_url"],
                "duration": self.current_media["duration"],
                "progress": progress,
            },
        }

        activity = Activity(
            type=ActivityType.watching,
            name=self.current_media["title"],
            details=json.dumps(activity_data),
        )
        await self.bot.change_presence(activity=activity)

    async def end_activity(self):
        """End the current media activity."""
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()

        await self.bot.change_presence(activity=None)
        self.current_media = None

    def is_playing(self) -> bool:
        """Check if media is currently playing.

        Returns:
            True if media is playing.
        """
        return self.current_media is not None
