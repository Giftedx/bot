"""Plex commands cog."""
import logging
from typing import Optional

import discord
from discord.ext import commands

from ...cogs.base import BaseCog
from ...services.plex.models import MediaInfo, StreamInfo
from ...bot.plex_bot import PlexBot

logger = logging.getLogger(__name__)

class PlexCog(BaseCog):
    """Cog for Plex media commands."""

    def __init__(self, bot: PlexBot):
        super().__init__(bot)
        self.bot: PlexBot = bot
        
    @commands.group(invoke_without_command=True)
    async def plex(self, ctx: commands.Context) -> None:
        """Plex command group. Use subcommands for specific actions."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @plex.command()
    async def search(self, ctx: commands.Context, *, query: str) -> None:
        """Search for media on Plex."""
        try:
            results = await self.bot.plex_client.search(query)
            if not results:
                await self.handle_response(
                    ctx,
                    content="No media found matching your search."
                )
                return

            # Create embed with results
            embed = discord.Embed(
                title="Plex Search Results",
                color=discord.Color.blue()
            )
            
            for i, media in enumerate(results[:5], 1):
                embed.add_field(
                    name=f"{i}. {media.title}",
                    value=f"Type: {media.type}\nDuration: {media.duration//60} minutes",
                    inline=False
                )

            await self.handle_response(ctx, embed=embed)
            
        except Exception as e:
            logger.error(f"Error searching Plex: {e}")
            await self.handle_response(
                ctx,
                content=f"Error searching: {e}",
                error_msg="Failed to search Plex media."
            )

    @plex.command()
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        """Play media from Plex in your voice channel."""
        # Ensure user is in voice channel
        voice_client = self.ensure_voice(ctx)
        if not voice_client:
            return

        try:
            # Search for media
            results = await self.bot.plex_client.search(query)
            if not results:
                await self.handle_response(
                    ctx,
                    content="No media found matching your search."
                )
                return

            # Get first result
            media = results[0]
            
            # Get stream info
            stream_info = await self.bot.plex_manager.get_stream_info(media)
            
            # Start playback
            success = await self.bot.plex_manager.start_stream(
                ctx.voice_client,
                media,
                stream_info
            )
            
            if success:
                embed = discord.Embed(
                    title="Now Playing",
                    description=f"Title: {media.title}",
                    color=discord.Color.green()
                )
                if stream_info.resolution:
                    embed.add_field(
                        name="Quality",
                        value=stream_info.resolution
                    )
                await self.handle_response(
                    ctx,
                    embed=embed,
                    reaction="▶️"
                )
            else:
                await self.handle_response(
                    ctx,
                    content="Failed to start playback.",
                    error_msg="Error starting media stream."
                )

        except Exception as e:
            logger.error(f"Error playing media: {e}")
            await self.handle_response(
                ctx,
                content=f"Error: {e}",
                error_msg="Failed to play media."
            )

    @plex.command()
    async def stop(self, ctx: commands.Context) -> None:
        """Stop current playback."""
        if not ctx.voice_client:
            await self.handle_response(
                ctx,
                content="Not playing anything!"
            )
            return

        try:
            await self.bot.plex_manager.stop_stream(ctx.voice_client)
            await self.handle_response(
                ctx,
                content="Playback stopped.",
                reaction="⏹️"
            )
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
            await self.handle_response(
                ctx,
                content=f"Error: {e}",
                error_msg="Failed to stop playback."
            )

    @plex.command()
    async def pause(self, ctx: commands.Context) -> None:
        """Pause/Resume current playback."""
        if not ctx.voice_client:
            await self.handle_response(
                ctx,
                content="Not in a voice channel!"
            )
            return

        try:
            state = await self.bot.plex_manager.toggle_pause(ctx.voice_client)
            
            await self.handle_response(
                ctx,
                content="Playback paused" if state.is_paused else "Playback resumed",
                reaction="⏸️" if state.is_paused else "▶️"
            )
        except Exception as e:
            logger.error(f"Error toggling pause: {e}")
            await self.handle_response(
                ctx,
                content=f"Error: {e}",
                error_msg="Failed to pause/resume playback."
            )

    @plex.command()
    async def nowplaying(self, ctx: commands.Context) -> None:
        """Show information about the currently playing media."""
        if not ctx.voice_client:
            await self.handle_response(
                ctx,
                content="Not playing anything!"
            )
            return

        try:
            state = await self.bot.plex_manager.get_playback_state(ctx.voice_client)
            if not state or not state.media:
                await self.handle_response(
                    ctx,
                    content="No active media session."
                )
                return

            embed = discord.Embed(
                title="Now Playing",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Title",
                value=state.media.title,
                inline=False
            )
            embed.add_field(
                name="Duration",
                value=f"{state.media.duration//60} minutes",
                inline=True
            )
            embed.add_field(
                name="Elapsed",
                value=f"{int(state.position)//60} minutes",
                inline=True
            )
            
            if state.media.thumb:
                embed.set_thumbnail(url=state.media.thumb)

            await self.handle_response(ctx, embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting now playing info: {e}")
            await self.handle_response(
                ctx,
                content=f"Error: {e}",
                error_msg="Failed to get playback information."
            )

async def setup(bot: PlexBot) -> None:
    """Add the cog to the bot."""
    await bot.add_cog(PlexCog(bot)) 