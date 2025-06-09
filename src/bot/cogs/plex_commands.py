from typing import Optional
from discord.ext import commands
from discord import FFmpegPCMAudio, VoiceClient
from src.core.plex_manager import PlexManager
from src.core.exceptions import MediaNotFoundError, PlexConnectionError, PlexAPIError, StreamingError # Updated import path
from src.core.virtual_display import VirtualDisplayManager  # type: ignore


class PlexCommands(commands.Cog):
    """Commands for playing Plex media in voice channels"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.plex_manager = PlexManager() # Changed instantiation
        self.display_manager = VirtualDisplayManager()
        self.voice_client: Optional[VoiceClient] = None

    @commands.command(name='play')
    async def play(self, ctx: commands.Context, media_name: str) -> None:
        """Play media from Plex library"""
        try:
            # Assuming fetch_media_url is an async method in PlexManager
            # that internally handles search and getting stream URL.
            media_url = await self.plex_manager.fetch_media_url(media_name) # type: ignore
            if not media_url: # Should ideally be covered by MediaNotFoundError if search fails
                await ctx.send("Media not found in Plex library.")
                return

            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send("You need to be in a voice channel to play media!")
                return

            voice_channel = ctx.author.voice.channel # type: ignore
            if self.voice_client and self.voice_client.is_connected():
                await self.voice_client.move_to(voice_channel)
            else:
                self.voice_client = await voice_channel.connect(reconnect=True)

            # Ensure previous playback is stopped if any
            if self.voice_client.is_playing() or self.voice_client.is_paused():
                self.voice_client.stop()

            self.voice_client.play(FFmpegPCMAudio(media_url))
            await ctx.send(f"Now playing: {media_name}")

        except MediaNotFoundError:
            await ctx.send(f"Sorry, I couldn't find '{media_name}' in the Plex library.")
        except PlexConnectionError:
            await ctx.send("There was a problem connecting to Plex. Please ensure it's running and configured correctly.")
        except PlexAPIError:
            await ctx.send("An API error occurred while communicating with Plex. Please try again later.")
        except StreamingError:
            await ctx.send("A streaming error occurred with Plex. Unable to play media.")
        except commands.errors.MissingRequiredArgument as e: # discord.py specific error
            await ctx.send(f"Oops! You forgot something. Command usage: `!play <media_name>` (Error: {e.param.name} is missing).")
        except Exception as e:
            # Log the full error for debugging
            # logger.error(f"Unexpected error in play command: {e}", exc_info=True) # Assuming logger is set up
            print(f"Unexpected error in play command: {e}") # Placeholder for logging
            await ctx.send(f"An unexpected error occurred: {str(e)}")

    @commands.command(name='queue')
    async def queue_media(self, ctx: commands.Context, media_name: str) -> None:
        """Add media to playback queue"""
        await ctx.send(f"{media_name} added to queue.")

    @commands.command(name='skip')
    async def skip_media(self, ctx: commands.Context) -> None:
        """Vote to skip current media"""
        await ctx.send("Vote to skip has been recorded.")

    @commands.command(name='pause')
    async def pause_media(self, ctx: commands.Context) -> None:
        """Pause current playback"""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            await ctx.send("Playback paused.")
        else:
            await ctx.send("No media playing")

    @commands.command(name='resume')
    async def resume_media(self, ctx: commands.Context) -> None:
        """Resume paused playback"""
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            await ctx.send("Playback resumed.")
        else:
            await ctx.send("No paused media")

    @commands.command(name='stop')
    async def stop_plex_media(self, ctx: commands.Context) -> None:
        """Stop playback and disconnect"""
        self.display_manager.stop_stream()
        if self.voice_client:
            await self.voice_client.disconnect(force=False)
            await ctx.send("Playback stopped")
        else:
            await ctx.send("Not currently playing")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PlexCommands(bot))
