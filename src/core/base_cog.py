"""Base cog providing common functionality for all cogs"""

import logging
from typing import Optional

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class BaseCog(commands.Cog):
    """Base cog class with shared functionality"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Default error handling for all cog commands"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command!")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                "I need the following permissions: "
                f"{', '.join(error.missing_permissions)}"
            )
        elif isinstance(error, commands.MissingRole):
            await ctx.send(
                f"You need the {error.missing_role} role to use this command!"
            )
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("This command can't be used in private messages!")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"This command is on cooldown. Try again in {error.retry_after:.1f}s"
            )
        elif isinstance(error, Exception):
            await ctx.send(str(error))
        else:
            await self.bot.process_commands(ctx.message)

    def cog_check(self, ctx: commands.Context) -> bool:
        """Default checks for all cog commands"""
        # Add any common checks here
        return True

    def ensure_voice(self, ctx: commands.Context) -> Optional[discord.VoiceClient]:
        """Utility to check voice state for audio commands"""
        if not ctx.author.voice:
            ctx.send("You need to be in a voice channel!")
            return None
        return ctx.guild.voice_client

    def log_command_use(self, ctx: commands.Context) -> None:
        """Log command usage with context"""
        logger.info(f"Command {ctx.command} used by {ctx.author} in {ctx.guild}")

    async def handle_response(
        self,
        ctx: commands.Context,
        content: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
        reaction: Optional[str] = None,
        error_msg: Optional[str] = None,
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
                except Exception:
                    pass
