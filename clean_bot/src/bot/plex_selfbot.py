import logging
import time
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

import discord
from discord.ext import commands
from plexapi.server import PlexServer
from plexapi.video import Video
from plexapi.media import Media
from plexapi.exceptions import NotFound, Unauthorized

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StreamInfo:
    """Information about a media stream."""
    stream_url: str
    duration: int
    media_type: str
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None
    resolution: Optional[str] = None
    bitrate: Optional[int] = None

@dataclass
class PlaybackState:
    """Current playback state."""
    media_id: str
    start_time: float
    position: float = 0
    is_playing: bool = False
    is_paused: bool = False
    volume: int = 100

class PlexSelfBot(commands.Bot):
    def __init__(self, plex_url: str, plex_token: str) -> None:
        # Set up intents
        intents = discord.Intents.default()
        intents.members = True
        intents.voice_states = True

        super().__init__(command_prefix="!", self_bot=True, intents=intents)

        try:
            # Initialize Plex
            self.plex = PlexServer(plex_url, plex_token)
            # Import here to avoid circular import
            from .media_player import MediaPlayer
            self.media_player = MediaPlayer()
        except Exception as e:
            logger.error(f"Failed to initialize Plex or MediaPlayer: {e}")
            raise

        self.current_stream: Optional[Dict[str, Any]] = None
        self.playback_states: Dict[int, PlaybackState] = {}  # channel_id -> state
        self.setup_commands()

    async def join_voice(self, ctx: commands.Context) -> bool:
        """Join a voice channel with error handling."""
        if not isinstance(ctx.author, discord.Member):
            await ctx.send("This command can only be used in a server.")
            return False

        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("You need to be in a voice channel!")
            return False

        try:
            if not ctx.voice_client:
                await ctx.author.voice.channel.connect()
            elif ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.voice_client.move_to(ctx.author.voice.channel)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to voice channel: {e}")
            await ctx.send(f"Error connecting to voice: {e}")
            return False

    def get_stream_info(self, media: Video) -> StreamInfo:
        """Get streaming information for media."""
        try:
            stream_url = media.getStreamURL()
            media_streams = media.media[0] if media.media else None
            
            if not media_streams:
                raise ValueError("No media streams available")

            return StreamInfo(
                stream_url=stream_url,
                duration=media.duration,
                media_type=media.type,
                video_codec=media_streams.videoCodec,
                audio_codec=media_streams.audioCodec,
                resolution=media_streams.videoResolution,
                bitrate=media_streams.bitrate
            )
        except Exception as e:
            logger.error(f"Error getting stream info: {e}")
            raise

    def setup_commands(self) -> None:
        @self.command(name="stream")
        async def stream_command(ctx: commands.Context, *, query: str) -> None:
            """Stream Plex media in voice channel."""
            if not await self.join_voice(ctx):
                return

            try:
                # Search for media
                results = self.plex.library.search(query)
                if not results:
                    await ctx.send("No media found.")
                    return

                media = next((item for item in results if isinstance(item, Video)), None)
                if not media:
                    await ctx.send("No playable media found.")
                    return

                # Get stream info
                stream_info = self.get_stream_info(media)
                
                # Start media playback
                success = await self.start_stream(ctx, stream_info, media)
                if success:
                    embed = discord.Embed(
                        title="Now Playing",
                        description=f"Title: {media.title}\nDuration: {media.duration//60000} minutes",
                        color=discord.Color.green()
                    )
                    if stream_info.resolution:
                        embed.add_field(name="Quality", value=stream_info.resolution)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Failed to start stream. Check logs for details.")

            except NotFound:
                await ctx.send("Media not found on Plex server.")
            except Unauthorized:
                await ctx.send("Unauthorized access to Plex server.")
            except Exception as e:
                logger.error(f"Error in stream command: {e}")
                await ctx.send(f"Error starting stream: {e}")

        @self.command(name="pause")
        async def pause_command(ctx: commands.Context) -> None:
            """Pause/Resume current stream."""
            if not ctx.voice_client or not ctx.voice_client.channel:
                await ctx.send("Not in a voice channel!")
                return

            state = self.playback_states.get(ctx.voice_client.channel.id)
            if not state:
                await ctx.send("No active stream!")
                return

            try:
                if state.is_paused:
                    self.media_player.resume()
                    state.is_paused = False
                    await ctx.send("▶️ Playback resumed")
                else:
                    self.media_player.pause()
                    state.is_paused = True
                    await ctx.send("⏸️ Playback paused")
            except Exception as e:
                logger.error(f"Error in pause command: {e}")
                await ctx.send(f"Error: {e}")

        @self.command(name="stop")
        async def stop_command(ctx: commands.Context) -> None:
            """Stop current stream."""
            if not ctx.voice_client or not ctx.voice_client.channel:
                await ctx.send("Not in a voice channel!")
                return

            try:
                await self.stop_stream(ctx)
                await ctx.send("⏹️ Playback stopped")
            except Exception as e:
                logger.error(f"Error in stop command: {e}")
                await ctx.send(f"Error: {e}")

        @self.command(name="search")
        async def search_command(ctx: commands.Context, *, query: str) -> None:
            """Search for media on Plex."""
            try:
                results = self.plex.library.search(query)
                if not results:
                    await ctx.send("No media found.")
                    return

                embed = discord.Embed(
                    title="Search Results",
                    color=discord.Color.blue()
                )

                for i, media in enumerate(results[:5], 1):
                    if isinstance(media, Video):
                        duration = f"{media.duration // 60000} minutes"
                        embed.add_field(
                            name=f"{i}. {media.title}",
                            value=f"Type: {media.type}\nDuration: {duration}",
                            inline=False
                        )

                await ctx.send(embed=embed)

            except Exception as e:
                logger.error(f"Error in search command: {e}")
                await ctx.send(f"Error searching: {e}")

    async def start_stream(
        self,
        ctx: commands.Context,
        stream_info: StreamInfo,
        media: Video
    ) -> bool:
        """Start streaming media with enhanced error handling."""
        try:
            # Store stream info
            self.current_stream = {
                'url': stream_info.stream_url,
                'media': media,
                'start_time': time.time(),
                'stream_info': stream_info
            }

            # Create playback state
            self.playback_states[ctx.voice_client.channel.id] = PlaybackState(
                media_id=str(media.ratingKey),
                start_time=time.time()
            )

            # Start media player
            if not self.media_player.start(stream_info.stream_url):
                self.current_stream = None
                logger.error("Failed to start media player")
                return False

            # Update Plex server about playback
            try:
                media.markAsPlaying()
            except Exception as e:
                logger.warning(f"Failed to mark media as playing: {e}")

            return True

        except Exception as e:
            logger.error(f"Error in start_stream: {e}")
            self.current_stream = None
            return False

    async def stop_stream(self, ctx: commands.Context) -> None:
        """Stop current stream and clean up."""
        if self.current_stream:
            try:
                # Stop media player
                self.media_player.stop()

                # Update Plex server
                if 'media' in self.current_stream:
                    try:
                        self.current_stream['media'].markAsStopped()
                    except Exception as e:
                        logger.warning(f"Failed to mark media as stopped: {e}")

                # Clean up state
                self.current_stream = None
                if ctx.voice_client and ctx.voice_client.channel:
                    self.playback_states.pop(ctx.voice_client.channel.id, None)

                # Disconnect from voice
                if ctx.voice_client:
                    await ctx.voice_client.disconnect()

            except Exception as e:
                logger.error(f"Error in stop_stream: {e}")
                await ctx.send(f"Error stopping stream: {e}")

    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        logger.info(f"Logged in as {self.user}")


def run_selfbot(token: str, plex_url: str, plex_token: str) -> None:
    """Run the Plex selfbot."""
    try:
        bot = PlexSelfBot(plex_url, plex_token)
        bot.run(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise
