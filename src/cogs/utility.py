"""Utility commands cog."""
import platform
import time
from datetime import datetime
from typing import Optional, List

import discord
from discord.ext import commands
from discord import app_commands

from ..core.base_cog import BaseCog, check_permissions

class UtilityCog(BaseCog):
    """General utility commands."""

    def setup_cog(self) -> None:
        """Set up the utility cog."""
        self.start_time = datetime.now()

    @commands.hybrid_command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        """Get the bot's current latency."""
        start_time = time.perf_counter()
        message = await ctx.send("Pinging...")
        end_time = time.perf_counter()

        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Bot Latency",
            value=f"{(end_time - start_time) * 1000:.2f}ms"
        )
        embed.add_field(
            name="API Latency",
            value=f"{self.bot.latency * 1000:.2f}ms"
        )

        await message.edit(content=None, embed=embed)

    @commands.hybrid_command(name="info")
    async def bot_info(self, ctx: commands.Context) -> None:
        """Get information about the bot."""
        embed = discord.Embed(
            title="ℹ️ Bot Information",
            color=discord.Color.blue()
        )

        # General info
        embed.add_field(
            name="Bot Version",
            value=self.config.get_config("version", "1.0.0")
        )
        embed.add_field(
            name="Python Version",
            value=platform.python_version()
        )
        embed.add_field(
            name="Discord.py Version",
            value=discord.__version__
        )

        # Stats
        total_members = sum(guild.member_count for guild in self.bot.guilds)
        embed.add_field(name="Servers", value=len(self.bot.guilds))
        embed.add_field(name="Total Members", value=total_members)
        
        # Uptime
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        embed.add_field(
            name="Uptime",
            value=f"{hours}h {minutes}m {seconds}s"
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="serverinfo")
    @commands.guild_only()
    async def server_info(self, ctx: commands.Context) -> None:
        """Get information about the current server."""
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"ℹ️ {guild.name}",
            color=guild.owner.color if guild.owner else discord.Color.blue()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        # General info
        embed.add_field(name="Owner", value=guild.owner.mention)
        embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"))
        embed.add_field(name="Region", value=str(guild.preferred_locale))

        # Member stats
        total_members = guild.member_count
        online_members = len([m for m in guild.members if m.status != discord.Status.offline])
        bot_count = len([m for m in guild.members if m.bot])
        
        embed.add_field(name="Total Members", value=total_members)
        embed.add_field(name="Online Members", value=online_members)
        embed.add_field(name="Bots", value=bot_count)

        # Channel stats
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(name="Text Channels", value=text_channels)
        embed.add_field(name="Voice Channels", value=voice_channels)
        embed.add_field(name="Categories", value=categories)

        # Role info
        embed.add_field(name="Roles", value=len(guild.roles))
        embed.add_field(name="Emojis", value=len(guild.emojis))
        embed.add_field(
            name="Boost Level",
            value=f"Level {guild.premium_tier}"
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="avatar")
    async def avatar(
        self,
        ctx: commands.Context,
        member: Optional[discord.Member] = None
    ) -> None:
        """Get a user's avatar.
        
        Args:
            member: The member whose avatar to show (default: command user)
        """
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"🖼️ {member.display_name}'s Avatar",
            color=member.color
        )
        
        embed.set_image(
            url=member.avatar.url if member.avatar else member.default_avatar.url
        )
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="roles")
    @commands.guild_only()
    async def list_roles(
        self,
        ctx: commands.Context,
        member: Optional[discord.Member] = None
    ) -> None:
        """List all roles or roles of a specific member.
        
        Args:
            member: Optional member whose roles to list
        """
        if member:
            roles = sorted(
                [role for role in member.roles if role != ctx.guild.default_role],
                key=lambda r: r.position,
                reverse=True
            )
            title = f"🎭 Roles for {member.display_name}"
        else:
            roles = sorted(
                [role for role in ctx.guild.roles if role != ctx.guild.default_role],
                key=lambda r: r.position,
                reverse=True
            )
            title = "🎭 Server Roles"

        role_list = [
            f"{role.mention} ({len(role.members)} members)"
            for role in roles
        ]

        if not role_list:
            await ctx.send("No roles found.")
            return

        await self.send_paginated_embed(
            ctx,
            title,
            role_list,
            items_per_page=10,
            color=discord.Color.blue()
        )

    @commands.hybrid_command(name="remind")
    async def remind(
        self,
        ctx: commands.Context,
        duration: int,
        *,
        reminder: str
    ) -> None:
        """Set a reminder.
        
        Args:
            duration: Time in minutes
            reminder: What to remind you about
        """
        if duration < 1:
            await ctx.send("Duration must be at least 1 minute.")
            return

        if duration > 1440:  # 24 hours
            confirm = await self.confirm_action(
                ctx,
                f"Are you sure you want to set a reminder for {duration} minutes "
                f"({duration/1440:.1f} days)?"
            )
            if not confirm:
                await ctx.send("Reminder cancelled.")
                return

        # Send confirmation
        embed = discord.Embed(
            title="⏰ Reminder Set",
            description=f"I'll remind you about: {reminder}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Duration", value=f"{duration} minutes")
        embed.add_field(
            name="Reminder Time",
            value=f"<t:{int((datetime.now().timestamp() + duration*60)):.0f}:R>"
        )
        
        await ctx.send(embed=embed)

        # Schedule reminder
        import asyncio
        await asyncio.sleep(duration * 60)
        
        try:
            reminder_embed = discord.Embed(
                title="⏰ Reminder",
                description=reminder,
                color=discord.Color.green()
            )
            await ctx.author.send(embed=reminder_embed)
        except discord.HTTPException:
            await ctx.send(
                f"{ctx.author.mention} Here's your reminder: {reminder}"
            )

async def setup(bot: commands.Bot) -> None:
    """Add the cog to the bot."""
    await bot.add_cog(UtilityCog(bot)) 