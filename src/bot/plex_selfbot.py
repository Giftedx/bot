import logging
import time
from typing import Any, Dict, Optional

import discord
from discord.ext import commands
from plexapi.server import PlexServer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        self.setup_commands()

    async def join_voice(self, ctx: commands.Context) -> bool:
        """Join a voice channel"""
        if not isinstance(ctx.author, discord.Member):
            await ctx.send("This command can only be used in a server.")
            return False

        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("You need to be in a voice channel!")
            return False

        if not ctx.voice_client:
            try:
                await ctx.author.voice.channel.connect()
            except Exception as e:
                logger.error(f"Failed to connect to voice channel: {e}")
                await ctx.send(f"Error connecting to voice: {e}")
                return False

        return True

    def setup_commands(self) -> None:
        @self.command(name="stream")
        async def stream_command(ctx: commands.Context, *, query: str) -> None:
            """Stream Plex media in voice channel"""
            if not await self.join_voice(ctx):
                return

            try:
                # Search for media
                movies = self.plex.library.section("Movies")
                results = movies.search(query)
                if not results:
                    await ctx.send("No media found.")
                    return

                media = results[0]
                stream_url = media.getStreamURL()

                # Start media playback
                success = await self.start_stream(ctx, stream_url, media)
                if success:
                    await ctx.send(
                        f"Now playing: {media.title}\n"
                        "Please start screensharing and select the VLC window."
                    )
                else:
                    await ctx.send("Failed to start stream. Check logs for details.")

            except Exception as e:
                logger.error(f"Error in stream command: {e}")
                await ctx.send(f"Error starting stream: {e}")

        @self.command(name="pause")
        async def pause_command(ctx: commands.Context) -> None:
            """Pause/Resume current stream"""
            if not self.current_stream:
                await ctx.send("No active stream!")
                return

            try:
                if self.media_player.pause():
                    await ctx.send("Playback paused/resumed.")
                else:
                    await ctx.send("Error pausing/resuming playback.")
            except Exception as e:
                logger.error(f"Error in pause command: {e}")
                await ctx.send(f"Error: {e}")

        @self.command(name="stop")
        async def stop_command(ctx: commands.Context) -> None:
            """Stop current stream"""
            if not self.current_stream:
                await ctx.send("No active stream!")
                return

            try:
                await self.stop_stream(ctx)
            except Exception as e:
                logger.error(f"Error in stop command: {e}")
                await ctx.send(f"Error: {e}")

        @self.command(name="search")
        async def search_command(ctx: commands.Context, *, query: str) -> None:
            """Search for media on Plex"""
            try:
                movies = self.plex.library.section("Movies")
                results = movies.search(query)

                if not results:
                    await ctx.send("No media found.")
                    return

                embed = discord.Embed(
                    title="Search Results", color=discord.Color.blue()
                )

                for i, media in enumerate(results[:5], 1):
                    duration = (
                        f"{media.duration // 60000} minutes"
                        if hasattr(media, "duration")
                        else "Unknown"
                    )
                    embed.add_field(
                        name=f"{i}. {media.title}",
                        value=f"Year: {getattr(media, 'year', 'Unknown')}\n"
                        f"Duration: {duration}",
                        inline=False,
                    )

                await ctx.send(embed=embed)

            except Exception as e:
                logger.error(f"Error in search command: {e}")
                await ctx.send(f"Error searching: {e}")

    async def start_stream(
        self, ctx: commands.Context, stream_url: str, media: Any
    ) -> bool:
        """Start streaming media"""
        try:
            # Store stream info
            self.current_stream = {
                "url": stream_url,
                "media": media,
                "start_time": time.time(),
            }

            # Start media player
            if not self.media_player.start(stream_url):
                self.current_stream = None
                logger.error("Failed to start media player")
                return False

            # Note: Camera mode must be enabled manually by the user
            await ctx.send("Please enable your camera/stream in Discord manually.")
            return True

        except Exception as e:
            logger.error(f"Error in start_stream: {e}")
            self.current_stream = None
            return False

    async def stop_stream(self, ctx: commands.Context) -> None:
        """Stop current stream"""
        if self.current_stream:
            try:
                self.current_stream = None
                self.media_player.stop()
                await ctx.send(
                    "Stream stopped. Please disable your camera/stream manually."
                )
            except Exception as e:
                logger.error(f"Error in stop_stream: {e}")
                await ctx.send(f"Error stopping stream: {e}")

    async def on_ready(self) -> None:
        """Called when the bot is ready"""
        logger.info(f"Logged in as {self.user}")


def run_selfbot(token: str, plex_url: str, plex_token: str) -> None:
    """Run the Plex selfbot"""
    try:
        bot = PlexSelfBot(plex_url, plex_token)
        bot.run(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise
