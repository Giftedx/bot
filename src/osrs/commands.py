from discord.ext import commands
import discord
from typing import Optional
from datetime import datetime
import asyncio
from .data_integration import OSRSDataManager

class OSRSCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = OSRSDataManager()
        self.training_sessions = {}

    async def cog_load(self):
        """Initialize the cog and load data"""
        await self.data_manager.initialize()

    @commands.group(invoke_without_command=True)
    async def osrs(self, ctx):
        """OSRS command group for game integration"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="OSRS Commands",
                description="Old School RuneScape commands and features",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Character",
                value="`create` - Create a new character\n"
                      "`stats` - View your stats\n"
                      "`train` - Train a skill",
                inline=False
            )
            embed.add_field(
                name="Items & Trading",
                value="`price` - Check GE prices\n"
                      "`search` - Search for items\n"
                      "`inventory` - View your inventory",
                inline=False
            )
            embed.add_field(
                name="Quests & Achievement Diaries",
                value="`quest` - Quest information\n"
                      "`diary` - Achievement diary status",
                inline=False
            )
            await ctx.send(embed=embed)

    @osrs.command()
    async def create(self, ctx, *, name: str):
        """Create a new OSRS character"""
        # Check if character exists
        existing = await self.bot.db.fetchrow(
            "SELECT * FROM osrs_characters WHERE user_id = $1",
            ctx.author.id
        )
        if existing:
            return await ctx.send("You already have a character!")

        # Create character with default stats
        stats = {skill: 1 for skill in self.data_manager.skills_cache.keys()}
        stats['hitpoints'] = 10  # Starting hitpoints is 10

        await self.bot.db.execute(
            """INSERT INTO osrs_characters (user_id, name, stats, created_at)
               VALUES ($1, $2, $3, $4)""",
            ctx.author.id, name, stats, datetime.utcnow()
        )

        embed = discord.Embed(
            title="Character Created!",
            description=f"Welcome to Old School RuneScape, {name}!",
            color=discord.Color.green()
        )
        embed.add_field(name="Combat Level", value="3")
        embed.set_footer(text="Use !osrs stats to view your stats")
        await ctx.send(embed=embed)

    @osrs.command()
    async def stats(self, ctx, *, member: discord.Member = None):
        """View character stats"""
        member = member or ctx.author
        char_data = await self.bot.db.fetchrow(
            "SELECT * FROM osrs_characters WHERE user_id = $1",
            member.id
        )
        if not char_data:
            return await ctx.send(f"{'You don\'t' if member == ctx.author else member.name + ' doesn\'t'} have a character!")

        stats = char_data['stats']
        combat_level = await self.data_manager.calculate_combat_level(stats)

        embed = discord.Embed(
            title=f"{char_data['name']}'s Stats",
            description=f"Combat Level: {combat_level}",
            color=discord.Color.blue()
        )

        # Group stats by type
        combat_stats = ["attack", "strength", "defence", "hitpoints", "ranged", "prayer", "magic"]
        skilling_stats = [skill for skill in stats.keys() if skill not in combat_stats]

        # Add combat stats
        combat_text = ""
        for skill in combat_stats:
            level = stats[skill]
            xp = await self.data_manager.get_xp_for_level(level)
            combat_text += f"**{skill.title()}:** {level} ({xp:,} xp)\n"
        embed.add_field(name="Combat Skills", value=combat_text, inline=False)

        # Add skilling stats
        skilling_text = ""
        for skill in skilling_stats:
            level = stats[skill]
            xp = await self.data_manager.get_xp_for_level(level)
            skilling_text += f"**{skill.title()}:** {level} ({xp:,} xp)\n"
        embed.add_field(name="Skilling", value=skilling_text, inline=False)

        await ctx.send(embed=embed)

    @osrs.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def train(self, ctx, skill: str, minutes: int = 60):
        """Train a specific skill"""
        if minutes < 1 or minutes > 180:
            return await ctx.send("Training time must be between 1 and 180 minutes!")

        char_data = await self.bot.db.fetchrow(
            "SELECT * FROM osrs_characters WHERE user_id = $1",
            ctx.author.id
        )
        if not char_data:
            return await ctx.send("You need to create a character first!")

        skill = skill.lower()
        if skill not in self.data_manager.skills_cache:
            return await ctx.send("Invalid skill name!")

        # Start training session
        if ctx.author.id in self.training_sessions:
            return await ctx.send("You're already training a skill!")

        current_level = char_data['stats'][skill]
        xp_rate = self.calculate_xp_rate(skill, current_level)
        total_xp = int(xp_rate * minutes)

        embed = discord.Embed(
            title="Training Session Started",
            description=f"Training {skill.title()} for {minutes} minutes",
            color=discord.Color.blue()
        )
        embed.add_field(name="Current Level", value=str(current_level))
        embed.add_field(name="XP Rate", value=f"{xp_rate:,}/min")
        embed.add_field(name="Estimated XP Gain", value=f"{total_xp:,}")
        
        msg = await ctx.send(embed=embed)
        
        # Start training session
        self.training_sessions[ctx.author.id] = {
            'skill': skill,
            'start_time': datetime.utcnow(),
            'duration': minutes,
            'message': msg
        }

        # Schedule training completion
        self.bot.loop.create_task(self.complete_training(ctx, ctx.author.id))

    async def complete_training(self, ctx, user_id: int):
        """Complete a training session"""
        session = self.training_sessions.get(user_id)
        if not session:
            return

        await asyncio.sleep(session['duration'] * 60)  # Convert minutes to seconds

        # Calculate XP gained
        char_data = await self.bot.db.fetchrow(
            "SELECT * FROM osrs_characters WHERE user_id = $1",
            user_id
        )
        if not char_data:
            del self.training_sessions[user_id]
            return

        skill = session['skill']
        current_level = char_data['stats'][skill]
        xp_rate = self.calculate_xp_rate(skill, current_level)
        xp_gained = int(xp_rate * session['duration'])

        # Update stats
        new_stats = char_data['stats'].copy()
        new_xp = await self.data_manager.get_xp_for_level(current_level) + xp_gained
        new_level = await self.data_manager.get_level_for_xp(new_xp)
        new_stats[skill] = new_level

        await self.bot.db.execute(
            """UPDATE osrs_characters 
               SET stats = $1
               WHERE user_id = $2""",
            new_stats, user_id
        )

        # Send completion message
        embed = discord.Embed(
            title="Training Complete!",
            description=f"Finished training {skill.title()}",
            color=discord.Color.green()
        )
        embed.add_field(name="XP Gained", value=f"{xp_gained:,}")
        embed.add_field(name="Levels Gained", value=str(new_level - current_level))
        embed.add_field(name="New Level", value=str(new_level))

        await ctx.send(f"<@{user_id}>", embed=embed)
        del self.training_sessions[user_id]

    def calculate_xp_rate(self, skill: str, current_level: int) -> int:
        """Calculate XP rate for a skill based on current level"""
        base_rates = {
            'woodcutting': 30,
            'mining': 35,
            'fishing': 40,
            'combat': 50,  # Base for combat skills
            'crafting': 45,
            'smithing': 40,
            'cooking': 50,
            'firemaking': 45,
            'other': 35  # Default for other skills
        }

        # Get base rate
        if skill in ['attack', 'strength', 'defence', 'ranged', 'magic']:
            base_rate = base_rates['combat']
        else:
            base_rate = base_rates.get(skill, base_rates['other'])

        # Scale with level (higher levels = better xp rates)
        level_multiplier = 1 + (current_level / 50)  # Max 3x at level 99
        return int(base_rate * level_multiplier)

    @osrs.command()
    async def price(self, ctx, *, item_name: str):
        """Check Grand Exchange prices for an item"""
        # Search for the item
        items = await self.data_manager.search_items(item_name)
        if not items:
            return await ctx.send("Item not found!")

        if len(items) > 1:
            # Multiple matches found, show a selection menu
            item_list = "\n".join(f"{i+1}. {item['name']}" for i, item in enumerate(items[:5]))
            await ctx.send(f"Multiple items found. Please specify:\n{item_list}")
            
            try:
                msg = await self.bot.wait_for(
                    'message',
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit(),
                    timeout=30.0
                )
                selection = int(msg.content)
                if selection < 1 or selection > len(items[:5]):
                    return await ctx.send("Invalid selection!")
                item = items[selection-1]
            except asyncio.TimeoutError:
                return await ctx.send("Selection timed out!")
            except ValueError:
                return await ctx.send("Invalid selection!")
        else:
            item = items[0]

        # Get current price
        price_data = await self.data_manager.get_ge_price(item['id'])
        if not price_data:
            return await ctx.send("Could not fetch price data!")

        embed = discord.Embed(
            title=item['name'],
            description=f"Current Grand Exchange Prices",
            color=discord.Color.gold()
        )
        embed.add_field(name="High Price", value=f"{price_data['high']:,} gp")
        embed.add_field(name="Low Price", value=f"{price_data['low']:,} gp")
        embed.add_field(name="Last Updated", value=f"<t:{price_data['timestamp']}:R>")
        
        if item.get('examine'):
            embed.set_footer(text=item['examine'])

        await ctx.send(embed=embed)

    @osrs.command()
    async def quest(self, ctx, *, quest_name: str):
        """Get information about a quest"""
        quest_data = await self.data_manager.get_quest_info(quest_name)
        if not quest_data:
            return await ctx.send("Quest not found!")

        embed = discord.Embed(
            title=quest_data['name'],
            description=quest_data.get('description', 'No description available.'),
            color=discord.Color.blue()
        )

        if quest_data.get('requirements'):
            reqs = quest_data['requirements']
            if reqs.get('skills'):
                skill_reqs = "\n".join(f"{skill}: {level}" for skill, level in reqs['skills'].items())
                embed.add_field(name="Skill Requirements", value=skill_reqs, inline=False)
            
            if reqs.get('quests'):
                quest_reqs = "\n".join(reqs['quests'])
                embed.add_field(name="Quest Requirements", value=quest_reqs, inline=False)

        if quest_data.get('rewards'):
            rewards = quest_data['rewards']
            reward_text = ""
            if rewards.get('xp'):
                reward_text += "**XP Rewards:**\n"
                reward_text += "\n".join(f"{skill}: {xp:,}" for skill, xp in rewards['xp'].items())
            if rewards.get('items'):
                reward_text += "\n\n**Item Rewards:**\n"
                reward_text += "\n".join(rewards['items'])
            embed.add_field(name="Rewards", value=reward_text, inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OSRSCommands(bot)) 