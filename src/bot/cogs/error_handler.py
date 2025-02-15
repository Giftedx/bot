import logging
import traceback
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from discord.ext import commands, tasks
from prometheus_client import Counter
import discord

logger = logging.getLogger(__name__)

class ErrorHandler(commands.Cog):
    """Global error handling for bot commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.error_counts = defaultdict(int)
        self.last_errors = {}
        self.error_thresholds = {
            'critical': 5,  # Number of errors before taking action
            'warning': 3
        }
        self.error_counter = Counter(
            'bot_error_counts_total',
            'Total number of errors handled',
            ['error_type', 'severity']
        )
        self.error_cooldowns = {}
        self.cooldown_time = 300  # 5 minutes cooldown between similar errors
        self.check_error_thresholds.start()
        self.max_recovery_attempts = 3
        self._recovery_attempts = defaultdict(int)

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.check_error_thresholds.cancel()

    @tasks.loop(minutes=5)
    async def check_error_thresholds(self):
        """Monitor error rates and clean up old errors"""
        try:
            now = datetime.now()
            old_threshold = now - timedelta(hours=1)

            # Reset counts older than 1 hour
            self.error_counts = defaultdict(int)
            self.last_errors = {
                k: v for k, v in self.last_errors.items()
                if v > old_threshold
            }
            self._recovery_attempts = defaultdict(int)
            self.error_cooldowns = {
                k: v for k, v in self.error_cooldowns.items()
                if v > now
            }
        except Exception as e:
            logger.error(f"Error in threshold check: {e}", exc_info=True)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Global error handler for commands"""
        error_type = type(error).__name__

        # Rate limit similar errors
        current_time = datetime.now()
        if error_type in self.error_cooldowns:
            if current_time < self.error_cooldowns[error_type]:
                return

        self.error_cooldowns[error_type] = current_time + timedelta(seconds=self.cooldown_time)
        self.error_counts[error_type] += 1

        try:
            if isinstance(error, commands.CommandNotFound):
                suggestions = self._get_command_suggestions(ctx.invoked_with)
                if suggestions:
                    await ctx.send(
                        f"Command not found! Did you mean: {', '.join(suggestions)}?\n"
                        f"Use {ctx.prefix}help to see all commands."
                    )
                else:
                    await ctx.send(f"Command not found! Use {ctx.prefix}help to see all commands.")
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
            logger.error(
                "Command error in %s: %s",
                ctx.command,
                error,
                exc_info=error,
                extra={
                    'command': ctx.command.name if ctx.command else 'Unknown',
                    'author': str(ctx.author),
                    'channel': str(ctx.channel),
                    'guild': str(ctx.guild) if ctx.guild else 'DM',
                    'message': ctx.message.content
                }
            )

            self.error_counter.labels(
                error_type=error_type,
                severity='error'
            ).inc()

            # Notify user of unexpected errors
            await ctx.send(
                "An unexpected error occurred. The issue has been logged and will be investigated."
            )

            # Notify bot owner of critical errors
            if self.error_counts[error_type] >= self.error_thresholds['critical']:
                await self._notify_owner(error, ctx)

        except Exception as e:
            logger.error(f"Error in error handler: {e}", exc_info=True)

    def _get_command_suggestions(self, attempted_command: str) -> list[str]:
        """Get similar command suggestions using string similarity"""
        all_commands = [cmd.name for cmd in self.bot.commands]
        return [
            cmd for cmd in all_commands
            if self._string_similarity(attempted_command, cmd) > 0.75
        ][:3]

    def _string_similarity(self, a: str, b: str) -> float:
        """Calculate similarity ratio between two strings"""
        # Simple Levenshtein-based similarity
        if len(a) < 3 or len(b) < 3:
            return 0

        a = a.lower()
        b = b.lower()

        if a == b:
            return 1.0

        # Calculate Levenshtein distance
        distances = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
        for i in range(len(a) + 1):
            distances[i][0] = i
        for j in range(len(b) + 1):
            distances[0][j] = j

        for i in range(1, len(a) + 1):
            for j in range(1, len(b) + 1):
                if a[i-1] == b[j-1]:
                    distances[i][j] = distances[i-1][j-1]
                else:
                    distances[i][j] = min(
                        distances[i-1][j],
                        distances[i][j-1],
                        distances[i-1][j-1]
                    ) + 1

        max_len = max(len(a), len(b))
        similarity = 1 - (distances[len(a)][len(b)] / max_len)
        return similarity

    async def _notify_owner(self, error: Exception, ctx: commands.Context) -> None:
        """Notify bot owner of critical errors"""
        if not self.bot.owner_id:
            return

        try:
            owner = await self.bot.fetch_user(self.bot.owner_id)
            error_msg = (
                f"Critical error in command: {ctx.command}\n"
                f"Used by: {ctx.author} ({ctx.author.id})\n"
                f"Guild: {ctx.guild.name} ({ctx.guild.id})\n"
                f"Channel: {ctx.channel.name} ({ctx.channel.id})\n"
                f"Error: {str(error)}\n"
                f"```py\n{traceback.format_exc()}\n```"
            )
            await owner.send(error_msg[:1900] + "..." if len(error_msg) > 1900 else error_msg)
        except Exception as e:
            logger.error(f"Failed to notify owner: {e}", exc_info=True)

async def setup(bot: commands.Bot) -> None:
    """Set up the error handler cog"""
    await bot.add_cog(ErrorHandler(bot))