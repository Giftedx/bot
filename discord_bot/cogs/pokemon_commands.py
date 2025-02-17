"""Pokemon-related commands and functionality."""

import discord
from discord.ext import commands
import aiohttp
import json
from typing import Optional
import random
import asyncio

class PokemonCommands(commands.Cog, name="Pokemon"):
    """Pokemon-related commands and games.
    
    This category includes commands for:
    - Looking up Pokemon information
    - Checking Pokemon types
    - Playing Pokemon-related games
    - Getting random Pokemon
    
    All data is fetched from the official PokeAPI.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.base_url = "https://pokeapi.co/api/v2"
        
    def cog_unload(self):
        """Clean up the aiohttp session when the cog is unloaded."""
        asyncio.create_task(self.session.close())
    
    async def get_pokemon_data(self, pokemon: str) -> Optional[dict]:
        """Fetch Pokemon data from the PokeAPI."""
        try:
            async with self.session.get(f"{self.base_url}/pokemon/{pokemon.lower()}") as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception as e:
            print(f"Error fetching Pokemon data: {e}")
            return None
    
    @commands.command(name="pokemon")
    async def pokemon_info(self, ctx, pokemon: str):
        """Get detailed information about a Pokemon.
        
        Fetches and displays comprehensive information about the specified Pokemon,
        including its stats, types, abilities, and sprite.
        
        Parameters:
        -----------
        pokemon: The name or Pokedex number of the Pokemon
        
        Examples:
        ---------
        !pokemon pikachu
        !pokemon 25
        !pokemon charizard
        
        Notes:
        ------
        - Pokemon names are case-insensitive
        - Can use either Pokemon name or Pokedex number
        - Shows base stats and abilities
        """
        async with ctx.typing():
            data = await self.get_pokemon_data(pokemon)
            
            if not data:
                await ctx.send(f"Could not find Pokemon: {pokemon}")
                return
            
            # Create embed
            embed = discord.Embed(
                title=f"#{data['id']} - {data['name'].capitalize()}",
                color=discord.Color.blue()
            )
            
            # Add sprite
            sprite_url = data['sprites']['front_default']
            if sprite_url:
                embed.set_thumbnail(url=sprite_url)
            
            # Basic info
            types = ", ".join(t['type']['name'].capitalize() for t in data['types'])
            embed.add_field(name="Types", value=types, inline=True)
            
            # Stats
            stats = "\n".join(f"{s['stat']['name'].capitalize()}: {s['base_stat']}" 
                            for s in data['stats'])
            embed.add_field(name="Stats", value=f"```\n{stats}```", inline=False)
            
            # Abilities
            abilities = ", ".join(a['ability']['name'].capitalize() for a in data['abilities'])
            embed.add_field(name="Abilities", value=abilities, inline=False)
            
            await ctx.send(embed=embed)
    
    @commands.command(name="random_pokemon")
    async def random_pokemon(self, ctx):
        """Get information about a random Pokemon.
        
        Randomly selects a Pokemon from all generations (up to Gen 8)
        and displays its information.
        
        Examples:
        ---------
        !random_pokemon
        
        Notes:
        ------
        - Includes Pokemon from all generations up to Gen 8
        - Shows same detailed information as !pokemon command
        """
        pokemon_id = random.randint(1, 898)  # Up to Gen 8
        async with ctx.typing():
            data = await self.get_pokemon_data(str(pokemon_id))
            
            if not data:
                await ctx.send("Error fetching random Pokemon.")
                return
            
            await self.pokemon_info(ctx, data['name'])
    
    @commands.command(name="guess_pokemon")
    async def guess_pokemon(self, ctx):
        """Start a Pokemon guessing game.
        
        Shows a Pokemon's sprite and gives players 30 seconds to guess
        which Pokemon it is. First person to guess correctly wins!
        
        Examples:
        ---------
        !guess_pokemon
        
        Notes:
        ------
        - 30 second time limit
        - Names must be exact (case-insensitive)
        - Anyone in the channel can guess
        """
        # Get random Pokemon
        pokemon_id = random.randint(1, 898)
        data = await self.get_pokemon_data(str(pokemon_id))
        
        if not data:
            await ctx.send("Error starting the game.")
            return
        
        # Create embed with silhouette
        embed = discord.Embed(
            title="Who's that Pokemon?",
            description="You have 30 seconds to guess!",
            color=discord.Color.blue()
        )
        sprite_url = data['sprites']['front_default']
        if sprite_url:
            embed.set_image(url=sprite_url)
        
        await ctx.send(embed=embed)
        
        def check(message):
            return (message.channel == ctx.channel and 
                   message.content.lower() == data['name'].lower())
        
        try:
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
            await ctx.send(f"🎉 Congratulations {msg.author.mention}! It was {data['name'].capitalize()}!")
        except asyncio.TimeoutError:
            await ctx.send(f"Time's up! It was {data['name'].capitalize()}!")
    
    @commands.command(name="type")
    async def type_info(self, ctx, type_name: str):
        """Get information about a Pokemon type.
        
        Displays detailed type effectiveness information, including:
        - Super effective against
        - Not very effective against
        - No effect against
        - Weaknesses and resistances
        
        Parameters:
        -----------
        type_name: The Pokemon type to look up
        
        Examples:
        ---------
        !type fire
        !type water
        !type dragon
        
        Notes:
        ------
        - Type names are case-insensitive
        - Shows all damage relations
        - Useful for battle strategy
        """
        async with ctx.typing():
            try:
                async with self.session.get(f"{self.base_url}/type/{type_name.lower()}") as resp:
                    if resp.status != 200:
                        await ctx.send(f"Could not find type: {type_name}")
                        return
                    
                    data = await resp.json()
                    
                    # Create embed
                    embed = discord.Embed(
                        title=f"Type: {data['name'].capitalize()}",
                        color=discord.Color.blue()
                    )
                    
                    # Damage relations
                    for relation, types in data['damage_relations'].items():
                        if types:
                            type_list = ", ".join(t['name'].capitalize() for t in types)
                            embed.add_field(
                                name=relation.replace('_', ' ').capitalize(),
                                value=type_list,
                                inline=False
                            )
                    
                    await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"Error fetching type data: {e}")

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(PokemonCommands(bot)) 