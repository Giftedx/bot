from discord.ext import commands
import discord
import asyncio
import random
from datetime import datetime
from typing import Dict, List, Optional

class OSRSCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_cache = {}  # Cache for XP rates
        self.world_cache = {}  # Cache for world data
        
    @commands.group(invoke_without_command=True)
    async def osrs(self, ctx):
        """OSRS base command group"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @osrs.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def train(self, ctx, skill: str, minutes: int = 60):
        """Train a specific skill"""
        # Get user data
        user_data = await self.bot.db.fetch_user_osrs(ctx.author.id)
        if not user_data:
            return await ctx.send("You need to create a character first!")

        # Calculate XP gain
        xp_gained = self.calculate_xp_gain(skill, minutes, user_data['level'])
        
        # Update database
        await self.bot.db.execute(
            '''UPDATE osrs_stats 
               SET xp = xp + $1, 
                   last_trained = NOW()
               WHERE user_id = $2 AND skill = $3''',
            xp_gained, ctx.author.id, skill
        )
        
        await ctx.send(f"You gained {xp_gained} XP in {skill}!")

    @osrs.command()
    async def create(self, ctx, name: str):
        """Create a new OSRS character"""
        # Check if character exists
        existing = await self.bot.db.fetch_user_osrs(ctx.author.id)
        if existing:
            return await ctx.send("You already have a character!")

        # Create character
        await self.bot.db.execute(
            '''INSERT INTO osrs_characters (user_id, name, stats, world)
               VALUES ($1, $2, $3, $4)''',
            ctx.author.id, name, self.default_stats(), 301
        )
        
        await ctx.send(f"Character **{name}** created!")

    def default_stats(self) -> Dict[str, int]:
        """Get default character stats"""
        return {
            "attack": 1,
            "strength": 1,
            "defense": 1,
            "hitpoints": 10,
            "prayer": 1,
            "magic": 1,
            "ranged": 1,
            "mining": 1,
            "woodcutting": 1
        }

class PokemonCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spawn_cooldowns = {}
        self.active_battles = {}
        
    @commands.group(invoke_without_command=True)
    async def pokemon(self, ctx):
        """Pokemon base command group"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @pokemon.command()
    async def catch(self, ctx, *, pokemon_name: str):
        """Attempt to catch a Pokemon"""
        # Check active spawn
        spawn_data = await self.bot.db.fetch_spawn(ctx.channel.id)
        if not spawn_data:
            return await ctx.send("There's no Pokemon to catch!")

        # Verify Pokemon name
        if spawn_data['name'].lower() != pokemon_name.lower():
            return await ctx.send("That's not the right Pokemon!")

        # Calculate catch chance
        catch_rate = self.calculate_catch_rate(spawn_data)
        if random.random() <= catch_rate:
            # Add to user's collection
            await self.bot.db.execute(
                '''INSERT INTO pokemon (user_id, pokemon_id, level)
                   VALUES ($1, $2, $3)''',
                ctx.author.id, spawn_data['pokemon_id'], spawn_data['level']
            )
            
            await ctx.send(f"Congratulations! You caught a level {spawn_data['level']} {pokemon_name}!")
        else:
            await ctx.send(f"Oh no! {pokemon_name} broke free!")

    @pokemon.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def battle(self, ctx, opponent: discord.Member):
        """Challenge another trainer to a battle"""
        if opponent.bot:
            return await ctx.send("You can't battle with a bot!")

        # Check if either user is in battle
        if ctx.author.id in self.active_battles or opponent.id in self.active_battles:
            return await ctx.send("One of the trainers is already in a battle!")

        # Get trainer Pokemon
        trainer1_pokemon = await self.get_trainer_pokemon(ctx.author.id)
        trainer2_pokemon = await self.get_trainer_pokemon(opponent.id)

        if not trainer1_pokemon or not trainer2_pokemon:
            return await ctx.send("Both trainers need Pokemon to battle!")

        # Create battle session
        battle_id = f"{ctx.author.id}:{opponent.id}"
        self.active_battles[battle_id] = {
            'trainer1': ctx.author.id,
            'trainer2': opponent.id,
            'pokemon1': trainer1_pokemon,
            'pokemon2': trainer2_pokemon,
            'current_turn': ctx.author.id
        }

        await self.start_battle(ctx, battle_id)

    async def start_battle(self, ctx, battle_id: str):
        """Start a Pokemon battle"""
        battle = self.active_battles[battle_id]
        
        # Send battle start message
        embed = discord.Embed(title="Pokemon Battle!", description="The battle is starting!")
        embed.add_field(name=ctx.author.name, value=f"Pokemon: {battle['pokemon1']['name']}")
        embed.add_field(name=ctx.author.name, value=f"Pokemon: {battle['pokemon2']['name']}")
        
        await ctx.send(embed=embed)
        
        # Battle loop
        while True:
            # Get current trainer and Pokemon
            current_trainer = ctx.author if battle['current_turn'] == ctx.author.id else ctx.guild.get_member(battle['trainer2'])
            current_pokemon = battle['pokemon1'] if battle['current_turn'] == ctx.author.id else battle['pokemon2']
            
            # Get move choice
            await ctx.send(f"{current_trainer.mention}'s turn! Choose a move: {', '.join(current_pokemon['moves'])}")
            
            try:
                move_msg = await self.bot.wait_for(
                    'message',
                    check=lambda m: m.author == current_trainer and m.channel == ctx.channel,
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                await ctx.send(f"{current_trainer.mention} took too long! Battle cancelled.")
                del self.active_battles[battle_id]
                return

            # Process move
            move = move_msg.content.lower()
            if move not in current_pokemon['moves']:
                await ctx.send("Invalid move! Battle cancelled.")
                del self.active_battles[battle_id]
                return

            # Calculate damage
            damage = self.calculate_damage(current_pokemon, move)
            
            # Apply damage to opponent
            if battle['current_turn'] == ctx.author.id:
                battle['pokemon2']['hp'] -= damage
                if battle['pokemon2']['hp'] <= 0:
                    await ctx.send(f"{ctx.author.mention} wins the battle!")
                    del self.active_battles[battle_id]
                    return
            else:
                battle['pokemon1']['hp'] -= damage
                if battle['pokemon1']['hp'] <= 0:
                    await ctx.send(f"{ctx.guild.get_member(battle['trainer2']).mention} wins the battle!")
                    del self.active_battles[battle_id]
                    return

            # Switch turns
            battle['current_turn'] = battle['trainer2'] if battle['current_turn'] == ctx.author.id else ctx.author.id

    def calculate_damage(self, pokemon: Dict, move: str) -> int:
        """Calculate move damage"""
        base_power = 40  # Default base power
        level = pokemon['level']
        attack = pokemon['stats']['attack']
        
        # Simple damage formula
        damage = ((2 * level / 5 + 2) * base_power * attack / 50) + 2
        return int(damage)

async def setup(bot):
    await bot.add_cog(OSRSCommands(bot))
    await bot.add_cog(PokemonCommands(bot)) 