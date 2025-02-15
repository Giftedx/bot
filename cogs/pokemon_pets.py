from typing import Dict, Optional, List
import random
from discord.ext import commands
import discord

from src.core.pet_system import Pet, PetManager, PetOrigin, PetRarity

class PokemonPetData:
    """Pokemon Pet data and encounter rates"""
    
    LEGENDARY_POKEMON = {
        "Mewtwo": {
            "type": ["Psychic"],
            "rarity": PetRarity.MYTHICAL,
            "abilities": ["Pressure", "Unnerve"],
            "base_stats": {"hp": 106, "attack": 110, "defense": 90, "sp_attack": 154, "sp_defense": 90, "speed": 130}
        },
        "Rayquaza": {
            "type": ["Dragon", "Flying"],
            "rarity": PetRarity.MYTHICAL,
            "abilities": ["Air Lock"],
            "base_stats": {"hp": 105, "attack": 150, "defense": 90, "sp_attack": 150, "sp_defense": 90, "speed": 95}
        }
    }
    
    RARE_POKEMON = {
        "Dragonite": {
            "type": ["Dragon", "Flying"],
            "rarity": PetRarity.VERY_RARE,
            "abilities": ["Inner Focus", "Multiscale"],
            "base_stats": {"hp": 91, "attack": 134, "defense": 95, "sp_attack": 100, "sp_defense": 100, "speed": 80}
        },
        "Tyranitar": {
            "type": ["Rock", "Dark"],
            "rarity": PetRarity.VERY_RARE,
            "abilities": ["Sand Stream"],
            "base_stats": {"hp": 100, "attack": 134, "defense": 110, "sp_attack": 95, "sp_defense": 100, "speed": 61}
        }
    }
    
    COMMON_POKEMON = {
        "Pikachu": {
            "type": ["Electric"],
            "rarity": PetRarity.UNCOMMON,
            "abilities": ["Static", "Lightning Rod"],
            "base_stats": {"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90}
        },
        "Eevee": {
            "type": ["Normal"],
            "rarity": PetRarity.UNCOMMON,
            "abilities": ["Run Away", "Adaptability"],
            "base_stats": {"hp": 55, "attack": 55, "defense": 50, "sp_attack": 45, "sp_defense": 65, "speed": 55}
        }
    }

class PokemonPets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pet_manager = PetManager()
    
    def get_pokemon_pool(self, encounter_type: str) -> Dict[str, dict]:
        """Get the appropriate pool of Pokemon based on encounter type"""
        if encounter_type == "legendary":
            return PokemonPetData.LEGENDARY_POKEMON
        elif encounter_type == "rare":
            return PokemonPetData.RARE_POKEMON
        else:
            return PokemonPetData.COMMON_POKEMON

    @commands.command()
    async def encounter(self, ctx, encounter_type: str = "common"):
        """Encounter a Pokemon that might become your pet"""
        encounter_type = encounter_type.lower()
        if encounter_type not in ["common", "rare", "legendary"]:
            await ctx.send("Invalid encounter type! Choose from: common, rare, legendary")
            return
            
        pokemon_pool = self.get_pokemon_pool(encounter_type)
        pokemon_name = random.choice(list(pokemon_pool.keys()))
        pokemon_data = pokemon_pool[pokemon_name]
        
        # Roll for catch chance
        catch_chance = self.pet_manager.roll_for_pet(PetOrigin.POKEMON)
        if catch_chance and catch_chance.value >= pokemon_data["rarity"].value:
            # Successfully caught the Pokemon as a pet
            pet_id = f"pokemon_{pokemon_name.lower()}_{ctx.author.id}"
            new_pet = Pet(
                pet_id=pet_id,
                name=pokemon_name,
                origin=PetOrigin.POKEMON,
                rarity=pokemon_data["rarity"],
                owner_id=ctx.author.id,
                base_stats=pokemon_data["base_stats"],
                abilities=pokemon_data["abilities"],
                metadata={"type": pokemon_data["type"]}
            )
            
            self.pet_manager.register_pet(new_pet)
            
            embed = discord.Embed(
                title="⭐ Pokemon Caught!",
                description=f"Congratulations! You caught a {pokemon_name}!",
                color=discord.Color.purple()
            )
            embed.add_field(name="Type", value=" / ".join(pokemon_data["type"]))
            embed.add_field(name="Rarity", value=pokemon_data["rarity"].name)
            embed.add_field(name="Abilities", value=", ".join(pokemon_data["abilities"]))
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Oh no! The {pokemon_name} got away!")

    @commands.command()
    async def train_pokemon(self, ctx, pokemon_name: str):
        """Train a specific Pokemon pet"""
        pets = self.pet_manager.get_pets_by_owner(ctx.author.id)
        pokemon_pets = [p for p in pets if p.origin == PetOrigin.POKEMON 
                       and p.name.lower() == pokemon_name.lower()]
        
        if not pokemon_pets:
            await ctx.send(f"You don't have a {pokemon_name} pet!")
            return
            
        pokemon = pokemon_pets[0]
        training_result = pokemon.interact("training")
        
        embed = discord.Embed(
            title="🏋️ Pokemon Training",
            description=f"Training session with {pokemon.name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Experience Gained", value=training_result["exp_gained"])
        embed.add_field(name="Current Level", value=training_result["current_level"])
        if training_result["leveled_up"]:
            embed.add_field(name="Level Up!", value="Your Pokemon grew stronger! 💪", inline=False)
            
        await ctx.send(embed=embed)

    @commands.command()
    async def my_pokemon(self, ctx):
        """Display all Pokemon pets owned by the user"""
        pets = self.pet_manager.get_pets_by_owner(ctx.author.id)
        pokemon_pets = [p for p in pets if p.origin == PetOrigin.POKEMON]
        
        if not pokemon_pets:
            await ctx.send("You don't have any Pokemon pets yet!")
            return
            
        embed = discord.Embed(
            title="Your Pokemon",
            description=f"You have {len(pokemon_pets)} Pokemon!",
            color=discord.Color.red()
        )
        
        for pokemon in pokemon_pets:
            pokemon_info = (f"Level: {pokemon.stats.level}\n"
                          f"Type: {' / '.join(pokemon.metadata['type'])}\n"
                          f"Happiness: {pokemon.stats.happiness}/100\n"
                          f"Abilities: {', '.join(pokemon.abilities)}")
            embed.add_field(name=pokemon.name, value=pokemon_info, inline=False)
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PokemonPets(bot)) 