from typing import Dict, Optional
import random
from discord.ext import commands
import discord

from src.core.pet_system import Pet, PetManager, PetOrigin, PetRarity

class OSRSPetData:
    """OSRS Pet data and drop rates"""
    
    BOSS_PETS = {
        "Baby Mole": {
            "boss": "Giant Mole",
            "base_rate": 3000,
            "rarity": PetRarity.RARE,
            "abilities": ["Dig", "Burrow"],
            "base_stats": {"hp": 10, "defense": 5, "cuteness": 8}
        },
        "Prince Black Dragon": {
            "boss": "King Black Dragon",
            "base_rate": 3000,
            "rarity": PetRarity.RARE,
            "abilities": ["Fire Breath", "Fly"],
            "base_stats": {"hp": 15, "attack": 8, "defense": 8}
        },
        "Vorki": {
            "boss": "Vorkath",
            "base_rate": 3000,
            "rarity": PetRarity.VERY_RARE,
            "abilities": ["Frost Breath", "Undead Resistance"],
            "base_stats": {"hp": 20, "magic": 10, "defense": 12}
        }
    }
    
    SKILLING_PETS = {
        "Rocky": {
            "skill": "Thieving",
            "base_rate": 247886,
            "rarity": PetRarity.VERY_RARE,
            "abilities": ["Pickpocket", "Stealth"],
            "base_stats": {"agility": 10, "stealth": 15, "luck": 8}
        },
        "Beaver": {
            "skill": "Woodcutting",
            "base_rate": 69846,
            "rarity": PetRarity.RARE,
            "abilities": ["Wood Sense", "Tree Climb"],
            "base_stats": {"woodcutting": 10, "agility": 5, "strength": 3}
        }
    }

class OSRSPets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pet_manager = PetManager()
        
    def calculate_drop_chance(self, base_rate: int, level: int) -> float:
        """Calculate drop chance based on level and base rate"""
        # Slight boost based on level
        level_modifier = 1 + (level * 0.01)
        return 1 / (base_rate / level_modifier)

    @commands.command()
    async def boss_hunt(self, ctx, boss_name: str):
        """Hunt for a boss pet"""
        boss_name = boss_name.title()
        if boss_name not in OSRSPetData.BOSS_PETS:
            await ctx.send(f"Unknown boss: {boss_name}")
            return

        # Get user's combat level from database (placeholder)
        combat_level = 99  # This should come from user's stats
        
        pet_data = OSRSPetData.BOSS_PETS[boss_name]
        drop_chance = self.calculate_drop_chance(pet_data["base_rate"], combat_level)
        
        if random.random() < drop_chance:
            # Create new pet
            pet_id = f"osrs_boss_{boss_name.lower()}_{ctx.author.id}"
            new_pet = Pet(
                pet_id=pet_id,
                name=boss_name,
                origin=PetOrigin.OSRS,
                rarity=pet_data["rarity"],
                owner_id=ctx.author.id,
                base_stats=pet_data["base_stats"],
                abilities=pet_data["abilities"],
                metadata={"boss": pet_data["boss"]}
            )
            
            self.pet_manager.register_pet(new_pet)
            
            embed = discord.Embed(
                title="🎉 Rare Drop!",
                description=f"Congratulations! You received {boss_name} pet!",
                color=discord.Color.gold()
            )
            embed.add_field(name="Rarity", value=pet_data["rarity"].name)
            embed.add_field(name="Abilities", value=", ".join(pet_data["abilities"]))
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"No pet this time! Keep hunting {boss_name}!")

    @commands.command()
    async def skill_pet(self, ctx, skill: str):
        """Try to get a skilling pet"""
        skill = skill.title()
        relevant_pets = {name: data for name, data in OSRSPetData.SKILLING_PETS.items() 
                        if data["skill"].lower() == skill.lower()}
        
        if not relevant_pets:
            await ctx.send(f"No pets available for skill: {skill}")
            return

        # Get user's skill level from database (placeholder)
        skill_level = 99  # This should come from user's stats
        
        for pet_name, pet_data in relevant_pets.items():
            drop_chance = self.calculate_drop_chance(pet_data["base_rate"], skill_level)
            
            if random.random() < drop_chance:
                # Create new pet
                pet_id = f"osrs_skill_{pet_name.lower()}_{ctx.author.id}"
                new_pet = Pet(
                    pet_id=pet_id,
                    name=pet_name,
                    origin=PetOrigin.OSRS,
                    rarity=pet_data["rarity"],
                    owner_id=ctx.author.id,
                    base_stats=pet_data["base_stats"],
                    abilities=pet_data["abilities"],
                    metadata={"skill": pet_data["skill"]}
                )
                
                self.pet_manager.register_pet(new_pet)
                
                embed = discord.Embed(
                    title="🎉 Skilling Pet!",
                    description=f"Congratulations! While training {skill}, you received {pet_name}!",
                    color=discord.Color.green()
                )
                embed.add_field(name="Rarity", value=pet_data["rarity"].name)
                embed.add_field(name="Abilities", value=", ".join(pet_data["abilities"]))
                
                await ctx.send(embed=embed)
                return
                
        await ctx.send(f"No pet this time! Keep training {skill}!")

    @commands.command()
    async def my_pets(self, ctx):
        """Display all OSRS pets owned by the user"""
        pets = self.pet_manager.get_pets_by_owner(ctx.author.id)
        osrs_pets = [p for p in pets if p.origin == PetOrigin.OSRS]
        
        if not osrs_pets:
            await ctx.send("You don't have any OSRS pets yet!")
            return
            
        embed = discord.Embed(
            title="Your OSRS Pets",
            description=f"You have {len(osrs_pets)} OSRS pets!",
            color=discord.Color.blue()
        )
        
        for pet in osrs_pets:
            pet_info = (f"Level: {pet.stats.level}\n"
                       f"Happiness: {pet.stats.happiness}/100\n"
                       f"Loyalty: {pet.stats.loyalty}\n"
                       f"Abilities: {', '.join(pet.abilities)}")
            embed.add_field(name=pet.name, value=pet_info, inline=False)
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OSRSPets(bot)) 