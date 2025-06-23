"""Base cog providing common functionality for all cogs."""
import logging
from typing import Optional, Any, Dict

import discord
from discord.ext import commands

from ..core.metrics import MetricsRegistry
from ..utils.formatting import format_error

logger = logging.getLogger(__name__)


class BaseCog(commands.Cog):
    """Base cog class with shared functionality."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._metrics = self._setup_metrics()

    def _setup_metrics(self) -> Dict[str, Any]:
        """Set up metrics for the cog."""
        metrics = MetricsRegistry()
        return {
            "commands": metrics.counter(
                f"{self.__class__.__name__.lower()}_commands_total",
                f"Total number of {self.__class__.__name__} commands executed",
            ),
            "errors": metrics.counter(
                f"{self.__class__.__name__.lower()}_errors_total",
                f"Total number of {self.__class__.__name__} errors",
                ["type"],
            ),
            "latency": metrics.histogram(
                f"{self.__class__.__name__.lower()}_command_latency_seconds",
                f"Command execution time for {self.__class__.__name__}",
                ["command"],
            ),
        }

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        """Called before any command in this cog is invoked."""
        self._metrics["commands"].inc()
        ctx.command_start_time = ctx.message.created_at.timestamp()

    async def cog_after_invoke(self, ctx: commands.Context) -> None:
        """Called after any command in this cog is invoked."""
        if hasattr(ctx, "command_start_time"):
            latency = ctx.message.created_at.timestamp() - ctx.command_start_time
            self._metrics["latency"].labels(command=ctx.command.name).observe(latency)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Handle errors for all commands in this cog."""
        error_type = type(error).__name__
        self._metrics["errors"].labels(type=error_type).inc()

        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        error_message = format_error(error)
        await ctx.send(error_message)

        if not isinstance(
            error, (commands.CommandNotFound, commands.MissingPermissions, commands.CheckFailure)
        ):
            logger.error(f"Error in {ctx.command} command: {error}", exc_info=True)

    def cog_check(self, ctx: commands.Context) -> bool:
        """Global check for all commands in this cog."""
        return True

    def ensure_voice(self, ctx: commands.Context) -> Optional[discord.VoiceClient]:
        """Utility to check voice state for audio commands."""
        if not ctx.author.voice:
            raise commands.CheckFailure("You need to be in a voice channel!")
        return ctx.guild.voice_client

    async def handle_response(
        self,
        ctx: commands.Context,
        content: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
        file: Optional[discord.File] = None,
        reaction: Optional[str] = None,
        error_msg: Optional[str] = None,
    ) -> None:
        """Standardized command response handling."""
        try:
            if file:
                await ctx.send(content=content, embed=embed, file=file)
            elif embed:
                await ctx.send(content=content, embed=embed)
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


async def setup(bot: commands.Bot) -> None:
    """Set up the base cog."""
    await bot.add_cog(BaseCog(bot))
