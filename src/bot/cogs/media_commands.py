"""Media playback commands for Discord bot."""
from typing import Optional, List, Dict, Any, cast
import logging
from discord.ext import commands
from discord import VoiceChannel, VoiceClient, Member, Embed, Color, Guild, VoiceState

from src.lib.cog_utils import CogBase

logger = logging.getLogger(__name__)


def is_guild_context(ctx: commands.Context) -> bool:
    """Check if the context is in a guild."""
    return ctx.guild is not None and isinstance(ctx.author, Member)


class MediaCommands(CogBase):
    """Media playback commands."""

    def __init__(self, bot: commands.Bot, **kwargs):
        super().__init__(bot, **kwargs)
        self.voice_clients: Dict[int, VoiceClient] = {}
        self.queues: Dict[int, List[Dict[str, Any]]] = {}

    async def cog_load(self) -> None:
        """Called when the cog is loaded."""
        logger.info("Media commands cog loaded")

    @commands.command(name="join")
    @commands.guild_only()
    async def join_voice(
        self, ctx: commands.Context, channel: Optional[VoiceChannel] = None
    ) -> None:
        """Join a voice channel."""
        if not is_guild_context(ctx):
            await ctx.send("This command can only be used in a server!")
            return

        guild = cast(Guild, ctx.guild)
        member = cast(Member, ctx.author)
        voice_state = cast(Optional[VoiceState], member.voice)

        # Get voice channel
        if not channel and voice_state and voice_state.channel:
            if isinstance(voice_state.channel, VoiceChannel):
                channel = voice_state.channel

        if not channel:
            await ctx.send("You need to be in a voice channel!")
            return

        try:
            voice_client: VoiceClient = await channel.connect()
            self.voice_clients[guild.id] = voice_client
            await ctx.send(f"Joined {channel.name}!")
        except Exception as e:
            logger.error(f"Error joining voice channel: {e}")
            await ctx.send("Failed to join voice channel!")

    @commands.command(name="leave")
    @commands.guild_only()
    async def leave_voice(self, ctx: commands.Context) -> None:
        """Leave the current voice channel."""
        if not is_guild_context(ctx):
            return

        guild = cast(Guild, ctx.guild)
        if guild.id not in self.voice_clients:
            await ctx.send("Not in a voice channel!")
            return

        try:
            await self.voice_clients[guild.id].disconnect()
            del self.voice_clients[guild.id]
            await ctx.send("Left voice channel!")
        except Exception as e:
            logger.error(f"Error leaving voice channel: {e}")
            await ctx.send("Failed to leave voice channel!")

    @commands.command(name="play")
    @commands.guild_only()
    async def play_media(self, ctx: commands.Context, *, query: str) -> None:
        """Play media from a URL or search query."""
        if not is_guild_context(ctx):
            return

        guild = cast(Guild, ctx.guild)
        if guild.id not in self.voice_clients:
            await ctx.send("Not in a voice channel!")
            return

        try:
            # Add to queue
            if guild.id not in self.queues:
                self.queues[guild.id] = []

            self.queues[guild.id].append({"query": query, "requester": ctx.author.id})

            await ctx.send(f"Added to queue: {query}")
        except Exception as e:
            logger.error(f"Error queueing media: {e}")
            await ctx.send("Failed to queue media!")

    @commands.command(name="stop")
    @commands.guild_only()
    async def stop_playback(self, ctx: commands.Context) -> None:
        """Stop current playback."""
        if not is_guild_context(ctx):
            return

        guild = cast(Guild, ctx.guild)
        if guild.id not in self.voice_clients:
            await ctx.send("Not playing anything!")
            return

        try:
            voice_client = self.voice_clients[guild.id]
            voice_client.stop()
            await ctx.send("Stopped playback!")
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
            await ctx.send("Failed to stop playback!")

    @commands.command(name="queue")
    @commands.guild_only()
    async def show_queue(self, ctx: commands.Context) -> None:
        """Show the current queue."""
        if not is_guild_context(ctx):
            return

        guild = cast(Guild, ctx.guild)
        if guild.id not in self.queues:
            await ctx.send("Queue is empty!")
            return

        queue = self.queues[guild.id]
        if not queue:
            await ctx.send("Queue is empty!")
            return

        embed = Embed(title="Media Queue", color=Color.blue())

        for i, item in enumerate(queue, 1):
            requester = guild.get_member(item["requester"])
            requester_name = requester.display_name if requester else "Unknown"

            embed.add_field(
                name=f"{i}. {item['query']}", value=f"Requested by: {requester_name}", inline=False
            )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Add the cog to the bot."""
    await bot.add_cog(MediaCommands(bot))
