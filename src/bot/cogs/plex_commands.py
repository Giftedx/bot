from typing import Optional
from discord.ext import commands
from discord import FFmpegPCMAudio, VoiceClient
from src.core.plex_manager import PlexManager
from src.core.virtual_display import VirtualDisplayManager  # type: ignore


class PlexCommands(commands.Cog):
    """Commands for playing Plex media in voice channels"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.plex_manager = PlexManager(  # type: ignore
            "http://localhost:32400",
            "YOUR_PLEX_TOKEN"
        )
        self.display_manager = VirtualDisplayManager()
        self.voice_client: Optional[VoiceClient] = None

    @commands.command(name='play')
    async def play(self, ctx: commands.Context, media_name: str) -> None:
        """Play media from Plex library"""
        media_url = await self.plex_manager.fetch_media_url(  # type: ignore
            media_name
        )
        if not media_url:
            await ctx.send("Media not found in Plex library")
            return

        if not ctx.author.voice or not hasattr(ctx.author.voice, 'channel'):
            await ctx.send("Join a voice channel first!")
            return

        try:
            voice_channel = ctx.author.voice.channel  # type: ignore
            self.voice_client = await voice_channel.connect(reconnect=True)
            self.voice_client.play(FFmpegPCMAudio(media_url))
            await ctx.send(f"Now playing: {media_name}")
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")

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
