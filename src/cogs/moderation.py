"""Moderation commands cog."""
from datetime import timedelta
from typing import Optional, Union

import discord
from discord.ext import commands

from ..core.base_cog import BaseCog, check_permissions


class ModerationCog(BaseCog):
    """Commands for server moderation."""

    def setup_cog(self) -> None:
        """Set up the moderation cog."""
        # Initialize any cog-specific state here
        self._warn_counts = {}

    @commands.command(name="warn")
    @commands.guild_only()
    @check_permissions(manage_messages=True)
    async def warn_user(
        self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"
    ) -> None:
        """Warn a user.

        Args:
            member: The member to warn
            reason: The reason for the warning
        """
        # Check if command is on cooldown
        if self.is_on_cooldown(ctx.author.id, "warn"):
            remaining = self.get_cooldown_remaining(ctx.author.id, "warn")
            await ctx.send(
                f"This command is on cooldown. Try again in {remaining.seconds} seconds."
            )
            return

        # Add cooldown
        self.add_cooldown(ctx.author.id, "warn", timedelta(minutes=1))

        # Track warning count
        if member.id not in self._warn_counts:
            self._warn_counts[member.id] = 0
        self._warn_counts[member.id] += 1

        # Create warning embed
        embed = discord.Embed(
            title="⚠️ Warning",
            description=f"{member.mention} has been warned.",
            color=discord.Color.yellow(),
        )
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Warning Count", value=str(self._warn_counts[member.id]))
        embed.set_footer(
            text=f"Warned by {ctx.author}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
        )

        await ctx.send(embed=embed)

        # DM the user
        try:
            await member.send(f"You have been warned in {ctx.guild.name} for: {reason}")
        except discord.HTTPException:
            await ctx.send("Could not DM user about the warning.")

    @commands.command(name="clear")
    @commands.guild_only()
    @check_permissions(manage_messages=True)
    async def clear_messages(self, ctx: commands.Context, amount: int = 10) -> None:
        """Clear a number of messages from the channel.

        Args:
            amount: Number of messages to clear (default: 10)
        """
        if amount < 1:
            await ctx.send("Please specify a positive number of messages to clear.")
            return

        if amount > 100:
            confirm = await self.confirm_action(
                ctx, f"Are you sure you want to delete {amount} messages?"
            )
            if not confirm:
                await ctx.send("Operation cancelled.")
                return

        try:
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 for command message
            await ctx.send(f"Deleted {len(deleted)-1} messages.", delete_after=5)
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete messages.")
        except discord.HTTPException as e:
            await ctx.send(f"Error deleting messages: {e}")

    @commands.command(name="timeout")
    @commands.guild_only()
    @check_permissions(moderate_members=True)
    async def timeout_user(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: int,
        *,
        reason: str = "No reason provided",
    ) -> None:
        """Timeout a user for a specified duration.

        Args:
            member: The member to timeout
            duration: Timeout duration in minutes
            reason: Reason for the timeout
        """
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot timeout someone with a higher or equal role.")
            return

        try:
            await member.timeout(timedelta(minutes=duration), reason=f"By {ctx.author}: {reason}")

            embed = discord.Embed(
                title="🔇 Timeout",
                description=f"{member.mention} has been timed out.",
                color=discord.Color.orange(),
            )
            embed.add_field(name="Duration", value=f"{duration} minutes")
            embed.add_field(name="Reason", value=reason)
            embed.set_footer(
                text=f"Timed out by {ctx.author}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
            )

            await ctx.send(embed=embed)

            # DM the user
            try:
                await member.send(
                    f"You have been timed out in {ctx.guild.name} "
                    f"for {duration} minutes.\nReason: {reason}"
                )
            except discord.HTTPException:
                await ctx.send("Could not DM user about the timeout.")

        except discord.Forbidden:
            await ctx.send("I don't have permission to timeout members.")
        except discord.HTTPException as e:
            await ctx.send(f"Error timing out member: {e}")

    @commands.command(name="infractions")
    @commands.guild_only()
    @check_permissions(manage_messages=True)
    async def view_infractions(
        self, ctx: commands.Context, member: Optional[discord.Member] = None
    ) -> None:
        """View warning count for a user or all users.

        Args:
            member: Optional member to view infractions for
        """
        if member:
            count = self._warn_counts.get(member.id, 0)
            await ctx.send(f"{member.mention} has {count} warning(s).")
        else:
            # Create list of all infractions
            infractions = []
            for user_id, count in self._warn_counts.items():
                member = ctx.guild.get_member(user_id)
                if member:
                    infractions.append(f"{member.mention}: {count} warning(s)")

            if not infractions:
                await ctx.send("No infractions recorded.")
                return

            # Send paginated embed
            await self.send_paginated_embed(
                ctx, "📋 Infractions", infractions, items_per_page=10, color=discord.Color.blue()
            )


async def setup(bot: commands.Bot) -> None:
    """Add the cog to the bot."""
    await bot.add_cog(ModerationCog(bot))
