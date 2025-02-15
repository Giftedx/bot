"""Base cog providing common functionality for all cogs"""
import logging
from typing import Optional, Dict, Any
import discord
from discord.ext import commands

from src.core.exceptions import BotError
from src.utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class BaseCog(commands.Cog):
    """Base cog class with shared functionality"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.error_handler = ErrorHandler(bot)

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Default error handling for all cog commands"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command!")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(f"I need the following permissions: {', '.join(error.missing_perms)}")
        elif isinstance(error, commands.MissingRole):
            await ctx.send(f"You need the {error.missing_role} role to use this command!")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("This command can't be used in private messages!")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.1f}s")
        elif isinstance(error, BotError):
            await ctx.send(str(error))
        else:
            await self.error_handler.on_command_error(ctx, error)

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Default checks for all cog commands"""
        # Add any common checks here
        return True

    async def ensure_voice(self, ctx: commands.Context) -> Optional[discord.VoiceClient]:
        """Utility to check voice state for audio commands"""
        if not ctx.author.voice:
            await ctx.send("You need to be in a voice channel!")
            return None
        return ctx.guild.voice_client

    def log_command_use(self, ctx: commands.Context) -> None:
        """Log command usage with context"""
        logger.info(
            f"Command {ctx.command} used by {ctx.author} in {ctx.guild}"
        )

    async def handle_response(
        self,
        ctx: commands.Context,
        content: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
        reaction: Optional[str] = None,
        error_msg: Optional[str] = None
    ) -> None:
        """Standardized command response handling"""
        try:
            if embed:
                await ctx.send(embed=embed)
            elif content:
                await ctx.send(content)
                
            if reaction:
                await ctx.message.add_reaction(reaction)
        except Exception as e:
            logger.error(f"Failed to send response: {e}")
            if error_msg:
                try:
                    await ctx.send(error_msg)
                except:
                    pass