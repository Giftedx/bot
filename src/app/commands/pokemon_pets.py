from typing import Dict
import random
from discord.ext import commands
import discord
from discord import app_commands

from src.core.pet_system import Pet, PetManager, PetOrigin, PetRarity
from src.core.bot import Bot


class PokemonPetData:
    """Pokemon Pet data and encounter rates"""

    LEGENDARY_POKEMON = {
        "Mewtwo": {
            "type": ["Psychic"],
            "rarity": PetRarity.MYTHICAL,
            "abilities": ["Pressure", "Unnerve"],
            "base_stats": {
                "hp": 106,
                "attack": 110,
                "defense": 90,
                "sp_attack": 154,
                "sp_defense": 90,
                "speed": 130,
            },
        },
        "Rayquaza": {
            "type": ["Dragon", "Flying"],
            "rarity": PetRarity.MYTHICAL,
            "abilities": ["Air Lock"],
            "base_stats": {
                "hp": 105,
                "attack": 150,
                "defense": 90,
                "sp_attack": 150,
                "sp_defense": 90,
                "speed": 95,
            },
        },
    }

    RARE_POKEMON = {
        "Dragonite": {
            "type": ["Dragon", "Flying"],
            "rarity": PetRarity.VERY_RARE,
            "abilities": ["Inner Focus", "Multiscale"],
            "base_stats": {
                "hp": 91,
                "attack": 134,
                "defense": 95,
                "sp_attack": 100,
                "sp_defense": 100,
                "speed": 80,
            },
        },
        "Tyranitar": {
            "type": ["Rock", "Dark"],
            "rarity": PetRarity.VERY_RARE,
            "abilities": ["Sand Stream"],
            "base_stats": {
                "hp": 100,
                "attack": 134,
                "defense": 110,
                "sp_attack": 95,
                "sp_defense": 100,
                "speed": 61,
            },
        },
    }

    COMMON_POKEMON = {
        "Pikachu": {
            "type": ["Electric"],
            "rarity": PetRarity.UNCOMMON,
            "abilities": ["Static", "Lightning Rod"],
            "base_stats": {
                "hp": 35,
                "attack": 55,
                "defense": 40,
                "sp_attack": 50,
                "sp_defense": 50,
                "speed": 90,
            },
        },
        "Eevee": {
            "type": ["Normal"],
            "rarity": PetRarity.UNCOMMON,
            "abilities": ["Run Away", "Adaptability"],
            "base_stats": {
                "hp": 55,
                "attack": 55,
                "defense": 50,
                "sp_attack": 45,
                "sp_defense": 65,
                "speed": 55,
            },
        },
    }


class PokemonPets(commands.Cog):
    def __init__(self, bot: Bot):
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

    @app_commands.command(name="pokemon_encounter", description="Encounter a Pokemon that might become your pet")
    @app_commands.describe(encounter_type="The type of encounter (common, rare, legendary)")
    async def encounter(self, interaction: discord.Interaction, encounter_type: str = "common"):
        """Encounter a Pokemon that might become your pet"""
        encounter_type = encounter_type.lower()
        if encounter_type not in ["common", "rare", "legendary"]:
            await interaction.response.send_message("Invalid encounter type! Choose from: common, rare, legendary", ephemeral=True)
            return

        pokemon_pool = self.get_pokemon_pool(encounter_type)
        pokemon_name = random.choice(list(pokemon_pool.keys()))
        pokemon_data = pokemon_pool[pokemon_name]

        catch_chance = self.pet_manager.roll_for_pet(PetOrigin.POKEMON)
        if catch_chance and catch_chance.value >= pokemon_data["rarity"].value:
            pet_id = f"pokemon_{pokemon_name.lower()}_{interaction.user.id}"
            new_pet = Pet(
                pet_id=pet_id,
                name=pokemon_name,
                origin=PetOrigin.POKEMON,
                rarity=pokemon_data["rarity"],
                owner_id=interaction.user.id,
                base_stats=pokemon_data["base_stats"],
                abilities=pokemon_data["abilities"],
                metadata={"type": pokemon_data["type"]},
            )

            self.pet_manager.register_pet(new_pet)

            embed = discord.Embed(
                title="⭐ Pokemon Caught!",
                description=f"Congratulations! You caught a {pokemon_name}!",
                color=discord.Color.purple(),
            )
            embed.add_field(name="Type", value=" / ".join(pokemon_data["type"]))
            embed.add_field(name="Rarity", value=pokemon_data["rarity"].name)
            embed.add_field(name="Abilities", value=", ".join(pokemon_data["abilities"]))

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"Oh no! The {pokemon_name} got away!", ephemeral=True)

    @app_commands.command(name="pokemon_train", description="Train a specific Pokemon pet")
    @app_commands.describe(pokemon_name="The name of your pokemon to train.")
    async def train_pokemon(self, interaction: discord.Interaction, pokemon_name: str):
        """Train a specific Pokemon pet"""
        pets = self.pet_manager.get_pets_by_owner(interaction.user.id)
        pokemon_pets = [
            p
            for p in pets
            if p.origin == PetOrigin.POKEMON and p.name.lower() == pokemon_name.lower()
        ]

        if not pokemon_pets:
            await interaction.response.send_message(f"You don't have a {pokemon_name} pet!", ephemeral=True)
            return

        pokemon = pokemon_pets[0]
        training_result = pokemon.interact("training")

        embed = discord.Embed(
            title="🏋️ Pokemon Training",
            description=f"Training session with {pokemon.name}",
            color=discord.Color.blue(),
        )

        embed.add_field(name="Experience Gained", value=training_result["exp_gained"])
        embed.add_field(name="Current Level", value=training_result["current_level"])
        if training_result["leveled_up"]:
            embed.add_field(name="Level Up!", value="Your Pokemon grew stronger! 💪", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="my_pokemon", description="Display all Pokemon pets owned by the user")
    async def my_pokemon(self, interaction: discord.Interaction):
        """Display all Pokemon pets owned by the user"""
        pets = self.pet_manager.get_pets_by_owner(interaction.user.id)
        pokemon_pets = [p for p in pets if p.origin == PetOrigin.POKEMON]

        if not pokemon_pets:
            await interaction.response.send_message("You don't have any Pokemon pets yet!", ephemeral=True)
            return

        embed = discord.Embed(
            title="Your Pokemon",
            description=f"You have {len(pokemon_pets)} Pokemon!",
            color=discord.Color.red(),
        )

        for pokemon in pokemon_pets:
            pokemon_info = (
                f"Level: {pokemon.stats.level}\n"
                f"Type: {' / '.join(pokemon.metadata['type'])}\n"
                f"Happiness: {pokemon.stats.happiness}/100\n"
                f"Abilities: {', '.join(pokemon.abilities)}"
            )
            embed.add_field(name=pokemon.name, value=pokemon_info, inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(PokemonPets(bot)) 