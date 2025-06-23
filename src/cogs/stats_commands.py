from discord.ext import commands
import discord
from typing import Optional, Dict
import logging
from datetime import datetime, timedelta

from ..osrs.core.player_stats import PlayerStats, PlayerStatsManager

logger = logging.getLogger(__name__)


class StatsCommands(commands.Cog):
    """Cross-game statistics commands"""

    def __init__(self, bot):
        self.bot = bot
        self.stats_manager = PlayerStatsManager()

    def get_player_stats(self, user_id: int) -> Optional[PlayerStats]:
        """Get player stats from database."""
        # TODO: Implement database loading
        return PlayerStats()  # Return default stats for now

    def format_skill_level(self, level: int, xp: float) -> str:
        """Format a skill level with XP for display."""
        if level >= 99:
            return f"99 ({xp:,.0f} xp)"

        next_level_xp = self.stats_manager.get_xp_for_level(level + 1)
        progress = self.stats_manager.get_level_progress(xp)

        return f"{level} ({progress:.1f}%)"

    def create_stats_embed(self, member: discord.Member, stats: PlayerStats) -> discord.Embed:
        """Create an embed displaying player stats."""
        embed = discord.Embed(title=f"{member.display_name}'s Stats", color=discord.Color.blue())

        # Combat stats
        combat_stats = (
            f"Attack: {self.format_skill_level(stats.attack, stats.attack_xp)}\n"
            f"Strength: {self.format_skill_level(stats.strength, stats.strength_xp)}\n"
            f"Defence: {self.format_skill_level(stats.defence, stats.defence_xp)}\n"
            f"Ranged: {self.format_skill_level(stats.ranged, stats.ranged_xp)}\n"
            f"Prayer: {self.format_skill_level(stats.prayer, stats.prayer_xp)}\n"
            f"Magic: {self.format_skill_level(stats.magic, stats.magic_xp)}\n"
            f"Hitpoints: {self.format_skill_level(stats.hitpoints, stats.hitpoints_xp)}"
        )
        embed.add_field(name="Combat Skills", value=combat_stats, inline=True)

        # Gathering skills
        gathering_stats = (
            f"Mining: {self.format_skill_level(stats.mining, stats.mining_xp)}\n"
            f"Fishing: {self.format_skill_level(stats.fishing, stats.fishing_xp)}\n"
            f"Woodcutting: {self.format_skill_level(stats.woodcutting, stats.woodcutting_xp)}\n"
            f"Farming: {self.format_skill_level(stats.farming, stats.farming_xp)}\n"
            f"Hunter: {self.format_skill_level(stats.hunter, stats.hunter_xp)}"
        )
        embed.add_field(name="Gathering Skills", value=gathering_stats, inline=True)

        # Artisan skills
        artisan_stats = (
            f"Smithing: {self.format_skill_level(stats.smithing, stats.smithing_xp)}\n"
            f"Crafting: {self.format_skill_level(stats.crafting, stats.crafting_xp)}\n"
            f"Fletching: {self.format_skill_level(stats.fletching, stats.fletching_xp)}\n"
            f"Construction: {self.format_skill_level(stats.construction, stats.construction_xp)}\n"
            f"Herblore: {self.format_skill_level(stats.herblore, stats.herblore_xp)}"
        )
        embed.add_field(name="Artisan Skills", value=artisan_stats, inline=True)

        # Support skills
        support_stats = (
            f"Agility: {self.format_skill_level(stats.agility, stats.agility_xp)}\n"
            f"Thieving: {self.format_skill_level(stats.thieving, stats.thieving_xp)}\n"
            f"Slayer: {self.format_skill_level(stats.slayer, stats.slayer_xp)}\n"
            f"Runecrafting: {self.format_skill_level(stats.runecrafting, stats.runecrafting_xp)}\n"
            f"Cooking: {self.format_skill_level(stats.cooking, stats.cooking_xp)}\n"
            f"Firemaking: {self.format_skill_level(stats.firemaking, stats.firemaking_xp)}"
        )
        embed.add_field(name="Support Skills", value=support_stats, inline=True)

        # Overall stats
        total_level = self.stats_manager.get_total_level(stats)
        combat_level = self.stats_manager.get_combat_level(stats)

        overall_stats = f"Total Level: {total_level:,}\n" f"Combat Level: {combat_level}"
        embed.add_field(name="Overall", value=overall_stats, inline=False)

        return embed

    @commands.command()
    async def stats(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Display your or another player's stats."""
        target = member or ctx.author
        stats = self.get_player_stats(target.id)

        if not stats:
            await ctx.send(f"No stats found for {target.display_name}")
            return

        embed = self.create_stats_embed(target, stats)
        await ctx.send(embed=embed)

    @commands.command()
    async def level(self, ctx: commands.Context, skill: str):
        """Display detailed information about a specific skill."""
        skill = skill.lower()
        stats = self.get_player_stats(ctx.author.id)

        if not stats:
            await ctx.send("No stats found.")
            return

        if not hasattr(stats, skill) or skill.endswith("_xp"):
            await ctx.send(f"Invalid skill: {skill}")
            return

        level = getattr(stats, skill)
        xp = getattr(stats, f"{skill}_xp")

        if level >= 99:
            embed = discord.Embed(
                title=f"{skill.title()} Level",
                description=f"Level 99 (Maximum)\nTotal XP: {xp:,.0f}",
                color=discord.Color.gold(),
            )
        else:
            current_xp = self.stats_manager.get_xp_for_level(level)
            next_xp = self.stats_manager.get_xp_for_level(level + 1)
            xp_needed = next_xp - xp
            progress = self.stats_manager.get_level_progress(xp)

            embed = discord.Embed(
                title=f"{skill.title()} Level",
                description=(
                    f"Level {level} ({progress:.1f}%)\n"
                    f"Current XP: {xp:,.0f}\n"
                    f"Next Level: {xp_needed:,.0f} XP needed"
                ),
                color=discord.Color.blue(),
            )

        await ctx.send(embed=embed)

    @commands.command()
    async def hiscores(self, ctx: commands.Context, skill: Optional[str] = None):
        """Display the hiscores for total level or a specific skill."""
        # TODO: Implement hiscores from database
        await ctx.send("Hiscores not implemented yet.")


async def setup(bot):
    await bot.add_cog(StatsCommands(bot))
