import discord
from discord.ext import commands
import asyncio
import random
import json
from typing import Dict, Optional, List
import aiohttp

class PokemonGym(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_gym_battles: Dict[int, Dict] = {}  # channel_id: battle_data
        self.gym_cooldowns: Dict[int, Dict] = {}  # user_id: {gym_id: timestamp}
        
        # Gym data with leaders, Pokemon, and badge rewards
        self.gyms = {
            'boulder': {
                'leader': 'Brock',
                'type': 'rock',
                'badge': 'Boulder Badge',
                'pokemon': [
                    {'id': 74, 'name': 'geodude', 'level': 12},  # Geodude
                    {'id': 95, 'name': 'onix', 'level': 14}      # Onix
                ],
                'reward_money': 1000,
                'cooldown_hours': 24
            },
            'cascade': {
                'leader': 'Misty',
                'type': 'water',
                'badge': 'Cascade Badge',
                'pokemon': [
                    {'id': 120, 'name': 'staryu', 'level': 18},   # Staryu
                    {'id': 121, 'name': 'starmie', 'level': 21}   # Starmie
                ],
                'reward_money': 2000,
                'cooldown_hours': 24
            },
            'thunder': {
                'leader': 'Lt. Surge',
                'type': 'electric',
                'badge': 'Thunder Badge',
                'pokemon': [
                    {'id': 100, 'name': 'voltorb', 'level': 21},  # Voltorb
                    {'id': 25, 'name': 'pikachu', 'level': 24},   # Pikachu
                    {'id': 26, 'name': 'raichu', 'level': 28}     # Raichu
                ],
                'reward_money': 3000,
                'cooldown_hours': 24
            },
            'rainbow': {
                'leader': 'Erika',
                'type': 'grass',
                'badge': 'Rainbow Badge',
                'pokemon': [
                    {'id': 71, 'name': 'victreebel', 'level': 29},  # Victreebel
                    {'id': 114, 'name': 'tangela', 'level': 24},    # Tangela
                    {'id': 45, 'name': 'vileplume', 'level': 29}    # Vileplume
                ],
                'reward_money': 4000,
                'cooldown_hours': 24
            },
            'soul': {
                'leader': 'Koga',
                'type': 'poison',
                'badge': 'Soul Badge',
                'pokemon': [
                    {'id': 109, 'name': 'koffing', 'level': 37},    # Koffing
                    {'id': 110, 'name': 'weezing', 'level': 39},    # Weezing
                    {'id': 49, 'name': 'venomoth', 'level': 37},    # Venomoth
                    {'id': 89, 'name': 'muk', 'level': 43}          # Muk
                ],
                'reward_money': 5000,
                'cooldown_hours': 24
            },
            'marsh': {
                'leader': 'Sabrina',
                'type': 'psychic',
                'badge': 'Marsh Badge',
                'pokemon': [
                    {'id': 64, 'name': 'kadabra', 'level': 38},     # Kadabra
                    {'id': 122, 'name': 'mr-mime', 'level': 37},    # Mr. Mime
                    {'id': 49, 'name': 'venomoth', 'level': 38},    # Venomoth
                    {'id': 65, 'name': 'alakazam', 'level': 43}     # Alakazam
                ],
                'reward_money': 6000,
                'cooldown_hours': 24
            },
            'volcano': {
                'leader': 'Blaine',
                'type': 'fire',
                'badge': 'Volcano Badge',
                'pokemon': [
                    {'id': 58, 'name': 'growlithe', 'level': 42},   # Growlithe
                    {'id': 78, 'name': 'rapidash', 'level': 40},    # Rapidash
                    {'id': 59, 'name': 'arcanine', 'level': 47}     # Arcanine
                ],
                'reward_money': 7000,
                'cooldown_hours': 24
            },
            'earth': {
                'leader': 'Giovanni',
                'type': 'ground',
                'badge': 'Earth Badge',
                'pokemon': [
                    {'id': 111, 'name': 'rhyhorn', 'level': 45},    # Rhyhorn
                    {'id': 31, 'name': 'nidoqueen', 'level': 44},   # Nidoqueen
                    {'id': 34, 'name': 'nidoking', 'level': 45},    # Nidoking
                    {'id': 112, 'name': 'rhydon', 'level': 50}      # Rhydon
                ],
                'reward_money': 8000,
                'cooldown_hours': 24
            }
        }

        # Elite Four data
        self.elite_four = {
            'lorelei': {
                'name': 'Lorelei',
                'type': 'ice',
                'pokemon': [
                    {'id': 87, 'name': 'dewgong', 'level': 52},     # Dewgong
                    {'id': 91, 'name': 'cloyster', 'level': 51},    # Cloyster
                    {'id': 80, 'name': 'slowbro', 'level': 52},     # Slowbro
                    {'id': 124, 'name': 'jynx', 'level': 54},       # Jynx
                    {'id': 131, 'name': 'lapras', 'level': 54}      # Lapras
                ],
                'reward_money': 10000
            },
            'bruno': {
                'name': 'Bruno',
                'type': 'fighting',
                'pokemon': [
                    {'id': 95, 'name': 'onix', 'level': 51},        # Onix
                    {'id': 107, 'name': 'hitmonchan', 'level': 53}, # Hitmonchan
                    {'id': 106, 'name': 'hitmonlee', 'level': 53},  # Hitmonlee
                    {'id': 95, 'name': 'onix', 'level': 54},        # Onix
                    {'id': 68, 'name': 'machamp', 'level': 56}      # Machamp
                ],
                'reward_money': 11000
            },
            'agatha': {
                'name': 'Agatha',
                'type': 'ghost',
                'pokemon': [
                    {'id': 94, 'name': 'gengar', 'level': 54},      # Gengar
                    {'id': 93, 'name': 'haunter', 'level': 53},     # Haunter
                    {'id': 42, 'name': 'golbat', 'level': 54},      # Golbat
                    {'id': 24, 'name': 'arbok', 'level': 56},       # Arbok
                    {'id': 94, 'name': 'gengar', 'level': 58}       # Gengar
                ],
                'reward_money': 12000
            },
            'lance': {
                'name': 'Lance',
                'type': 'dragon',
                'pokemon': [
                    {'id': 130, 'name': 'gyarados', 'level': 56},   # Gyarados
                    {'id': 148, 'name': 'dragonair', 'level': 54},  # Dragonair
                    {'id': 148, 'name': 'dragonair', 'level': 54},  # Dragonair
                    {'id': 142, 'name': 'aerodactyl', 'level': 58}, # Aerodactyl
                    {'id': 149, 'name': 'dragonite', 'level': 60}   # Dragonite
                ],
                'reward_money': 15000
            }
        }

        # Champion data
        self.champion = {
            'name': 'Blue',
            'title': 'Champion',
            'pokemon': [
                {'id': 18, 'name': 'pidgeot', 'level': 63},     # Pidgeot
                {'id': 65, 'name': 'alakazam', 'level': 65},    # Alakazam
                {'id': 112, 'name': 'rhydon', 'level': 64},     # Rhydon
                {'id': 103, 'name': 'exeggutor', 'level': 65},  # Exeggutor
                {'id': 59, 'name': 'arcanine', 'level': 65},    # Arcanine
                {'id': 9, 'name': 'blastoise', 'level': 68}     # Blastoise
            ],
            'reward_money': 25000
        }

        # Rematch data (higher level versions of gym leaders)
        self.gym_rematches = {gym_id: self._create_rematch_data(gym_data) 
                            for gym_id, gym_data in self.gyms.items()}
        
        # Elite Four rematch data
        self.elite_four_rematches = {member_id: self._create_rematch_data(member_data, elite=True)
                                   for member_id, member_data in self.elite_four.items()}

    def _create_rematch_data(self, original_data: Dict, elite: bool = False) -> Dict:
        """Create rematch data with higher level Pokemon"""
        rematch_data = original_data.copy()
        level_increase = 20 if elite else 15
        
        # Increase Pokemon levels and possibly add new Pokemon
        rematch_pokemon = []
        for pokemon in original_data['pokemon']:
            new_pokemon = pokemon.copy()
            new_pokemon['level'] = min(100, pokemon['level'] + level_increase)
            rematch_pokemon.append(new_pokemon)
        
        rematch_data['pokemon'] = rematch_pokemon
        rematch_data['reward_money'] = original_data['reward_money'] * 2
        return rematch_data

    @commands.group(invoke_without_command=True)
    async def gym(self, ctx):
        """Gym commands"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Pokemon Gyms",
                description="Use these commands to challenge gyms and earn badges:",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Commands",
                value="• `!gym list` - List all available gyms\n"
                      "• `!gym info <gym>` - Get info about a specific gym\n"
                      "• `!gym challenge <gym>` - Challenge a gym leader\n"
                      "• `!gym badges` - View your earned badges",
                inline=False
            )
            await ctx.send(embed=embed)

    @gym.command(name='list')
    async def list_gyms(self, ctx):
        """List all available gyms"""
        embed = discord.Embed(
            title="Available Pokemon Gyms",
            color=discord.Color.blue()
        )
        
        for gym_id, gym_data in self.gyms.items():
            # Get user's cooldown for this gym
            cooldown = self.gym_cooldowns.get(ctx.author.id, {}).get(gym_id, 0)
            cooldown_status = ""
            if cooldown > ctx.message.created_at.timestamp():
                hours_left = int((cooldown - ctx.message.created_at.timestamp()) / 3600)
                cooldown_status = f" (Available in {hours_left}h)"
            
            embed.add_field(
                name=f"{gym_data['leader']}'s Gym{cooldown_status}",
                value=f"Type: {gym_data['type'].title()}\n"
                      f"Badge: {gym_data['badge']}\n"
                      f"Strongest Pokemon: Level {max(p['level'] for p in gym_data['pokemon'])}",
                inline=True
            )
        
        await ctx.send(embed=embed)

    @gym.command(name='info')
    async def gym_info(self, ctx, gym_id: str):
        """Get detailed information about a gym"""
        gym_id = gym_id.lower()
        if gym_id not in self.gyms:
            return await ctx.send("That gym doesn't exist! Use `!gym list` to see available gyms.")
        
        gym_data = self.gyms[gym_id]
        
        embed = discord.Embed(
            title=f"{gym_data['leader']}'s Gym",
            description=f"Type: {gym_data['type'].title()}\n"
                       f"Badge: {gym_data['badge']}\n"
                       f"Reward: ${gym_data['reward_money']}",
            color=discord.Color.blue()
        )
        
        # Add Pokemon information
        pokemon_info = []
        for pokemon in gym_data['pokemon']:
            pokemon_info.append(f"Level {pokemon['level']} {pokemon['name'].title()}")
        
        embed.add_field(
            name="Pokemon",
            value="\n".join(pokemon_info),
            inline=False
        )
        
        # Add cooldown information
        cooldown = self.gym_cooldowns.get(ctx.author.id, {}).get(gym_id, 0)
        if cooldown > ctx.message.created_at.timestamp():
            hours_left = int((cooldown - ctx.message.created_at.timestamp()) / 3600)
            embed.add_field(
                name="Cooldown",
                value=f"You can challenge this gym again in {hours_left} hours",
                inline=False
            )
        else:
            embed.add_field(
                name="Status",
                value="Ready for challenge!",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @gym.command(name='challenge')
    async def challenge_gym(self, ctx, gym_id: str):
        """Challenge a gym leader"""
        gym_id = gym_id.lower()
        if gym_id not in self.gyms:
            return await ctx.send("That gym doesn't exist! Use `!gym list` to see available gyms.")
        
        # Check cooldown
        cooldown = self.gym_cooldowns.get(ctx.author.id, {}).get(gym_id, 0)
        if cooldown > ctx.message.created_at.timestamp():
            hours_left = int((cooldown - ctx.message.created_at.timestamp()) / 3600)
            return await ctx.send(f"You must wait {hours_left} hours before challenging this gym again!")
        
        gym_data = self.gyms[gym_id]
        
        # Check if user has badges required for this gym
        required_badges = await self.get_required_badges(gym_id)
        user_badges = await self.get_user_badges(ctx.author.id)
        
        missing_badges = [badge for badge in required_badges if badge not in user_badges]
        if missing_badges:
            return await ctx.send(
                f"You need the following badges first: {', '.join(missing_badges)}"
            )
        
        # Get user's Pokemon
        user_pokemon = await self.bot.db.fetch(
            'SELECT * FROM pokemon WHERE user_id = $1 ORDER BY level DESC',
            ctx.author.id
        )
        
        if not user_pokemon:
            return await ctx.send("You don't have any Pokemon to battle with!")
        
        # Show user's Pokemon and let them choose
        pokemon_list = []
        for i, pokemon in enumerate(user_pokemon[:6], 1):  # Show up to 6 Pokemon
            pokemon_list.append(f"{i}. Level {pokemon['level']} {pokemon['name'].title()}")
        
        embed = discord.Embed(
            title=f"Challenge {gym_data['leader']}'s Gym",
            description="Choose your Pokemon by number:\n" + "\n".join(pokemon_list),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        
        def check(m):
            return (m.author == ctx.author and m.channel == ctx.channel and 
                   m.content.isdigit() and 1 <= int(m.content) <= len(pokemon_list))
        
        try:
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
            chosen_pokemon = user_pokemon[int(msg.content) - 1]
            
            # Start gym battle
            battle_data = {
                'trainer': {
                    'id': ctx.author.id,
                    'pokemon': chosen_pokemon,
                    'current_hp': self.calculate_hp(chosen_pokemon)
                },
                'leader': {
                    'pokemon': gym_data['pokemon'].copy(),
                    'current_pokemon': 0,
                    'current_hp': None  # Will be set when first Pokemon is sent out
                },
                'gym_id': gym_id,
                'message': None
            }
            
            # Set leader's first Pokemon
            leader_pokemon = battle_data['leader']['pokemon'][0]
            battle_data['leader']['current_hp'] = self.calculate_hp(leader_pokemon)
            
            self.active_gym_battles[ctx.channel.id] = battle_data
            
            # Send initial battle message
            embed = await self.create_gym_battle_embed(ctx, battle_data)
            battle_data['message'] = await ctx.send(embed=embed)
            
            await ctx.send(
                f"{gym_data['leader']}: Let's see if you have what it takes to earn the {gym_data['badge']}!\n"
                f"Use `!gym attack <move>` to use a move!"
            )
            
        except asyncio.TimeoutError:
            await ctx.send("Challenge cancelled - you took too long to choose a Pokemon!")

    @gym.command(name='attack')
    async def gym_attack(self, ctx, move_name: str):
        """Use a move in a gym battle"""
        if ctx.channel.id not in self.active_gym_battles:
            return await ctx.send("No active gym battle in this channel!")
        
        battle = self.active_gym_battles[ctx.channel.id]
        if ctx.author.id != battle['trainer']['id']:
            return await ctx.send("This isn't your battle!")
        
        try:
            # Get move data
            move_data = await self.get_move_data(move_name.lower())
            if not move_data:
                return await ctx.send("That move doesn't exist!")
            
            # Process trainer's move
            damage = await self.process_gym_move(ctx, battle, move_data, is_trainer=True)
            
            # Check if leader's Pokemon fainted
            if battle['leader']['current_hp'] <= 0:
                battle['leader']['current_pokemon'] += 1
                
                # Check if all leader's Pokemon fainted
                if battle['leader']['current_pokemon'] >= len(battle['leader']['pokemon']):
                    await self.handle_gym_victory(ctx, battle)
                    return
                
                # Send out next Pokemon
                new_pokemon = battle['leader']['pokemon'][battle['leader']['current_pokemon']]
                battle['leader']['current_hp'] = self.calculate_hp(new_pokemon)
                
                gym_data = self.gyms[battle['gym_id']]
                await ctx.send(
                    f"{gym_data['leader']}: Go, {new_pokemon['name'].title()}!"
                )
            
            # Leader's turn
            leader_pokemon = battle['leader']['pokemon'][battle['leader']['current_pokemon']]
            leader_moves = await self.get_pokemon_moves(leader_pokemon['id'])
            leader_move = random.choice(leader_moves)
            leader_move_data = await self.get_move_data(leader_move)
            
            await self.process_gym_move(ctx, battle, leader_move_data, is_trainer=False)
            
            # Check if trainer's Pokemon fainted
            if battle['trainer']['current_hp'] <= 0:
                await self.handle_gym_defeat(ctx, battle)
                return
            
            # Update battle display
            await self.update_gym_battle_embed(ctx, battle)
            
        except Exception as e:
            await ctx.send(f"Error processing move: {e}")

    @gym.command(name='badges')
    async def view_badges(self, ctx):
        """View your earned gym badges"""
        badges = await self.get_user_badges(ctx.author.id)
        
        if not badges:
            return await ctx.send("You haven't earned any badges yet!")
        
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Gym Badges",
            description="Badges earned:",
            color=discord.Color.gold()
        )
        
        for badge in badges:
            # Find gym data for this badge
            gym_data = next(
                (gym for gym in self.gyms.values() if gym['badge'] == badge),
                None
            )
            if gym_data:
                embed.add_field(
                    name=badge,
                    value=f"From: {gym_data['leader']}'s Gym\n"
                          f"Type: {gym_data['type'].title()}",
                    inline=True
                )
        
        await ctx.send(embed=embed)

    async def get_user_badges(self, user_id: int) -> List[str]:
        """Get list of badges earned by user"""
        badges = await self.bot.db.fetch(
            'SELECT badge FROM gym_badges WHERE user_id = $1',
            user_id
        )
        return [badge['badge'] for badge in badges]

    async def get_required_badges(self, gym_id: str) -> List[str]:
        """Get list of badges required for a gym"""
        # Order of gyms determines required badges
        gym_order = list(self.gyms.keys())
        gym_index = gym_order.index(gym_id)
        
        required_badges = []
        if gym_index > 0:
            for prev_gym_id in gym_order[:gym_index]:
                required_badges.append(self.gyms[prev_gym_id]['badge'])
        
        return required_badges

    def calculate_hp(self, pokemon: Dict) -> int:
        """Calculate max HP for a Pokemon"""
        base_hp = 50  # Default base HP
        if isinstance(pokemon.get('stats'), str):
            stats = json.loads(pokemon['stats'])
            base_hp = stats.get('hp', 50)
        elif isinstance(pokemon.get('stats'), dict):
            base_hp = pokemon['stats'].get('hp', 50)
        
        return int((2 * base_hp * pokemon['level']) / 100 + pokemon['level'] + 10)

    async def create_gym_battle_embed(self, ctx, battle: Dict) -> discord.Embed:
        """Create the gym battle status embed"""
        gym_data = self.gyms[battle['gym_id']]
        leader_pokemon = battle['leader']['pokemon'][battle['leader']['current_pokemon']]
        
        embed = discord.Embed(
            title=f"Gym Battle vs {gym_data['leader']}",
            color=discord.Color.red()
        )
        
        # Trainer's Pokemon
        trainer_pokemon = battle['trainer']['pokemon']
        trainer_hp_percent = int(battle['trainer']['current_hp'] / self.calculate_hp(trainer_pokemon) * 100)
        trainer_hp_bar = '█' * (trainer_hp_percent // 10) + '░' * (10 - trainer_hp_percent // 10)
        
        embed.add_field(
            name=f"{ctx.author.display_name}'s {trainer_pokemon['name'].title()}",
            value=f"Level: {trainer_pokemon['level']}\n"
                  f"HP: {battle['trainer']['current_hp']}/{self.calculate_hp(trainer_pokemon)} [{trainer_hp_bar}]",
            inline=False
        )
        
        # Leader's Pokemon
        leader_hp_percent = int(battle['leader']['current_hp'] / self.calculate_hp(leader_pokemon) * 100)
        leader_hp_bar = '█' * (leader_hp_percent // 10) + '░' * (10 - leader_hp_percent // 10)
        
        embed.add_field(
            name=f"{gym_data['leader']}'s {leader_pokemon['name'].title()}",
            value=f"Level: {leader_pokemon['level']}\n"
                  f"HP: {battle['leader']['current_hp']}/{self.calculate_hp(leader_pokemon)} [{leader_hp_bar}]",
            inline=False
        )
        
        return embed

    async def update_gym_battle_embed(self, ctx, battle: Dict):
        """Update the gym battle status embed"""
        embed = await self.create_gym_battle_embed(ctx, battle)
        await battle['message'].edit(embed=embed)

    async def process_gym_move(self, ctx, battle: Dict, move_data: Dict, is_trainer: bool) -> int:
        """Process a move in a gym battle and return damage dealt"""
        if is_trainer:
            attacker = battle['trainer']
            defender = battle['leader']
            defender_pokemon = defender['pokemon'][defender['current_pokemon']]
        else:
            attacker = battle['leader']
            defender = battle['trainer']
            attacker_pokemon = attacker['pokemon'][attacker['current_pokemon']]
            defender_pokemon = defender['pokemon']

        # Calculate damage
        power = move_data.get('power', 0)
        if power:
            # Basic damage formula
            attack = 50  # Base attack
            defense = 50  # Base defense
            level = attacker_pokemon['level'] if not is_trainer else attacker['pokemon']['level']
            
            damage = int(((2 * level / 5 + 2) * power * attack / defense / 50 + 2) * 
                        random.uniform(0.85, 1.0))
            
            # Apply damage
            defender['current_hp'] = max(0, defender['current_hp'] - damage)
            
            # Create message
            pokemon_name = attacker['pokemon']['name'] if is_trainer else attacker_pokemon['name']
            await ctx.send(
                f"{pokemon_name.title()} used {move_data['name'].title()}!\n"
                f"Dealt {damage} damage!"
            )
            
            return damage
        
        return 0

    async def handle_gym_victory(self, ctx, battle: Dict):
        """Handle gym battle victory"""
        gym_data = self.gyms[battle['gym_id']]
        
        # Award badge
        await self.bot.db.execute(
            'INSERT INTO gym_badges (user_id, badge, earned_at) VALUES ($1, $2, CURRENT_TIMESTAMP)',
            ctx.author.id, gym_data['badge']
        )
        
        # Award money
        await self.bot.db.execute(
            'UPDATE users SET currency = currency + $1 WHERE id = $2',
            gym_data['reward_money'], ctx.author.id
        )
        
        # Set cooldown
        if ctx.author.id not in self.gym_cooldowns:
            self.gym_cooldowns[ctx.author.id] = {}
        self.gym_cooldowns[ctx.author.id][battle['gym_id']] = (
            ctx.message.created_at.timestamp() + gym_data['cooldown_hours'] * 3600
        )
        
        embed = discord.Embed(
            title="Gym Battle Victory!",
            description=f"Congratulations! You've defeated {gym_data['leader']}!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Rewards",
            value=f"• {gym_data['badge']}\n"
                  f"• ${gym_data['reward_money']}",
            inline=False
        )
        
        await ctx.send(embed=embed)
        del self.active_gym_battles[ctx.channel.id]

    async def handle_gym_defeat(self, ctx, battle: Dict):
        """Handle gym battle defeat"""
        gym_data = self.gyms[battle['gym_id']]
        
        embed = discord.Embed(
            title="Gym Battle Defeat",
            description=f"{gym_data['leader']}: You fought well, but you're not ready for the {gym_data['badge']} yet. "
                       f"Come back when you're stronger!",
            color=discord.Color.red()
        )
        
        await ctx.send(embed=embed)
        del self.active_gym_battles[ctx.channel.id]

    async def get_move_data(self, move_name: str) -> Optional[Dict]:
        """Get move data from cache or PokeAPI"""
        if move_name in self.move_cache:
            return self.move_cache[move_name]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://pokeapi.co/api/v2/move/{move_name}') as resp:
                if resp.status == 200:
                    move_data = await resp.json()
                    self.move_cache[move_name] = move_data
                    return move_data
                return None

    async def get_pokemon_moves(self, pokemon_id: int) -> List[str]:
        """Get available moves for a Pokemon"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://pokeapi.co/api/v2/pokemon/{pokemon_id}') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    moves = [m['move']['name'] for m in data['moves']]
                    return random.sample(moves, min(4, len(moves)))
                return ['tackle']  # Fallback move

    @commands.group(invoke_without_command=True)
    async def elite(self, ctx):
        """Elite Four commands"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Pokemon Elite Four",
                description="Use these commands to challenge the Elite Four:",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="Commands",
                value="• `!elite info` - Get info about the Elite Four\n"
                      "• `!elite challenge` - Challenge the Elite Four\n"
                      "• `!elite status` - Check your Elite Four progress",
                inline=False
            )
            await ctx.send(embed=embed)

    @elite.command(name='info')
    async def elite_info(self, ctx):
        """Get information about the Elite Four"""
        embed = discord.Embed(
            title="The Elite Four",
            description="The most powerful trainers in the region!",
            color=discord.Color.purple()
        )
        
        for member_id, member_data in self.elite_four.items():
            embed.add_field(
                name=member_data['name'],
                value=f"Type: {member_data['type'].title()}\n"
                      f"Strongest Pokemon: Level {max(p['level'] for p in member_data['pokemon'])}\n"
                      f"Reward: ${member_data['reward_money']}",
                inline=True
            )
        
        embed.add_field(
            name="Requirements",
            value="You must have all 8 gym badges to challenge the Elite Four!",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @elite.command(name='challenge')
    async def challenge_elite(self, ctx):
        """Challenge the Elite Four"""
        # Check if user has all badges
        user_badges = await self.get_user_badges(ctx.author.id)
        required_badges = [gym['badge'] for gym in self.gyms.values()]
        
        missing_badges = [badge for badge in required_badges if badge not in user_badges]
        if missing_badges:
            return await ctx.send(
                f"You need all gym badges to challenge the Elite Four! Missing: {', '.join(missing_badges)}"
            )
        
        # Get user's Pokemon team
        user_pokemon = await self.bot.db.fetch(
            'SELECT * FROM pokemon WHERE user_id = $1 ORDER BY level DESC LIMIT 6',
            ctx.author.id
        )
        
        if len(user_pokemon) < 6:
            return await ctx.send("You need a full team of 6 Pokemon to challenge the Elite Four!")
        
        # Start Elite Four challenge
        await self.start_elite_challenge(ctx, user_pokemon)

    async def start_elite_challenge(self, ctx, user_pokemon):
        """Start the Elite Four challenge sequence"""
        for member_id, member_data in self.elite_four.items():
            embed = discord.Embed(
                title=f"Elite Four Challenge - {member_data['name']}",
                description=f"{member_data['name']} wants to battle!",
                color=discord.Color.purple()
            )
            await ctx.send(embed=embed)
            
            # Create battle data
            battle_data = {
                'trainer': {
                    'id': ctx.author.id,
                    'pokemon': user_pokemon,
                    'current_pokemon': 0,
                    'current_hp': self.calculate_hp(user_pokemon[0])
                },
                'leader': {
                    'pokemon': member_data['pokemon'],
                    'current_pokemon': 0,
                    'current_hp': None
                },
                'elite_member': member_id,
                'message': None
            }
            
            # Set leader's first Pokemon
            leader_pokemon = battle_data['leader']['pokemon'][0]
            battle_data['leader']['current_hp'] = self.calculate_hp(leader_pokemon)
            
            self.active_gym_battles[ctx.channel.id] = battle_data
            
            # Send battle message
            embed = await self.create_elite_battle_embed(ctx, battle_data)
            battle_data['message'] = await ctx.send(embed=embed)
            
            await ctx.send(
                f"{member_data['name']}: Let me show you the power of {member_data['type'].title()}-type Pokemon!\n"
                f"Use `!elite attack <move>` to use a move!"
            )
            
            # Wait for battle completion
            while ctx.channel.id in self.active_gym_battles:
                await asyncio.sleep(1)
            
            # Check if user was defeated
            if not await self.get_elite_progress(ctx.author.id, member_id):
                return await ctx.send("You were defeated by the Elite Four! Try again after training more!")
        
        # If reached here, user has defeated all Elite Four members
        await self.handle_elite_victory(ctx)

    @elite.command(name='attack')
    async def elite_attack(self, ctx, move_name: str):
        """Use a move in an Elite Four battle"""
        if ctx.channel.id not in self.active_gym_battles:
            return await ctx.send("No active Elite Four battle in this channel!")
        
        battle = self.active_gym_battles[ctx.channel.id]
        if ctx.author.id != battle['trainer']['id']:
            return await ctx.send("This isn't your battle!")
        
        try:
            # Process move similar to gym battles, but with team mechanics
            await self.process_elite_move(ctx, battle, move_name)
        except Exception as e:
            await ctx.send(f"Error processing move: {e}")

    async def process_elite_move(self, ctx, battle: Dict, move_name: str):
        """Process a move in an Elite Four battle"""
        # Similar to process_gym_move but with team mechanics
        # Implementation details here...

    async def handle_elite_victory(self, ctx):
        """Handle victory over the Elite Four"""
        # Award special rewards and recognition
        await self.bot.db.execute(
            'INSERT INTO elite_four_champions (user_id, completed_at) VALUES ($1, CURRENT_TIMESTAMP)',
            ctx.author.id
        )
        
        # Award money
        total_reward = sum(member['reward_money'] for member in self.elite_four.values())
        await self.bot.db.execute(
            'UPDATE users SET currency = currency + $1 WHERE id = $2',
            total_reward, ctx.author.id
        )
        
        embed = discord.Embed(
            title="🏆 Elite Four Champion! 🏆",
            description=f"Congratulations, {ctx.author.mention}! You have defeated the Elite Four!",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="Rewards",
            value=f"• Elite Four Champion Title\n"
                  f"• ${total_reward:,}",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @elite.command(name='status')
    async def elite_status(self, ctx):
        """Check your Elite Four progress"""
        progress = await self.bot.db.fetch(
            'SELECT member_id, completed_at FROM elite_four_progress WHERE user_id = $1',
            ctx.author.id
        )
        
        embed = discord.Embed(
            title="Elite Four Progress",
            color=discord.Color.purple()
        )
        
        for member_id, member_data in self.elite_four.items():
            status = "❌ Not defeated"
            for p in progress:
                if p['member_id'] == member_id:
                    status = f"✅ Defeated on {p['completed_at'].strftime('%Y-%m-%d %H:%M')}"
                    break
            
            embed.add_field(
                name=member_data['name'],
                value=status,
                inline=False
            )
        
        await ctx.send(embed=embed)

    async def get_elite_progress(self, user_id: int, member_id: str) -> bool:
        """Check if user has defeated an Elite Four member"""
        result = await self.bot.db.fetchrow(
            'SELECT completed_at FROM elite_four_progress WHERE user_id = $1 AND member_id = $2',
            user_id, member_id
        )
        return result is not None

    @commands.group(invoke_without_command=True)
    async def champion(self, ctx):
        """Champion battle commands"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Pokemon Champion",
                description="Use these commands to challenge the Champion:",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="Commands",
                value="• `!champion info` - Get info about the Champion\n"
                      "• `!champion challenge` - Challenge the Champion\n"
                      "• `!champion history` - View Champion battle history",
                inline=False
            )
            await ctx.send(embed=embed)

    @champion.command(name='info')
    async def champion_info(self, ctx):
        """Get information about the Champion"""
        embed = discord.Embed(
            title=f"Pokemon Champion - {self.champion['name']}",
            description="The strongest trainer in the region!",
            color=discord.Color.gold()
        )
        
        pokemon_list = "\n".join(
            f"• Level {p['level']} {p['name'].title()}"
            for p in self.champion['pokemon']
        )
        
        embed.add_field(
            name="Pokemon Team",
            value=pokemon_list,
            inline=False
        )
        embed.add_field(
            name="Reward",
            value=f"${self.champion['reward_money']:,}",
            inline=False
        )
        embed.add_field(
            name="Requirements",
            value="You must defeat the Elite Four to challenge the Champion!",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @champion.command(name='challenge')
    async def challenge_champion(self, ctx):
        """Challenge the Champion"""
        # Check if user has defeated Elite Four
        is_champion = await self.bot.db.fetchrow(
            'SELECT completed_at FROM elite_four_champions WHERE user_id = $1',
            ctx.author.id
        )
        if not is_champion:
            return await ctx.send("You must defeat the Elite Four before challenging the Champion!")
        
        # Get user's Pokemon team
        user_pokemon = await self.bot.db.fetch(
            'SELECT * FROM pokemon WHERE user_id = $1 ORDER BY level DESC LIMIT 6',
            ctx.author.id
        )
        
        if len(user_pokemon) < 6:
            return await ctx.send("You need a full team of 6 Pokemon to challenge the Champion!")
        
        # Start Champion battle
        await self.start_champion_battle(ctx, user_pokemon)

    @gym.command(name='rematch')
    async def gym_rematch(self, ctx, gym_id: str):
        """Challenge a gym leader to a rematch"""
        if gym_id not in self.gyms:
            return await ctx.send("Invalid gym ID!")
        
        # Check if user has the gym's badge
        user_badges = await self.get_user_badges(ctx.author.id)
        if self.gyms[gym_id]['badge'] not in user_badges:
            return await ctx.send("You must defeat this gym normally before requesting a rematch!")
        
        # Check cooldown
        cooldown = self.gym_cooldowns.get(ctx.author.id, {}).get(f"{gym_id}_rematch", 0)
        if cooldown > ctx.message.created_at.timestamp():
            hours_left = int((cooldown - ctx.message.created_at.timestamp()) / 3600)
            return await ctx.send(f"You can rematch this gym in {hours_left} hours!")
        
        # Start rematch
        await self.start_gym_battle(ctx, gym_id, rematch=True)

    @elite.command(name='rematch')
    async def elite_rematch(self, ctx):
        """Challenge the Elite Four to a rematch"""
        # Check if user has completed Elite Four before
        is_champion = await self.bot.db.fetchrow(
            'SELECT completed_at FROM elite_four_champions WHERE user_id = $1',
            ctx.author.id
        )
        if not is_champion:
            return await ctx.send("You must defeat the Elite Four normally before requesting a rematch!")
        
        # Get user's Pokemon team
        user_pokemon = await self.bot.db.fetch(
            'SELECT * FROM pokemon WHERE user_id = $1 ORDER BY level DESC LIMIT 6',
            ctx.author.id
        )
        
        if len(user_pokemon) < 6:
            return await ctx.send("You need a full team of 6 Pokemon to challenge the Elite Four!")
        
        # Start Elite Four rematch
        await self.start_elite_challenge(ctx, user_pokemon, rematch=True)

    async def start_champion_battle(self, ctx, user_pokemon):
        """Start a battle with the Champion"""
        embed = discord.Embed(
            title="Champion Battle",
            description=f"Champion {self.champion['name']} accepts your challenge!",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)
        
        # Create battle data
        battle_data = {
            'trainer': {
                'id': ctx.author.id,
                'pokemon': user_pokemon,
                'current_pokemon': 0,
                'current_hp': self.calculate_hp(user_pokemon[0])
            },
            'leader': {
                'pokemon': self.champion['pokemon'],
                'current_pokemon': 0,
                'current_hp': None
            },
            'is_champion': True,
            'message': None
        }
        
        # Set champion's first Pokemon
        champion_pokemon = battle_data['leader']['pokemon'][0]
        battle_data['leader']['current_hp'] = self.calculate_hp(champion_pokemon)
        
        self.active_gym_battles[ctx.channel.id] = battle_data
        
        # Send battle message
        embed = await self.create_champion_battle_embed(ctx, battle_data)
        battle_data['message'] = await ctx.send(embed=embed)
        
        await ctx.send(
            f"Champion {self.champion['name']}: Show me the bond between you and your Pokemon!\n"
            f"Use `!champion attack <move>` to use a move!"
        )

    @champion.command(name='attack')
    async def champion_attack(self, ctx, move_name: str):
        """Use a move in a Champion battle"""
        if ctx.channel.id not in self.active_gym_battles:
            return await ctx.send("No active Champion battle in this channel!")
        
        battle = self.active_gym_battles[ctx.channel.id]
        if not battle.get('is_champion'):
            return await ctx.send("This isn't a Champion battle!")
        
        if ctx.author.id != battle['trainer']['id']:
            return await ctx.send("This isn't your battle!")
        
        try:
            await self.process_champion_move(ctx, battle, move_name)
        except Exception as e:
            await ctx.send(f"Error processing move: {e}")

    async def process_champion_move(self, ctx, battle: Dict, move_name: str):
        """Process a move in a Champion battle"""
        # Similar to process_elite_move but with champion-specific logic
        # Implementation details here...

    async def handle_champion_victory(self, ctx):
        """Handle victory over the Champion"""
        # Record victory
        await self.bot.db.execute(
            '''INSERT INTO champion_victories 
               (user_id, completed_at) VALUES ($1, CURRENT_TIMESTAMP)''',
            ctx.author.id
        )
        
        # Award money
        await self.bot.db.execute(
            'UPDATE users SET currency = currency + $1 WHERE id = $2',
            self.champion['reward_money'], ctx.author.id
        )
        
        embed = discord.Embed(
            title="🎊 New Champion! 🎊",
            description=f"Congratulations, {ctx.author.mention}! You have defeated Champion {self.champion['name']}!",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="Rewards",
            value=f"• Pokemon League Champion Title\n"
                  f"• ${self.champion['reward_money']:,}\n"
                  f"• Access to special Champion-only features",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @champion.command(name='history')
    async def champion_history(self, ctx):
        """View Champion battle history"""
        victories = await self.bot.db.fetch(
            'SELECT * FROM champion_victories ORDER BY completed_at DESC LIMIT 10'
        )
        
        embed = discord.Embed(
            title="Champion Battle History",
            color=discord.Color.gold()
        )
        
        if not victories:
            embed.description = "No one has defeated the Champion yet!"
        else:
            for victory in victories:
                user = ctx.guild.get_member(victory['user_id'])
                if user:
                    embed.add_field(
                        name=user.display_name,
                        value=f"Defeated on {victory['completed_at'].strftime('%Y-%m-%d %H:%M')}",
                        inline=False
                    )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PokemonGym(bot)) 