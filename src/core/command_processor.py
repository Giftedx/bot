import asyncio
import logging
from typing import Dict

import discord
from discord.ext import commands

from src.utils.error_handler import ErrorHandler
from src.utils.rate_limiter import AsyncRateLimiter

logger = logging.getLogger(__name__)


class CommandProcessor:
    """Centralized command processing with rate limiting, metrics, and error handling"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.error_handler = ErrorHandler()
        self._command_semaphore = asyncio.Semaphore(10)
        self._command_timeouts: Dict[str, float] = {}
        self._rate_limiter = AsyncRateLimiter(rate=100, period=60.0, burst_size=20)

    async def process_command(self, ctx: commands.Context) -> None:
        """Process a command with rate limiting and error handling"""
        if ctx.command is None:
            return

        async with self._command_semaphore:
            try:
                # Rate limit check
                cmd_key = f"{ctx.author.id}:{ctx.command.name}"
                if not await self._rate_limiter.acquire(cmd_key):
                    await ctx.send(
                        "You're using commands too quickly! Please slow " "down."
                    )
                    return

                # Execute command
                await self.bot.invoke(ctx)

            except commands.CommandOnCooldown as e:
                await ctx.send(
                    f"This command is on cooldown. Try again in {e.retry_after:.1f}s"
                )
            except commands.MissingPermissions as _:
                await ctx.send("You don't have permission to use this command!")
            except commands.BotMissingPermissions as e:
                await ctx.send(
                    f"I need the following permissions: "
                    f"{', '.join(e.missing_permissions)}"
                )
            except commands.MissingRole as e:
                await ctx.send(
                    f"You need the {e.missing_role} role to use this command!"
                )
            except commands.NoPrivateMessage:
                await ctx.send("This command can't be used in private messages!")
            except Exception as e:
                await self.error_handler.on_command_error(ctx, e)

    async def process_message(self, message: discord.Message) -> None:
        """Process a message, extracting and handling any commands"""
        if message.author.bot:
            return

        try:
            ctx = await self.bot.get_context(message)
            if ctx.command is not None:
                await self.process_command(ctx)
        except Exception as e:
            self.error_handler.log_error(e, {"message": message.content})
