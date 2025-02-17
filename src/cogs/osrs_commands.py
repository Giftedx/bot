"""OSRS Game Commands"""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Dict, List, TypedDict
from enum import Enum
import random
import asyncio

from ..core.game_client import GameClient, PlayerState
from ..osrs.mechanics import (
    CombatStyle, AttackType, CombatStats, Equipment,
    PrayerMultipliers, ExperienceTable, DropRates
)

class OSRSCommands(commands.Cog):
    """OSRS Game Commands"""
    
    def __init__(self, bot: commands.Bot, game_client: GameClient):
        self.bot = bot
        self.game = game_client
        
    # Core Commands
    
    @app_commands.command(name='register', description='Register as a new player')
    async def register(self, interaction: discord.Interaction):
        """Register as a new player"""
        player = await self.game.register_player(
            str(interaction.user.id),
            interaction.user.name
        )
        
        embed = discord.Embed(
            title="Welcome to OSRS!",
            description=f"Account created for {player.username}",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Getting Started",
            value="Use !help to see available commands\nTry training some skills with !train"
        )
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name='stats', description='View your stats')
    async def stats(self, interaction: discord.Interaction):
        """View your stats"""
        player = self.game.players.get(str(interaction.user.id))
        if not player:
            await interaction.response.send_message(
                "You must register first with !register",
                ephemeral=True
            )
            return
            
        embed = discord.Embed(
            title=f"{player.username}'s Stats",
            color=discord.Color.blue()
        )
        
        # Combat stats
        combat_text = (
            f"Combat Level: {player.combat_stats.calculate_combat_level()}\n"
            f"Attack: {player.combat_stats.attack}\n"
            f"Strength: {player.combat_stats.strength}\n"
            f"Defence: {player.combat_stats.defence}\n"
            f"Ranged: {player.combat_stats.ranged}\n"
            f"Magic: {player.combat_stats.magic}\n"
            f"Prayer: {player.combat_stats.prayer}\n"
            f"Hitpoints: {player.combat_stats.hitpoints}"
        )
        embed.add_field(name="Combat", value=combat_text, inline=True)
        
        # Skills
        skills_text = "\n".join(
            f"{skill.title()}: {level}" 
            for skill, level in sorted(player.skills.items())
            if skill not in {"hitpoints", "attack", "strength", "defence", "ranged", "magic", "prayer"}
        )
        embed.add_field(name="Skills", value=skills_text, inline=True)
        
        # Total level & XP
        embed.add_field(
            name="Totals",
            value=f"Total Level: {player.total_level}\nTotal XP: {player.total_xp:,}",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
        
    # Combat Commands
    
    @app_commands.command(name='attack', description='Attack an NPC')
    async def attack(self, interaction: discord.Interaction, target: str):
        """Attack an NPC"""
        player = self.game.players.get(str(interaction.user.id))
        if not player:
            await interaction.response.send_message(
                "You must register first with !register",
                ephemeral=True
            )
            return
            
        response = await self.game.attack_target(player, target)
        await interaction.response.send_message(response)
        
    @app_commands.command(name='prayer', description='Toggle prayers')
    async def prayer(self, interaction: discord.Interaction, prayer: str):
        """Toggle prayers on/off"""
        player = self.game.players.get(str(interaction.user.id))
        if not player:
            await interaction.response.send_message(
                "You must register first with !register",
                ephemeral=True
            )
            return
            
        response = await self.game.toggle_prayer(player, prayer)
        await interaction.response.send_message(response)
        
    # Skilling Commands
    
    @app_commands.command(name='train', description='Train a skill')
    async def train(self, interaction: discord.Interaction, skill: str):
        """Train a skill"""
        player = self.game.players.get(str(interaction.user.id))
        if not player:
            await interaction.response.send_message(
                "You must register first with !register",
                ephemeral=True
            )
            return
            
        response = await self.game.train_skill(player, skill)
        await interaction.response.send_message(response)
        
    @app_commands.command(name='farm', description='Farming commands')
    async def farm(
        self,
        interaction: discord.Interaction,
        action: str,
        patch: Optional[str] = None,
        seed: Optional[str] = None
    ):
        """Farming system commands"""
        player = self.game.players.get(str(interaction.user.id))
        if not player:
            await interaction.response.send_message(
                "You must register first with !register",
                ephemeral=True
            )
            return
            
        if action == "plant" and patch and seed:
            response = await self.game.plant_seed(player, patch, seed)
        elif action == "check":
            await self.game.check_farming_patches(player)
            response = "Checked farming patches"
        else:
            response = "Usage: !farm [plant/check] [patch] [seed]"
            
        await interaction.response.send_message(response)
        
    @app_commands.command(name='build', description='Construction commands')
    async def build(
        self,
        interaction: discord.Interaction,
        room: str,
        x: int,
        y: int,
        z: int
    ):
        """Construction system commands"""
        player = self.game.players.get(str(interaction.user.id))
        if not player:
            await interaction.response.send_message(
                "You must register first with !register",
                ephemeral=True
            )
            return
            
        response = await self.game.build_room(player, room, x, y, z)
        await interaction.response.send_message(response)
        
    # Minigame Commands
    
    @app_commands.command(name='minigame', description='Join a minigame')
    async def minigame(
        self,
        interaction: discord.Interaction,
        game: str,
        action: str = "join"
    ):
        """Minigame commands"""
        player = self.game.players.get(str(interaction.user.id))
        if not player:
            await interaction.response.send_message(
                "You must register first with !register",
                ephemeral=True
            )
            return
            
        # TODO: Implement minigame system
        await interaction.response.send_message("Minigame system coming soon!")
        
    # Quest Commands
    
    @app_commands.command(name='quest', description='View or start quests')
    async def quest(
        self,
        interaction: discord.Interaction,
        quest: Optional[str] = None
    ):
        """Quest system commands"""
        player = self.game.players.get(str(interaction.user.id))
        if not player:
            await interaction.response.send_message(
                "You must register first with !register",
                ephemeral=True
            )
            return
            
        if quest:
            # Start/continue specific quest
            # TODO: Implement quest system
            await interaction.response.send_message(f"Quest '{quest}' coming soon!")
        else:
            # Show quest list
            embed = discord.Embed(
                title=f"{player.username}'s Quests",
                color=discord.Color.blue()
            )
            
            for quest_name, status in player.quests.items():
                embed.add_field(
                    name=quest_name,
                    value=status.value.title(),
                    inline=True
                )
                
            embed.add_field(
                name="Quest Points",
                value=str(player.quest_points),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
    # Bank & Inventory Commands
    
    @app_commands.command(name='inventory', description='View your inventory')
    async def inventory(self, interaction: discord.Interaction):
        """View your inventory"""
        player = self.game.players.get(str(interaction.user.id))
        if not player:
            await interaction.response.send_message(
                "You must register first with !register",
                ephemeral=True
            )
            return
            
        response = self.game.get_inventory(player)
        await interaction.response.send_message(response)
        
    @app_commands.command(name='bank', description='View your bank')
    async def bank(self, interaction: discord.Interaction):
        """View your bank"""
        player = self.game.players.get(str(interaction.user.id))
        if not player:
            await interaction.response.send_message(
                "You must register first with !register",
                ephemeral=True
            )
            return
            
        response = self.game.get_bank(player)
        await interaction.response.send_message(response)
        
    # Achievement Commands
    
    @app_commands.command(name='achievements', description='View achievements')
    async def achievements(self, interaction: discord.Interaction):
        """View achievements and diaries"""
        player = self.game.players.get(str(interaction.user.id))
        if not player:
            await interaction.response.send_message(
                "You must register first with !register",
                ephemeral=True
            )
            return
            
        embed = discord.Embed(
            title=f"{player.username}'s Achievements",
            color=discord.Color.gold()
        )
        
        # Achievement Diaries
        for region, tiers in player.achievement_diary_progress.items():
            diary_text = "\n".join(
                f"{tier.title()}: {'✅' if completed else '❌'}"
                for tier, completed in tiers.items()
            )
            embed.add_field(
                name=f"{region.title()} Diary",
                value=diary_text,
                inline=True
            )
            
        # Other Achievements
        if player.unlocked_achievements:
            achievements_text = "\n".join(sorted(player.unlocked_achievements))
            embed.add_field(
                name="Other Achievements",
                value=achievements_text,
                inline=False
            )
            
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot) -> None:
    """Add the cog to the bot"""
    await bot.add_cog(OSRSCommands(bot, bot.game_client)) 