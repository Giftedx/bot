import logging
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from typing import Optional

logger = logging.getLogger(__name__)


class PokemonSlash(commands.Cog, name="Pokemon"):
    """Pokemon slash commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.base_url = "https://pokeapi.co/api/v2"
        self.move_cache: dict[str, dict] = {}
        self.type_cache: dict[str, dict] = {}
        self.ability_cache: dict[str, dict] = {}
        self.item_cache: dict[str, dict] = {}

    def cog_unload(self):
        """Clean up the aiohttp session when the cog is unloaded."""
        self.bot.loop.create_task(self.session.close())

    async def get_pokemon_data(self, pokemon: str) -> Optional[dict]:
        """Fetch Pokemon data from the PokeAPI."""
        try:
            async with self.session.get(f"{self.base_url}/pokemon/{pokemon.lower()}") as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception as e:
            logger.error(f"Error fetching Pokemon data: {e}", exc_info=True)
            return None

    @app_commands.command(
        name="pokemon-info", description="Get detailed information about a Pokemon."
    )
    @app_commands.describe(pokemon="The name or Pokedex number of the Pokemon.")
    async def pokemon_info(self, interaction: discord.Interaction, pokemon: str):
        """Gets detailed information about a Pokemon."""
        await interaction.response.defer()
        data = await self.get_pokemon_data(pokemon)

        if not data:
            await interaction.followup.send(f"Could not find Pokemon: {pokemon}", ephemeral=True)
            return

        # Create embed
        embed = discord.Embed(
            title=f"#{data['id']} - {data['name'].capitalize()}", color=discord.Color.blue()
        )

        # Add sprite
        sprite_url = data["sprites"]["front_default"]
        if sprite_url:
            embed.set_thumbnail(url=sprite_url)

        # Basic info
        types = ", ".join(t["type"]["name"].capitalize() for t in data["types"])
        embed.add_field(name="Types", value=types, inline=True)

        # Stats
        stats = "\n".join(
            f"{s['stat']['name'].capitalize()}: {s['base_stat']}" for s in data["stats"]
        )
        embed.add_field(name="Stats", value=f"```\n{stats}```", inline=False)

        # Abilities
        abilities = ", ".join(a["ability"]["name"].capitalize() for a in data["abilities"])
        embed.add_field(name="Abilities", value=abilities, inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="pokemon-type", description="Get information about a Pokemon type.")
    @app_commands.describe(type_name="The Pokemon type to look up.")
    async def pokemon_type(self, interaction: discord.Interaction, type_name: str):
        """Gets information about a Pokemon type."""
        await interaction.response.defer()
        try:
            async with self.session.get(f"{self.base_url}/type/{type_name.lower()}") as resp:
                if resp.status != 200:
                    await interaction.followup.send(
                        f"Could not find type: {type_name}", ephemeral=True
                    )
                    return

                data = await resp.json()

                # Create embed
                embed = discord.Embed(
                    title=f"Type: {data['name'].capitalize()}", color=discord.Color.blue()
                )

                # Damage relations
                for relation, types in data["damage_relations"].items():
                    if types:
                        type_list = ", ".join(t["name"].capitalize() for t in types)
                        embed.add_field(
                            name=relation.replace("_", " ").capitalize(),
                            value=type_list,
                            inline=False,
                        )

                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error fetching type data for '{type_name}': {e}", exc_info=True)
            await interaction.followup.send(
                "An error occurred while fetching type data.", ephemeral=True
            )

    async def get_move_data(self, move_name: str) -> Optional[dict]:
        """Fetch move data from the PokeAPI."""
        try:
            async with self.session.get(
                f"{self.base_url}/move/{move_name.lower().replace(' ', '-')}"
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception as e:
            logger.error(f"Error fetching move data: {e}", exc_info=True)
            return None

    @app_commands.command(name="pokemon-move", description="Get details about a Pokemon move.")
    @app_commands.describe(move_name="The name of the move to look up.")
    async def pokemon_move(self, interaction: discord.Interaction, move_name: str):
        """Gets details about a Pokemon move."""
        await interaction.response.defer()
        data = await self.get_move_data(move_name)

        if not data:
            await interaction.followup.send(f"Could not find move: {move_name}", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Move: {data['name'].capitalize()}",
            description=data["flavor_text_entries"][0]["flavor_text"],
            color=discord.Color.green(),
        )

        embed.add_field(name="Type", value=data["type"]["name"].capitalize(), inline=True)
        embed.add_field(name="Power", value=data.get("power", "N/A"), inline=True)
        embed.add_field(name="Accuracy", value=data.get("accuracy", "N/A"), inline=True)
        embed.add_field(name="PP", value=data.get("pp", "N/A"), inline=True)
        embed.add_field(name="Priority", value=data.get("priority", "N/A"), inline=True)
        embed.add_field(
            name="Damage Class", value=data["damage_class"]["name"].capitalize(), inline=True
        )

        effect = data["effect_entries"][0]["effect"]
        if "short_effect" in data["effect_entries"][0]:
            effect = data["effect_entries"][0]["short_effect"]

        embed.add_field(
            name="Effect",
            value=effect.replace("$effect_chance", str(data.get("effect_chance", ""))),
            inline=False,
        )

        await interaction.followup.send(embed=embed)

    async def get_ability_data(self, ability_name: str) -> Optional[dict]:
        """Fetch ability data from the PokeAPI."""
        try:
            async with self.session.get(
                f"{self.base_url}/ability/{ability_name.lower().replace(' ', '-')}"
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception as e:
            logger.error(f"Error fetching ability data: {e}", exc_info=True)
            return None

    @app_commands.command(
        name="pokemon-ability", description="Get details about a Pokemon ability."
    )
    @app_commands.describe(ability_name="The name of the ability to look up.")
    async def pokemon_ability(self, interaction: discord.Interaction, ability_name: str):
        """Gets details about a Pokemon ability."""
        await interaction.response.defer()
        data = await self.get_ability_data(ability_name)

        if not data:
            await interaction.followup.send(
                f"Could not find ability: {ability_name}", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"Ability: {data['name'].capitalize()}",
            description=[
                entry["flavor_text"]
                for entry in data["flavor_text_entries"]
                if entry["language"]["name"] == "en"
            ][0],
            color=discord.Color.orange(),
        )

        effect_entry = [
            entry for entry in data["effect_entries"] if entry["language"]["name"] == "en"
        ]
        if effect_entry:
            embed.add_field(name="Effect", value=effect_entry[0]["effect"], inline=False)

        pokemon_list = [p["pokemon"]["name"].capitalize() for p in data["pokemon"]]
        if pokemon_list:
            embed.add_field(
                name="Pokemon with this ability", value=", ".join(pokemon_list[:10]), inline=False
            )

        await interaction.followup.send(embed=embed)

    async def get_item_data(self, item_name: str) -> Optional[dict]:
        """Fetch item data from the PokeAPI."""
        if item_name in self.item_cache:
            return self.item_cache[item_name]
        try:
            async with self.session.get(
                f"{self.base_url}/item/{item_name.lower().replace(' ', '-')}"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.item_cache[item_name] = data
                    return data
                return None
        except Exception as e:
            logger.error(f"Error fetching item data: {e}", exc_info=True)
            return None

    @app_commands.command(name="pokemon_item", description="Get information about a Pokémon item.")
    @app_commands.describe(name="The name of the item.")
    async def pokemon_item(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        data = await self.get_item_data(name)

        if not data:
            await interaction.followup.send(f"Could not find item: {name}", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Item: {data['name'].capitalize()}",
            description=[
                e["flavor_text"]
                for e in data["flavor_text_entries"]
                if e["language"]["name"] == "en"
            ][0],
            color=discord.Color.gold(),
        )

        if data["sprites"]["default"]:
            embed.set_thumbnail(url=data["sprites"]["default"])

        embed.add_field(name="Category", value=data["category"]["name"].capitalize(), inline=True)
        embed.add_field(name="Cost", value=data.get("cost", "N/A"), inline=True)

        effect_entry = [
            entry for entry in data["effect_entries"] if entry["language"]["name"] == "en"
        ]
        if effect_entry:
            embed.add_field(name="Effect", value=effect_entry[0]["short_effect"], inline=False)

        await interaction.followup.send(embed=embed)

    async def get_nature_data(self, nature_name: str) -> Optional[dict]:
        """Fetch nature data from the PokeAPI."""
        try:
            async with self.session.get(
                f"{self.base_url}/nature/{nature_name.lower().replace(' ', '-')}"
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception as e:
            logger.error(f"Error fetching nature data: {e}", exc_info=True)
            return None

    @app_commands.command(name="pokemon-nature", description="Get details about a Pokemon nature.")
    @app_commands.describe(nature_name="The name of the nature to look up.")
    async def pokemon_nature(self, interaction: discord.Interaction, nature_name: str):
        """Gets details about a Pokemon nature."""
        await interaction.response.defer()
        data = await self.get_nature_data(nature_name)

        if not data:
            await interaction.followup.send(f"Could not find nature: {nature_name}", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Nature: {data['name'].capitalize()}", color=discord.Color.dark_green()
        )

        if data["increased_stat"]:
            embed.add_field(
                name="Increased Stat",
                value=data["increased_stat"]["name"].capitalize(),
                inline=True,
            )
        else:
            embed.add_field(name="Increased Stat", value="None", inline=True)

        if data["decreased_stat"]:
            embed.add_field(
                name="Decreased Stat",
                value=data["decreased_stat"]["name"].capitalize(),
                inline=True,
            )
        else:
            embed.add_field(name="Decreased Stat", value="None", inline=True)

        if data["likes_flavor"]:
            embed.add_field(
                name="Likes Flavor", value=data["likes_flavor"]["name"].capitalize(), inline=True
            )
        if data["hates_flavor"]:
            embed.add_field(
                name="Hates Flavor", value=data["hates_flavor"]["name"].capitalize(), inline=True
            )

        await interaction.followup.send(embed=embed)

    async def get_location_data(self, pokemon_name: str) -> Optional[list]:
        """Fetch location data from the PokeAPI."""
        try:
            async with self.session.get(
                f"{self.base_url}/pokemon/{pokemon_name.lower().replace(' ', '-')}/encounters"
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception as e:
            logger.error(f"Error fetching location data: {e}", exc_info=True)
            return None

    @app_commands.command(name="pokemon-location", description="Get spawn locations for a Pokemon.")
    @app_commands.describe(pokemon_name="The name of the Pokemon to look up.")
    async def pokemon_location(self, interaction: discord.Interaction, pokemon_name: str):
        """Gets spawn locations for a Pokemon."""
        await interaction.response.defer()
        data = await self.get_location_data(pokemon_name)

        if not data:
            await interaction.followup.send(
                f"Could not find location data for: {pokemon_name}", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"Locations for {pokemon_name.capitalize()}", color=discord.Color.blue()
        )

        if not data:
            embed.description = "No location data found for this Pokemon."
        else:
            locations = [loc["location_area"]["name"].replace("-", " ").title() for loc in data]
            if locations:
                embed.description = "\n".join(locations[:25])
            else:
                embed.description = "No specific locations found in the wild for this Pokemon."

        await interaction.followup.send(embed=embed)

    async def get_evolution_chain(self, pokemon_name: str) -> Optional[dict]:
        """Fetch evolution chain data from the PokeAPI."""
        try:
            async with self.session.get(
                f"{self.base_url}/pokemon-species/{pokemon_name.lower().replace(' ', '-')}"
            ) as species_resp:
                if species_resp.status != 200:
                    return None
                species_data = await species_resp.json()
                evolution_chain_url = species_data["evolution_chain"]["url"]

            async with self.session.get(evolution_chain_url) as chain_resp:
                if chain_resp.status == 200:
                    return await chain_resp.json()
                return None
        except Exception as e:
            logger.error(f"Error fetching evolution chain data: {e}", exc_info=True)
            return None

    @app_commands.command(
        name="pokemon-evolution", description="Get the evolution chain for a Pokemon."
    )
    @app_commands.describe(pokemon_name="The name of the Pokemon to look up.")
    async def pokemon_evolution(self, interaction: discord.Interaction, pokemon_name: str):
        """Gets the evolution chain for a Pokemon."""
        await interaction.response.defer()
        chain_data = await self.get_evolution_chain(pokemon_name)

        if not chain_data:
            await interaction.followup.send(
                f"Could not find evolution data for: {pokemon_name}", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"Evolution Chain for {pokemon_name.capitalize()}", color=discord.Color.purple()
        )

        chain = []
        current = chain_data["chain"]
        while current:
            chain.append(current["species"]["name"].capitalize())
            if current["evolves_to"]:
                current = current["evolves_to"][0]
            else:
                current = None

        if chain:
            embed.description = " -> ".join(chain)
        else:
            embed.description = "No evolution chain found for this Pokemon."

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="pokemon-sprite", description="Get the sprite for a Pokemon.")
    @app_commands.describe(pokemon_name="The name of the Pokemon to look up.")
    async def pokemon_sprite(self, interaction: discord.Interaction, pokemon_name: str):
        """Gets the sprite for a Pokemon."""
        await interaction.response.defer()
        data = await self.get_pokemon_data(pokemon_name)

        if not data or not data["sprites"]["front_default"]:
            await interaction.followup.send(
                f"Could not find sprite for: {pokemon_name}", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"Sprite for {data['name'].capitalize()}", color=discord.Color.red()
        )
        embed.set_image(url=data["sprites"]["front_default"])

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(PokemonSlash(bot))
