"""Base cog class with advanced features."""
from typing import Optional, Callable, Dict, List
import asyncio
import logging
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from .config import Config
from ..utils.formatting import format_error

logger = logging.getLogger(__name__)


def check_permissions(**perms: bool) -> Callable:
    """Check if the user has required permissions."""

    async def predicate(ctx: commands.Context) -> bool:
        ch = ctx.channel
        permissions = ch.permissions_for(ctx.author)

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise commands.MissingPermissions(missing)

    return commands.check(predicate)


class BaseCog(commands.Cog):
    """Base cog class with shared functionality."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self._last_member = None
        self._cooldowns: Dict[str, Dict[int, datetime]] = {}
        self.setup_cog()

    def setup_cog(self) -> None:
        """Set up the cog. Override this in subclasses."""
        pass

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Global checks for all commands in this cog."""
        return True

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Handle errors for all commands in this cog."""
        if hasattr(ctx.command, "on_error"):
            return

        error_type = type(error).__name__
        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        error_message = format_error(error)

        # Send error message to user
        try:
            embed = discord.Embed(
                title="Error", description=error_message, color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send(f"An error occurred: {error_message}")

        # Log error if it's not a common user error
        if not isinstance(
            error,
            (
                commands.CommandNotFound,
                commands.MissingPermissions,
                commands.CheckFailure,
                commands.CommandOnCooldown,
            ),
        ):
            logger.error(f"Command error in {ctx.command}: {error}", exc_info=True)

    def add_cooldown(self, user_id: int, command_name: str, duration: timedelta) -> None:
        """Add a cooldown for a user and command."""
        if command_name not in self._cooldowns:
            self._cooldowns[command_name] = {}
        self._cooldowns[command_name][user_id] = datetime.now() + duration

    def is_on_cooldown(self, user_id: int, command_name: str) -> bool:
        """Check if a command is on cooldown for a user."""
        if command_name not in self._cooldowns:
            return False

        if user_id not in self._cooldowns[command_name]:
            return False

        if datetime.now() > self._cooldowns[command_name][user_id]:
            del self._cooldowns[command_name][user_id]
            return False

        return True

    def get_cooldown_remaining(self, user_id: int, command_name: str) -> Optional[timedelta]:
        """Get remaining cooldown time for a user and command."""
        if not self.is_on_cooldown(user_id, command_name):
            return None

        return self._cooldowns[command_name][user_id] - datetime.now()

    @staticmethod
    def require_permissions(**perms: bool) -> Callable:
        """Decorator to check permissions."""
        return check_permissions(**perms)

    async def send_paginated_embed(
        self,
        ctx: commands.Context,
        title: str,
        items: List[str],
        items_per_page: int = 10,
        color: discord.Color = discord.Color.blue(),
        timeout: int = 60,
    ) -> None:
        """Send a paginated embed message."""
        pages = [items[i : i + items_per_page] for i in range(0, len(items), items_per_page)]
        total_pages = len(pages)

        if not pages:
            embed = discord.Embed(title=title, description="No items to display", color=color)
            await ctx.send(embed=embed)
            return

        current_page = 0

        def get_embed(page_num: int) -> discord.Embed:
            embed = discord.Embed(title=title, color=color)
            embed.description = "\n".join(pages[page_num])
            embed.set_footer(text=f"Page {page_num + 1}/{total_pages}")
            return embed

        message = await ctx.send(embed=get_embed(0))

        if total_pages == 1:
            return

        # Add navigation reactions
        reactions = ["⬅️", "➡️"]
        for reaction in reactions:
            await message.add_reaction(reaction)

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                user == ctx.author
                and str(reaction.emoji) in reactions
                and reaction.message.id == message.id
            )

        while True:
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=timeout, check=check
                )

                if str(reaction.emoji) == "⬅️":
                    current_page = (current_page - 1) % total_pages
                elif str(reaction.emoji) == "➡️":
                    current_page = (current_page + 1) % total_pages

                await message.edit(embed=get_embed(current_page))
                await message.remove_reaction(reaction, user)

            except asyncio.TimeoutError:
                await message.clear_reactions()
                break

    async def confirm_action(self, ctx: commands.Context, prompt: str, timeout: int = 30) -> bool:
        """Ask for user confirmation before proceeding."""
        embed = discord.Embed(
            title="Confirmation", description=prompt, color=discord.Color.yellow()
        )
        embed.set_footer(text="React with ✅ to confirm or ❌ to cancel")

        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                user == ctx.author
                and str(reaction.emoji) in ["✅", "❌"]
                and reaction.message.id == message.id
            )

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=timeout, check=check)
            await message.delete()
            return str(reaction.emoji) == "✅"
        except asyncio.TimeoutError:
            await message.delete()
            return False

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
