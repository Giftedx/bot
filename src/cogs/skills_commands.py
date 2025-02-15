import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List

from ..lib.skilling.skills import Skills, SkillName, calculate_xp_for_level

class SkillsCommands(commands.Cog):
    """OSRS Skills and Training Commands"""

    def __init__(self, bot):
        self.bot = bot
        self.skills_emoji = {
            SkillName.ATTACK: "⚔️",
            SkillName.STRENGTH: "💪",
            SkillName.DEFENCE: "🛡️",
            SkillName.HITPOINTS: "❤️",
            SkillName.RANGED: "🏹",
            SkillName.PRAYER: "✨",
            SkillName.MAGIC: "🔮",
            SkillName.COOKING: "🍳",
            SkillName.WOODCUTTING: "🪓",
            SkillName.FLETCHING: "🎯",
            SkillName.FISHING: "🎣",
            SkillName.FIREMAKING: "🔥",
            SkillName.CRAFTING: "⚒️",
            SkillName.SMITHING: "🔨",
            SkillName.MINING: "⛏️",
            SkillName.HERBLORE: "🌿",
            SkillName.AGILITY: "🏃",
            SkillName.THIEVING: "💰",
            SkillName.SLAYER: "💀",
            SkillName.FARMING: "🌱",
            SkillName.RUNECRAFT: "🌀",
            SkillName.HUNTER: "🦊",
            SkillName.CONSTRUCTION: "🏠"
        }

    @app_commands.command(name='stats', description='View your skill levels and experience')
    async def stats(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        """View your or another player's stats"""
        target = member or interaction.user
        
        # Get player's skills from database
        player_skills = await self.get_player_skills(target.id)
        if not player_skills:
            await interaction.response.send_message(
                f"{'You have' if target == interaction.user else f'{target.name} has'} no stats yet. "
                "Start training to gain experience!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{target.name}'s Skills",
            color=discord.Color.blue()
        )

        # Combat skills
        combat_skills = [
            SkillName.ATTACK, SkillName.STRENGTH, SkillName.DEFENCE,
            SkillName.HITPOINTS, SkillName.RANGED, SkillName.PRAYER,
            SkillName.MAGIC
        ]
        combat_text = ""
        for skill in combat_skills:
            emoji = self.skills_emoji[skill]
            level = player_skills.get_skill_data(skill)["level"]
            xp = player_skills.get_skill_data(skill)["xp"]
            virtual_level = player_skills.get_skill_data(skill)["virtual_level"]
            
            if virtual_level and virtual_level > level:
                combat_text += f"{emoji} {skill.value.title()}: {level} ({virtual_level}) | {xp:,} XP\n"
            else:
                combat_text += f"{emoji} {skill.value.title()}: {level} | {xp:,} XP\n"
        
        embed.add_field(name="Combat Skills", value=combat_text, inline=True)

        # Other skills
        other_skills = [s for s in SkillName if s not in combat_skills]
        other_text = ""
        for skill in other_skills:
            emoji = self.skills_emoji[skill]
            level = player_skills.get_skill_data(skill)["level"]
            xp = player_skills.get_skill_data(skill)["xp"]
            virtual_level = player_skills.get_skill_data(skill)["virtual_level"]
            
            if virtual_level and virtual_level > level:
                other_text += f"{emoji} {skill.value.title()}: {level} ({virtual_level}) | {xp:,} XP\n"
            else:
                other_text += f"{emoji} {skill.value.title()}: {level} | {xp:,} XP\n"
        
        embed.add_field(name="Other Skills", value=other_text, inline=True)

        # Total level and XP
        total_level = player_skills.get_total_level()
        total_xp = player_skills.get_total_xp()
        combat_level = player_skills.get_combat_level()

        embed.add_field(
            name="Overall",
            value=f"Total Level: {total_level:,}\nTotal XP: {total_xp:,}\nCombat Level: {combat_level}",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='xp', description='Calculate XP needed for a level')
    async def xp_calc(
        self,
        interaction: discord.Interaction,
        skill: str,
        target_level: int,
        current_level: Optional[int] = None
    ):
        """Calculate XP needed to reach a target level"""
        try:
            skill_name = SkillName(skill.lower())
        except ValueError:
            await interaction.response.send_message(
                f"Invalid skill name. Valid skills: {', '.join(s.value for s in SkillName)}",
                ephemeral=True
            )
            return

        if target_level < 1 or target_level > 99:
            await interaction.response.send_message(
                "Target level must be between 1 and 99.",
                ephemeral=True
            )
            return

        if current_level is not None and (current_level < 1 or current_level >= target_level):
            await interaction.response.send_message(
                "Current level must be between 1 and your target level.",
                ephemeral=True
            )
            return

        target_xp = calculate_xp_for_level(target_level)
        current_xp = calculate_xp_for_level(current_level) if current_level else 0
        xp_needed = target_xp - current_xp

        embed = discord.Embed(
            title=f"XP Calculator - {skill_name.value.title()}",
            color=discord.Color.blue()
        )

        if current_level:
            embed.add_field(
                name="Current Level",
                value=f"{current_level} ({current_xp:,} XP)",
                inline=True
            )

        embed.add_field(
            name="Target Level",
            value=f"{target_level} ({target_xp:,} XP)",
            inline=True
        )

        embed.add_field(
            name="XP Needed",
            value=f"{xp_needed:,} XP",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='hiscores', description='View the hiscores for a skill')
    async def hiscores(
        self,
        interaction: discord.Interaction,
        skill: Optional[str] = None,
        page: int = 1
    ):
        """View the hiscores for overall or a specific skill"""
        if page < 1:
            await interaction.response.send_message("Page number must be positive.", ephemeral=True)
            return

        per_page = 10
        offset = (page - 1) * per_page

        if skill:
            try:
                skill_name = SkillName(skill.lower())
            except ValueError:
                await interaction.response.send_message(
                    f"Invalid skill name. Valid skills: {', '.join(s.value for s in SkillName)}",
                    ephemeral=True
                )
                return
        else:
            skill_name = None

        # Get hiscores from database
        if skill_name:
            title = f"{skill_name.value.title()} Hiscores"
            players = await self.get_skill_hiscores(skill_name, offset, per_page)
        else:
            title = "Overall Hiscores"
            players = await self.get_overall_hiscores(offset, per_page)

        if not players:
            await interaction.response.send_message(
                f"No players found on page {page}.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=title,
            color=discord.Color.gold()
        )

        for i, (player_id, level, xp) in enumerate(players, start=offset + 1):
            player = await self.bot.fetch_user(player_id)
            if player:
                if skill_name:
                    embed.add_field(
                        name=f"#{i}. {player.name}",
                        value=f"Level: {level} | XP: {xp:,}",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"#{i}. {player.name}",
                        value=f"Total Level: {level:,} | Total XP: {xp:,}",
                        inline=False
                    )

        embed.set_footer(text=f"Page {page}")
        await interaction.response.send_message(embed=embed)

    async def get_player_skills(self, player_id: int) -> Optional[Skills]:
        """Get a player's skills from the database"""
        # TODO: Implement database retrieval
        # For now, return a new Skills instance
        return Skills()

    async def get_skill_hiscores(self, skill: SkillName, offset: int, limit: int) -> List[tuple]:
        """Get hiscores for a specific skill"""
        # TODO: Implement database retrieval
        # Return format: List of (player_id, level, xp)
        return []

    async def get_overall_hiscores(self, offset: int, limit: int) -> List[tuple]:
        """Get overall hiscores"""
        # TODO: Implement database retrieval
        # Return format: List of (player_id, total_level, total_xp)
        return []

async def setup(bot):
    await bot.add_cog(SkillsCommands(bot)) 