"""Error handling system for the Discord bot.

Provides centralized error handling, recovery, and user feedback through:
- Error rate monitoring and throttling
- Automatic recovery attempts
- User-friendly error messages
- Metric collection
"""

import logging
import traceback
import asyncio
import sys
from typing import Dict, Any, Optional, AsyncContextManager
from datetime import datetime, timedelta
from collections import defaultdict
from discord.ext import commands, tasks
from prometheus_client import Counter
import discord
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Handles command errors with retries and backoff."""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 1.5
    ) -> None:
        """Initialize error handler.
        
        Args:
            max_retries: Maximum number of retries
            backoff_factor: Multiplier for retry delay
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._current_try = 0

    @asynccontextmanager
    async def handle_errors(self) -> AsyncContextManager[None]:
        """Context manager for handling errors with retry logic."""
        try:
            yield
            self._current_try = 0
        except Exception as e:
            self._current_try += 1
            if self._current_try >= self.max_retries:
                logger.error(
                    f"Failed after {self.max_retries} attempts: {e}",
                    exc_info=True
                )
                raise
            logger.warning(
                f"Error on attempt {self._current_try}: {e}"
            )
            # Let the caller handle the retry timing

    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Handle command errors with user feedback"""
        error_type = type(error).__name__

        # Rate limit similar errors
        now = datetime.now()
        if error_type in self.error_cooldowns:
            if now < self.error_cooldowns[error_type]:
                return
        
        self.error_cooldowns[error_type] = now + timedelta(minutes=5)
        self.error_counts[error_type] += 1

        try:
            if isinstance(error, commands.CommandNotFound):
                await ctx.send(f"Command not found! Use {ctx.prefix}help to see available commands.")
                return

            if isinstance(error, commands.MissingPermissions):
                perms = ", ".join(error.missing_permissions)
                await ctx.send(f"You need these permissions to use this command: `{perms}`")
                return

            if isinstance(error, commands.BotMissingPermissions):
                perms = ", ".join(error.missing_permissions)
                await ctx.send(f"I need these permissions to run this command: `{perms}`")
                return

            if isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(
                    f"Missing required argument: `{error.param.name}`\n"
                    f"Use `{ctx.prefix}help {ctx.command}` to see proper usage"
                )
                return

            if isinstance(error, commands.BadArgument):
                if 'Member "' in str(error) and '" not found' in str(error):
                    await ctx.send("Could not find that user!")
                else:
                    await ctx.send(f"Invalid argument. Use `{ctx.prefix}help {ctx.command}` to see proper usage")
                return

            if isinstance(error, commands.CommandOnCooldown):
                await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.1f} seconds")
                return

            if isinstance(error, commands.NoPrivateMessage):
                await ctx.send("This command cannot be used in private messages")
                return

            if isinstance(error, commands.CheckFailure):
                await ctx.send("You don't have permission to use this command")
                return

            if isinstance(error, discord.Forbidden):
                await ctx.send("I don't have permission to do that!")
                return

            # Log unexpected errors
            self.log_error(error, {
                'command': ctx.command.name if ctx.command else 'Unknown',
                'author': str(ctx.author),
                'channel': str(ctx.channel),
                'guild': str(ctx.guild) if ctx.guild else 'DM',
                'message': ctx.message.content
            })

            await ctx.send(
                "An unexpected error occurred. The issue has been logged and will be investigated."
            )

        except Exception as e:
            logger.error("Error in error handler: %s", e, exc_info=True)

    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an error with additional context and update metrics"""
        error_type = type(error).__name__
        self.error_counts[error_type] += 1
        self.last_errors[error_type] = datetime.now()
        
        log_data = {
            'error_type': error_type,
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc()
        }
        if context:
            log_data.update(context)
        
        logger.error(
            "Error occurred: %s",
            error,
            extra=log_data,
            exc_info=True
        )

        self.error_counter.labels(
            error_type=error_type,
            severity='error'
        ).inc()

        # Notify bot owner of critical errors
        if self.error_counts[error_type] >= 5:  # Critical threshold
            self._notify_owner(error, context)

    async def _notify_owner(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Notify bot owner of critical errors"""
        if not self.bot.owner_id:
            return

        try:
            owner = await self.bot.fetch_user(self.bot.owner_id)
            error_msg = (
                f"Critical error occurred: {type(error).__name__}\n"
                f"Details: {str(error)}\n"
                f"Context: {context}\n"
                f"```py\n{traceback.format_exc()}\n```"
            )
            await owner.send(error_msg[:1900] + "..." if len(error_msg) > 1900 else error_msg)
        except Exception as e:
            logger.error("Failed to notify owner: %s", e, exc_info=True)

class ErrorHandlerCog(commands.Cog):
    """Discord cog for handling command errors and monitoring error rates"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.error_handler = ErrorHandler()
        self.check_error_thresholds.start()

    def cog_unload(self):
        self.check_error_thresholds.cancel()

    @tasks.loop(minutes=5)
    async def check_error_thresholds(self):
        """Monitor and reset error rates periodically"""
        try:
            # Reset error counts older than 1 hour
            now = datetime.now()
            cutoff = now - timedelta(hours=1)
            
            for error_type, last_time in list(self.error_handler.last_errors.items()):
                if last_time < cutoff:
                    del self.error_handler.error_counts[error_type]
                    del self.error_handler.last_errors[error_type]
                    del self.error_handler.error_cooldowns[error_type]

        except Exception as e:
            logger.error("Error in threshold check: %s", e, exc_info=True)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Forward command errors to the error handler"""
        await self.error_handler.on_command_error(ctx, error)

    @commands.Cog.listener()
    async def on_error(self, event: str, *args, **kwargs):
        """Handle non-command errors"""
        error = sys.exc_info()[1]
        self.error_handler.log_error(
            error,
            {
                'event': event,
                'args': args,
                'kwargs': kwargs
            }
        )

async def setup(bot: commands.Bot) -> None:
    """Set up the error handler cog"""
    await bot.add_cog(ErrorHandlerCog(bot))