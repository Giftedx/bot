"""Utility commands cog."""
import platform
import asyncio
from datetime import datetime
from typing import Optional, List

import discord
from discord.ext import commands
from discord import app_commands

from src.core.bot import Bot


class Utility(commands.Cog):
    """General utility commands."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.start_time = datetime.now()

    @app_commands.command(name="ping", description="Get the bot's current latency.")
    async def ping(self, interaction: discord.Interaction) -> None:
        """Get the bot's current latency."""
        embed = discord.Embed(title="🏓 Pong!", color=discord.Color.green())
        embed.add_field(name="API Latency", value=f"{self.bot.latency * 1000:.2f}ms")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="info", description="Get information about the bot.")
    async def bot_info(self, interaction: discord.Interaction) -> None:
        """Get information about the bot."""
        embed = discord.Embed(title="ℹ️ Bot Information", color=discord.Color.blue())

        # General info
        embed.add_field(name="Bot Version", value=self.bot.config_manager.get_config("version", "1.0.0"))
        embed.add_field(name="Python Version", value=platform.python_version())
        embed.add_field(name="Discord.py Version", value=discord.__version__)

        # Stats
        total_members = sum(guild.member_count for guild in self.bot.guilds)
        embed.add_field(name="Servers", value=len(self.bot.guilds))
        embed.add_field(name="Total Members", value=total_members)

        # Uptime
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        embed.add_field(name="Uptime", value=f"{hours}h {minutes}m {seconds}s")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Get information about the current server.")
    @app_commands.guild_only()
    async def server_info(self, interaction: discord.Interaction) -> None:
        """Get information about the current server."""
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"ℹ️ {guild.name}",
            color=guild.owner.color if guild.owner else discord.Color.blue(),
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        # General info
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "N/A")
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
        embed.add_field(name="Boost Level", value=f"Level {guild.premium_tier}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Get a user's avatar.")
    @app_commands.describe(member="The member whose avatar to show (defaults to you)")
    async def avatar(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        """Get a user's avatar."""
        target_member = member or interaction.user
        
        if not isinstance(target_member, discord.Member) and not isinstance(target_member, discord.User):
             await interaction.response.send_message("Could not find that user.", ephemeral=True)
             return

        embed = discord.Embed(title=f"🖼️ {target_member.display_name}'s Avatar", color=target_member.color if isinstance(target_member, discord.Member) else discord.Color.default())

        embed.set_image(url=target_member.avatar.url if target_member.avatar else target_member.default_avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="roles", description="List all roles or roles of a specific member.")
    @app_commands.describe(member="Optional member whose roles to list")
    @app_commands.guild_only()
    async def list_roles(
        self, interaction: discord.Interaction, member: Optional[discord.Member] = None
    ) -> None:
        """List all roles or roles of a specific member."""
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if member:
            roles = sorted(
                [role for role in member.roles if role != guild.default_role],
                key=lambda r: r.position,
                reverse=True,
            )
            title = f"🎭 Roles for {member.display_name}"
        else:
            roles = sorted(
                [role for role in guild.roles if role != guild.default_role],
                key=lambda r: r.position,
                reverse=True,
            )
            title = "🎭 Server Roles"

        role_list = [f"{role.mention} ({len(role.members)} members)" for role in roles]

        if not role_list:
            await interaction.response.send_message("No roles found.", ephemeral=True)
            return

        await self._send_paginated_embed(
            interaction, title, role_list, items_per_page=10, color=discord.Color.blue()
        )

    @app_commands.command(name="remind", description="Set a reminder.")
    @app_commands.describe(duration="Time in minutes", reminder="What to remind you about")
    async def remind(self, interaction: discord.Interaction, duration: int, reminder: str) -> None:
        """Set a reminder."""
        if duration < 1:
            await interaction.response.send_message("Duration must be at least 1 minute.", ephemeral=True)
            return

        if duration > 1440:  # 24 hours
            confirm = await self._confirm_action(
                interaction,
                f"Are you sure you want to set a reminder for {duration} minutes "
                f"({duration/1440:.1f} days)?",
            )
            if not confirm:
                await interaction.followup.send("Reminder cancelled.", ephemeral=True)
                return

        embed = discord.Embed(
            title="⏰ Reminder Set",
            description=f"I'll remind you about: {reminder}",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Duration", value=f"{duration} minutes")
        embed.add_field(
            name="Reminder Time",
            value=f"<t:{int((datetime.now().timestamp() + duration*60)):.0f}:R>",
        )

        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.followup.send(embed=embed)

        await asyncio.sleep(duration * 60)

        try:
            reminder_embed = discord.Embed(
                title="⏰ Reminder", description=reminder, color=discord.Color.green()
            )
            await interaction.user.send(embed=reminder_embed)
        except discord.HTTPException:
            # Fails if user has DMs closed
            pass

    async def _send_paginated_embed(
        self,
        interaction: discord.Interaction,
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
            await interaction.response.send_message(embed=embed)
            return

        current_page = 0

        def get_embed(page_num: int) -> discord.Embed:
            embed = discord.Embed(title=title, color=color)
            embed.description = "\n".join(pages[page_num])
            embed.set_footer(text=f"Page {page_num + 1}/{total_pages}")
            return embed
        
        if interaction.response.is_done():
            message = await interaction.followup.send(embed=get_embed(0))
        else:
            await interaction.response.send_message(embed=get_embed(0))
            message = await interaction.original_response()

        if total_pages == 1:
            return

        reactions = ["⬅️", "➡️"]
        for reaction in reactions:
            await message.add_reaction(reaction)

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                user == interaction.user
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

    async def _confirm_action(self, interaction: discord.Interaction, prompt: str, timeout: int = 30) -> bool:
        """Ask for user confirmation before proceeding."""
        embed = discord.Embed(
            title="Confirmation", description=prompt, color=discord.Color.yellow()
        )
        embed.set_footer(text="React with ✅ to confirm or ❌ to cancel")
        
        if interaction.response.is_done():
            message = await interaction.followup.send(embed=embed, wait=True)
        else:
            await interaction.response.send_message(embed=embed)
            message = await interaction.original_response()

        await message.add_reaction("✅")
        await message.add_reaction("❌")

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                user == interaction.user
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


async def setup(bot: Bot) -> None:
    """Add the cog to the bot."""
    await bot.add_cog(Utility(bot))
