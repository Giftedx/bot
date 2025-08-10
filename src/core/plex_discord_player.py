"""
Plex media playback integration for Discord voice channels.
Allows streaming Plex content directly in Discord voice channels.
"""
import asyncio
import logging
from typing import Dict, Optional, Any
import time

import discord
from discord.ext import commands
from plexapi.server import PlexServer
from plexapi.video import Video
from plexapi.audio import Track

logger = logging.getLogger(__name__)


class PlexDiscordPlayer:
    """Handles Plex media playback in Discord voice channels."""

    def __init__(self, bot: commands.Bot, plex_url: str, plex_token: str):
        self.bot = bot
        self.plex = PlexServer(plex_url, plex_token)
        self.active_streams: Dict[int, Dict[str, Any]] = {}  # voice_channel_id -> stream_info
        self.stream_settings = {
            "video_quality": "1080p",
            "audio_quality": "high",
            "transcode_audio": True,
            "transcode_video": True,
            "max_audio_channels": 2,
            "bitrate": "4mbps",
        }

    async def start_stream(
        self, ctx: commands.Context, media_id: str
    ) -> Optional[discord.Activity]:
        """
        Start streaming Plex media in a Discord voice channel.

        Args:
            ctx: The command context
            media_id: The Plex media ID to stream

        Returns:
            The Discord activity for the stream if successful
        """
        try:
            # Check if user is in a voice channel
            if not ctx.author.voice:
                await ctx.send("You need to be in a voice channel to start a stream!")
                return None

            voice_channel = ctx.author.voice.channel

            # Check if already streaming in this channel
            if voice_channel.id in self.active_streams:
                await ctx.send("There's already an active stream in this channel!")
                return None

            # Get media from Plex
            media = self.plex.fetchItem(int(media_id))
            if not media:
                await ctx.send(f"Could not find media with ID {media_id}")
                return None

            # Create optimized stream URL
            stream_url = self._create_stream_url(media)

            # Create Discord activity
            activity = await self._create_activity(media, stream_url)

            # Connect to voice channel and start streaming
            voice_client = await voice_channel.connect()

            # Store stream info
            self.active_streams[voice_channel.id] = {
                "voice_client": voice_client,
                "media": media,
                "activity": activity,
                "start_time": time.time(),
                "paused": False,
                "current_position": 0,
            }

            # Start audio stream
            await self._start_audio_stream(voice_client, stream_url)

            # Update bot activity
            await self.bot.change_presence(activity=discord.Activity(**activity))

            return activity

        except Exception as e:
            logger.error(f"Failed to start Plex stream: {e}")
            await ctx.send(f"Error starting stream: {str(e)}")
            return None

    async def stop_stream(self, ctx: commands.Context):
        """Stop an active stream in the voice channel."""
        if not ctx.author.voice:
            await ctx.send("You're not in a voice channel!")
            return

        voice_channel = ctx.author.voice.channel

        if voice_channel.id not in self.active_streams:
            await ctx.send("No active stream in this channel!")
            return

        try:
            stream = self.active_streams[voice_channel.id]
            await stream["voice_client"].disconnect()
            del self.active_streams[voice_channel.id]
            await self.bot.change_presence(activity=None)
            await ctx.send("Stream stopped!")

        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            await ctx.send(f"Error stopping stream: {str(e)}")

    async def pause_stream(self, ctx: commands.Context):
        """Pause the current stream."""
        if not self._check_stream_permissions(ctx):
            return

        stream = self.active_streams[ctx.author.voice.channel.id]
        stream["paused"] = True
        stream["voice_client"].pause()
        await ctx.send("Stream paused!")

    async def resume_stream(self, ctx: commands.Context):
        """Resume a paused stream."""
        if not self._check_stream_permissions(ctx):
            return

        stream = self.active_streams[ctx.author.voice.channel.id]
        stream["paused"] = False
        stream["voice_client"].resume()
        await ctx.send("Stream resumed!")

    async def seek(self, ctx: commands.Context, timestamp: str):
        """Seek to a specific position in the stream."""
        if not self._check_stream_permissions(ctx):
            return

        try:
            # Parse timestamp (format: HH:MM:SS or MM:SS)
            seconds = self._parse_timestamp(timestamp)
            stream = self.active_streams[ctx.author.voice.channel.id]

            # Create new stream URL with offset
            stream_url = self._create_stream_url(stream["media"], offset=seconds)

            # Restart stream from new position
            await stream["voice_client"].stop()
            await self._start_audio_stream(stream["voice_client"], stream_url)
            stream["current_position"] = seconds

            await ctx.send(f"Seeked to {timestamp}!")

        except ValueError:
            await ctx.send("Invalid timestamp format! Use HH:MM:SS or MM:SS")
        except Exception as e:
            logger.error(f"Error seeking: {e}")
            await ctx.send(f"Error seeking: {str(e)}")

    def _check_stream_permissions(self, ctx: commands.Context) -> bool:
        """Check if user has permission to control the stream."""
        if not ctx.author.voice:
            asyncio.create_task(ctx.send("You're not in a voice channel!"))
            return False

        voice_channel = ctx.author.voice.channel
        if voice_channel.id not in self.active_streams:
            asyncio.create_task(ctx.send("No active stream in this channel!"))
            return False

        return True

    def _create_stream_url(self, media: Any, offset: int = 0) -> str:
        """Create an optimized stream URL for the media."""
        # Set up transcoding parameters
        params = {
            "videoQuality": self.stream_settings["video_quality"],
            "audioQuality": self.stream_settings["audio_quality"],
            "maxAudioChannels": self.stream_settings["max_audio_channels"],
            "videoBitrate": self.stream_settings["bitrate"],
        }

        if offset > 0:
            params["offset"] = offset * 1000  # Convert to milliseconds

        if isinstance(media, Video):
            params.update({"videoCodec": "h264", "audioCodec": "aac"})
        elif isinstance(media, Track):
            params.update({"audioCodec": "mp3"})

        return media.getStreamURL(**params)

    async def _create_activity(self, media: Any, stream_url: str) -> dict:
        """Create a Discord activity for the stream."""
        activity_type = "STREAMING"
        if isinstance(media, Video):
            details = f"Watching {media.title}"
            if hasattr(media, "grandparentTitle"):  # TV Show episode
                details = f"Watching {media.grandparentTitle} - {media.title}"
        elif isinstance(media, Track):
            details = f"Listening to {media.title}"
            if media.grandparentTitle:  # Song in album
                details = f"Listening to {media.title} by {media.grandparentTitle}"
        else:
            details = f"Streaming {media.title}"

        return {
            "type": activity_type,
            "name": media.title,
            "url": stream_url,
            "details": details,
            "assets": {
                "large_image": media.thumb if hasattr(media, "thumb") else None,
                "large_text": media.title,
                "small_image": "plex_icon",
                "small_text": "Plex",
            },
            "timestamps": {"start": int(time.time())},
        }

    async def _start_audio_stream(self, voice_client: discord.VoiceClient, stream_url: str):
        """Start streaming audio in the voice channel."""
        # Create FFmpeg audio source with proper options
        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -b:a 192k",  # Audio only, 192kbps bitrate
        }

        audio_source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_options)
        voice_client.play(audio_source)

    def _parse_timestamp(self, timestamp: str) -> int:
        """Parse a timestamp string into seconds."""
        parts = timestamp.split(":")
        if len(parts) == 2:  # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        else:
            raise ValueError("Invalid timestamp format")
