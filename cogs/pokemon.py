import discord
from discord.ext import commands
import asyncio
import random
import json
from typing import Dict, Optional
import aiohttp

class Pokemon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_spawns: Dict[int, Dict] = {}  # channel_id: spawn_data
        self.catching_users: Dict[int, bool] = {}  # user_id: is_catching
        self.spawn_chance = 0.1  # 10% chance of spawn per message

    async def get_pokemon_data(self, pokemon_id: int) -> Optional[Dict]:
        """Fetch Pokemon data from PokeAPI"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://pokeapi.co/api/v2/pokemon/{pokemon_id}') as resp:
                if resp.status == 200:
                    return await resp.json()
                return None

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle Pokemon spawns"""
        if message.author.bot:
            return

        # Random chance to spawn Pokemon
        if random.random() < self.spawn_chance:
            # Don't spawn if there's already an active spawn
            if message.channel.id in self.active_spawns:
                return

            # Generate random Pokemon (Gen 1 for now)
            pokemon_id = random.randint(1, 151)
            pokemon_data = await self.get_pokemon_data(pokemon_id)
            
            if pokemon_data:
                level = random.randint(1, 100)
                spawn_data = {
                    'pokemon_id': pokemon_id,
                    'name': pokemon_data['name'],
                    'level': level,
                    'caught': False
                }
                self.active_spawns[message.channel.id] = spawn_data

                # Create spawn embed
                embed = discord.Embed(
                    title="A wild Pokémon appeared!",
                    description="Use `!catch <pokemon>` to catch it!",
                    color=discord.Color.green()
                )
                embed.set_image(url=pokemon_data['sprites']['front_default'])
                await message.channel.send(embed=embed)

    @commands.command()
    async def catch(self, ctx, pokemon_name: str):
        """Try to catch a Pokemon"""
        if ctx.author.id in self.catching_users:
            return await ctx.send("You're already trying to catch a Pokemon!")

        if ctx.channel.id not in self.active_spawns:
            return await ctx.send("There's no Pokemon to catch!")

        spawn_data = self.active_spawns[ctx.channel.id]
        if spawn_data['caught']:
            return await ctx.send("This Pokemon has already been caught!")

        if pokemon_name.lower() != spawn_data['name'].lower():
            return await ctx.send("That's not the right Pokemon!")

        try:
            self.catching_users[ctx.author.id] = True

            # 60% base catch rate
            catch_rate = 0.6
            
            # Catching animation
            msg = await ctx.send("Throwing a Pokeball...")
            await asyncio.sleep(1)
            await msg.edit(content="The ball is shaking...")
            await asyncio.sleep(1)

            if random.random() < catch_rate:
                # Successful catch
                spawn_data['caught'] = True
                
                # Save to database
                await self.bot.db.execute(
                    '''INSERT INTO pokemon (user_id, pokemon_id, name, level, stats)
                       VALUES ($1, $2, $3, $4, $5)''',
                    ctx.author.id, spawn_data['pokemon_id'],
                    spawn_data['name'], spawn_data['level'],
                    json.dumps({
                        'hp': random.randint(1, 31),
                        'attack': random.randint(1, 31),
                        'defense': random.randint(1, 31),
                        'sp_attack': random.randint(1, 31),
                        'sp_defense': random.randint(1, 31),
                        'speed': random.randint(1, 31)
                    })
                )

                await msg.edit(
                    content=f"Congratulations! You caught a level {spawn_data['level']} {spawn_data['name']}!"
                )
                del self.active_spawns[ctx.channel.id]
            else:
                await msg.edit(content=f"Oh no! The {spawn_data['name']} broke free!")

        except Exception as e:
            await ctx.send(f"Error catching Pokemon: {e}")
        finally:
            if ctx.author.id in self.catching_users:
                del self.catching_users[ctx.author.id]

    @commands.command()
    async def pokemon(self, ctx):
        """List your Pokemon"""
        try:
            pokemon_list = await self.bot.db.fetch(
                'SELECT * FROM pokemon WHERE user_id = $1 ORDER BY caught_at DESC',
                ctx.author.id
            )
            
            if not pokemon_list:
                return await ctx.send("You don't have any Pokemon!")

            # Create paginated embed
            pokemon_per_page = 10
            pages = []
            
            for i in range(0, len(pokemon_list), pokemon_per_page):
                page_pokemon = pokemon_list[i:i + pokemon_per_page]
                embed = discord.Embed(
                    title="Your Pokemon",
                    color=discord.Color.blue()
                )
                
                for pokemon in page_pokemon:
                    stats = json.loads(pokemon['stats'])
                    embed.add_field(
                        name=f"Level {pokemon['level']} {pokemon['name'].title()}",
                        value=f"HP: {stats['hp']}\n"
                              f"Attack: {stats['attack']}\n"
                              f"Defense: {stats['defense']}\n"
                              f"Caught: {pokemon['caught_at'].strftime('%Y-%m-%d %H:%M')}",
                        inline=True
                    )
                pages.append(embed)

            if len(pages) == 1:
                await ctx.send(embed=pages[0])
            else:
                current_page = 0
                message = await ctx.send(embed=pages[current_page])

                # Add reactions for navigation
                await message.add_reaction("◀️")
                await message.add_reaction("▶️")

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]

                while True:
                    try:
                        reaction, user = await self.bot.wait_for(
                            "reaction_add",
                            timeout=60.0,
                            check=check
                        )

                        if str(reaction.emoji) == "▶️":
                            current_page = (current_page + 1) % len(pages)
                        elif str(reaction.emoji) == "◀️":
                            current_page = (current_page - 1) % len(pages)

                        await message.edit(embed=pages[current_page])
                        await message.remove_reaction(reaction, user)

                    except asyncio.TimeoutError:
                        break

        except Exception as e:
            await ctx.send(f"Error listing Pokemon: {e}")

    @commands.command()
    async def info(self, ctx, pokemon_name: str):
        """Get detailed information about one of your Pokemon"""
        try:
            pokemon = await self.bot.db.fetchrow(
                'SELECT * FROM pokemon WHERE user_id = $1 AND LOWER(name) = LOWER($2)',
                ctx.author.id, pokemon_name
            )
            
            if not pokemon:
                return await ctx.send("You don't have that Pokemon!")

            # Get Pokemon data from PokeAPI
            pokemon_data = await self.get_pokemon_data(pokemon['pokemon_id'])
            if not pokemon_data:
                return await ctx.send("Error fetching Pokemon data!")

            stats = json.loads(pokemon['stats'])
            
            embed = discord.Embed(
                title=f"Level {pokemon['level']} {pokemon['name'].title()}",
                color=discord.Color.blue()
            )
            
            # Add sprite
            embed.set_thumbnail(url=pokemon_data['sprites']['front_default'])
            
            # Add stats
            embed.add_field(
                name="Stats",
                value=f"HP: {stats['hp']}\n"
                      f"Attack: {stats['attack']}\n"
                      f"Defense: {stats['defense']}\n"
                      f"Sp. Attack: {stats['sp_attack']}\n"
                      f"Sp. Defense: {stats['sp_defense']}\n"
                      f"Speed: {stats['speed']}",
                inline=False
            )
            
            # Add types
            types = [t['type']['name'] for t in pokemon_data['types']]
            embed.add_field(
                name="Types",
                value=', '.join(t.title() for t in types),
                inline=False
            )
            
            # Add catch date
            embed.add_field(
                name="Caught on",
                value=pokemon['caught_at'].strftime('%Y-%m-%d %H:%M'),
                inline=False
            )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error showing Pokemon info: {e}")

async def setup(bot):
    await bot.add_cog(Pokemon(bot)) 