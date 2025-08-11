import discord
from discord import app_commands
from discord.ext import commands
import random
from typing import Dict, Optional, List

class PokemonGym(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_gym_battles: Dict[int, Dict] = {}  # channel_id: battle_data
        self.gym_cooldowns: Dict[int, Dict] = {}  # user_id: {gym_id: timestamp}

        # In a real app, this would be loaded from a database or config files
        self.gyms = {
            "boulder": {"leader": "Brock", "type": "rock", "badge": "Boulder Badge", "pokemon": [{"id": 74, "name": "geodude", "level": 12, "moves": ["tackle", "defense curl"], "stats": {"attack": 80, "defense": 100}}, {"id": 95, "name": "onix", "level": 14, "moves": ["tackle", "harden", "bind"], "stats": {"attack": 45, "defense": 160}}], "reward_money": 1000, "cooldown_hours": 24},
            "cascade": {"leader": "Misty", "type": "water", "badge": "Cascade Badge", "pokemon": [{"id": 120, "name": "staryu", "level": 18, "moves": ["tackle", "water gun"], "stats": {"attack": 45, "defense": 55}}, {"id": 121, "name": "starmie", "level": 21, "moves": ["water gun", "swift", "harden"], "stats": {"attack": 75, "defense": 85}}], "reward_money": 2000, "cooldown_hours": 24},
            # ... other gyms
        }
        self.elite_four = {
            "lorelei": {"name": "Lorelei", "type": "ice", "pokemon": [], "reward_money": 10000},
            "bruno": {"name": "Bruno", "type": "fighting", "pokemon": [], "reward_money": 11000},
            "agatha": {"name": "Agatha", "type": "ghost", "pokemon": [], "reward_money": 12000},
            "lance": {"name": "Lance", "type": "dragon", "pokemon": [], "reward_money": 15000},
        }
        self.champion = {"name": "Blue", "title": "Champion", "pokemon": [], "reward_money": 25000}

    # Groups for slash commands
    gym = app_commands.Group(name="gym", description="Pokemon Gym commands")
    elite = app_commands.Group(name="elite", description="Elite Four commands")
    champion = app_commands.Group(name="champion", description="Pokemon Champion commands")

    # Helper Functions
    def calculate_hp(self, pokemon: Dict) -> int:
        return 50 + (pokemon['level'] * 5)

    async def get_move_data(self, move_name: str) -> Optional[Dict]:
        # Mocked move data
        moves = {
            "tackle": {"power": 40, "type": "normal"}, "defense curl": {"power": 0, "type": "normal"},
            "harden": {"power": 0, "type": "normal"}, "bind": {"power": 15, "type": "normal"},
            "water gun": {"power": 40, "type": "water"}, "swift": {"power": 60, "type": "normal"}
        }
        return moves.get(move_name.lower())

    def calculate_damage(self, attacker: Dict, defender: Dict, move: Dict) -> int:
        if move.get('power', 0) == 0: return 0
        power = move['power']
        attack = attacker['stats']['attack']
        defense = defender['stats']['defense']
        level = attacker['level']
        damage = (((2 * level / 5 + 2) * power * attack / defense) / 50) + 2
        return int(damage * random.uniform(0.85, 1.0))

    # Gym Commands
    @gym.command(name="list", description="List all available gyms")
    async def list_gyms(self, interaction: discord.Interaction):
        """List all available gyms"""
        await interaction.response.defer()
        embed = discord.Embed(title="Available Pokemon Gyms", color=discord.Color.blue())

        for gym_id, gym_data in self.gyms.items():
            # Cooldowns should be managed in the database
            cooldown_status = ""
            embed.add_field(
                name=f"{gym_data['leader']}'s Gym{cooldown_status}",
                value=f"Type: {gym_data['type'].title()}\n"
                      f"Badge: {gym_data['badge']}",
                inline=True,
            )
        await interaction.followup.send(embed=embed)

    @gym.command(name="info", description="Get info about a specific gym")
    @app_commands.describe(gym_id="The ID of the gym (e.g., boulder)")
    async def gym_info(self, interaction: discord.Interaction, gym_id: str):
        """Get info about a specific gym"""
        await interaction.response.defer()
        gym_id = gym_id.lower()
        if gym_id not in self.gyms:
            await interaction.followup.send("Gym not found!", ephemeral=True)
            return

        gym_data = self.gyms[gym_id]
        embed = discord.Embed(title=f"{gym_data['leader']}'s Gym", color=discord.Color.blue())
        
        pokemon_list = []
        for p in gym_data['pokemon']:
            pokemon_list.append(f"• {p['name'].title()} (Lvl {p['level']})")

        embed.description = f"**Leader:** {gym_data['leader']}\n**Type:** {gym_data['type'].title()}"
        embed.add_field(name="Pokemon", value="\n".join(pokemon_list), inline=False)
        embed.add_field(name="Badge Reward", value=gym_data['badge'], inline=True)
        embed.add_field(name="Money Reward", value=f"{gym_data['reward_money']} coins", inline=True)
        
        await interaction.followup.send(embed=embed)

    @gym.command(name="badges", description="View your earned badges")
    async def view_badges(self, interaction: discord.Interaction):
        """View your earned badges"""
        await interaction.response.defer()
        
        badges = await self.bot.db.fetchvals(
            "SELECT badge_name FROM user_badges WHERE user_id = $1",
            interaction.user.id
        )

        embed = discord.Embed(title=f"{interaction.user.name}'s Badges", color=discord.Color.gold())
        if not badges:
            embed.description = "You have no badges yet."
        else:
            embed.description = "\n".join(f"• {badge}" for badge in badges)
            
        await interaction.followup.send(embed=embed)

    @gym.command(name="challenge", description="Challenge a gym leader")
    @app_commands.describe(gym_id="The ID of the gym to challenge")
    async def challenge_gym(self, interaction: discord.Interaction, gym_id: str):
        """Challenge a gym leader"""
        await interaction.response.defer()
        gym_id = gym_id.lower()
        if gym_id not in self.gyms:
            await interaction.followup.send("Gym not found!", ephemeral=True)
            return

        # Check cooldown
        # This should be a proper DB check
        
        # Check badge requirements
        # required_badges = await self.get_required_badges(gym_id)
        # user_badges = await self.get_user_badges(interaction.user.id)
        # if not all(b in user_badges for b in required_badges):
        #     await interaction.followup.send("You don't have the required badges to challenge this gym.", ephemeral=True)
        #     return

        user_pokemon = await self.bot.db.fetch("SELECT * FROM user_pokemon WHERE user_id = $1", interaction.user.id)
        if not user_pokemon:
            await interaction.followup.send("You have no pokemon to battle with!", ephemeral=True)
            return

        options = [discord.SelectOption(label=f"{p['nickname'] or p['pokemon_name']} (Lvl {p['level']})", value=str(p['id'])) for p in user_pokemon]
        select = discord.ui.Select(placeholder="Choose your team (up to 6)", options=options, max_values=6)

        async def select_callback(interaction: discord.Interaction):
            selected_ids = [int(val) for val in select.values]
            selected_pokemon = [p for p in user_pokemon if p['id'] in selected_ids]
            
            await self.start_gym_battle(interaction, gym_id, selected_pokemon)

        select.callback = select_callback
        view = discord.ui.View()
        view.add_item(select)
        await interaction.followup.send("Select your team for the gym battle:", view=view, ephemeral=True)

    async def start_gym_battle(self, interaction: discord.Interaction, gym_id: str, trainer_pokemon: List[Dict]):
        if interaction.channel.id in self.active_gym_battles:
            await interaction.response.send_message("A gym battle is already active in this channel.", ephemeral=True)
            return

        gym_data = self.gyms[gym_id]
        
        battle_state = {
            "gym_id": gym_id,
            "leader": gym_data['leader'],
            "trainer_id": interaction.user.id,
            "trainer_pokemon": [dict(p) for p in trainer_pokemon],
            "gym_pokemon": [p for p in gym_data['pokemon']],
            "current_trainer_pokemon_index": 0,
            "current_gym_pokemon_index": 0,
            "turn": "trainer",
            "message_id": None
        }
        
        self.active_gym_battles[interaction.channel.id] = battle_state
        
        embed = await self.create_gym_battle_embed(interaction, battle_state)
        view = self.create_gym_battle_view(interaction)
        
        msg = await interaction.followup.send(embed=embed, view=view, ephemeral=False)
        self.active_gym_battles[interaction.channel.id]['message_id'] = msg.id

    def create_gym_battle_view(self, interaction: discord.Interaction):
        view = discord.ui.View(timeout=180)
        attack_button = discord.ui.Button(label="Attack", style=discord.ButtonStyle.green)
        switch_button = discord.ui.Button(label="Switch Pokemon", style=discord.ButtonStyle.blurple)
        forfeit_button = discord.ui.Button(label="Forfeit", style=discord.ButtonStyle.red)

        async def attack_callback(interaction: discord.Interaction):
            await interaction.response.send_message("Attack logic to be implemented", ephemeral=True)

        async def switch_callback(interaction: discord.Interaction):
            await interaction.response.send_message("Switch logic to be implemented", ephemeral=True)
        
        async def forfeit_callback(interaction: discord.Interaction):
            await interaction.response.send_message("Forfeit logic to be implemented", ephemeral=True)

        attack_button.callback = attack_callback
        switch_button.callback = switch_callback
        forfeit_button.callback = forfeit_callback
        
        view.add_item(attack_button)
        view.add_item(switch_button)
        view.add_item(forfeit_button)
        return view

    async def create_gym_battle_embed(self, interaction: discord.Interaction, battle: Dict) -> discord.Embed:
        trainer_p = battle['trainer_pokemon'][battle['current_trainer_pokemon_index']]
        gym_p = battle['gym_pokemon'][battle['current_gym_pokemon_index']]

        # temp hp for embed
        trainer_p['current_hp'] = trainer_p.get('current_hp', self.calculate_hp(trainer_p))
        gym_p['current_hp'] = gym_p.get('current_hp', self.calculate_hp(gym_p))

        embed = discord.Embed(title=f"Gym Battle: {interaction.user.name} vs {battle['leader']}", color=discord.Color.red())
        
        embed.add_field(
            name=f"{interaction.user.name}'s {trainer_p.get('nickname') or trainer_p['pokemon_name']}",
            value=f"HP: {trainer_p['current_hp']} / {self.calculate_hp(trainer_p)}",
            inline=True
        )
        embed.add_field(
            name=f"{battle['leader']}'s {gym_p['name']}",
            value=f"HP: {gym_p['current_hp']} / {self.calculate_hp(gym_p)}",
            inline=True
        )
        
        turn_name = interaction.user.name if battle['turn'] == 'trainer' else battle['leader']
        embed.set_footer(text=f"It's {turn_name}'s turn.")
        
        return embed


async def setup(bot):
    cog = PokemonGym(bot)
    bot.tree.add_command(cog.gym)
    bot.tree.add_command(cog.elite)
    bot.tree.add_command(cog.champion)
    await bot.add_cog(cog) 