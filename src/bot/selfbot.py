from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING, Any
import discord
from discord.ext import commands
from src.core.exceptions import MediaNotFoundError
from src.core.di_container import Container
from src.services.plex.plex_service import PlexService
from src.core.config import Settings
from dependency_injector.wiring import inject, Provide
from src.utils.redis_manager import RedisManager

if TYPE_CHECKING:
    pass  # For type checking purposes only

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SelfBot(commands.Bot):
    """Self-bot implementation. Only used in specific approved scenarios."""
    
    @inject
    def __init__(
        self,
        *args: Any,
        settings: Settings = Provide[Container.config],
        **kwargs: Any
    ) -> None:
        intents = discord.Intents.default()
        super().__init__(
            command_prefix=settings.get("COMMAND_PREFIX", "!"),
            self_bot=True,
            intents=intents
        )
        self.settings = settings

    async def setup_hook(self) -> None:
        """Set up the self-bot."""
        logger.info("Selfbot setup complete")

    async def on_ready(self) -> None:
        """Handle bot ready event."""
        logger.info(f"Logged in as {self.user}")


class VoiceCommandsCog(commands.Cog):
    def __init__(self, bot: SelfBot) -> None:
        self.bot = bot
        self._last_channel: Optional[discord.VoiceChannel] = None

    @commands.command()
    async def play(
        self, 
        ctx: commands.Context, 
        channel: Optional[discord.VoiceChannel] = None, 
        *, 
        media: str
    ) -> None:
        """Play media in a voice channel from Plex"""
        target_channel = channel or (ctx.author.voice.channel if isinstance(ctx.author, discord.Member) and ctx.author.voice else self._last_channel)
        
        if not target_channel:
            await ctx.send("No voice channel specified or found in history.")
            return
            
        try:
            media_url = await PlexService().fetch_media_url(media)
            voice_client: discord.VoiceClient = await target_channel.connect()
            voice_client.play(discord.FFmpegPCMAudio(media_url))
            self._last_channel = target_channel
            await ctx.send(f"Now playing: {media}")
        except MediaNotFoundError:
            await ctx.send("Media not found in Plex library")
        except discord.ClientException as e:
            logger.error("Voice connection error: %s", e)
            await ctx.send("Already connected to a voice channel")
        except Exception as e:
            logger.error("Playback error: %s", e, exc_info=True)
            await ctx.send("Failed to play media. Check logs for details.")

    @commands.command()
    async def skip(self, ctx: commands.Context) -> None:
        """Vote to skip current track"""
        if not ctx.guild or not isinstance(ctx.author, discord.Member) or not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Not in a voice channel")
            return

        guild_id = ctx.guild.id
        vote_key = f"skip_votes:{guild_id}"
        current_votes = await RedisManager.increment(vote_key)
        members = len(ctx.author.voice.channel.members) - 1  # exclude bot
        required = max(2, members // 2)
        
        if current_votes >= required:
            if ctx.voice_client:
                ctx.voice_client.stop()
                await RedisManager.delete(vote_key)
                await ctx.send("Skipping current track...")
        else:
            await ctx.send(f"Vote recorded ({current_votes}/{required} needed)")
