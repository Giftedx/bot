"""OSRS game commands implementation."""

import random
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import time
import asyncio
import json

import discord
from discord.ext import commands

from . import game_math
from .database import osrs_db
from .gathering import gathering_system
from .models import Player, SkillType
from .world_manager import world_manager


class FishingSpot:
    def __init__(self, name: str, required_level: int, fish_types: List[Dict[str, Any]], tool_required: str):
        self.name = name
        self.required_level = required_level
        self.fish_types = fish_types  # List of dicts with 'name', 'xp', 'level_req', and 'chance'
        self.tool_required = tool_required

FISHING_SPOTS = {
    'lumbridge': FishingSpot('Lumbridge Fishing Spot', 1, [
        {'name': 'Shrimp', 'xp': 10, 'level_req': 1, 'chance': 0.7},
        {'name': 'Anchovy', 'xp': 15, 'level_req': 5, 'chance': 0.3}
    ], 'Small Fishing Net'),
    'karamja': FishingSpot('Karamja Dock', 5, [
        {'name': 'Sardine', 'xp': 20, 'level_req': 5, 'chance': 0.6},
        {'name': 'Herring', 'xp': 30, 'level_req': 10, 'chance': 0.4}
    ], 'Fishing Rod'),
    'barbarian': FishingSpot('Barbarian Village', 20, [
        {'name': 'Pike', 'xp': 60, 'level_req': 25, 'chance': 0.5},
        {'name': 'Salmon', 'xp': 70, 'level_req': 30, 'chance': 0.5}
    ], 'Fly Fishing Rod')
}

COOKABLE_ITEMS = {
    'Shrimp': {'level_req': 1, 'xp': 30, 'burn_chance': 0.3},
    'Anchovy': {'level_req': 1, 'xp': 30, 'burn_chance': 0.3},
    'Sardine': {'level_req': 1, 'xp': 40, 'burn_chance': 0.3},
    'Herring': {'level_req': 5, 'xp': 50, 'burn_chance': 0.3},
    'Pike': {'level_req': 20, 'xp': 80, 'burn_chance': 0.3},
    'Salmon': {'level_req': 25, 'xp': 90, 'burn_chance': 0.3}
}

class MiningSpot:
    def __init__(self, name: str, required_level: int, ores: List[Dict[str, Any]], tool_required: str):
        self.name = name
        self.required_level = required_level
        self.ores = ores  # List of dicts with 'name', 'xp', 'level_req', 'chance', and 'respawn_time'
        self.tool_required = tool_required

MINING_SPOTS = {
    'lumbridge': MiningSpot('Lumbridge Swamp Mine', 1, [
        {'name': 'Copper ore', 'xp': 17.5, 'level_req': 1, 'chance': 0.8, 'respawn_time': 2},
        {'name': 'Tin ore', 'xp': 17.5, 'level_req': 1, 'chance': 0.8, 'respawn_time': 2}
    ], 'Bronze pickaxe'),
    'varrock': MiningSpot('Varrock East Mine', 15, [
        {'name': 'Iron ore', 'xp': 35, 'level_req': 15, 'chance': 0.6, 'respawn_time': 3},
        {'name': 'Coal', 'xp': 50, 'level_req': 30, 'chance': 0.4, 'respawn_time': 4}
    ], 'Steel pickaxe'),
    'mining_guild': MiningSpot('Mining Guild', 60, [
        {'name': 'Mithril ore', 'xp': 80, 'level_req': 55, 'chance': 0.4, 'respawn_time': 6},
        {'name': 'Adamantite ore', 'xp': 95, 'level_req': 70, 'chance': 0.2, 'respawn_time': 8}
    ], 'Rune pickaxe')
}

PICKAXES = {
    'Bronze pickaxe': {'level_req': 1, 'power': 1},
    'Iron pickaxe': {'level_req': 1, 'power': 2},
    'Steel pickaxe': {'level_req': 5, 'power': 3},
    'Mithril pickaxe': {'level_req': 20, 'power': 4},
    'Adamant pickaxe': {'level_req': 30, 'power': 5},
    'Rune pickaxe': {'level_req': 40, 'power': 6},
    'Dragon pickaxe': {'level_req': 60, 'power': 7}
}

class WoodcuttingSpot:
    def __init__(self, name: str, required_level: int, trees: List[Dict[str, Any]], tool_required: str):
        self.name = name
        self.required_level = required_level
        self.trees = trees  # List of dicts with 'name', 'xp', 'level_req', 'chance', and 'respawn_time'
        self.tool_required = tool_required

WOODCUTTING_SPOTS = {
    'lumbridge': WoodcuttingSpot('Lumbridge Trees', 1, [
        {'name': 'Normal logs', 'xp': 25, 'level_req': 1, 'chance': 0.8, 'respawn_time': 2},
        {'name': 'Oak logs', 'xp': 37.5, 'level_req': 15, 'chance': 0.6, 'respawn_time': 3}
    ], 'Bronze axe'),
    'draynor': WoodcuttingSpot('Draynor Village', 15, [
        {'name': 'Willow logs', 'xp': 67.5, 'level_req': 30, 'chance': 0.5, 'respawn_time': 4},
        {'name': 'Maple logs', 'xp': 100, 'level_req': 45, 'chance': 0.4, 'respawn_time': 5}
    ], 'Steel axe'),
    'seers': WoodcuttingSpot("Seers' Village", 60, [
        {'name': 'Yew logs', 'xp': 175, 'level_req': 60, 'chance': 0.3, 'respawn_time': 7},
        {'name': 'Magic logs', 'xp': 250, 'level_req': 75, 'chance': 0.2, 'respawn_time': 10}
    ], 'Rune axe')
}

AXES = {
    'Bronze axe': {'level_req': 1, 'power': 1},
    'Iron axe': {'level_req': 1, 'power': 2},
    'Steel axe': {'level_req': 5, 'power': 3},
    'Mithril axe': {'level_req': 20, 'power': 4},
    'Adamant axe': {'level_req': 30, 'power': 5},
    'Rune axe': {'level_req': 40, 'power': 6},
    'Dragon axe': {'level_req': 60, 'power': 7}
}

CRAFTABLE_ITEMS = {
    'Bronze bar': {
        'level_req': 1,
        'xp': 12.5,
        'materials': {
            'Copper ore': 1,
            'Tin ore': 1
        }
    },
    'Iron bar': {
        'level_req': 15,
        'xp': 25,
        'materials': {
            'Iron ore': 1
        }
    },
    'Steel bar': {
        'level_req': 30,
        'xp': 37.5,
        'materials': {
            'Iron ore': 1,
            'Coal': 2
        }
    },
    'Mithril bar': {
        'level_req': 50,
        'xp': 50,
        'materials': {
            'Mithril ore': 1,
            'Coal': 4
        }
    },
    'Adamantite bar': {
        'level_req': 70,
        'xp': 75,
        'materials': {
            'Adamantite ore': 1,
            'Coal': 6
        }
    }
}

JEWELRY_ITEMS = {
    'Gold ring': {
        'level_req': 5,
        'xp': 15,
        'materials': {
            'Gold bar': 1
        }
    },
    'Sapphire ring': {
        'level_req': 20,
        'xp': 40,
        'materials': {
            'Gold bar': 1,
            'Sapphire': 1
        }
    },
    'Emerald ring': {
        'level_req': 27,
        'xp': 55,
        'materials': {
            'Gold bar': 1,
            'Emerald': 1
        }
    },
    'Ruby ring': {
        'level_req': 34,
        'xp': 70,
        'materials': {
            'Gold bar': 1,
            'Ruby': 1
        }
    },
    'Diamond ring': {
        'level_req': 43,
        'xp': 85,
        'materials': {
            'Gold bar': 1,
            'Diamond': 1
        }
    }
}

ACHIEVEMENTS = {
    # Skill-based achievements
    'Novice Fisher': {
        'description': 'Reach level 10 in Fishing',
        'type': 'skill',
        'skill': 'fishing',
        'requirement': 10,
        'reward_xp': 1000,
        'reward_items': {'Fishing potion': 1}
    },
    'Advanced Fisher': {
        'description': 'Reach level 50 in Fishing',
        'type': 'skill',
        'skill': 'fishing',
        'requirement': 50,
        'reward_xp': 5000,
        'reward_items': {'Dragon harpoon': 1}
    },
    'Master Miner': {
        'description': 'Reach level 50 in Mining',
        'type': 'skill',
        'skill': 'mining',
        'requirement': 50,
        'reward_xp': 5000,
        'reward_items': {'Dragon pickaxe': 1}
    },
    'Woodcutting Expert': {
        'description': 'Reach level 50 in Woodcutting',
        'type': 'skill',
        'skill': 'woodcutting',
        'requirement': 50,
        'reward_xp': 5000,
        'reward_items': {'Dragon axe': 1}
    },
    'Master Craftsman': {
        'description': 'Reach level 50 in Crafting',
        'type': 'skill',
        'skill': 'crafting',
        'requirement': 50,
        'reward_xp': 5000,
        'reward_items': {'Crafting cape': 1}
    },
    
    # Item collection achievements
    'Ore Collector': {
        'description': 'Collect 100 of each type of ore',
        'type': 'collection',
        'items': {
            'Copper ore': 100,
            'Tin ore': 100,
            'Iron ore': 100,
            'Coal': 100,
            'Mithril ore': 100,
            'Adamantite ore': 100
        },
        'reward_xp': 10000,
        'reward_items': {'Mining cape': 1}
    },
    'Master Angler': {
        'description': 'Catch 100 of each type of fish',
        'type': 'collection',
        'items': {
            'Shrimp': 100,
            'Anchovy': 100,
            'Sardine': 100,
            'Herring': 100,
            'Pike': 100,
            'Salmon': 100
        },
        'reward_xp': 10000,
        'reward_items': {'Fishing cape': 1}
    },
    'Lumberjack': {
        'description': 'Chop 100 of each type of logs',
        'type': 'collection',
        'items': {
            'Normal logs': 100,
            'Oak logs': 100,
            'Willow logs': 100,
            'Maple logs': 100,
            'Yew logs': 100,
            'Magic logs': 100
        },
        'reward_xp': 10000,
        'reward_items': {'Woodcutting cape': 1}
    }
}

CLAN_RANKS = {
    'Recruit': 1,
    'Corporal': 2,
    'Sergeant': 3,
    'Lieutenant': 4,
    'Captain': 5,
    'General': 6,
    'Owner': 7
}

CLAN_PERMISSIONS = {
    'Recruit': ['view_info', 'chat'],
    'Corporal': ['view_info', 'chat', 'invite'],
    'Sergeant': ['view_info', 'chat', 'invite', 'kick_recruits'],
    'Lieutenant': ['view_info', 'chat', 'invite', 'kick_recruits', 'kick_corporals', 'promote_to_corporal'],
    'Captain': ['view_info', 'chat', 'invite', 'kick_recruits', 'kick_corporals', 'kick_sergeants', 'promote_to_sergeant'],
    'General': ['view_info', 'chat', 'invite', 'kick_recruits', 'kick_corporals', 'kick_sergeants', 'kick_lieutenants', 'promote_to_lieutenant'],
    'Owner': ['all']
}

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
    async def mine(self, ctx, location: str):
        """Start mining at the specified location"""
        location = location.lower()
        if location not in MINING_SPOTS:
            available_spots = ', '.join(MINING_SPOTS.keys())
            await ctx.send(f'Invalid mining spot. Available locations: {available_spots}')
            return

        spot = MINING_SPOTS[location]
        player = await self.get_player(ctx.author.id)
        
        if player.skills['mining'] < spot.required_level:
            await ctx.send(f'You need level {spot.required_level} Mining to mine here.')
            return

        # Find best pickaxe player can use
        best_pickaxe = None
        best_power = 0
        for pickaxe, info in PICKAXES.items():
            if (pickaxe in player.inventory and 
                info['level_req'] <= player.skills['mining'] and 
                info['power'] > best_power):
                best_pickaxe = pickaxe
                best_power = info['power']

        if not best_pickaxe:
            await ctx.send('You need a pickaxe to mine here.')
            return

        # Start mining session
        mining_embed = discord.Embed(
            title=f'Mining at {spot.name}',
            description=f'Using your {best_pickaxe}...',
            color=discord.Color.dark_grey()
        )
        message = await ctx.send(embed=mining_embed)

        # Simulate mining for 60 seconds
        end_time = time.time() + 60
        total_xp = 0
        ores_mined = {}

        while time.time() < end_time:
            # Determine ore based on probabilities and level
            possible_ores = [o for o in spot.ores if player.skills['mining'] >= o['level_req']]
            if not possible_ores:
                continue

            # Calculate mining success chance based on pickaxe power and mining level
            base_chance = 0.2 + (best_power * 0.05) + (player.skills['mining'] * 0.003)
            
            for ore in possible_ores:
                if random.random() < base_chance * ore['chance']:
                    # Successfully mined ore
                    if ore['name'] not in ores_mined:
                        ores_mined[ore['name']] = 0
                    ores_mined[ore['name']] += 1
                    total_xp += ore['xp']

                    # Add ore to inventory
                    if ore['name'] not in player.inventory:
                        player.inventory[ore['name']] = 0
                    player.inventory[ore['name']] += 1

                    # Update embed
                    ore_list = '\n'.join([f'{ore}: {count}' for ore, count in ores_mined.items()])
                    mining_embed.description = f'Using {best_pickaxe}\n\nOres mined:\n{ore_list}\n\nTotal XP: {total_xp}'
                    await message.edit(embed=mining_embed)

                    # Wait for ore to respawn
                    await asyncio.sleep(ore['respawn_time'])
                    break
            else:
                await asyncio.sleep(1)  # Wait a second before trying again if no ore was mined

        # Update player's mining XP
        player.skills['mining'] += total_xp
        await self.update_player(player)

        # Final update
        ore_list = '\n'.join([f'{ore}: {count}' for ore, count in ores_mined.items()])
        mining_embed.description = f'Mining session ended!\n\nOres mined:\n{ore_list}\n\nTotal XP gained: {total_xp}'
        await message.edit(embed=mining_embed)

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

    @osrs.group(invoke_without_command=True)
    async def bank(self, ctx):
        """Bank management commands"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="🏦 Bank Commands",
                description="Manage your OSRS bank account",
                color=discord.Color.gold()
            )
            
            commands = """
            `!osrs bank` - Show this help menu
            `!osrs bank view` - View bank contents
            `!osrs bank deposit <item> [amount]` - Deposit items
            `!osrs bank withdraw <item> [amount]` - Withdraw items
            `!osrs bank search <query>` - Search bank items
            """
            embed.add_field(name="Commands", value=commands, inline=False)
            
            await ctx.send(embed=embed)
    
    @bank.command(name="view")
    async def view_bank(self, ctx):
        """View bank contents"""
        player = osrs_db.load_character(ctx.author.id)
        if not player:
            return await ctx.send(
                "You don't have a character! Use `!osrs create <name>` to make one."
            )
        
        embed = discord.Embed(
            title=f"{player.name}'s Bank",
            color=discord.Color.gold()
        )
        
        if not player.bank.items:
            embed.description = "Your bank is empty!"
        else:
            # Group items by category
            categories = {}
            for item_id, quantity in player.bank.items.items():
                item = osrs_db.get_item(item_id)
                if not item:
                    continue
                    
                category = item.category
                if category not in categories:
                    categories[category] = []
                categories[category].append(f"{item.name}: {quantity:,}")
            
            # Add fields for each category
            for category, items in categories.items():
                embed.add_field(
                    name=category,
                    value="\n".join(items) or "None",
                    inline=True
                )
        
        embed.set_footer(
            text=f"Total items: {player.bank.get_total_items()}/{player.bank.max_slots}"
        )
        await ctx.send(embed=embed)
    
    @bank.command(name="deposit")
    async def deposit_item(self, ctx, item: str, amount: int = 1):
        """Deposit items into bank"""
        player = osrs_db.load_character(ctx.author.id)
        if not player:
            return await ctx.send(
                "You don't have a character! Use `!osrs create <name>` to make one."
            )
        
        # Find item in inventory
        inventory_item = next(
            (i for i in player.inventory if i.item.name.lower() == item.lower()),
            None
        )
        if not inventory_item:
            return await ctx.send(f"You don't have any {item} in your inventory!")
        
        # Validate amount
        if amount > inventory_item.quantity:
            amount = inventory_item.quantity
        
        # Deposit to bank
        if player.bank.add_item(inventory_item.item.id, amount):
            # Remove from inventory
            inventory_item.quantity -= amount
            if inventory_item.quantity == 0:
                player.inventory.remove(inventory_item)
            
            await ctx.send(
                f"Deposited {amount:,}x {inventory_item.item.name} into your bank."
            )
        else:
            await ctx.send("Your bank is full!")
    
    @bank.command(name="withdraw")
    async def withdraw_item(self, ctx, item: str, amount: int = 1):
        """Withdraw items from bank"""
        player = osrs_db.load_character(ctx.author.id)
        if not player:
            return await ctx.send(
                "You don't have a character! Use `!osrs create <name>` to make one."
            )
        
        # Find item in bank
        item_data = next(
            (
                (item_id, osrs_db.get_item(item_id))
                for item_id in player.bank.items
                if osrs_db.get_item(item_id).name.lower() == item.lower()
            ),
            None
        )
        
        if not item_data:
            return await ctx.send(f"You don't have any {item} in your bank!")
            
        item_id, item_obj = item_data
        
        # Validate amount
        bank_quantity = player.bank.get_item_quantity(item_id)
        if amount > bank_quantity:
            amount = bank_quantity
        
        # Check inventory space
        if len(player.inventory) >= 28:
            return await ctx.send("Your inventory is full!")
        
        # Withdraw from bank
        if player.bank.remove_item(item_id, amount):
            # Add to inventory
            inventory_item = next(
                (i for i in player.inventory if i.item.id == item_id),
                None
            )
            
            if inventory_item:
                inventory_item.quantity += amount
            else:
                player.inventory.append(
                    InventoryItem(item=item_obj, quantity=amount)
                )
            
            await ctx.send(
                f"Withdrew {amount:,}x {item_obj.name} from your bank."
            )
        else:
            await ctx.send(f"You don't have enough {item} in your bank!")
    
    @bank.command(name="search")
    async def search_bank(self, ctx, *, query: str):
        """Search for items in bank"""
        player = osrs_db.load_character(ctx.author.id)
        if not player:
            return await ctx.send(
                "You don't have a character! Use `!osrs create <name>` to make one."
            )
        
        # Search for items
        matches = []
        for item_id in player.bank.items:
            item = osrs_db.get_item(item_id)
            if not item:
                continue
                
            if query.lower() in item.name.lower():
                quantity = player.bank.get_item_quantity(item_id)
                matches.append(f"{item.name}: {quantity:,}")
        
        if not matches:
            return await ctx.send(f"No items matching '{query}' found in your bank.")
        
        # Create embed
        embed = discord.Embed(
            title=f"Bank Search: {query}",
            description="\n".join(matches),
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Found {len(matches)} items")
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='fish', description='Start fishing at a specific location')
    async def fish(self, ctx: commands.Context, location: str):
        """Start fishing at the specified location"""
        location = location.lower()
        if location not in FISHING_SPOTS:
            available_spots = ', '.join(FISHING_SPOTS.keys())
            await ctx.send(f'Invalid fishing spot. Available locations: {available_spots}')
            return

        spot = FISHING_SPOTS[location]
        player = await self.get_player(ctx.author.id)
        
        if player.skills['fishing'] < spot.required_level:
            await ctx.send(f'You need level {spot.required_level} Fishing to fish here.')
            return

        if spot.tool_required not in player.inventory:
            await ctx.send(f'You need a {spot.tool_required} to fish here.')
            return

        # Start fishing session
        fishing_embed = discord.Embed(
            title=f'Fishing at {spot.name}',
            description='You cast your line...',
            color=discord.Color.blue()
        )
        message = await ctx.send(embed=fishing_embed)

        # Simulate fishing for 60 seconds
        end_time = time.time() + 60
        total_xp = 0
        catches = []

        while time.time() < end_time:
            await asyncio.sleep(5)  # Fish every 5 seconds
            
            # Determine catch based on probabilities
            possible_fish = [f for f in spot.fish_types if player.skills['fishing'] >= f['level_req']]
            if not possible_fish:
                continue

            total_chance = sum(f['chance'] for f in possible_fish)
            roll = random.random() * total_chance
            
            current_sum = 0
            caught_fish = None
            for fish in possible_fish:
                current_sum += fish['chance']
                if roll <= current_sum:
                    caught_fish = fish
                    break

            if caught_fish:
                catches.append(caught_fish['name'])
                total_xp += caught_fish['xp']
                
                # Update embed
                fishing_embed.description = f'Current catches: {", ".join(catches)}\nTotal XP: {total_xp}'
                await message.edit(embed=fishing_embed)

        # Update player's fishing XP and inventory
        player.skills['fishing'] += total_xp
        for fish in catches:
            if fish not in player.inventory:
                player.inventory[fish] = 0
            player.inventory[fish] += 1

        await self.update_player(player)

        # Final update
        fishing_embed.description = f'Fishing session ended!\nCaught: {", ".join(catches)}\nTotal XP gained: {total_xp}'
        await message.edit(embed=fishing_embed)

    @commands.hybrid_command(name='fishing_spots', description='View available fishing spots')
    async def fishing_spots(self, ctx: commands.Context):
        """Display information about available fishing spots"""
        embed = discord.Embed(
            title='OSRS Fishing Spots',
            description='Here are all available fishing locations:',
            color=discord.Color.blue()
        )

        for spot_name, spot in FISHING_SPOTS.items():
            fish_info = '\n'.join([f"- {fish['name']} (Level {fish['level_req']}, {fish['xp']} XP)" 
                                 for fish in spot.fish_types])
            embed.add_field(
                name=f'{spot.name} (Level {spot.required_level}+)',
                value=f'Tool required: {spot.tool_required}\n{fish_info}',
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name='cook', description='Cook a raw food item')
    async def cook(self, ctx: commands.Context, item: str, amount: int = 1):
        """Cook a specified amount of raw food items"""
        item = item.title()  # Capitalize first letter of each word
        if item not in COOKABLE_ITEMS:
            cookable = ', '.join(COOKABLE_ITEMS.keys())
            await ctx.send(f'Invalid item. You can cook: {cookable}')
            return

        player = await self.get_player(ctx.author.id)
        
        # Check cooking level
        if player.skills['cooking'] < COOKABLE_ITEMS[item]['level_req']:
            await ctx.send(f"You need level {COOKABLE_ITEMS[item]['level_req']} Cooking to cook {item}.")
            return

        # Check if player has the raw items
        raw_item = f'Raw {item}'
        if raw_item not in player.inventory or player.inventory[raw_item] < amount:
            await ctx.send(f"You don't have enough {raw_item} to cook.")
            return

        # Create embed for cooking progress
        cooking_embed = discord.Embed(
            title='Cooking Progress',
            description=f'Starting to cook {amount}x {item}...',
            color=discord.Color.orange()
        )
        message = await ctx.send(embed=cooking_embed)

        successful_cooks = 0
        burnt = 0
        total_xp = 0

        for i in range(amount):
            # Calculate burn chance based on level
            level_difference = player.skills['cooking'] - COOKABLE_ITEMS[item]['level_req']
            burn_chance = max(0.05, COOKABLE_ITEMS[item]['burn_chance'] - (level_difference * 0.01))
            
            # Cook the item
            player.inventory[raw_item] -= 1
            
            if random.random() > burn_chance:
                # Successful cook
                successful_cooks += 1
                total_xp += COOKABLE_ITEMS[item]['xp']
                
                # Add cooked item to inventory
                cooked_item = item
                if cooked_item not in player.inventory:
                    player.inventory[cooked_item] = 0
                player.inventory[cooked_item] += 1
            else:
                # Burnt food
                burnt += 1
                burnt_item = f'Burnt {item}'
                if burnt_item not in player.inventory:
                    player.inventory[burnt_item] = 0
                player.inventory[burnt_item] += 1

            # Update progress every 5 items or on last item
            if (i + 1) % 5 == 0 or i == amount - 1:
                cooking_embed.description = (
                    f'Progress: {i + 1}/{amount}\n'
                    f'Successfully cooked: {successful_cooks}\n'
                    f'Burnt: {burnt}\n'
                    f'XP gained: {total_xp}'
                )
                await message.edit(embed=cooking_embed)
            
            await asyncio.sleep(1.5)  # 1.5 second per cook

        # Update player's cooking XP
        player.skills['cooking'] += total_xp
        await self.update_player(player)

        # Final update
        cooking_embed.description = (
            f'Cooking session completed!\n'
            f'Successfully cooked: {successful_cooks}x {item}\n'
            f'Burnt: {burnt}x {item}\n'
            f'Total XP gained: {total_xp}'
        )
        await message.edit(embed=cooking_embed)

    @commands.hybrid_command(name='cooking_guide', description='View cooking information')
    async def cooking_guide(self, ctx: commands.Context):
        """Display information about cookable items"""
        embed = discord.Embed(
            title='OSRS Cooking Guide',
            description='Here are all the items you can cook:',
            color=discord.Color.orange()
        )

        for item, info in COOKABLE_ITEMS.items():
            embed.add_field(
                name=f'{item} (Level {info["level_req"]})',
                value=f'XP: {info["xp"]}\nBase burn chance: {info["burn_chance"]*100}%',
                inline=True
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name='mining_spots', description='View available mining spots')
    async def mining_spots(self, ctx: commands.Context):
        """Display information about available mining spots"""
        embed = discord.Embed(
            title='OSRS Mining Spots',
            description='Here are all available mining locations:',
            color=discord.Color.dark_grey()
        )

        for spot_name, spot in MINING_SPOTS.items():
            ore_info = '\n'.join([f"- {ore['name']} (Level {ore['level_req']}, {ore['xp']} XP)" 
                                for ore in spot.ores])
            embed.add_field(
                name=f'{spot.name} (Level {spot.required_level}+)',
                value=f'Tool required: {spot.tool_required}\n{ore_info}',
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name='pickaxes', description='View available pickaxes')
    async def pickaxes(self, ctx: commands.Context):
        """Display information about available pickaxes"""
        embed = discord.Embed(
            title='OSRS Pickaxes',
            description='Here are all the pickaxes you can use:',
            color=discord.Color.dark_grey()
        )

        for pickaxe, info in PICKAXES.items():
            embed.add_field(
                name=pickaxe,
                value=f"Level required: {info['level_req']}\nMining power: {info['power']}",
                inline=True
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name='chop', description='Start woodcutting at a specific location')
    async def chop(self, ctx: commands.Context, location: str):
        """Start woodcutting at the specified location"""
        location = location.lower()
        if location not in WOODCUTTING_SPOTS:
            available_spots = ', '.join(WOODCUTTING_SPOTS.keys())
            await ctx.send(f'Invalid woodcutting spot. Available locations: {available_spots}')
            return

        spot = WOODCUTTING_SPOTS[location]
        player = await self.get_player(ctx.author.id)
        
        if player.skills['woodcutting'] < spot.required_level:
            await ctx.send(f'You need level {spot.required_level} Woodcutting to chop here.')
            return

        # Find best axe player can use
        best_axe = None
        best_power = 0
        for axe, info in AXES.items():
            if (axe in player.inventory and 
                info['level_req'] <= player.skills['woodcutting'] and 
                info['power'] > best_power):
                best_axe = axe
                best_power = info['power']

        if not best_axe:
            await ctx.send('You need an axe to chop trees.')
            return

        # Start woodcutting session
        woodcutting_embed = discord.Embed(
            title=f'Woodcutting at {spot.name}',
            description=f'Using your {best_axe}...',
            color=discord.Color.dark_green()
        )
        message = await ctx.send(embed=woodcutting_embed)

        # Simulate woodcutting for 60 seconds
        end_time = time.time() + 60
        total_xp = 0
        logs_chopped = {}

        while time.time() < end_time:
            # Determine tree based on probabilities and level
            possible_trees = [t for t in spot.trees if player.skills['woodcutting'] >= t['level_req']]
            if not possible_trees:
                continue

            # Calculate woodcutting success chance based on axe power and woodcutting level
            base_chance = 0.2 + (best_power * 0.05) + (player.skills['woodcutting'] * 0.003)
            
            for tree in possible_trees:
                if random.random() < base_chance * tree['chance']:
                    # Successfully chopped logs
                    if tree['name'] not in logs_chopped:
                        logs_chopped[tree['name']] = 0
                    logs_chopped[tree['name']] += 1
                    total_xp += tree['xp']

                    # Add logs to inventory
                    if tree['name'] not in player.inventory:
                        player.inventory[tree['name']] = 0
                    player.inventory[tree['name']] += 1

                    # Update embed
                    log_list = '\n'.join([f'{log}: {count}' for log, count in logs_chopped.items()])
                    woodcutting_embed.description = f'Using {best_axe}\n\nLogs chopped:\n{log_list}\n\nTotal XP: {total_xp}'
                    await message.edit(embed=woodcutting_embed)

                    # Wait for tree to respawn
                    await asyncio.sleep(tree['respawn_time'])
                    break
            else:
                await asyncio.sleep(1)  # Wait a second before trying again if no logs were chopped

        # Update player's woodcutting XP
        player.skills['woodcutting'] += total_xp
        await self.update_player(player)

        # Final update
        log_list = '\n'.join([f'{log}: {count}' for log, count in logs_chopped.items()])
        woodcutting_embed.description = f'Woodcutting session ended!\n\nLogs chopped:\n{log_list}\n\nTotal XP gained: {total_xp}'
        await message.edit(embed=woodcutting_embed)

    @commands.hybrid_command(name='woodcutting_spots', description='View available woodcutting spots')
    async def woodcutting_spots(self, ctx: commands.Context):
        """Display information about available woodcutting spots"""
        embed = discord.Embed(
            title='OSRS Woodcutting Spots',
            description='Here are all available woodcutting locations:',
            color=discord.Color.dark_green()
        )

        for spot_name, spot in WOODCUTTING_SPOTS.items():
            tree_info = '\n'.join([f"- {tree['name']} (Level {tree['level_req']}, {tree['xp']} XP)" 
                                for tree in spot.trees])
            embed.add_field(
                name=f'{spot.name} (Level {spot.required_level}+)',
                value=f'Tool required: {spot.tool_required}\n{tree_info}',
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name='axes', description='View available woodcutting axes')
    async def axes(self, ctx: commands.Context):
        """Display information about available woodcutting axes"""
        embed = discord.Embed(
            title='OSRS Woodcutting Axes',
            description='Here are all the axes you can use:',
            color=discord.Color.dark_green()
        )

        for axe, info in AXES.items():
            embed.add_field(
                name=axe,
                value=f"Level required: {info['level_req']}\nWoodcutting power: {info['power']}",
                inline=True
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name='smelt', description='Smelt ore into bars')
    async def smelt(self, ctx: commands.Context, item: str, amount: int = 1):
        """Smelt a specified amount of bars"""
        item = item.title()  # Capitalize first letter of each word
        if item not in CRAFTABLE_ITEMS:
            craftable = ', '.join(CRAFTABLE_ITEMS.keys())
            await ctx.send(f'Invalid item. You can smelt: {craftable}')
            return

        player = await self.get_player(ctx.author.id)
        
        # Check crafting level
        if player.skills['crafting'] < CRAFTABLE_ITEMS[item]['level_req']:
            await ctx.send(f"You need level {CRAFTABLE_ITEMS[item]['level_req']} Crafting to smelt {item}.")
            return

        # Check if player has the required materials
        for material, required_amount in CRAFTABLE_ITEMS[item]['materials'].items():
            if material not in player.inventory or player.inventory[material] < required_amount * amount:
                await ctx.send(f"You need {required_amount * amount}x {material} to smelt {amount}x {item}.")
                return

        # Create embed for smelting progress
        smelting_embed = discord.Embed(
            title='Smelting Progress',
            description=f'Starting to smelt {amount}x {item}...',
            color=discord.Color.orange()
        )
        message = await ctx.send(embed=smelting_embed)

        total_xp = 0
        items_created = 0

        for i in range(amount):
            # Remove materials from inventory
            for material, required_amount in CRAFTABLE_ITEMS[item]['materials'].items():
                player.inventory[material] -= required_amount

            # Add crafted item to inventory
            if item not in player.inventory:
                player.inventory[item] = 0
            player.inventory[item] += 1
            
            items_created += 1
            total_xp += CRAFTABLE_ITEMS[item]['xp']

            # Update progress every 5 items or on last item
            if (i + 1) % 5 == 0 or i == amount - 1:
                smelting_embed.description = (
                    f'Progress: {i + 1}/{amount}\n'
                    f'Items created: {items_created}\n'
                    f'XP gained: {total_xp}'
                )
                await message.edit(embed=smelting_embed)
            
            await asyncio.sleep(2)  # 2 seconds per smelt

        # Update player's crafting XP
        player.skills['crafting'] += total_xp
        await self.update_player(player)

        # Final update
        smelting_embed.description = (
            f'Smelting completed!\n'
            f'Created: {items_created}x {item}\n'
            f'Total XP gained: {total_xp}'
        )
        await message.edit(embed=smelting_embed)

    @commands.hybrid_command(name='craft', description='Craft jewelry')
    async def craft(self, ctx: commands.Context, item: str, amount: int = 1):
        """Craft a specified amount of jewelry"""
        item = item.title()  # Capitalize first letter of each word
        if item not in JEWELRY_ITEMS:
            craftable = ', '.join(JEWELRY_ITEMS.keys())
            await ctx.send(f'Invalid item. You can craft: {craftable}')
            return

        player = await self.get_player(ctx.author.id)
        
        # Check crafting level
        if player.skills['crafting'] < JEWELRY_ITEMS[item]['level_req']:
            await ctx.send(f"You need level {JEWELRY_ITEMS[item]['level_req']} Crafting to craft {item}.")
            return

        # Check if player has the required materials
        for material, required_amount in JEWELRY_ITEMS[item]['materials'].items():
            if material not in player.inventory or player.inventory[material] < required_amount * amount:
                await ctx.send(f"You need {required_amount * amount}x {material} to craft {amount}x {item}.")
                return

        # Create embed for crafting progress
        crafting_embed = discord.Embed(
            title='Crafting Progress',
            description=f'Starting to craft {amount}x {item}...',
            color=discord.Color.gold()
        )
        message = await ctx.send(embed=crafting_embed)

        total_xp = 0
        items_created = 0

        for i in range(amount):
            # Remove materials from inventory
            for material, required_amount in JEWELRY_ITEMS[item]['materials'].items():
                player.inventory[material] -= required_amount

            # Add crafted item to inventory
            if item not in player.inventory:
                player.inventory[item] = 0
            player.inventory[item] += 1
            
            items_created += 1
            total_xp += JEWELRY_ITEMS[item]['xp']

            # Update progress every 5 items or on last item
            if (i + 1) % 5 == 0 or i == amount - 1:
                crafting_embed.description = (
                    f'Progress: {i + 1}/{amount}\n'
                    f'Items created: {items_created}\n'
                    f'XP gained: {total_xp}'
                )
                await message.edit(embed=crafting_embed)
            
            await asyncio.sleep(1.5)  # 1.5 seconds per craft

        # Update player's crafting XP
        player.skills['crafting'] += total_xp
        await self.update_player(player)

        # Final update
        crafting_embed.description = (
            f'Crafting completed!\n'
            f'Created: {items_created}x {item}\n'
            f'Total XP gained: {total_xp}'
        )
        await message.edit(embed=crafting_embed)

    @commands.hybrid_command(name='crafting_guide', description='View crafting information')
    async def crafting_guide(self, ctx: commands.Context):
        """Display information about craftable items"""
        embed = discord.Embed(
            title='OSRS Crafting Guide',
            description='Here are all the items you can craft:',
            color=discord.Color.gold()
        )

        # Smelting section
        embed.add_field(
            name='Smelting (Bars)',
            value='Use the `!smelt` command to create these items:',
            inline=False
        )
        for item, info in CRAFTABLE_ITEMS.items():
            materials = ', '.join([f'{amount}x {material}' for material, amount in info['materials'].items()])
            embed.add_field(
                name=f'{item} (Level {info["level_req"]})',
                value=f'Materials needed: {materials}\nXP: {info["xp"]}',
                inline=True
            )

        # Jewelry section
        embed.add_field(
            name='Jewelry',
            value='Use the `!craft` command to create these items:',
            inline=False
        )
        for item, info in JEWELRY_ITEMS.items():
            materials = ', '.join([f'{amount}x {material}' for material, amount in info['materials'].items()])
            embed.add_field(
                name=f'{item} (Level {info["level_req"]})',
                value=f'Materials needed: {materials}\nXP: {info["xp"]}',
                inline=True
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name='achievements', description='View your achievements')
    async def achievements(self, ctx: commands.Context):
        """Display achievement progress and completed achievements"""
        player = await self.get_player(ctx.author.id)
        
        if 'achievements' not in player.data:
            player.data['achievements'] = {}
            await self.update_player(player)

        embed = discord.Embed(
            title='OSRS Achievements',
            description='Your achievement progress:',
            color=discord.Color.gold()
        )

        for achievement, info in ACHIEVEMENTS.items():
            # Check if achievement is already completed
            if achievement in player.data['achievements']:
                status = '✅ Completed'
            else:
                # Calculate progress based on achievement type
                if info['type'] == 'skill':
                    current = player.skills[info['skill']]
                    required = info['requirement']
                    progress = f'{current}/{required} {info["skill"].title()}'
                    status = f'🔄 In Progress - {progress}'
                elif info['type'] == 'collection':
                    progress_items = []
                    for item, required in info['items'].items():
                        current = player.inventory.get(item, 0)
                        progress_items.append(f'{item}: {current}/{required}')
                    status = '🔄 In Progress\n' + '\n'.join(progress_items)

            # Add field to embed
            embed.add_field(
                name=achievement,
                value=f'{info["description"]}\n{status}',
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name='check_achievements', description='Check for completed achievements')
    async def check_achievements(self, ctx: commands.Context):
        """Check and reward completed achievements"""
        player = await self.get_player(ctx.author.id)
        
        if 'achievements' not in player.data:
            player.data['achievements'] = {}

        completed_achievements = []

        for achievement, info in ACHIEVEMENTS.items():
            # Skip already completed achievements
            if achievement in player.data['achievements']:
                continue

            # Check if achievement is completed
            completed = False
            if info['type'] == 'skill':
                if player.skills[info['skill']] >= info['requirement']:
                    completed = True
            elif info['type'] == 'collection':
                completed = True
                for item, required in info['items'].items():
                    if item not in player.inventory or player.inventory[item] < required:
                        completed = False
                        break

            if completed:
                completed_achievements.append(achievement)
                # Mark achievement as completed
                player.data['achievements'][achievement] = datetime.now().isoformat()
                
                # Add rewards
                if 'reward_items' in info:
                    for item, amount in info['reward_items'].items():
                        if item not in player.inventory:
                            player.inventory[item] = 0
                        player.inventory[item] += amount

                # Add XP reward if applicable
                if 'reward_xp' in info and info['type'] == 'skill':
                    player.skills[info['skill']] += info['reward_xp']

        await self.update_player(player)

        if completed_achievements:
            embed = discord.Embed(
                title='Achievements Completed! 🎉',
                description='You have completed the following achievements:',
                color=discord.Color.gold()
            )

            for achievement in completed_achievements:
                info = ACHIEVEMENTS[achievement]
                rewards = []
                if 'reward_items' in info:
                    for item, amount in info['reward_items'].items():
                        rewards.append(f'{amount}x {item}')
                if 'reward_xp' in info:
                    rewards.append(f'{info["reward_xp"]} XP')

                embed.add_field(
                    name=achievement,
                    value=f'{info["description"]}\nRewards: {", ".join(rewards)}',
                    inline=False
                )

            await ctx.send(embed=embed)
        else:
            await ctx.send('No new achievements completed. Keep working hard! Use `!achievements` to view your progress.')

    @commands.hybrid_command(name='create_clan', description='Create a new clan')
    async def create_clan(self, ctx: commands.Context, clan_name: str):
        """Create a new clan with the specified name"""
        player = await self.get_player(ctx.author.id)
        
        # Check if player is already in a clan
        if 'clan' in player.data:
            await ctx.send('You are already in a clan. Leave your current clan first.')
            return

        # Create clan data
        clan_data = {
            'name': clan_name,
            'owner_id': ctx.author.id,
            'members': {
                str(ctx.author.id): {
                    'rank': 'Owner',
                    'join_date': datetime.now().isoformat()
                }
            },
            'created_date': datetime.now().isoformat(),
            'xp': 0,
            'level': 1
        }

        # Update player data
        player.data['clan'] = clan_name
        await self.update_player(player)

        # Store clan data in database
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                '''
                INSERT INTO clans (name, data)
                VALUES ($1, $2)
                ON CONFLICT (name)
                DO UPDATE SET data = $2
                ''',
                clan_name,
                json.dumps(clan_data)
            )

        embed = discord.Embed(
            title='Clan Created! 🎉',
            description=f'Successfully created clan: {clan_name}',
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='clan_info', description='View clan information')
    async def clan_info(self, ctx: commands.Context, clan_name: str = None):
        """Display information about a clan"""
        if clan_name is None:
            player = await self.get_player(ctx.author.id)
            if 'clan' not in player.data:
                await ctx.send('You are not in a clan. Specify a clan name to view info about another clan.')
                return
            clan_name = player.data['clan']

        # Get clan data from database
        async with self.bot.pool.acquire() as conn:
            clan_record = await conn.fetchrow(
                'SELECT data FROM clans WHERE name = $1',
                clan_name
            )
            if not clan_record:
                await ctx.send(f'Clan "{clan_name}" not found.')
                return
            
            clan_data = json.loads(clan_record['data'])

        embed = discord.Embed(
            title=f'Clan: {clan_name}',
            description=f'Level {clan_data["level"]} - {clan_data["xp"]} XP',
            color=discord.Color.blue()
        )

        # Add member list grouped by rank
        members_by_rank = {}
        for member_id, member_data in clan_data['members'].items():
            rank = member_data['rank']
            if rank not in members_by_rank:
                members_by_rank[rank] = []
            user = await self.bot.fetch_user(int(member_id))
            members_by_rank[rank].append(user.name)

        for rank in CLAN_RANKS:
            if rank in members_by_rank:
                embed.add_field(
                    name=rank,
                    value='\n'.join(members_by_rank[rank]),
                    inline=True
                )

        embed.set_footer(text=f'Created on {clan_data["created_date"]}')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='clan_invite', description='Invite a player to your clan')
    async def clan_invite(self, ctx: commands.Context, member: discord.Member):
        """Invite a player to join your clan"""
        player = await self.get_player(ctx.author.id)
        
        # Check if player is in a clan
        if 'clan' not in player.data:
            await ctx.send('You are not in a clan.')
            return

        # Get clan data
        async with self.bot.pool.acquire() as conn:
            clan_record = await conn.fetchrow(
                'SELECT data FROM clans WHERE name = $1',
                player.data['clan']
            )
            if not clan_record:
                await ctx.send('Error: Clan not found.')
                return
            
            clan_data = json.loads(clan_record['data'])
            member_data = clan_data['members'].get(str(ctx.author.id))
        
        # Check if player has permission to invite
        if 'invite' not in CLAN_PERMISSIONS[member_data['rank']] and member_data['rank'] != 'Owner':
            await ctx.send('You do not have permission to invite members.')
            return

        # Create invite
        if 'invites' not in clan_data:
            clan_data['invites'] = {}
        clan_data['invites'][str(member.id)] = {
            'inviter_id': ctx.author.id,
            'invite_date': datetime.now().isoformat()
        }

        # Update clan data
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                'UPDATE clans SET data = $1 WHERE name = $2',
                json.dumps(clan_data),
                player.data['clan']
            )

        embed = discord.Embed(
            title='Clan Invitation',
            description=f'{member.mention} has been invited to join {player.data["clan"]}!\nUse `!join_clan {player.data["clan"]}` to accept.',
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='join_clan', description='Join a clan you were invited to')
    async def join_clan(self, ctx: commands.Context, clan_name: str):
        """Join a clan you were invited to"""
        player = await self.get_player(ctx.author.id)
        
        # Check if player is already in a clan
        if 'clan' in player.data:
            await ctx.send('You are already in a clan. Leave your current clan first.')
            return

        # Get clan data
        async with self.bot.pool.acquire() as conn:
            clan_record = await conn.fetchrow(
                'SELECT data FROM clans WHERE name = $1',
                clan_name
            )
            if not clan_record:
                await ctx.send(f'Clan "{clan_name}" not found.')
                return
            
            clan_data = json.loads(clan_record['data'])

        # Check if player was invited
        if 'invites' not in clan_data or str(ctx.author.id) not in clan_data['invites']:
            await ctx.send('You have not been invited to this clan.')
            return

        # Add player to clan
        clan_data['members'][str(ctx.author.id)] = {
            'rank': 'Recruit',
            'join_date': datetime.now().isoformat()
        }
        # Remove invite
        del clan_data['invites'][str(ctx.author.id)]

        # Update clan data
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                'UPDATE clans SET data = $1 WHERE name = $2',
                json.dumps(clan_data),
                clan_name
            )

        # Update player data
        player.data['clan'] = clan_name
        await self.update_player(player)

        embed = discord.Embed(
            title='Welcome to the Clan! 🎉',
            description=f'You have successfully joined {clan_name}!',
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='leave_clan', description='Leave your current clan')
    async def leave_clan(self, ctx: commands.Context):
        """Leave your current clan"""
        player = await self.get_player(ctx.author.id)
        
        # Check if player is in a clan
        if 'clan' not in player.data:
            await ctx.send('You are not in a clan.')
            return

        # Get clan data
        async with self.bot.pool.acquire() as conn:
            clan_record = await conn.fetchrow(
                'SELECT data FROM clans WHERE name = $1',
                player.data['clan']
            )
            if not clan_record:
                await ctx.send('Error: Clan not found.')
                return
            
            clan_data = json.loads(clan_record['data'])
        
        # Check if player is the owner
        if clan_data['members'][str(ctx.author.id)]['rank'] == 'Owner':
            await ctx.send('As the owner, you cannot leave the clan. Transfer ownership first or disband the clan.')
            return

        # Remove player from clan
        del clan_data['members'][str(ctx.author.id)]

        # Update clan data
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                'UPDATE clans SET data = $1 WHERE name = $2',
                json.dumps(clan_data),
                player.data['clan']
            )

        # Store clan name before removing it
        clan_name = player.data['clan']

        # Remove clan from player data
        del player.data['clan']
        await self.update_player(player)

        embed = discord.Embed(
            title='Clan Departure',
            description=f'You have left {clan_name}.',
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='promote', description='Promote a clan member')
    async def promote(self, ctx: commands.Context, member: discord.Member):
        """Promote a clan member to the next rank"""
        player = await self.get_player(ctx.author.id)
        
        # Check if player is in a clan
        if 'clan' not in player.data:
            await ctx.send('You are not in a clan.')
            return

        # Get clan data
        async with self.bot.pool.acquire() as conn:
            clan_record = await conn.fetchrow(
                'SELECT data FROM clans WHERE name = $1',
                player.data['clan']
            )
            if not clan_record:
                await ctx.send('Error: Clan not found.')
                return
            
            clan_data = json.loads(clan_record['data'])

        promoter_rank = clan_data['members'][str(ctx.author.id)]['rank']
        
        # Check if target is in the clan
        if str(member.id) not in clan_data['members']:
            await ctx.send('That player is not in your clan.')
            return

        current_rank = clan_data['members'][str(member.id)]['rank']
        current_rank_level = CLAN_RANKS[current_rank]
        promoter_rank_level = CLAN_RANKS[promoter_rank]

        # Check if promoter has permission
        if f'promote_to_{current_rank.lower()}' not in CLAN_PERMISSIONS[promoter_rank] and promoter_rank != 'Owner':
            await ctx.send('You do not have permission to promote to this rank.')
            return

        # Find next rank
        next_rank = None
        for rank, level in CLAN_RANKS.items():
            if level == current_rank_level + 1 and level < promoter_rank_level:
                next_rank = rank
                break

        if not next_rank:
            await ctx.send('Cannot promote member any further.')
            return

        # Update member's rank
        clan_data['members'][str(member.id)]['rank'] = next_rank

        # Update clan data
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                'UPDATE clans SET data = $1 WHERE name = $2',
                json.dumps(clan_data),
                player.data['clan']
            )

        embed = discord.Embed(
            title='Clan Promotion',
            description=f'{member.mention} has been promoted to {next_rank}!',
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='kick', description='Kick a member from the clan')
    async def kick(self, ctx: commands.Context, member: discord.Member):
        """Kick a member from the clan"""
        player = await self.get_player(ctx.author.id)
        
        # Check if player is in a clan
        if 'clan' not in player.data:
            await ctx.send('You are not in a clan.')
            return

        clan_data = await self.get_clan(player.data['clan'])
        kicker_rank = clan_data['members'][str(ctx.author.id)]['rank']
        
        # Check if target is in the clan
        if str(member.id) not in clan_data['members']:
            await ctx.send('That player is not in your clan.')
            return

        target_rank = clan_data['members'][str(member.id)]['rank']
        
        # Check if kicker has permission
        if f'kick_{target_rank.lower()}s' not in CLAN_PERMISSIONS[kicker_rank] and kicker_rank != 'Owner':
            await ctx.send('You do not have permission to kick this rank.')
            return

        # Remove member from clan
        del clan_data['members'][str(member.id)]
        await self.update_clan(player.data['clan'], clan_data)

        # Remove clan from kicked player's data
        kicked_player = await self.get_player(member.id)
        if kicked_player and 'clan' in kicked_player.data:
            del kicked_player.data['clan']
            await self.update_player(kicked_player)

        embed = discord.Embed(
            title='Clan Member Kicked',
            description=f'{member.mention} has been kicked from the clan.',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    async def get_clan(self, clan_name: str) -> Optional[Dict]:
        """Retrieve clan data from the database"""
        async with self.bot.pool.acquire() as conn:
            clan = await conn.fetchrow(
                'SELECT * FROM clans WHERE name = $1',
                clan_name
            )
            return dict(clan) if clan else None

    async def update_clan(self, clan_name: str, clan_data: Dict):
        """Update or create clan data in the database"""
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                '''
                INSERT INTO clans (name, data)
                VALUES ($1, $2)
                ON CONFLICT (name)
                DO UPDATE SET data = $2
                ''',
                clan_name,
                json.dumps(clan_data)
            )

    @commands.hybrid_group(name='marriage', description='Marriage system commands')
    async def marriage(self, ctx: commands.Context):
        """Marriage system commands"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title='💕 Marriage System',
                description='Manage your relationships in OSRS',
                color=discord.Color.pink()
            )
            
            commands = """
            `!marriage propose <@user>` - Propose to another player
            `!marriage accept` - Accept a marriage proposal
            `!marriage decline` - Decline a marriage proposal
            `!marriage divorce` - End your marriage
            `!marriage status` - Check your marriage status
            """
            embed.add_field(name='Commands', value=commands, inline=False)
            
            await ctx.send(embed=embed)

    @marriage.command(name='propose', description='Propose marriage to another player')
    async def propose(self, ctx: commands.Context, member: discord.Member):
        """Propose marriage to another player"""
        if member.id == ctx.author.id:
            await ctx.send("You can't marry yourself!")
            return

        player = await self.get_player(ctx.author.id)
        target = await self.get_player(member.id)

        # Check if either player is already married
        async with self.bot.pool.acquire() as conn:
            existing_marriage = await conn.fetchrow(
                '''
                SELECT * FROM marriages 
                WHERE user1_id = $1 OR user2_id = $1 OR user1_id = $2 OR user2_id = $2
                ''',
                ctx.author.id, member.id
            )

            if existing_marriage:
                await ctx.send('One or both players are already married!')
                return

            # Check for existing proposal
            existing_proposal = await conn.fetchrow(
                'SELECT * FROM marriage_proposals WHERE proposer_id = $1 OR target_id = $1',
                ctx.author.id
            )

            if existing_proposal:
                await ctx.send('You already have an active marriage proposal!')
                return

            # Create proposal
            await conn.execute(
                '''
                INSERT INTO marriage_proposals (proposer_id, target_id, proposed_at)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
                ''',
                ctx.author.id, member.id
            )

        embed = discord.Embed(
            title='💝 Marriage Proposal',
            description=f'{ctx.author.mention} has proposed to {member.mention}!\n'
                       f'{member.mention} can use `!marriage accept` or `!marriage decline` to respond.',
            color=discord.Color.pink()
        )
        await ctx.send(embed=embed)

    @marriage.command(name='accept', description='Accept a marriage proposal')
    async def accept(self, ctx: commands.Context):
        """Accept a marriage proposal"""
        async with self.bot.pool.acquire() as conn:
            # Check for proposal
            proposal = await conn.fetchrow(
                'SELECT * FROM marriage_proposals WHERE target_id = $1',
                ctx.author.id
            )

            if not proposal:
                await ctx.send('You have no pending marriage proposals!')
                return

            # Create marriage
            await conn.execute(
                '''
                INSERT INTO marriages (user1_id, user2_id, married_at)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
                ''',
                proposal['proposer_id'], ctx.author.id
            )

            # Delete proposal
            await conn.execute(
                'DELETE FROM marriage_proposals WHERE proposer_id = $1',
                proposal['proposer_id']
            )

        proposer = await self.bot.fetch_user(proposal['proposer_id'])
        embed = discord.Embed(
            title='💒 Marriage Ceremony',
            description=f'Congratulations! {proposer.mention} and {ctx.author.mention} are now married!',
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @marriage.command(name='decline', description='Decline a marriage proposal')
    async def decline(self, ctx: commands.Context):
        """Decline a marriage proposal"""
        async with self.bot.pool.acquire() as conn:
            # Check for proposal
            proposal = await conn.fetchrow(
                'SELECT * FROM marriage_proposals WHERE target_id = $1',
                ctx.author.id
            )

            if not proposal:
                await ctx.send('You have no pending marriage proposals!')
                return

            # Delete proposal
            await conn.execute(
                'DELETE FROM marriage_proposals WHERE proposer_id = $1',
                proposal['proposer_id']
            )

        proposer = await self.bot.fetch_user(proposal['proposer_id'])
        embed = discord.Embed(
            title='💔 Marriage Declined',
            description=f'{proposer.mention} has declined your marriage proposal.',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @marriage.command(name='divorce', description='End your marriage')
    async def divorce(self, ctx: commands.Context):
        """End your marriage"""
        async with self.bot.pool.acquire() as conn:
            # Check for marriage
            marriage = await conn.fetchrow(
                'SELECT * FROM marriages WHERE user1_id = $1 OR user2_id = $1',
                ctx.author.id
            )

            if not marriage:
                await ctx.send('You are not married!')
                return

            # Delete marriage
            await conn.execute(
                'DELETE FROM marriages WHERE user1_id = $1 OR user2_id = $1',
                ctx.author.id
            )

        proposer = await self.bot.fetch_user(marriage['user1_id'])
        partner = await self.bot.fetch_user(marriage['user2_id'])
        embed = discord.Embed(
            title='💔 Marriage Ended',
            description=f'{proposer.mention} and {partner.mention} have decided to divorce.',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @marriage.command(name='status', description='Check your marriage status')
    async def status(self, ctx: commands.Context):
        """Check your marriage status"""
        async with self.bot.pool.acquire() as conn:
            # Check for marriage
            marriage = await conn.fetchrow(
                'SELECT * FROM marriages WHERE user1_id = $1 OR user2_id = $1',
                ctx.author.id
            )

            if not marriage:
                await ctx.send('You are not married!')
                return

            proposer = await self.bot.fetch_user(marriage['user1_id'])
            partner = await self.bot.fetch_user(marriage['user2_id'])
            embed = discord.Embed(
                title='💕 Marriage Status',
                description=f'You are married to {proposer.mention} and {partner.mention}.',
                color=discord.Color.pink()
            )
            await ctx.send(embed=embed)

    @commands.hybrid_group(name='reputation', description='Reputation system commands')
    async def reputation(self, ctx: commands.Context):
        """Reputation system commands"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title='⭐ Reputation System',
                description='Manage your reputation in OSRS',
                color=discord.Color.gold()
            )
            
            commands = """
            `!reputation give <@user> <points>` - Give reputation points to another player
            `!reputation check` - Check your reputation points
            `!reputation leaderboard` - View the reputation points leaderboard
            """
            embed.add_field(name='Commands', value=commands, inline=False)
            
            await ctx.send(embed=embed)

    @reputation.command(name='give', description='Give reputation points to another player')
    async def give_rep(self, ctx: commands.Context, member: discord.Member, points: int):
        """Give reputation points to another player"""
        if member.id == ctx.author.id:
            await ctx.send("You can't give reputation points to yourself!")
            return

        player = await self.get_player(ctx.author.id)
        target = await self.get_player(member.id)

        # Check if player has enough points to give
        if player.skills['thieving'] < points:
            await ctx.send(f"You don't have enough thieving points to give {points} points.")
            return

        # Give reputation points
        player.skills['thieving'] -= points
        target.skills['thieving'] += points

        # Update database
        if not osrs_db.update_skills(ctx.author.id, player.skills):
            await ctx.send("Error saving progress. Please try again.")
            return
        if not osrs_db.update_skills(member.id, target.skills):
            await ctx.send("Error saving progress. Please try again.")
            return

        # Log the transaction
        osrs_db.log_thieving(ctx.author.id, points)
        osrs_db.log_thieving(member.id, points)

        embed = discord.Embed(
            title='Reputation Points Given',
            description=f'You have given {points} reputation points to {member.mention}.',
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @reputation.command(name='check', description='Check reputation points')
    async def check_rep(self, ctx: commands.Context, member: discord.Member = None):
        """Check reputation points for yourself or another player"""
        target = member or ctx.author

        async with self.bot.pool.acquire() as conn:
            # Get total reputation
            rep_record = await conn.fetchrow(
                'SELECT points FROM reputation WHERE user_id = $1',
                target.id
            )

            points = rep_record['points'] if rep_record else 0

            # Get recent reputation received
            recent_rep = await conn.fetch(
                '''
                SELECT giver_id, given_at 
                FROM reputation_history 
                WHERE receiver_id = $1 
                ORDER BY given_at DESC 
                LIMIT 5
                ''',
                target.id
            )

        embed = discord.Embed(
            title=f'⭐ Reputation for {target.name}',
            description=f'Total Points: {points}',
            color=discord.Color.gold()
        )

        if recent_rep:
            recent_givers = []
            for rep in recent_rep:
                giver = await self.bot.fetch_user(rep['giver_id'])
                time_ago = datetime.now() - rep['given_at'].replace(tzinfo=None)
                days_ago = time_ago.days
                if days_ago == 0:
                    time_str = 'today'
                elif days_ago == 1:
                    time_str = 'yesterday'
                else:
                    time_str = f'{days_ago} days ago'
                recent_givers.append(f'{giver.name} ({time_str})')
            
            embed.add_field(
                name='Recent Reputation From:',
                value='\n'.join(recent_givers),
                inline=False
            )

        await ctx.send(embed=embed)

    @reputation.command(name='leaderboard', description='View reputation leaderboard')
    async def rep_leaderboard(self, ctx: commands.Context):
        """View the reputation points leaderboard"""
        async with self.bot.pool.acquire() as conn:
            top_users = await conn.fetch(
                '''
                SELECT user_id, points 
                FROM reputation 
                ORDER BY points DESC 
                LIMIT 10
                '''
            )

        if not top_users:
            await ctx.send('No reputation points have been given yet!')
            return

        embed = discord.Embed(
            title='⭐ Reputation Leaderboard',
            color=discord.Color.gold()
        )

        leaderboard = []
        for i, record in enumerate(top_users, 1):
            user = await self.bot.fetch_user(record['user_id'])
            leaderboard.append(f'{i}. {user.name}: {record["points"]} points')

        embed.description = '\n'.join(leaderboard)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OSRSCommands(bot))
