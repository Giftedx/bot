"""OSRS game commands implementation."""

import random
from datetime import datetime, timedelta
from typing import Dict, Optional

import discord
from discord.ext import commands

from . import game_math
from .database import osrs_db
from .gathering import gathering_system
from .models import Player, SkillType
from .world_manager import world_manager


class OSRSCommands(commands.Cog):
    """Old School RuneScape (OSRS) Simulation"""

    def __init__(self, bot):
        self.bot = bot
        self.training_cooldowns: Dict[int, datetime] = {}
        self.world_cache = {}
        self.SKILLS = {
            "attack": "⚔️",
            "strength": "💪",
            "defence": "🛡️",
            "hitpoints": "❤️",
            "ranged": "🏹",
            "prayer": "✨",
            "magic": "🔮",
            "mining": "⛏️",
            "woodcutting": "🪓",
            "fishing": "🎣",
            "cooking": "🍳",
            "crafting": "🔨",
            "smithing": "⚒️",
            "firemaking": "🔥",
            "agility": "🏃",
            "herblore": "🌿",
            "thieving": "💰",
            "fletching": "🏹",
            "slayer": "💀",
            "farming": "🌱",
            "construction": "🏠",
            "hunter": "🦊",
            "runecraft": "🌀",
        }

    @commands.group(invoke_without_command=True)
    async def osrs(self, ctx):
        """⚔️ OSRS Adventure System"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="⚔️ OSRS Adventure System",
                description="Welcome to Old School RuneScape!",
                color=discord.Color.gold(),
            )

            character = """
            `!osrs create <name>` - Create character
            `!osrs stats` - View your stats
            `!osrs train <skill>` - Train a skill
            `!osrs inventory` - View inventory
            """
            embed.add_field(name="🎮 Character", value=character, inline=False)

            worlds = """
            `!osrs world` - Current world
            `!osrs worlds` - List all worlds
            `!osrs join <id>` - Join a world
            """
            embed.add_field(name="🌍 Worlds", value=worlds, inline=False)

            gathering = """
            `!osrs mine <ore>` - Mine ores
            `!osrs chop <tree>` - Cut trees
            `!osrs resources` - List resources
            """
            embed.add_field(name="📦 Gathering", value=gathering, inline=False)

            embed.set_footer(text="Use !help osrs <command> for more details")
            await ctx.send(embed=embed)

    @osrs.command(name="create")
    async def create_character(self, ctx, name: str):
        """Create a new OSRS character"""
        # Check if character exists
        existing = osrs_db.load_character(ctx.author.id)
        if existing:
            return await ctx.send("You already have a character!")

        # Create new character
        player = Player(id=ctx.author.id, name=name)
        if not osrs_db.create_character(player):
            return await ctx.send("Error creating character. Please try again.")

        embed = discord.Embed(title="Character Created!", color=discord.Color.green())
        embed.add_field(name="Name", value=name)
        embed.add_field(name="Combat Level", value=str(player.get_combat_level()))
        await ctx.send(embed=embed)

    @osrs.command(name="stats")
    async def show_stats(self, ctx):
        """Show your character stats"""
        player = osrs_db.load_character(ctx.author.id)
        if not player:
            return await ctx.send(
                "You don't have a character! Use `!osrs create <name>` to make one."
            )

        embed = discord.Embed(
            title=f"{player.name}'s Stats", color=discord.Color.blue()
        )

        # Combat skills
        combat_skills = [
            SkillType.ATTACK,
            SkillType.STRENGTH,
            SkillType.DEFENCE,
            SkillType.HITPOINTS,
            SkillType.RANGED,
            SkillType.PRAYER,
            SkillType.MAGIC,
        ]
        combat_text = ""
        for skill in combat_skills:
            emoji = self.SKILLS[skill.value]
            level = player.skills[skill].level
            combat_text += f"{emoji} {skill.value.title()}: {level}\n"
        embed.add_field(name="Combat Skills", value=combat_text, inline=True)

        # Other skills
        other_skills = [s for s in SkillType if s not in combat_skills]
        other_text = ""
        for skill in other_skills:
            emoji = self.SKILLS[skill.value]
            level = player.skills[skill].level
            other_text += f"{emoji} {skill.value.title()}: {level}\n"
        embed.add_field(name="Other Skills", value=other_text, inline=True)

        embed.add_field(
            name="Combat Level", value=str(player.get_combat_level()), inline=False
        )
        await ctx.send(embed=embed)

    @osrs.command(name="train")
    async def train_skill(self, ctx, skill: str, minutes: Optional[int] = 60):
        """Train a specific skill"""
        player = osrs_db.load_character(ctx.author.id)
        if not player:
            return await ctx.send(
                "You don't have a character! Use `!osrs create <name>` to make one."
            )

        # Validate skill name
        try:
            skill_type = SkillType(skill.lower())
        except ValueError:
            return await ctx.send(f"Invalid skill: {skill}")

        # Check cooldown
        now = datetime.now()
        if ctx.author.id in self.training_cooldowns:
            remaining = (self.training_cooldowns[ctx.author.id] - now).total_seconds()
            if remaining > 0:
                return await ctx.send(
                    f"You can train again in {int(remaining)} seconds."
                )

        # Calculate XP gain
        base_xp = random.randint(20, 50)  # Base XP per minute
        total_xp = game_math.calculate_xp_rate(
            skill_type, base_xp * minutes, player.skills[skill_type].level
        )

        # Add XP and check for level up
        old_level = player.skills[skill_type].level
        leveled = player.skills[skill_type].add_xp(int(total_xp))

        # Update database
        if not osrs_db.update_skills(ctx.author.id, player.skills):
            await ctx.send("Error saving progress. Please try again.")
            return

        # Log training session
        osrs_db.log_training(ctx.author.id, skill_type, int(total_xp), minutes * 60)

        # Create response embed
        embed = discord.Embed(
            title=f"Training {skill_type.value.title()}", color=discord.Color.green()
        )
        embed.add_field(name="Time Spent", value=f"{minutes} minutes")
        embed.add_field(name="XP Gained", value=f"{int(total_xp):,}")

        if leveled:
            new_level = player.skills[skill_type].level
            embed.add_field(
                name="Level Up!", value=f"{old_level} → {new_level}", inline=False
            )

        # Set cooldown
        self.training_cooldowns[ctx.author.id] = now + timedelta(minutes=1)

        await ctx.send(embed=embed)

    @osrs.command(name="mine")
    async def mine_ore(self, ctx, ore: str):
        """Mine an ore deposit"""
        player = osrs_db.load_character(ctx.author.id)
        if not player:
            return await ctx.send(
                "You don't have a character! Use `!osrs create <name>` to make one."
            )

        # Check cooldown
        now = datetime.now()
        if ctx.author.id in self.training_cooldowns:
            remaining = (self.training_cooldowns[ctx.author.id] - now).total_seconds()
            if remaining > 0:
                return await ctx.send(
                    f"You can mine again in {int(remaining)} seconds."
                )

        # Try to gather the resource
        amount, xp = gathering_system.gather_resource(
            ore, player.skills[SkillType.MINING].level
        )

        if amount == 0:
            await ctx.send(f"Failed to mine {ore}!")
            return

        # Update player and save to database
        old_level = player.skills[SkillType.MINING].level
        leveled = player.skills[SkillType.MINING].add_xp(int(xp))

        if not osrs_db.update_skills(ctx.author.id, player.skills):
            await ctx.send("Error saving progress. Please try again.")
            return

        # Log the gathering activity
        osrs_db.log_training(
            ctx.author.id, SkillType.MINING, int(xp), 3  # 3 seconds per attempt
        )

        # Create response
        embed = discord.Embed(
            title=f"Mining {ore.title()}", color=discord.Color.green()
        )
        embed.add_field(name="Amount", value=str(amount))
        embed.add_field(name="XP Gained", value=f"{int(xp):,}")

        if leveled:
            new_level = player.skills[SkillType.MINING].level
            embed.add_field(
                name="Level Up!", value=f"{old_level} → {new_level}", inline=False
            )

        # Set cooldown
        self.training_cooldowns[ctx.author.id] = now + timedelta(seconds=3)

        await ctx.send(embed=embed)

    @osrs.command(name="chop")
    async def chop_tree(self, ctx, tree: str):
        """Cut down a tree"""
        player = osrs_db.load_character(ctx.author.id)
        if not player:
            return await ctx.send(
                "You don't have a character! Use `!osrs create <name>` to make one."
            )

        # Check cooldown
        now = datetime.now()
        if ctx.author.id in self.training_cooldowns:
            remaining = (self.training_cooldowns[ctx.author.id] - now).total_seconds()
            if remaining > 0:
                return await ctx.send(
                    f"You can chop again in {int(remaining)} seconds."
                )

        # Try to gather the resource
        amount, xp = gathering_system.gather_resource(
            tree, player.skills[SkillType.WOODCUTTING].level
        )

        if amount == 0:
            await ctx.send(f"Failed to chop {tree} tree!")
            return

        # Update player and save to database
        old_level = player.skills[SkillType.WOODCUTTING].level
        leveled = player.skills[SkillType.WOODCUTTING].add_xp(int(xp))

        if not osrs_db.update_skills(ctx.author.id, player.skills):
            await ctx.send("Error saving progress. Please try again.")
            return

        # Log the gathering activity
        osrs_db.log_training(
            ctx.author.id, SkillType.WOODCUTTING, int(xp), 3  # 3 seconds per attempt
        )

        # Create response
        embed = discord.Embed(
            title=f"Chopping {tree.title()}", color=discord.Color.green()
        )
        embed.add_field(name="Amount", value=str(amount))
        embed.add_field(name="XP Gained", value=f"{int(xp):,}")

        if leveled:
            new_level = player.skills[SkillType.WOODCUTTING].level
            embed.add_field(
                name="Level Up!", value=f"{old_level} → {new_level}", inline=False
            )

        # Set cooldown
        self.training_cooldowns[ctx.author.id] = now + timedelta(seconds=3)

        await ctx.send(embed=embed)

    @osrs.command(name="resources")
    async def list_resources(self, ctx):
        """List available gathering resources"""
        embed = discord.Embed(title="Available Resources", color=discord.Color.blue())

        # Mining resources
        mining_text = ""
        for name, resource in gathering_system.resources.items():
            if resource.skill == SkillType.MINING:
                mining_text += f"**{name.title()}** (level {resource.level})\n"
                mining_text += f"• XP: {resource.base_xp}\n"
        embed.add_field(name="⛏️ Mining", value=mining_text, inline=False)

        # Woodcutting resources
        wc_text = ""
        for name, resource in gathering_system.resources.items():
            if resource.skill == SkillType.WOODCUTTING:
                wc_text += f"**{name.title()}** (level {resource.level})\n"
                wc_text += f"• XP: {resource.base_xp}\n"
        embed.add_field(name="🪓 Woodcutting", value=wc_text, inline=False)

        await ctx.send(embed=embed)

    @osrs.group(invoke_without_command=True)
    async def worlds(self, ctx):
        """🌍 OSRS World System

        World Types:
        • Regular - Standard gameplay
        • PvP - Player vs Player enabled
        • Skill - Boosted skill XP
        • Mini-game - Special activities

        Features:
        • Different activities per world
        • World-specific bonuses
        • Player population limits
        • Special events

        Commands:
        • !osrs world - Show current world
        • !osrs worlds - List all worlds
        • !osrs join <id> - Join a world
        • !osrs players - Show player count

        Tips:
        • Check world type before joining
        • Some worlds have requirements
        • Busy worlds = better interaction
        • Events are world-specific
        """
        # ... rest of worlds implementation

    # ... rest of OSRS commands ...


async def setup(bot):
    await bot.add_cog(OSRSCommands(bot))
