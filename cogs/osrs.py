import discord
from discord.ext import commands
import asyncio
import json
import random
from typing import Dict, Optional

class OSRS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.training_users = {}
        self.skills = [
            'attack', 'strength', 'defence', 'ranged', 'prayer',
            'magic', 'runecrafting', 'construction', 'hitpoints',
            'agility', 'herblore', 'thieving', 'crafting',
            'fletching', 'slayer', 'hunter', 'mining', 'smithing',
            'fishing', 'cooking', 'firemaking', 'woodcutting', 'farming'
        ]

    @commands.group(invoke_without_command=True)
    async def osrs(self, ctx):
        """OSRS commands group"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @osrs.command(name='create')
    async def create_character(self, ctx, name: str):
        """Create a new OSRS character"""
        try:
            # Check if character already exists
            existing = await self.bot.db.fetchrow(
                'SELECT id FROM osrs_characters WHERE user_id = $1 AND name = $2',
                ctx.author.id, name
            )
            if existing:
                return await ctx.send("You already have a character with that name!")

            # Create character
            char_id = await self.bot.db.fetchval(
                '''INSERT INTO osrs_characters (user_id, name, stats, inventory, world)
                   VALUES ($1, $2, $3, $4, $5) RETURNING id''',
                ctx.author.id, name, 
                json.dumps({'combat_level': 3}),
                json.dumps({}),
                301  # Default world
            )

            # Initialize skills
            for skill in self.skills:
                await self.bot.db.execute(
                    '''INSERT INTO osrs_stats (character_id, skill, xp, level)
                       VALUES ($1, $2, $3, $4)''',
                    char_id, skill, 0, 1
                )

            await ctx.send(f"Created new character: {name}")
        except Exception as e:
            await ctx.send(f"Error creating character: {e}")

    @osrs.command(name='stats')
    async def show_stats(self, ctx, character_name: Optional[str] = None):
        """Show character stats"""
        try:
            # Get character
            query = '''
                SELECT c.*, s.skill, s.level, s.xp
                FROM osrs_characters c
                JOIN osrs_stats s ON c.id = s.character_id
                WHERE c.user_id = $1
            '''
            params = [ctx.author.id]
            
            if character_name:
                query += " AND c.name = $2"
                params.append(character_name)
            
            rows = await self.bot.db.fetch(query, *params)
            
            if not rows:
                return await ctx.send(
                    "Character not found! Use `!osrs create <name>` to create one."
                )

            # Group stats by character
            stats = {}
            for row in rows:
                if row['name'] not in stats:
                    stats[row['name']] = {
                        'stats': {},
                        'total_level': 0,
                        'total_xp': 0
                    }
                stats[row['name']]['stats'][row['skill']] = {
                    'level': row['level'],
                    'xp': row['xp']
                }
                stats[row['name']]['total_level'] += row['level']
                stats[row['name']]['total_xp'] += row['xp']

            # Create embed for each character
            for name, data in stats.items():
                embed = discord.Embed(
                    title=f"OSRS Stats - {name}",
                    color=discord.Color.gold()
                )
                
                # Add stats fields
                for skill in self.skills:
                    skill_data = data['stats'].get(skill, {'level': 1, 'xp': 0})
                    embed.add_field(
                        name=skill.title(),
                        value=f"Level: {skill_data['level']}\nXP: {skill_data['xp']:,}",
                        inline=True
                    )

                # Add total stats
                embed.add_field(
                    name="Total Level",
                    value=f"{data['total_level']:,}",
                    inline=False
                )
                embed.add_field(
                    name="Total XP",
                    value=f"{data['total_xp']:,}",
                    inline=False
                )

                await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error showing stats: {e}")

    @osrs.command(name='train')
    async def train_skill(self, ctx, character_name: str, skill: str, minutes: int = 60):
        """Train a skill"""
        if ctx.author.id in self.training_users:
            return await ctx.send("You're already training!")

        if minutes < 1 or minutes > 180:
            return await ctx.send("Training time must be between 1 and 180 minutes!")

        skill = skill.lower()
        if skill not in self.skills:
            return await ctx.send(f"Invalid skill! Available skills: {', '.join(self.skills)}")

        try:
            # Get character
            character = await self.bot.db.fetchrow(
                'SELECT * FROM osrs_characters WHERE user_id = $1 AND name = $2',
                ctx.author.id, character_name
            )
            if not character:
                return await ctx.send("Character not found!")

            # Get current skill stats
            stats = await self.bot.db.fetchrow(
                'SELECT * FROM osrs_stats WHERE character_id = $1 AND skill = $2',
                character['id'], skill
            )

            # Start training
            self.training_users[ctx.author.id] = True
            await ctx.send(f"Started training {skill}! This will take {minutes} minutes.")

            # Training loop
            for i in range(minutes):
                if i > 0 and i % 5 == 0:  # Update every 5 minutes
                    await ctx.send(f"{character_name} is training {skill}... {i}/{minutes} minutes")
                
                # Calculate XP gain (random amount based on current level)
                xp_gain = random.randint(10, 50) * stats['level']
                
                # Update stats
                await self.bot.db.execute(
                    'UPDATE osrs_stats SET xp = xp + $1 WHERE id = $2',
                    xp_gain, stats['id']
                )
                
                await asyncio.sleep(60)  # Wait 1 minute

            # Get final stats
            final_stats = await self.bot.db.fetchrow(
                'SELECT * FROM osrs_stats WHERE id = $1',
                stats['id']
            )

            # Calculate gains
            xp_gained = final_stats['xp'] - stats['xp']
            levels_gained = final_stats['level'] - stats['level']

            embed = discord.Embed(
                title="Training Complete!",
                description=f"{character_name} finished training {skill}!",
                color=discord.Color.green()
            )
            embed.add_field(name="XP Gained", value=f"{xp_gained:,}")
            embed.add_field(name="Levels Gained", value=str(levels_gained))
            embed.add_field(
                name="Current Level",
                value=f"{final_stats['level']} ({final_stats['xp']:,} XP)",
                inline=False
            )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error during training: {e}")
        finally:
            if ctx.author.id in self.training_users:
                del self.training_users[ctx.author.id]

    @osrs.command(name='world')
    async def change_world(self, ctx, character_name: str, world: int):
        """Change game world"""
        if not 301 <= world <= 580:
            return await ctx.send("Invalid world! Must be between 301 and 580.")

        try:
            result = await self.bot.db.execute(
                'UPDATE osrs_characters SET world = $1 WHERE user_id = $2 AND name = $3',
                world, ctx.author.id, character_name
            )
            if result == 'UPDATE 0':
                await ctx.send("Character not found!")
            else:
                await ctx.send(f"{character_name} switched to World {world}!")
        except Exception as e:
            await ctx.send(f"Error changing world: {e}")

    @osrs.command(name='inventory')
    async def show_inventory(self, ctx, character_name: str):
        """Show character inventory"""
        try:
            character = await self.bot.db.fetchrow(
                'SELECT * FROM osrs_characters WHERE user_id = $1 AND name = $2',
                ctx.author.id, character_name
            )
            if not character:
                return await ctx.send("Character not found!")

            inventory = json.loads(character['inventory'])
            if not inventory:
                return await ctx.send("Inventory is empty!")

            embed = discord.Embed(
                title=f"{character_name}'s Inventory",
                color=discord.Color.blue()
            )
            
            for item, amount in inventory.items():
                embed.add_field(
                    name=item,
                    value=f"Amount: {amount:,}",
                    inline=True
                )

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error showing inventory: {e}")

async def setup(bot):
    await bot.add_cog(OSRS(bot)) 