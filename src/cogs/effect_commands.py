from discord.ext import commands
import discord
from typing import Optional
import logging
from datetime import datetime

from ..lib.cog_utils import CogBase  # Unified dependencies

logger = logging.getLogger(__name__)


class EffectCommands(CogBase):
    """Effect and buff system commands"""

    def __init__(self, bot, **kwargs):
        super().__init__(bot, **kwargs)

    @commands.group(name="effect", aliases=["buff"], invoke_without_command=True)
    async def effect(self, ctx):
        """Effect system commands"""
        await ctx.send_help(ctx.command)

    @effect.command(name="list")
    async def effect_list(self, ctx, target: Optional[discord.Member] = None):
        """List active effects"""
        player_id = str(target.id if target else ctx.author.id)
        effects = self.database.get_active_effects(int(player_id))

        if not effects:
            await ctx.send(f"No active effects for " f"{target.display_name if target else 'you'}!")
            return

        # Create embed
        embed = discord.Embed(
            title=f"Active Effects for {target.display_name if target else ctx.author.display_name}",
            color=discord.Color.blue(),
            timestamp=datetime.now(),
        )

        # Group effects by source
        effects_by_source = {}
        for effect in effects:
            source = effect["source"]
            if source not in effects_by_source:
                effects_by_source[source] = []
            effects_by_source[source].append(effect)

        # Add fields for each source
        for source, source_effects in effects_by_source.items():
            effect_list = []
            for effect in source_effects:
                # Format duration
                duration = ""
                if effect["expires_at"]:
                    expires = datetime.fromisoformat(effect["expires_at"])
                    remaining = expires - datetime.now()
                    if remaining.total_seconds() > 0:
                        hours = int(remaining.total_seconds() // 3600)
                        minutes = int((remaining.total_seconds() % 3600) // 60)
                        duration = f" ({hours}h {minutes}m remaining)"

                # Format effect data
                data = effect["data"]
                stats = []
                for stat, value in data.get("stats", {}).items():
                    symbol = "+" if value > 0 else ""
                    stats.append(f"{stat}: {symbol}{value}")

                effect_list.append(
                    f"• {effect['type']}{duration}\n"
                    f"  {', '.join(stats) if stats else data.get('description', 'No description')}"
                )

            embed.add_field(name=source.title(), value="\n".join(effect_list), inline=False)

        await ctx.send(embed=embed)

    @effect.command(name="info")
    async def effect_info(self, ctx, effect_id: int):
        """Show detailed effect information"""
        effect = self.database.get_effect(effect_id)
        if not effect:
            await ctx.send("Effect not found!")
            return

        # Create embed
        embed = discord.Embed(
            title=f"Effect: {effect['type']}", color=discord.Color.blue(), timestamp=datetime.now()
        )

        # Add basic info
        embed.add_field(name="Source", value=effect["source"], inline=True)

        embed.add_field(
            name="Status", value="Active" if effect["active"] else "Expired", inline=True
        )

        # Add duration
        if effect["expires_at"]:
            expires = datetime.fromisoformat(effect["expires_at"])
            remaining = expires - datetime.now()
            if remaining.total_seconds() > 0:
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                embed.add_field(name="Time Remaining", value=f"{hours}h {minutes}m", inline=True)
            else:
                embed.add_field(name="Status", value="Expired", inline=True)
        else:
            embed.add_field(name="Duration", value="Permanent", inline=True)

        # Add effect data
        data = effect["data"]

        if "stats" in data:
            stats = []
            for stat, value in data["stats"].items():
                symbol = "+" if value > 0 else ""
                stats.append(f"{stat}: {symbol}{value}")

            embed.add_field(name="Stats", value="\n".join(stats), inline=False)

        if "description" in data:
            embed.add_field(name="Description", value=data["description"], inline=False)

        if "conditions" in data:
            conditions = []
            for condition, value in data["conditions"].items():
                conditions.append(f"{condition}: {value}")

            embed.add_field(name="Conditions", value="\n".join(conditions), inline=False)

        await ctx.send(embed=embed)

    @effect.command(name="remove")
    @commands.has_permissions(manage_messages=True)
    async def effect_remove(self, ctx, effect_id: int):
        """Remove an effect (Mod only)"""
        effect = self.database.get_effect(effect_id)
        if not effect:
            await ctx.send("Effect not found!")
            return

        # Add confirmation
        user = self.bot.get_user(int(effect["player_id"]))
        username = user.display_name if user else "Unknown"

        confirm = await ctx.send(
            f"Are you sure you want to remove the {effect['type']} effect from {username}? "
            "React with ✅ to confirm."
        )
        await confirm.add_reaction("✅")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == "✅"

        try:
            await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
        except TimeoutError:
            await ctx.send("Effect removal cancelled.")
            return

        # Remove effect
        self.database.remove_effect(effect_id)

        await ctx.send(f"Removed {effect['type']} effect from {username}.")

    @effect.command(name="add")
    @commands.has_permissions(manage_messages=True)
    async def effect_add(
        self, ctx, target: discord.Member, effect_type: str, duration: Optional[str] = None
    ):
        """Add an effect to a player (Mod only)"""
        player_id = str(target.id)

        # Parse duration
        duration_seconds = None
        if duration:
            try:
                value = int(duration[:-1])
                unit = duration[-1].lower()
                if unit == "h":
                    duration_seconds = value * 3600
                elif unit == "m":
                    duration_seconds = value * 60
                elif unit == "s":
                    duration_seconds = value
                else:
                    raise ValueError
            except ValueError:
                await ctx.send(
                    "Invalid duration format! Use a number followed by h/m/s "
                    "(e.g. 2h for 2 hours)"
                )
                return

        # Add effect
        effect_id = self.database.add_effect(
            int(player_id),
            effect_type,
            "admin",
            {"description": f"Added by {ctx.author.display_name}", "stats": {"admin_buff": 1}},
            duration_seconds,
        )

        # Create embed
        embed = discord.Embed(
            title="Effect Added",
            description=f"Added {effect_type} effect to {target.display_name}",
            color=discord.Color.green(),
            timestamp=datetime.now(),
        )

        if duration:
            embed.add_field(name="Duration", value=duration, inline=True)
        else:
            embed.add_field(name="Duration", value="Permanent", inline=True)

        embed.add_field(name="Effect ID", value=effect_id, inline=True)

        await ctx.send(embed=embed)

    @effect.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def effect_clear(self, ctx, target: discord.Member):
        """Clear all effects from a player (Mod only)"""
        player_id = str(target.id)

        # Add confirmation
        confirm = await ctx.send(
            f"Are you sure you want to clear ALL effects from {target.display_name}? "
            "React with ✅ to confirm."
        )
        await confirm.add_reaction("✅")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == "✅"

        try:
            await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
        except TimeoutError:
            await ctx.send("Effect clear cancelled.")
            return

        # Clear effects
        count = self.database.clear_effects(int(player_id))

        await ctx.send(f"Cleared {count} effects from {target.display_name}.")


async def setup(bot):
    await bot.add_cog(EffectCommands(bot))
