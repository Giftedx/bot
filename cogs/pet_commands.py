import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import discord
from discord.ext import commands


class PetCommands(commands.Cog):
    """Pet system for adopting and raising virtual pets"""

    def __init__(self, bot):
        self.bot = bot
        self.active_battles = {}
        self.training_cooldowns = {}
        self.PET_TYPES = {
            "dog": {
                "emoji": "🐕",
                "skills": ["fetch", "guard", "tricks"],
                "base_stats": {"health": 100, "attack": 15, "defense": 10},
                "training_bonus": "loyalty",
            },
            "cat": {
                "emoji": "🐱",
                "skills": ["hunt", "sneak", "agility"],
                "base_stats": {"health": 80, "attack": 20, "defense": 8},
                "training_bonus": "agility",
            },
            "dragon": {
                "emoji": "🐲",
                "skills": ["fly", "breathe-fire", "roar"],
                "base_stats": {"health": 150, "attack": 25, "defense": 20},
                "training_bonus": "strength",
            },
            "phoenix": {
                "emoji": "🦅",
                "skills": ["rebirth", "heal", "flame"],
                "base_stats": {"health": 120, "attack": 18, "defense": 15},
                "training_bonus": "magic",
            },
            "unicorn": {
                "emoji": "🦄",
                "skills": ["heal", "magic", "rainbow"],
                "base_stats": {"health": 110, "attack": 15, "defense": 12},
                "training_bonus": "healing",
            },
        }

    @commands.group(invoke_without_command=True)
    async def pet(self, ctx):
        """🐾 Pet System

        Main Features:
        1️⃣ Pet Management
        • Adopt different types of pets
        • Name and customize your pets
        • View pet stats and skills
        • Release unwanted pets

        2️⃣ Training System
        • Train pets to improve stats
        • Learn new skills
        • Complete daily tasks
        • Earn rewards

        3️⃣ Battle System
        • Challenge other pets
        • Turn-based combat
        • Use special abilities
        • Earn experience

        Commands:
        🏠 Management
        • !pet adopt <type> <name> - Get a new pet
        • !pet list - View your pets
        • !pet info <name> - Pet details
        • !pet rename <old> <new> - Rename pet
        • !pet release <name> - Release pet

        📈 Training
        • !pet train <name> - Train your pet
        • !pet feed <name> - Feed your pet
        • !pet play <name> - Play with pet
        • !pet stats <name> - View progress

        ⚔️ Battling
        • !pet battle @user - Challenge another pet
        • !pet accept - Accept challenge
        • !pet move <skill> - Use skill in battle
        • !pet heal - Heal your pet

        Use !help pet <command> for details
        Example: !help pet adopt"""

        embed = discord.Embed(
            title="🐾 Pet Adventure System",
            description="Welcome to the Pet System!",
            color=discord.Color.green(),
        )

        # Available Pets Section
        pets = "\n".join(
            f"{data['emoji']} {ptype.title()} - {data['training_bonus'].title()} bonus"
            for ptype, data in self.PET_TYPES.items()
        )
        embed.add_field(name="🏠 Available Pets", value=pets, inline=False)

        # Commands Section
        management = """
        `!pet adopt <type> <name>` - Get new pet
        `!pet list` - View your pets
        `!pet info <name>` - Pet details
        `!pet rename <old> <new>` - Rename pet
        """
        embed.add_field(name="📋 Pet Management", value=management, inline=False)

        training = """
        `!pet train <name>` - Train pet
        `!pet feed <name>` - Feed pet
        `!pet play <name>` - Play with pet
        `!pet stats <name>` - Check progress
        """
        embed.add_field(name="📈 Training System", value=training, inline=False)

        battle = """
        `!pet battle @user` - Battle pets
        `!pet accept` - Accept challenge
        `!pet move <skill>` - Use skill
        `!pet heal` - Heal your pet
        """
        embed.add_field(name="⚔️ Battle System", value=battle, inline=False)

        tips = """
        • Different pets have unique skills
        • Train daily for best results
        • Keep your pet happy and fed
        • Battle to gain experience
        """
        embed.add_field(name="💡 Quick Tips", value=tips, inline=False)

        await ctx.send(embed=embed)

    @pet.command(name="adopt")
    async def adopt_pet(self, ctx, pet_type: str, name: str):
        """Adopt a new pet companion!

        Available Pet Types:
        🐕 Dog - Loyal and strong
        🐱 Cat - Agile and sneaky
        🐲 Dragon - Powerful and tough
        🦅 Phoenix - Magical and resilient
        🦄 Unicorn - Healing and support

        Each pet type has:
        • Unique skills and abilities
        • Different base stats
        • Special training bonuses
        • Distinct battle styles

        Usage: !pet adopt <type> <name>
        Example: !pet adopt dog Buddy"""

        pet_type = pet_type.lower()
        if pet_type not in self.PET_TYPES:
            types = ", ".join(self.PET_TYPES.keys())
            await ctx.send(f"Invalid pet type! Choose from: {types}")
            return

        # Add pet to user's collection
        pet_data = {
            "type": pet_type,
            "name": name,
            "level": 1,
            "exp": 0,
            "stats": self.PET_TYPES[pet_type]["base_stats"].copy(),
            "skills": [],
            "happiness": 100,
            "hunger": 0,
        }

        # Save to database here
        embed = discord.Embed(
            title="🎉 New Pet Adopted!",
            description=f"Welcome {self.PET_TYPES[pet_type]['emoji']} **{name}** to your family!",
            color=discord.Color.green(),
        )
        embed.add_field(name="Type", value=pet_type.title(), inline=True)
        embed.add_field(name="Level", value="1", inline=True)
        embed.add_field(
            name="Base Stats",
            value="\n".join(f"{k}: {v}" for k, v in pet_data["stats"].items()),
            inline=False,
        )

        await ctx.send(embed=embed)

    @pet.command(name="train")
    async def train_pet(self, ctx, name: str):
        """Train your pet to improve their stats!

        Training System:
        • Improves pet's base stats
        • Teaches new skills
        • Increases experience
        • Has cooldown periods

        Each pet type gains:
        • Unique stat bonuses
        • Special abilities
        • Type-specific skills

        Usage: !pet train <name>
        Example: !pet train Buddy"""

        # Check cooldown
        user_id = ctx.author.id
        if user_id in self.training_cooldowns:
            if datetime.now() < self.training_cooldowns[user_id]:
                remaining = (self.training_cooldowns[user_id] - datetime.now()).seconds
                await ctx.send(f"Training cooldown: {remaining} seconds remaining!")
                return

        # Training animation
        embed = discord.Embed(
            title="🎯 Pet Training",
            description=f"Training {name}...",
            color=discord.Color.blue(),
        )
        msg = await ctx.send(embed=embed)

        # Training progress animation
        progress = ["⬛"] * 10
        for i in range(10):
            progress[i] = "🟩"
            embed.description = f"Training {name}...\n{''.join(progress)}"
            await msg.edit(embed=embed)
            await asyncio.sleep(0.5)

        # Calculate rewards
        exp_gain = random.randint(10, 20)
        stat_gain = random.randint(1, 3)

        embed.description = f"Training Complete!\n{name} gained:"
        embed.add_field(name="Experience", value=f"+{exp_gain} XP", inline=True)
        embed.add_field(name="Stats", value=f"+{stat_gain} to random stat", inline=True)

        # Set cooldown (1 hour)
        self.training_cooldowns[user_id] = datetime.now() + timedelta(hours=1)

        await msg.edit(embed=embed)

    @pet.command(name="battle")
    async def pet_battle(self, ctx, opponent: discord.Member):
        """Battle your pet against others!

        Battle System:
        • Turn-based combat
        • Use pet skills
        • Type advantages
        • Strategy matters

        Battle Flow:
        1. Challenge opponent
        2. Select pets to battle
        3. Take turns using moves
        4. Battle until one pet faints

        Usage: !pet battle @user
        Example: !pet battle @Friend"""

        if opponent.bot:
            await ctx.send("You can't battle with a bot!")
            return

        battle_id = f"{ctx.author.id}:{opponent.id}"
        if battle_id in self.active_battles:
            await ctx.send("One of these trainers is already in a battle!")
            return

        embed = discord.Embed(
            title="⚔️ Pet Battle Challenge!",
            description=f"{ctx.author.mention} challenges {opponent.mention} to a pet battle!",
            color=discord.Color.red(),
        )
        embed.set_footer(
            text=f"{opponent.name}, use !pet accept to accept the challenge!"
        )

        self.active_battles[battle_id] = {
            "challenger": ctx.author.id,
            "opponent": opponent.id,
            "status": "waiting",
        }

        await ctx.send(embed=embed)

    @pet.command(name="info")
    async def pet_info(self, ctx, name: str):
        """View detailed information about your pet

        Shows:
        • Basic Information
        • Current Stats
        • Known Skills
        • Training Progress
        • Battle History
        • Happiness & Health

        Usage: !pet info <name>
        Example: !pet info Buddy"""

        # Get pet info from database
        # This is example data
        pet_data = {
            "name": name,
            "type": "dog",
            "level": 5,
            "exp": 450,
            "stats": {"health": 120, "attack": 18, "defense": 12},
            "skills": ["fetch", "guard"],
            "happiness": 95,
            "hunger": 20,
        }

        embed = discord.Embed(
            title=f"{self.PET_TYPES[pet_data['type']]['emoji']} {name}'s Info",
            color=discord.Color.blue(),
        )

        # Basic Info
        embed.add_field(
            name="Basic Info",
            value=f"Type: {pet_data['type'].title()}\nLevel: {pet_data['level']}\nXP: {pet_data['exp']}/500",
            inline=False,
        )

        # Stats
        stats = "\n".join(f"{k.title()}: {v}" for k, v in pet_data["stats"].items())
        embed.add_field(name="Stats", value=stats, inline=True)

        # Skills
        skills = "\n".join(f"• {s.title()}" for s in pet_data["skills"])
        embed.add_field(name="Skills", value=skills or "No skills learned", inline=True)

        # Status
        status = f"Happiness: {'❤️' * (pet_data['happiness'] // 20)}\nHunger: {'🍖' * (pet_data['hunger'] // 20)}"
        embed.add_field(name="Status", value=status, inline=False)

        await ctx.send(embed=embed)

    @pet.command(name="list")
    async def list_pets(self, ctx):
        """View all your pets

        Shows for each pet:
        • Name and type
        • Current level
        • Basic stats
        • Happiness status

        Usage: !pet list"""

        # Example pets data
        pets = [
            {"name": "Buddy", "type": "dog", "level": 5, "happiness": 95},
            {"name": "Smokey", "type": "dragon", "level": 3, "happiness": 80},
        ]

        embed = discord.Embed(
            title=f"🏠 {ctx.author.name}'s Pet Collection", color=discord.Color.blue()
        )

        for pet in pets:
            embed.add_field(
                name=f"{self.PET_TYPES[pet['type']]['emoji']} {pet['name']}",
                value=f"Type: {pet['type'].title()}\nLevel: {pet['level']}\nHappiness: {'❤️' * (pet['happiness'] // 20)}",
                inline=True,
            )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(PetCommands(bot))
