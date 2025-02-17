"""Fun and entertainment commands with special features."""

import discord
from discord.ext import commands
import random
import asyncio
import json
import os
from typing import Optional, Dict, List
import datetime
import aiohttp

class FunCommands(commands.Cog, name="Fun"):
    """Fun commands and special features.
    
    This category includes commands for:
    - Memes and jokes
    - Virtual pet system
    - Battle arena
    - Shop and economy
    - Interactive map
    - Minigames
    - Easter eggs
    - And more fun stuff!
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.pets = {}
        self.user_data = {}
        self.shops = {}
        self.battles = {}
        self.minigames = {}
        self.load_data()
        
    def load_data(self):
        """Load user data, pets, and shop information."""
        # Create data directory if it doesn't exist
        if not os.path.exists('data'):
            os.makedirs('data')
            
        # Load or create user data
        try:
            with open('data/user_data.json', 'r') as f:
                self.user_data = json.load(f)
        except FileNotFoundError:
            self.user_data = {}
            
        # Load or create pet data
        try:
            with open('data/pets.json', 'r') as f:
                self.pets = json.load(f)
        except FileNotFoundError:
            self.pets = {}
            
        # Load or create shop data
        try:
            with open('data/shops.json', 'r') as f:
                self.shops = json.load(f)
        except FileNotFoundError:
            self.shops = {
                'pet_shop': {
                    'egg': 100,
                    'food': 50,
                    'toy': 75
                },
                'battle_shop': {
                    'sword': 200,
                    'shield': 150,
                    'potion': 80
                }
            }
            
        self.save_data()
        
    def save_data(self):
        """Save all data to files."""
        with open('data/user_data.json', 'w') as f:
            json.dump(self.user_data, f, indent=4)
        with open('data/pets.json', 'w') as f:
            json.dump(self.pets, f, indent=4)
        with open('data/shops.json', 'w') as f:
            json.dump(self.shops, f, indent=4)
    
    def get_user_data(self, user_id: int) -> dict:
        """Get or create user data."""
        if str(user_id) not in self.user_data:
            self.user_data[str(user_id)] = {
                'coins': 100,
                'inventory': [],
                'pets': [],
                'battles_won': 0,
                'last_daily': None
            }
            self.save_data()
        return self.user_data[str(user_id)]
    
    @commands.command(name="meme")
    async def get_meme(self, ctx):
        """Get a random meme from Reddit.
        
        Fetches a random meme from popular meme subreddits.
        
        Examples:
        ---------
        !meme
        
        Notes:
        ------
        - SFW memes only
        - Updates regularly
        - Sources: r/memes, r/dankmemes, r/wholesomememes
        """
        subreddits = ['memes', 'dankmemes', 'wholesomememes']
        subreddit = random.choice(subreddits)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://www.reddit.com/r/{subreddit}/hot.json?limit=100') as response:
                data = await response.json()
                posts = [post['data'] for post in data['data']['children'] if not post['data']['is_self']]
                post = random.choice(posts)
                
                embed = discord.Embed(
                    title=post['title'],
                    url=f"https://reddit.com{post['permalink']}",
                    color=discord.Color.random()
                )
                embed.set_image(url=post['url'])
                embed.set_footer(text=f"👍 {post['ups']} | 💬 {post['num_comments']}")
                
                await ctx.send(embed=embed)
    
    @commands.command(name="joke")
    async def tell_joke(self, ctx):
        """Tell a random joke.
        
        Gets a random joke from a curated collection.
        
        Examples:
        ---------
        !joke
        
        Notes:
        ------
        - Family friendly jokes
        - Multiple categories
        - Includes dad jokes
        """
        async with aiohttp.ClientSession() as session:
            async with session.get('https://official-joke-api.appspot.com/random_joke') as response:
                joke = await response.json()
                
                embed = discord.Embed(
                    title="😄 Here's a joke!",
                    color=discord.Color.random()
                )
                embed.add_field(name=joke['setup'], value=f"||{joke['punchline']}||", inline=False)
                
                await ctx.send(embed=embed)
    
    @commands.group(name="pet", invoke_without_command=True)
    async def pet_group(self, ctx):
        """Virtual pet system commands.
        
        Manage your virtual pets with various activities.
        
        Subcommands:
        ------------
        adopt - Adopt a new pet
        feed - Feed your pet
        play - Play with your pet
        list - List your pets
        stats - Check pet stats
        
        Examples:
        ---------
        !pet adopt
        !pet feed Fluffy
        !pet play Buddy
        """
        await ctx.send_help(ctx.command)
    
    @pet_group.command(name="adopt")
    async def adopt_pet(self, ctx, name: str):
        """Adopt a new virtual pet.
        
        Parameters:
        -----------
        name: Name for your new pet
        
        Examples:
        ---------
        !pet adopt Fluffy
        
        Notes:
        ------
        - Costs 100 coins
        - Random pet type
        - Unique name required
        """
        user_data = self.get_user_data(ctx.author.id)
        
        if user_data['coins'] < 100:
            await ctx.send("You need 100 coins to adopt a pet!")
            return
            
        if name in [pet['name'] for pet in user_data['pets']]:
            await ctx.send("You already have a pet with that name!")
            return
            
        pet_types = ['dog', 'cat', 'dragon', 'unicorn', 'phoenix']
        new_pet = {
            'name': name,
            'type': random.choice(pet_types),
            'happiness': 100,
            'hunger': 0,
            'level': 1,
            'exp': 0
        }
        
        user_data['pets'].append(new_pet)
        user_data['coins'] -= 100
        self.save_data()
        
        embed = discord.Embed(
            title="🎉 New Pet Adopted!",
            description=f"Welcome {name} the {new_pet['type']} to your family!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @pet_group.command(name="feed")
    async def feed_pet(self, ctx, name: str):
        """Feed your virtual pet.
        
        Parameters:
        -----------
        name: Name of the pet to feed
        
        Examples:
        ---------
        !pet feed Fluffy
        
        Notes:
        ------
        - Reduces hunger
        - Increases happiness
        - Requires food items
        """
        user_data = self.get_user_data(ctx.author.id)
        pet = next((p for p in user_data['pets'] if p['name'].lower() == name.lower()), None)
        
        if not pet:
            await ctx.send("You don't have a pet with that name!")
            return
            
        if 'food' not in user_data['inventory']:
            await ctx.send("You need food to feed your pet! Buy some from the shop.")
            return
            
        pet['hunger'] = max(0, pet['hunger'] - 30)
        pet['happiness'] = min(100, pet['happiness'] + 10)
        user_data['inventory'].remove('food')
        self.save_data()
        
        embed = discord.Embed(
            title="🍖 Feeding Time!",
            description=f"{name} enjoyed their meal!",
            color=discord.Color.green()
        )
        embed.add_field(name="Hunger", value=f"{pet['hunger']}/100", inline=True)
        embed.add_field(name="Happiness", value=f"{pet['happiness']}/100", inline=True)
        
        await ctx.send(embed=embed)
    
    @pet_group.command(name="play")
    async def play_with_pet(self, ctx, name: str):
        """Play with your virtual pet.
        
        Parameters:
        -----------
        name: Name of the pet to play with
        
        Examples:
        ---------
        !pet play Fluffy
        
        Notes:
        ------
        - Increases happiness
        - Gains experience
        - Random mini-games
        """
        user_data = self.get_user_data(ctx.author.id)
        pet = next((p for p in user_data['pets'] if p['name'].lower() == name.lower()), None)
        
        if not pet:
            await ctx.send("You don't have a pet with that name!")
            return
            
        games = [
            "fetch",
            "hide and seek",
            "trick training",
            "obstacle course"
        ]
        game = random.choice(games)
        
        embed = discord.Embed(
            title="🎮 Playtime!",
            description=f"Playing {game} with {name}...",
            color=discord.Color.blue()
        )
        message = await ctx.send(embed=embed)
        
        await asyncio.sleep(2)
        
        # Add experience and happiness
        exp_gained = random.randint(5, 15)
        pet['exp'] += exp_gained
        pet['happiness'] = min(100, pet['happiness'] + 20)
        
        # Level up check
        level_up = False
        while pet['exp'] >= 100 * pet['level']:
            pet['exp'] -= 100 * pet['level']
            pet['level'] += 1
            level_up = True
            
        self.save_data()
        
        embed.add_field(name="Experience Gained", value=f"+{exp_gained} EXP", inline=True)
        embed.add_field(name="Happiness", value=f"{pet['happiness']}/100", inline=True)
        
        if level_up:
            embed.add_field(
                name="Level Up!",
                value=f"{name} is now level {pet['level']}!",
                inline=False
            )
            
        await message.edit(embed=embed)
    
    @pet_group.command(name="train")
    async def train_pet(self, ctx, name: str, skill: str):
        """Train your pet in a specific skill.
        
        Parameters:
        -----------
        name: Name of the pet to train
        skill: Skill to train (agility/strength/intelligence)
        
        Examples:
        ---------
        !pet train Fluffy agility
        
        Notes:
        ------
        - Improves pet abilities
        - Requires energy
        - Unlocks new tricks
        """
        valid_skills = ['agility', 'strength', 'intelligence']
        if skill.lower() not in valid_skills:
            await ctx.send(f"Invalid skill! Choose from: {', '.join(valid_skills)}")
            return
            
        user_data = self.get_user_data(ctx.author.id)
        pet = next((p for p in user_data['pets'] if p['name'].lower() == name.lower()), None)
        
        if not pet:
            await ctx.send("You don't have a pet with that name!")
            return
            
        # Initialize skills if not present
        if 'skills' not in pet:
            pet['skills'] = {skill: 1 for skill in valid_skills}
            
        # Training session
        embed = discord.Embed(
            title="🎯 Training Session",
            description=f"Training {name}'s {skill}...",
            color=discord.Color.blue()
        )
        message = await ctx.send(embed=embed)
        
        await asyncio.sleep(2)
        
        # Improve skill and add experience
        skill_gain = random.randint(1, 3)
        exp_gained = random.randint(10, 20)
        
        pet['skills'][skill] += skill_gain
        pet['exp'] += exp_gained
        pet['happiness'] = max(0, pet['happiness'] - 10)  # Training is tiring
        
        # Level up check
        level_up = False
        while pet['exp'] >= 100 * pet['level']:
            pet['exp'] -= 100 * pet['level']
            pet['level'] += 1
            level_up = True
            
        self.save_data()
        
        embed.add_field(
            name=f"{skill.capitalize()} Improvement",
            value=f"+{skill_gain} (Now: {pet['skills'][skill]})",
            inline=True
        )
        embed.add_field(name="Experience Gained", value=f"+{exp_gained} EXP", inline=True)
        
        if level_up:
            embed.add_field(
                name="Level Up!",
                value=f"{name} is now level {pet['level']}!",
                inline=False
            )
            
        await message.edit(embed=embed)
    
    @pet_group.command(name="evolve")
    async def evolve_pet(self, ctx, name: str):
        """Evolve your pet to a stronger form.
        
        Parameters:
        -----------
        name: Name of the pet to evolve
        
        Examples:
        ---------
        !pet evolve Fluffy
        
        Notes:
        ------
        - Requires level 20
        - Permanent transformation
        - New abilities unlocked
        """
        user_data = self.get_user_data(ctx.author.id)
        pet = next((p for p in user_data['pets'] if p['name'].lower() == name.lower()), None)
        
        if not pet:
            await ctx.send("You don't have a pet with that name!")
            return
            
        if pet['level'] < 20:
            await ctx.send(f"{name} needs to be level 20 to evolve! (Current level: {pet['level']})")
            return
            
        # Evolution options based on pet type
        evolution_paths = {
            'dog': ['Wolf', 'Cerberus', 'Fenrir'],
            'cat': ['Panther', 'Sphinx', 'Manticore'],
            'dragon': ['Wyvern', 'Hydra', 'Elder Dragon'],
            'unicorn': ['Pegasus', 'Alicorn', 'Celestial Steed'],
            'phoenix': ['Inferno Phoenix', 'Eternal Phoenix', 'Cosmic Phoenix']
        }
        
        if pet['type'] not in evolution_paths:
            await ctx.send("This pet type cannot evolve!")
            return
            
        # Get evolution options
        current_stage = 0
        for i, form in enumerate(evolution_paths[pet['type']]):
            if form == pet.get('evolution', pet['type']):
                current_stage = i + 1
                
        if current_stage >= len(evolution_paths[pet['type']]):
            await ctx.send(f"{name} has reached their final form!")
            return
            
        next_form = evolution_paths[pet['type']][current_stage]
        
        # Confirm evolution
        embed = discord.Embed(
            title="✨ Evolution Available!",
            description=f"Do you want to evolve {name} into a {next_form}?",
            color=discord.Color.purple()
        )
        embed.add_field(
            name="Current Form",
            value=pet.get('evolution', pet['type']),
            inline=True
        )
        embed.add_field(name="Next Form", value=next_form, inline=True)
        
        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]
            
        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "✅":
                # Evolve the pet
                pet['evolution'] = next_form
                pet['level'] += 1  # Bonus level
                self.save_data()
                
                embed = discord.Embed(
                    title="🌟 Evolution Complete!",
                    description=f"Congratulations! {name} evolved into a {next_form}!",
                    color=discord.Color.gold()
                )
                await message.edit(embed=embed)
            else:
                await ctx.send("Evolution cancelled.")
                
        except asyncio.TimeoutError:
            await ctx.send("Evolution timed out.")
    
    @pet_group.command(name="battle")
    async def pet_battle(self, ctx, name: str, opponent: discord.Member):
        """Battle your pet against another player's pet.
        
        Parameters:
        -----------
        name: Name of your pet
        opponent: The player to battle against
        
        Examples:
        ---------
        !pet battle Fluffy @user
        
        Notes:
        ------
        - Turn-based combat
        - Uses pet stats
        - Rewards for winning
        """
        if opponent.bot:
            await ctx.send("You can't battle against bots!")
            return
            
        if opponent == ctx.author:
            await ctx.send("You can't battle against yourself!")
            return
            
        # Get pets
        user_data = self.get_user_data(ctx.author.id)
        opponent_data = self.get_user_data(opponent.id)
        
        pet = next((p for p in user_data['pets'] if p['name'].lower() == name.lower()), None)
        if not pet:
            await ctx.send("You don't have a pet with that name!")
            return
            
        # Ask opponent to choose their pet
        if not opponent_data['pets']:
            await ctx.send(f"{opponent.mention} doesn't have any pets!")
            return
            
        embed = discord.Embed(
            title="⚔️ Pet Battle Challenge!",
            description=f"{ctx.author.mention}'s {name} challenges you to a battle!\nChoose your pet by number:",
            color=discord.Color.red()
        )
        
        for i, p in enumerate(opponent_data['pets'], 1):
            embed.add_field(
                name=f"{i}. {p['name']}",
                value=f"Level {p['level']} {p.get('evolution', p['type'])}",
                inline=True
            )
            
        await ctx.send(f"{opponent.mention}", embed=embed)
        
        def check(m):
            return m.author == opponent and m.channel == ctx.channel and m.content.isdigit()
            
        try:
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
            choice = int(msg.content)
            
            if not 1 <= choice <= len(opponent_data['pets']):
                await ctx.send("Invalid choice!")
                return
                
            opponent_pet = opponent_data['pets'][choice - 1]
            
            # Battle system
            embed = discord.Embed(
                title="🏟️ Pet Battle Arena",
                description=f"{name} vs {opponent_pet['name']}",
                color=discord.Color.gold()
            )
            
            # Show stats
            embed.add_field(
                name=name,
                value=f"Level: {pet['level']}\nType: {pet.get('evolution', pet['type'])}",
                inline=True
            )
            embed.add_field(
                name=opponent_pet['name'],
                value=f"Level: {opponent_pet['level']}\nType: {opponent_pet.get('evolution', opponent_pet['type'])}",
                inline=True
            )
            
            battle_msg = await ctx.send(embed=embed)
            
            # Battle rounds
            pet_hp = 100 + (pet['level'] * 10)
            opponent_hp = 100 + (opponent_pet['level'] * 10)
            
            while pet_hp > 0 and opponent_hp > 0:
                # Calculate damage
                pet_damage = random.randint(5, 15) + (pet['level'] * 2)
                opponent_damage = random.randint(5, 15) + (opponent_pet['level'] * 2)
                
                # Apply damage
                opponent_hp -= pet_damage
                pet_hp -= opponent_damage
                
                # Update battle status
                embed.description = (
                    f"{name}: {max(0, pet_hp)} HP (-{opponent_damage})\n"
                    f"{opponent_pet['name']}: {max(0, opponent_hp)} HP (-{pet_damage})"
                )
                await battle_msg.edit(embed=embed)
                await asyncio.sleep(2)
                
            # Determine winner
            winner = ctx.author if pet_hp > opponent_hp else opponent
            winner_pet = name if pet_hp > opponent_hp else opponent_pet['name']
            
            # Award prizes
            prize_coins = random.randint(50, 150)
            winner_data = self.get_user_data(winner.id)
            winner_data['coins'] += prize_coins
            
            # Award experience
            if pet_hp > opponent_hp:
                pet['exp'] += 50
            else:
                opponent_pet['exp'] += 50
                
            self.save_data()
            
            embed.description = (
                f"🏆 {winner.mention}'s {winner_pet} wins!\n"
                f"Prize: {prize_coins} coins"
            )
            await battle_msg.edit(embed=embed)
            
        except asyncio.TimeoutError:
            await ctx.send("Battle challenge timed out.")
            
    @pet_group.command(name="adventure")
    async def pet_adventure(self, ctx, name: str):
        """Send your pet on an adventure.
        
        Parameters:
        -----------
        name: Name of the pet to send on adventure
        
        Examples:
        ---------
        !pet adventure Fluffy
        
        Notes:
        ------
        - Random events
        - Find treasure
        - Gain experience
        - Time-based cooldown
        """
        user_data = self.get_user_data(ctx.author.id)
        pet = next((p for p in user_data['pets'] if p['name'].lower() == name.lower()), None)
        
        if not pet:
            await ctx.send("You don't have a pet with that name!")
            return
            
        # Check cooldown
        last_adventure = pet.get('last_adventure')
        if last_adventure:
            last_time = datetime.datetime.fromisoformat(last_adventure)
            if datetime.datetime.utcnow() - last_time < datetime.timedelta(hours=1):
                time_left = datetime.timedelta(hours=1) - (datetime.datetime.utcnow() - last_time)
                await ctx.send(f"{name} needs to rest for {str(time_left).split('.')[0]} more!")
                return
                
        # Adventure events
        events = [
            {
                'name': 'Treasure Hunt',
                'description': 'found a buried treasure!',
                'coins': (50, 150),
                'exp': (20, 40)
            },
            {
                'name': 'Monster Battle',
                'description': 'defeated a fearsome monster!',
                'coins': (100, 200),
                'exp': (30, 50)
            },
            {
                'name': 'Lost City',
                'description': 'discovered an ancient lost city!',
                'coins': (150, 300),
                'exp': (40, 60)
            },
            {
                'name': 'Magical Spring',
                'description': 'found a magical spring and gained power!',
                'coins': (75, 125),
                'exp': (50, 70)
            }
        ]
        
        event = random.choice(events)
        coins = random.randint(*event['coins'])
        exp = random.randint(*event['exp'])
        
        embed = discord.Embed(
            title=f"🗺️ {event['name']}",
            description=f"{name} {event['description']}",
            color=discord.Color.green()
        )
        
        # Update pet and user data
        pet['exp'] += exp
        user_data['coins'] += coins
        pet['last_adventure'] = datetime.datetime.utcnow().isoformat()
        
        # Level up check
        level_up = False
        while pet['exp'] >= 100 * pet['level']:
            pet['exp'] -= 100 * pet['level']
            pet['level'] += 1
            level_up = True
            
        self.save_data()
        
        embed.add_field(name="Coins Found", value=f"+{coins} coins", inline=True)
        embed.add_field(name="Experience Gained", value=f"+{exp} EXP", inline=True)
        
        if level_up:
            embed.add_field(
                name="Level Up!",
                value=f"{name} is now level {pet['level']}!",
                inline=False
            )
            
        await ctx.send(embed=embed)
    
    @commands.group(name="battle", invoke_without_command=True)
    async def battle_group(self, ctx):
        """Battle system commands.
        
        Engage in battles with other users or NPCs.
        
        Subcommands:
        ------------
        challenge - Challenge another user
        train - Train against an NPC
        stats - View battle statistics
        ranking - View battle rankings
        
        Examples:
        ---------
        !battle challenge @user
        !battle train
        !battle stats
        """
        await ctx.send_help(ctx.command)
    
    @battle_group.command(name="challenge")
    async def battle_challenge(self, ctx, opponent: discord.Member):
        """Challenge another user to a battle.
        
        Parameters:
        -----------
        opponent: The user to challenge
        
        Examples:
        ---------
        !battle challenge @user
        
        Notes:
        ------
        - Both users need weapons
        - Winner gets coins
        - Affects rankings
        """
        if opponent.bot:
            await ctx.send("You can't challenge bots!")
            return
            
        if opponent == ctx.author:
            await ctx.send("You can't challenge yourself!")
            return
            
        # Check if both users have required items
        challenger_data = self.get_user_data(ctx.author.id)
        opponent_data = self.get_user_data(opponent.id)
        
        if 'sword' not in challenger_data['inventory']:
            await ctx.send("You need a sword to battle!")
            return
            
        # Ask opponent to accept
        await ctx.send(f"{opponent.mention}, you've been challenged to a battle! React with ⚔️ to accept or ❌ to decline.")
        
        def check(reaction, user):
            return user == opponent and str(reaction.emoji) in ['⚔️', '❌']
            
        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            if str(reaction.emoji) == '⚔️':
                # Battle logic
                winner = random.choice([ctx.author, opponent])
                coins = random.randint(50, 150)
                
                winner_data = self.get_user_data(winner.id)
                winner_data['coins'] += coins
                winner_data['battles_won'] += 1
                self.save_data()
                
                embed = discord.Embed(
                    title="⚔️ Battle Results",
                    description=f"{winner.mention} wins {coins} coins!",
                    color=discord.Color.gold()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("Battle declined!")
        except asyncio.TimeoutError:
            await ctx.send("Battle challenge timed out!")
    
    @commands.group(name="shop", invoke_without_command=True)
    async def shop_group(self, ctx):
        """Shop and economy system commands.
        
        Buy and sell items using the bot's currency.
        
        Subcommands:
        ------------
        list - List available items
        buy - Buy an item
        sell - Sell an item
        inventory - View your inventory
        
        Examples:
        ---------
        !shop list
        !shop buy sword
        !shop sell potion
        """
        await ctx.send_help(ctx.command)
    
    @shop_group.command(name="list")
    async def shop_list(self, ctx, category: str = "all"):
        """List items available in the shop.
        
        Parameters:
        -----------
        category: Shop category (pet_shop/battle_shop/all)
        
        Examples:
        ---------
        !shop list
        !shop list pet_shop
        
        Notes:
        ------
        - Shows prices
        - Shows item descriptions
        - Categories have different items
        """
        embed = discord.Embed(
            title="🏪 Shop",
            color=discord.Color.blue()
        )
        
        if category == "all" or category == "pet_shop":
            embed.add_field(
                name="Pet Shop",
                value="\n".join(f"{item}: {price} coins" for item, price in self.shops['pet_shop'].items()),
                inline=False
            )
            
        if category == "all" or category == "battle_shop":
            embed.add_field(
                name="Battle Shop",
                value="\n".join(f"{item}: {price} coins" for item, price in self.shops['battle_shop'].items()),
                inline=False
            )
            
        await ctx.send(embed=embed)
    
    @commands.group(name="map", invoke_without_command=True)
    async def map_group(self, ctx):
        """Interactive map system commands.
        
        Explore different locations with unique features.
        
        Subcommands:
        ------------
        explore - Explore a location
        travel - Travel to a new location
        info - Get location information
        
        Examples:
        ---------
        !map explore
        !map travel forest
        !map info castle
        """
        await ctx.send_help(ctx.command)
    
    @map_group.command(name="explore")
    async def explore_location(self, ctx):
        """Explore your current location.
        
        Find items, coins, and encounter events.
        
        Examples:
        ---------
        !map explore
        
        Notes:
        ------
        - Random events
        - Find treasure
        - Meet NPCs
        """
        events = [
            "found a treasure chest with {coins} coins!",
            "discovered a mysterious cave...",
            "encountered a friendly merchant",
            "found a magical item!",
            "discovered a secret pathway"
        ]
        
        coins = random.randint(10, 50)
        event = random.choice(events).format(coins=coins)
        
        user_data = self.get_user_data(ctx.author.id)
        user_data['coins'] += coins
        self.save_data()
        
        embed = discord.Embed(
            title="🗺️ Exploration",
            description=f"You {event}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="daily")
    async def daily_reward(self, ctx):
        """Claim your daily reward.
        
        Get coins and items every 24 hours.
        
        Examples:
        ---------
        !daily
        
        Notes:
        ------
        - Once per day
        - Random rewards
        - Streak bonuses
        """
        user_data = self.get_user_data(ctx.author.id)
        
        # Check if reward is available
        if user_data['last_daily']:
            last_daily = datetime.datetime.fromisoformat(user_data['last_daily'])
            if datetime.datetime.utcnow() - last_daily < datetime.timedelta(days=1):
                time_left = datetime.timedelta(days=1) - (datetime.datetime.utcnow() - last_daily)
                await ctx.send(f"You can claim your next daily reward in {str(time_left).split('.')[0]}")
                return
                
        # Give reward
        coins = random.randint(100, 200)
        user_data['coins'] += coins
        user_data['last_daily'] = datetime.datetime.utcnow().isoformat()
        self.save_data()
        
        embed = discord.Embed(
            title="Daily Reward!",
            description=f"You received {coins} coins!",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)
    
    # Easter Eggs (these are secret commands that aren't shown in help)
    @commands.command(name="cookie", hidden=True)
    async def cookie(self, ctx):
        """🍪"""
        await ctx.send("Here's a cookie! 🍪")
    
    @commands.command(name="flip", hidden=True)
    async def flip(self, ctx):
        """(╯°□°）╯︵ ┻━┻"""
        flips = ["(╯°□°）╯︵ ┻━┻", "┬─┬ ノ( ゜-゜ノ)", "(ノಠ益ಠ)ノ彡┻━┻"]
        await ctx.send(random.choice(flips))
    
    @commands.command(name="hug", hidden=True)
    async def hug(self, ctx, user: discord.Member = None):
        """⊂(・﹏・⊂)"""
        if user:
            await ctx.send(f"{ctx.author.mention} hugs {user.mention} ⊂(・﹏・⊂)")
        else:
            await ctx.send("⊂(・﹏・⊂)")
    
    @commands.command(name="secret", hidden=True)
    async def secret(self, ctx):
        """Shhh... it's a secret!"""
        secrets = [
            "The cake is a lie!",
            "There are no easter eggs here...",
            "You found a secret! But what does it mean?",
            "42 is the answer, but what's the question?",
            "Behind you! ...just kidding"
        ]
        await ctx.send(random.choice(secrets))

    @commands.group(name="minigame", aliases=["mg"], invoke_without_command=True)
    async def minigame_group(self, ctx):
        """Play various minigames.
        
        Fun minigames to play alone or with friends.
        
        Subcommands:
        ------------
        wordchain - Word chain game
        trivia - Trivia game
        scramble - Word scramble
        memory - Memory card game
        math - Math challenge
        
        Examples:
        ---------
        !minigame wordchain
        !minigame trivia
        !mg scramble
        """
        await ctx.send_help(ctx.command)

    @minigame_group.command(name="wordchain")
    async def word_chain(self, ctx):
        """Play word chain game.
        
        Each player must say a word starting with the last letter of the previous word.
        
        Examples:
        ---------
        !minigame wordchain
        
        Notes:
        ------
        - 30 second time limit per turn
        - No word repetitions
        - English words only
        """
        await ctx.send("Word Chain Game! Say a word starting with any letter.")
        
        words_used = set()
        last_letter = None
        
        while True:
            try:
                def check(m):
                    return m.channel == ctx.channel and not m.author.bot
                
                msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                word = msg.content.lower()
                
                # Check if it's a valid word
                if last_letter and word[0] != last_letter:
                    await ctx.send(f"Word must start with '{last_letter}'! Game Over!")
                    break
                    
                if word in words_used:
                    await ctx.send(f"'{word}' has already been used! Game Over!")
                    break
                    
                words_used.add(word)
                last_letter = word[-1]
                await msg.add_reaction("✅")
                
            except asyncio.TimeoutError:
                await ctx.send("Time's up! Game Over!")
                break

    @minigame_group.command(name="scramble")
    async def word_scramble(self, ctx):
        """Play word scramble game.
        
        Unscramble the given word within the time limit.
        
        Examples:
        ---------
        !minigame scramble
        
        Notes:
        ------
        - 30 second time limit
        - Points based on word length
        - Multiple difficulty levels
        """
        words = {
            'easy': ['python', 'gaming', 'discord', 'server', 'emoji'],
            'medium': ['computer', 'keyboard', 'internet', 'software'],
            'hard': ['programming', 'developer', 'algorithm', 'database']
        }
        
        difficulty = random.choice(list(words.keys()))
        word = random.choice(words[difficulty])
        scrambled = ''.join(random.sample(word, len(word)))
        
        embed = discord.Embed(
            title="Word Scramble",
            description=f"Unscramble this word: **{scrambled}**\nDifficulty: {difficulty}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        
        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author
            
        try:
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
            
            if msg.content.lower() == word:
                points = len(word) * {'easy': 1, 'medium': 2, 'hard': 3}[difficulty]
                user_data = self.get_user_data(ctx.author.id)
                user_data['coins'] += points
                self.save_data()
                
                await ctx.send(f"🎉 Correct! You earned {points} coins!")
            else:
                await ctx.send(f"❌ Wrong! The word was: {word}")
                
        except asyncio.TimeoutError:
            await ctx.send(f"Time's up! The word was: {word}")

    @minigame_group.command(name="memory")
    async def memory_game(self, ctx):
        """Play memory card game.
        
        Match pairs of cards in this memory challenge.
        
        Examples:
        ---------
        !minigame memory
        
        Notes:
        ------
        - 60 second time limit
        - Points for matches
        - Multiple difficulty levels
        """
        emojis = ['🍎', '🍌', '🍇', '🍊', '🍐', '🍓', '🍒', '🥝', '🥑', '🥕']
        grid_size = 4
        cards = random.sample(emojis, (grid_size * grid_size) // 2) * 2
        random.shuffle(cards)
        
        # Create grid
        grid = []
        for i in range(0, len(cards), grid_size):
            grid.append(cards[i:i + grid_size])
            
        # Create display grid (hidden cards)
        display = [['❓' for _ in range(grid_size)] for _ in range(grid_size)]
        
        def display_grid():
            return '\n'.join([' '.join(row) for row in display])
            
        game_msg = await ctx.send(f"Memory Game! Match the pairs:\n{display_grid()}")
        
        matches = 0
        attempts = 0
        
        while matches < (grid_size * grid_size) // 2:
            # Get first card
            await ctx.send("Enter the position of first card (row col):")
            try:
                msg = await self.bot.wait_for('message', timeout=60.0, 
                                            check=lambda m: m.author == ctx.author)
                row1, col1 = map(int, msg.content.split())
                if not (0 <= row1 < grid_size and 0 <= col1 < grid_size):
                    await ctx.send("Invalid position!")
                    continue
                    
                # Show first card
                display[row1][col1] = grid[row1][col1]
                await game_msg.edit(content=f"Memory Game:\n{display_grid()}")
                
                # Get second card
                await ctx.send("Enter the position of second card (row col):")
                msg = await self.bot.wait_for('message', timeout=60.0,
                                            check=lambda m: m.author == ctx.author)
                row2, col2 = map(int, msg.content.split())
                if not (0 <= row2 < grid_size and 0 <= col2 < grid_size):
                    await ctx.send("Invalid position!")
                    display[row1][col1] = '❓'
                    continue
                    
                # Show second card
                display[row2][col2] = grid[row2][col2]
                await game_msg.edit(content=f"Memory Game:\n{display_grid()}")
                
                # Check if match
                if grid[row1][col1] == grid[row2][col2]:
                    matches += 1
                    await ctx.send("Match found! 🎉")
                else:
                    await asyncio.sleep(2)
                    display[row1][col1] = '❓'
                    display[row2][col2] = '❓'
                    await game_msg.edit(content=f"Memory Game:\n{display_grid()}")
                    
                attempts += 1
                
            except (asyncio.TimeoutError, ValueError, IndexError):
                await ctx.send("Game Over!")
                return
                
        # Game completed
        points = max(100 - (attempts - matches) * 10, 10)
        user_data = self.get_user_data(ctx.author.id)
        user_data['coins'] += points
        self.save_data()
        
        await ctx.send(f"🎉 Congratulations! You completed the game in {attempts} attempts and earned {points} coins!")

    @minigame_group.command(name="math")
    async def math_challenge(self, ctx, difficulty: str = "easy"):
        """Play math challenge game.
        
        Solve math problems within the time limit.
        
        Parameters:
        -----------
        difficulty: Game difficulty (easy/medium/hard)
        
        Examples:
        ---------
        !minigame math
        !minigame math hard
        
        Notes:
        ------
        - 20 second time limit
        - Points based on difficulty
        - Streak bonuses
        """
        difficulties = {
            'easy': (1, 10, ['+', '-']),
            'medium': (1, 20, ['+', '-', '*']),
            'hard': (1, 50, ['+', '-', '*', '/'])
        }
        
        if difficulty not in difficulties:
            await ctx.send("Invalid difficulty! Choose: easy, medium, or hard")
            return
            
        min_num, max_num, operators = difficulties[difficulty]
        score = 0
        rounds = 5
        
        for round_num in range(1, rounds + 1):
            # Generate problem
            num1 = random.randint(min_num, max_num)
            num2 = random.randint(min_num, max_num)
            operator = random.choice(operators)
            
            # Calculate answer
            if operator == '+':
                answer = num1 + num2
            elif operator == '-':
                answer = num1 - num2
            elif operator == '*':
                answer = num1 * num2
            else:  # Division
                num1 = num2 * random.randint(1, 10)  # Ensure clean division
                answer = num1 // num2
                
            # Show problem
            await ctx.send(f"Round {round_num}/{rounds}: What is {num1} {operator} {num2}?")
            
            try:
                msg = await self.bot.wait_for('message', timeout=20.0,
                                            check=lambda m: m.author == ctx.author)
                
                if int(msg.content) == answer:
                    points = {'easy': 10, 'medium': 20, 'hard': 30}[difficulty]
                    score += points
                    await ctx.send(f"Correct! +{points} points")
                else:
                    await ctx.send(f"Wrong! The answer was {answer}")
                    
            except (asyncio.TimeoutError, ValueError):
                await ctx.send(f"Time's up! The answer was {answer}")
                
        # Award coins based on score
        user_data = self.get_user_data(ctx.author.id)
        user_data['coins'] += score
        self.save_data()
        
        await ctx.send(f"Game Over! Final score: {score} points\nYou earned {score} coins!")

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(FunCommands(bot)) 