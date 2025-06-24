import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import math
from typing import Dict, List, Optional
from datetime import datetime, timezone
import json
import aiohttp

class TournamentCreateModal(discord.ui.Modal, title="Create a new Pokemon Tournament"):
    name = discord.ui.TextInput(label="Tournament Name")
    tournament_type = discord.ui.TextInput(label="Tournament Type", placeholder="e.g. single_elimination, level_cap")
    max_participants = discord.ui.TextInput(label="Max Participants")
    min_level = discord.ui.TextInput(label="Minimum Pokemon Level", default="1")
    max_level = discord.ui.TextInput(label="Maximum Pokemon Level", default="100")
    entry_fee = discord.ui.TextInput(label="Entry Fee (coins)", default="0")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer() # defer so we can do more processing
        # Pass the modal and interaction to a method that can handle the logic
        await self.cog.create_tournament_from_modal(interaction, self)


class PokemonTournament(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_tournament_battles: Dict[int, Dict] = {}  # channel_id: battle_data
        self.active_battles = {}  # channel_id: battle_data
        self.battle_locks = {}  # user_id: is_battling
        self.spectators = {}  # channel_id: set(user_ids)
        self.move_cache = {}  # move_name: move_data
        self.type_cache = {}  # type_name: type_data

        # Tournament types with special rules
        self.tournament_types = {
            "single_elimination": {
                "description": "Standard single elimination bracket tournament",
                "requires_power_of_two": True,
                "rules": {},
            },
            "double_elimination": {
                "description": "Double elimination with winners and losers brackets",
                "requires_power_of_two": True,
                "rules": {},
            },
            "round_robin": {
                "description": "Everyone plays against everyone",
                "requires_power_of_two": False,
                "rules": {},
            },
            "type_restricted": {
                "description": "Pokemon must be of specific type(s)",
                "requires_power_of_two": True,
                "rules": {"allowed_types": []},  # Set during tournament creation
            },
            "level_cap": {
                "description": "Pokemon levels are capped and scaled",
                "requires_power_of_two": True,
                "rules": {"level_cap": 50, "scale_to_cap": True},  # Set during tournament creation
            },
        }

    tournament = app_commands.Group(name="tournament", description="Pokemon tournament commands")

    @tournament.command(name="create", description="Create a new tournament")
    @app_commands.checks.has_permissions(administrator=True)
    async def create_tournament(self, interaction: discord.Interaction):
        """Create a new tournament"""
        modal = TournamentCreateModal()
        modal.cog = self # Pass the cog instance to the modal
        await interaction.response.send_modal(modal)

    async def create_tournament_from_modal(self, interaction: discord.Interaction, modal: TournamentCreateModal):
        name = modal.name.value
        tournament_type = modal.tournament_type.value.lower()
        
        if tournament_type not in self.tournament_types:
            await interaction.followup.send("Invalid tournament type!", ephemeral=True)
            return

        try:
            max_participants = int(modal.max_participants.value)
            if self.tournament_types[tournament_type]["requires_power_of_two"]:
                if not math.log2(max_participants).is_integer():
                    await interaction.followup.send(
                        "Participant count must be a power of 2 for this tournament type!",
                        ephemeral=True
                    )
                    return
        except ValueError:
            await interaction.followup.send("Invalid number for max participants!", ephemeral=True)
            return

        try:
            min_level = max(1, min(100, int(modal.min_level.value)))
            max_level = max(min_level, min(100, int(modal.max_level.value)))
        except ValueError:
            await interaction.followup.send("Invalid level range!", ephemeral=True)
            return
            
        try:
            entry_fee = max(0, int(modal.entry_fee.value))
        except ValueError:
            await interaction.followup.send("Invalid amount for entry fee!", ephemeral=True)
            return
        
        rules = {}
        # We might need another modal for special rules, for now, we'll use defaults
        # or require a separate command to configure them.
        # For simplicity in this migration, let's just use the defaults for now.

        tournament_id = await self.bot.db.fetchval(
            """INSERT INTO pokemon_tournaments 
               (name, tournament_type, max_participants, min_level, max_level, 
                entry_fee, prize_pool, rules, created_by, guild_id)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
               RETURNING id""",
            name, tournament_type, max_participants, min_level, max_level,
            entry_fee, entry_fee * max_participants, json.dumps(rules),
            interaction.user.id, interaction.guild.id
        )

        embed = discord.Embed(
            title="Tournament Created!",
            description=f"Tournament **{name}** has been created!",
            color=discord.Color.green(),
        )
        embed.add_field(name="ID", value=str(tournament_id), inline=True)
        embed.add_field(
            name="Type", value=tournament_type.replace("_", " ").title(), inline=True
        )
        embed.add_field(name="Max Participants", value=str(max_participants), inline=True)
        embed.add_field(name="Level Range", value=f"{min_level}-{max_level}", inline=True)
        embed.add_field(name="Entry Fee", value=f"{entry_fee} coins", inline=True)
        embed.add_field(
            name="Prize Pool", value=f"{entry_fee * max_participants} coins", inline=True
        )

        if rules:
            rules_text = "\n".join(f"• {k}: {v}" for k, v in rules.items())
            embed.add_field(name="Special Rules", value=rules_text, inline=False)

        embed.add_field(
            name="How to Join",
            value=f"Use `/tournament join id:{tournament_id}` to participate!",
            inline=False,
        )
        await interaction.followup.send(embed=embed)

    @tournament.command(name="list", description="List active tournaments")
    async def list_tournaments(self, interaction: discord.Interaction):
        """List active tournaments"""
        tournaments = await self.bot.db.fetch(
            """SELECT * FROM pokemon_tournaments 
               WHERE status != 'completed' AND guild_id = $1
               ORDER BY created_at DESC""",
            interaction.guild.id
        )

        if not tournaments:
            await interaction.response.send_message("No active tournaments found!", ephemeral=True)
            return

        embed = discord.Embed(title="Active Pokemon Tournaments", color=discord.Color.blue())

        for t in tournaments:
            participants = await self.bot.db.fetchval(
                "SELECT COUNT(*) FROM tournament_participants WHERE tournament_id = $1", t["id"]
            )

            embed.add_field(
                name=f"{t['name']} (ID: {t['id']})",
                value=f"Type: {t['tournament_type'].replace('_', ' ').title()}\n"
                f"Status: {t['status'].replace('_', ' ').title()}\n"
                f"Participants: {participants}/{t['max_participants']}\n"
                f"Level Range: {t['min_level']}-{t['max_level']}\n"
                f"Entry Fee: {t['entry_fee']} coins\n"
                f"Prize Pool: {t['prize_pool']} coins",
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    @tournament.command(name="info", description="Get detailed information about a tournament")
    @app_commands.describe(tournament_id="The ID of the tournament")
    async def tournament_info(self, interaction: discord.Interaction, tournament_id: int):
        """Get detailed information about a tournament"""
        tournament = await self.bot.db.fetchrow(
            "SELECT * FROM pokemon_tournaments WHERE id = $1 AND guild_id = $2",
            tournament_id, interaction.guild.id
        )

        if not tournament:
            await interaction.response.send_message("Tournament not found!", ephemeral=True)
            return

        participants_records = await self.bot.db.fetch(
            """SELECT u.username, tp.current_wins, tp.current_losses, tp.eliminated
               FROM tournament_participants tp
               JOIN users u ON tp.user_id = u.id
               WHERE tp.tournament_id = $1
               ORDER BY tp.current_wins DESC""",
            tournament_id
        )
        
        participant_list = []
        for p in participants_records:
            status = "Eliminated" if p['eliminated'] else f"{p['current_wins']}W / {p['current_losses']}L"
            participant_list.append(f"• {p['username']} ({status})")

        embed = discord.Embed(
            title=f"Tournament Info: {tournament['name']}",
            description=f"**ID:** {tournament['id']}\n"
                        f"**Status:** {tournament['status'].replace('_', ' ').title()}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Details",
                        value=f"**Type:** {tournament['tournament_type'].replace('_', ' ').title()}\n"
                              f"**Participants:** {len(participants_records)}/{tournament['max_participants']}\n"
                              f"**Level Range:** {tournament['min_level']}-{tournament['max_level']}\n"
                              f"**Entry Fee:** {tournament['entry_fee']} coins\n"
                              f"**Prize Pool:** {tournament['prize_pool']} coins",
                        inline=False)
        
        if participant_list:
            embed.add_field(name="Participants", value="\n".join(participant_list) or "None yet", inline=False)
        else:
            embed.add_field(name="Participants", value="No one has joined yet.", inline=False)


        await interaction.response.send_message(embed=embed)

    @tournament.command(name="join", description="Join a tournament")
    @app_commands.describe(tournament_id="The ID of the tournament")
    async def join_tournament(self, interaction: discord.Interaction, tournament_id: int):
        """Join a tournament"""
        await interaction.response.defer()
        
        tournament = await self.bot.db.fetchrow(
            "SELECT * FROM pokemon_tournaments WHERE id = $1 AND guild_id = $2",
            tournament_id, interaction.guild.id
        )

        if not tournament:
            await interaction.followup.send("Tournament not found!", ephemeral=True)
            return
            
        if tournament['status'] != 'pending':
            await interaction.followup.send("This tournament is not open for new participants.", ephemeral=True)
            return

        # Check if user is already in the tournament
        is_participant = await self.bot.db.fetchval(
            "SELECT 1 FROM tournament_participants WHERE tournament_id = $1 AND user_id = $2",
            tournament_id, interaction.user.id
        )
        if is_participant:
            await interaction.followup.send("You are already in this tournament.", ephemeral=True)
            return

        # Check for participant limit
        participant_count = await self.bot.db.fetchval(
            "SELECT COUNT(*) FROM tournament_participants WHERE tournament_id = $1",
            tournament_id
        )
        if participant_count >= tournament['max_participants']:
            await interaction.followup.send("This tournament is full.", ephemeral=True)
            return

        # Check entry fee
        if tournament['entry_fee'] > 0:
            user_balance = await self.bot.db.fetchval("SELECT coins FROM users WHERE id = $1", interaction.user.id)
            if user_balance < tournament['entry_fee']:
                await interaction.followup.send(f"You don't have enough coins to join. Entry fee: {tournament['entry_fee']}", ephemeral=True)
                return

        # Get user's pokemon
        user_pokemon = await self.bot.db.fetch(
            "SELECT * FROM user_pokemon WHERE user_id = $1 AND level BETWEEN $2 AND $3",
            interaction.user.id, tournament['min_level'], tournament['max_level']
        )
        
        if not user_pokemon:
            await interaction.followup.send("You don't have any eligible pokemon for this tournament.", ephemeral=True)
            return

        # Create a select menu for pokemon selection
        options = [
            discord.SelectOption(label=f"{p['nickname'] or p['pokemon_name']} (Lvl {p['level']})", value=str(p['id']))
            for p in user_pokemon
        ]
        select = discord.ui.Select(placeholder="Choose your pokemon...", options=options)

        async def select_callback(interaction: discord.Interaction):
            selected_pokemon_id = int(select.values[0])
            
            # Deduct entry fee
            if tournament['entry_fee'] > 0:
                await self.bot.db.execute(
                    "UPDATE users SET coins = coins - $1 WHERE id = $2",
                    tournament['entry_fee'], interaction.user.id
                )
            
            # Add participant
            await self.bot.db.execute(
                """INSERT INTO tournament_participants 
                   (tournament_id, user_id, pokemon_id) 
                   VALUES ($1, $2, $3)""",
                tournament_id, interaction.user.id, selected_pokemon_id
            )

            await interaction.response.send_message(f"You have joined the '{tournament['name']}' tournament!", ephemeral=True)
            
            # Update prize pool
            await self.bot.db.execute(
                "UPDATE pokemon_tournaments SET prize_pool = prize_pool + $1 WHERE id = $2",
                tournament['entry_fee'], tournament_id
            )

        select.callback = select_callback
        view = discord.ui.View()
        view.add_item(select)
        await interaction.followup.send("Select your pokemon for the tournament:", view=view, ephemeral=True)


    @tournament.command(name="leave", description="Leave a tournament")
    @app_commands.describe(tournament_id="The ID of the tournament")
    async def leave_tournament(self, interaction: discord.Interaction, tournament_id: int):
        """Leave a tournament"""
        await interaction.response.defer()

        tournament = await self.bot.db.fetchrow(
            "SELECT * FROM pokemon_tournaments WHERE id = $1 AND guild_id = $2",
            tournament_id, interaction.guild.id
        )

        if not tournament:
            await interaction.followup.send("Tournament not found!", ephemeral=True)
            return

        if tournament['status'] != 'pending':
            await interaction.followup.send("You cannot leave a tournament that has already started.", ephemeral=True)
            return

        # Check if user is in the tournament
        participant = await self.bot.db.fetchrow(
            "SELECT 1 FROM tournament_participants WHERE tournament_id = $1 AND user_id = $2",
            tournament_id, interaction.user.id
        )
        if not participant:
            await interaction.followup.send("You are not in this tournament.", ephemeral=True)
            return

        # Remove participant
        await self.bot.db.execute(
            "DELETE FROM tournament_participants WHERE tournament_id = $1 AND user_id = $2",
            tournament_id, interaction.user.id
        )
        
        # Refund entry fee and update prize pool
        if tournament['entry_fee'] > 0:
            await self.bot.db.execute(
                "UPDATE users SET coins = coins + $1 WHERE id = $2",
                tournament['entry_fee'], interaction.user.id
            )
            await self.bot.db.execute(
                "UPDATE pokemon_tournaments SET prize_pool = prize_pool - $1 WHERE id = $2",
                tournament['entry_fee'], tournament_id
            )

        await interaction.followup.send(f"You have left the '{tournament['name']}' tournament.", ephemeral=True)

    @tournament.command(name="start", description="Start a tournament")
    @app_commands.describe(tournament_id="The ID of the tournament")
    @app_commands.checks.has_permissions(administrator=True)
    async def start_tournament(self, interaction: discord.Interaction, tournament_id: int):
        """Start a tournament"""
        await interaction.response.defer()

        tournament = await self.bot.db.fetchrow(
            "SELECT * FROM pokemon_tournaments WHERE id = $1 AND guild_id = $2",
            tournament_id, interaction.guild.id
        )

        if not tournament:
            await interaction.followup.send("Tournament not found!", ephemeral=True)
            return

        if tournament['status'] != 'pending':
            await interaction.followup.send("This tournament has already started or is completed.", ephemeral=True)
            return

        participants = await self.bot.db.fetch("SELECT * FROM tournament_participants WHERE tournament_id = $1", tournament_id)
        if len(participants) < 2:
            await interaction.followup.send("Not enough participants to start the tournament.", ephemeral=True)
            return
            
        if self.tournament_types[tournament['tournament_type']]['requires_power_of_two']:
            if not math.log2(len(participants)).is_integer():
                await interaction.followup.send("Participant count must be a power of 2 for this tournament type.", ephemeral=True)
                return

        await self.bot.db.execute(
            "UPDATE pokemon_tournaments SET status = 'in_progress' WHERE id = $1",
            tournament_id
        )

        await self.generate_next_round_matches(interaction, tournament_id)

        await interaction.followup.send(f"The '{tournament['name']}' tournament has started!")

    async def generate_next_round_matches(self, interaction: discord.Interaction, tournament_id: int):
        # This is a complex function. For now, we will just implement a simple pairing logic.
        # A full implementation would depend on the tournament type (single elim, double elim, round robin)
        
        participants = await self.bot.db.fetch("SELECT * FROM tournament_participants WHERE tournament_id = $1 AND eliminated = false", tournament_id)
        
        # Simple random pairing for now
        random.shuffle(participants)
        
        round_number = await self.bot.db.fetchval(
            "SELECT COALESCE(MAX(round_number), 0) + 1 FROM tournament_matches WHERE tournament_id = $1",
            tournament_id
        )

        for i in range(0, len(participants), 2):
            if i + 1 < len(participants):
                p1 = participants[i]
                p2 = participants[i+1]

                await self.bot.db.execute(
                    """INSERT INTO tournament_matches 
                       (tournament_id, round_number, player1_id, player2_id, status)
                       VALUES ($1, $2, $3, $4, 'pending')""",
                    tournament_id, round_number, p1['user_id'], p2['user_id']
                )
        
        # Announce matches
        # In a real scenario, you'd want to DM users or post in a specific channel
        await interaction.channel.send(f"Round {round_number} matches for tournament {tournament_id} have been generated! Use `/tournament matches` to see your opponent.")

    @tournament.command(name="bracket", description="View tournament bracket")
    @app_commands.describe(tournament_id="The ID of the tournament")
    async def view_bracket(self, interaction: discord.Interaction, tournament_id: int):
        """View tournament bracket"""
        await interaction.response.defer()

        tournament = await self.bot.db.fetchrow("SELECT * FROM pokemon_tournaments WHERE id = $1", tournament_id)
        if not tournament:
            await interaction.followup.send("Tournament not found!", ephemeral=True)
            return

        matches = await self.bot.db.fetch(
            """SELECT m.*, 
                      p1.username as p1_name, 
                      p2.username as p2_name,
                      winner.username as winner_name
               FROM tournament_matches m
               JOIN users p1 ON m.player1_id = p1.id
               JOIN users p2 ON m.player2_id = p2.id
               LEFT JOIN users winner ON m.winner_id = winner.id
               WHERE m.tournament_id = $1 
               ORDER BY m.round_number, m.match_number""",
            tournament_id
        )

        embed = discord.Embed(title=f"Bracket for {tournament['name']}", color=discord.Color.blue())

        if not matches:
            embed.description = "No matches have been generated yet."
            await interaction.followup.send(embed=embed)
            return

        rounds = {}
        for match in matches:
            round_num = match['round_number']
            if round_num not in rounds:
                rounds[round_num] = []
            rounds[round_num].append(match)

        for round_num, round_matches in sorted(rounds.items()):
            match_list = []
            for match in round_matches:
                if match['winner_name']:
                    match_list.append(f"• **{match['p1_name']}** vs {match['p2_name']} -> **Winner: {match['winner_name']}**")
                else:
                    match_list.append(f"• {match['p1_name']} vs {match['p2_name']} ({match['status']})")
            embed.add_field(name=f"Round {round_num}", value="\n".join(match_list), inline=False)
            
        await interaction.followup.send(embed=embed)


    @tournament.command(name="matches", description="View your upcoming matches")
    async def view_matches(self, interaction: discord.Interaction):
        """View your upcoming matches"""
        await interaction.response.defer()

        matches = await self.bot.db.fetch(
            """SELECT m.*, t.name as tournament_name, p1.username as p1_name, p2.username as p2_name
               FROM tournament_matches m
               JOIN pokemon_tournaments t ON m.tournament_id = t.id
               JOIN users p1 ON m.player1_id = p1.id
               JOIN users p2 ON m.player2_id = p2.id
               WHERE (m.player1_id = $1 OR m.player2_id = $1) AND m.status = 'pending'
               ORDER BY t.created_at, m.round_number""",
            interaction.user.id
        )

        if not matches:
            await interaction.followup.send("You have no upcoming matches.", ephemeral=True)
            return

        embed = discord.Embed(title="Your Upcoming Matches", color=discord.Color.blue())
        for match in matches:
            opponent_name = match['p2_name'] if match['p1_name'] == interaction.user.name else match['p1_name']
            embed.add_field(
                name=f"{match['tournament_name']} - Round {match['round_number']}",
                value=f"vs **{opponent_name}**\nTo battle, use `/tournament battle tournament_id:{match['tournament_id']} match_number:{match['match_number']}`",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)

    @tournament.command(name="battle", description="Start your tournament match")
    @app_commands.describe(tournament_id="The ID of the tournament", match_number="The match number from the bracket")
    async def tournament_battle(self, interaction: discord.Interaction, tournament_id: int, match_number: int):
        await interaction.response.defer()

        # Simplified validation, a real implementation would be more robust
        match = await self.bot.db.fetchrow(
            """SELECT * FROM tournament_matches 
               WHERE tournament_id = $1 AND match_number = $2 AND (player1_id = $3 OR player2_id = $3)""",
            tournament_id, match_number, interaction.user.id
        )

        if not match:
            await interaction.followup.send("Match not found or you are not a participant.", ephemeral=True)
            return

        if match['status'] != 'pending':
            await interaction.followup.send("This match is not pending.", ephemeral=True)
            return
            
        # Prevent starting a battle if one is already active in the channel
        if interaction.channel.id in self.active_tournament_battles:
            await interaction.followup.send("A tournament battle is already active in this channel.", ephemeral=True)
            return

        # Fetch pokemon data for both players
        p1_pokemon = await self.bot.db.fetchrow("SELECT * FROM user_pokemon WHERE id = (SELECT pokemon_id FROM tournament_participants WHERE user_id = $1 AND tournament_id = $2)", match['player1_id'], tournament_id)
        p2_pokemon = await self.bot.db.fetchrow("SELECT * FROM user_pokemon WHERE id = (SELECT pokemon_id FROM tournament_participants WHERE user_id = $1 AND tournament_id = $2)", match['player2_id'], tournament_id)

        # Initialize battle state
        battle_state = {
            "tournament_id": tournament_id,
            "match_id": match['id'],
            "players": {
                match['player1_id']: {"pokemon": dict(p1_pokemon), "current_hp": self.calculate_hp(p1_pokemon)},
                match['player2_id']: {"pokemon": dict(p2_pokemon), "current_hp": self.calculate_hp(p2_pokemon)},
            },
            "turn": match['player1_id'], # Player 1 starts
            "message_id": None, # Will be set after sending the first message
        }
        self.active_tournament_battles[interaction.channel.id] = battle_state
        
        embed = await self.create_tournament_battle_embed(interaction, battle_state)
        view = self.create_battle_view(interaction) # A new function to create the view
        
        msg = await interaction.followup.send(embed=embed, view=view)
        self.active_tournament_battles[interaction.channel.id]["message_id"] = msg.id


    def create_battle_view(self, interaction: discord.Interaction):
        view = discord.ui.View(timeout=180)
        
        attack_button = discord.ui.Button(label="Attack", style=discord.ButtonStyle.green)
        forfeit_button = discord.ui.Button(label="Forfeit", style=discord.ButtonStyle.red)

        async def attack_callback(interaction: discord.Interaction):
            battle = self.active_tournament_battles.get(interaction.channel.id)
            if not battle or battle['turn'] != interaction.user.id:
                await interaction.response.send_message("It's not your turn!", ephemeral=True)
                return

            player = battle['players'][interaction.user.id]
            moves = json.loads(player['pokemon']['moves'])
            
            options = [discord.SelectOption(label=move) for move in moves]
            move_select = discord.ui.Select(placeholder="Choose your move...", options=options)
            
            async def move_callback(interaction: discord.Interaction):
                move_name = move_select.values[0]
                await self.process_attack(interaction, move_name)

            move_select.callback = move_callback
            move_view = discord.ui.View()
            move_view.add_item(move_select)
            await interaction.response.send_message("Select your move:", view=move_view, ephemeral=True)

        async def forfeit_callback(interaction: discord.Interaction):
            # Simplified forfeit logic
            battle = self.active_tournament_battles.get(interaction.channel.id)
            if not battle:
                return 

            winner_id = [pid for pid in battle['players'] if pid != interaction.user.id][0]
            await self.handle_tournament_victory(interaction, winner_id)


        attack_button.callback = attack_callback
        forfeit_button.callback = forfeit_callback
        
        view.add_item(attack_button)
        view.add_item(forfeit_button)
        return view

    async def process_attack(self, interaction: discord.Interaction, move_name: str):
        battle = self.active_tournament_battles.get(interaction.channel.id)
        if not battle:
            return

        attacker_id = battle['turn']
        defender_id = [pid for pid in battle['players'] if pid != attacker_id][0]
        
        attacker = battle['players'][attacker_id]
        defender = battle['players'][defender_id]

        move = await self.get_move_data(move_name)
        if not move:
            await interaction.response.send_message("Could not retrieve move data.", ephemeral=True)
            return
            
        damage = self.calculate_tournament_damage(attacker['pokemon'], defender['pokemon'], move)
        defender['current_hp'] = max(0, defender['current_hp'] - damage)

        if defender['current_hp'] <= 0:
            await interaction.message.delete() # remove the move selection message
            await self.handle_tournament_victory(interaction, attacker_id)
            return

        # Switch turns
        battle['turn'] = defender_id
        
        await self.update_tournament_battle_embed(interaction)
        await interaction.message.delete()


    async def handle_tournament_victory(self, interaction: discord.Interaction, winner_id: int):
        battle = self.active_tournament_battles.pop(interaction.channel.id, None)
        if not battle:
            return

        loser_id = [pid for pid in battle['players'] if pid != winner_id][0]
        
        await self.bot.db.execute(
            "UPDATE tournament_matches SET winner_id = $1, status = 'completed' WHERE id = $2",
            winner_id, battle['match_id']
        )
        await self.bot.db.execute("UPDATE tournament_participants SET current_wins = current_wins + 1 WHERE tournament_id = $1 AND user_id = $2", battle['tournament_id'], winner_id)
        await self.bot.db.execute("UPDATE tournament_participants SET current_losses = current_losses + 1, eliminated = true WHERE tournament_id = $1 AND user_id = $2", battle['tournament_id'], loser_id)

        winner_user = await self.bot.fetch_user(winner_id)
        
        original_message = await interaction.channel.fetch_message(battle['message_id'])
        if original_message:
            await original_message.delete()
            
        await interaction.channel.send(f"The battle is over! {winner_user.name} is victorious!")

        # Check if the tournament is over or if new matches need to be generated
        # This is a complex part that would require checking all matches for the round
        # and then for the whole tournament. For now, we'll just end the match.


    async def update_tournament_battle_embed(self, interaction: discord.Interaction):
        battle = self.active_tournament_battles.get(interaction.channel.id)
        if not battle:
            return

        embed = await self.create_tournament_battle_embed(interaction, battle)
        
        message = await interaction.channel.fetch_message(battle['message_id'])
        if message:
            await message.edit(embed=embed)


    def calculate_tournament_damage(self, attacker: Dict, defender: Dict, move: Dict) -> int:
        # Simplified damage calculation
        power = move.get('power', 50)
        attack = attacker['attack']
        defense = defender['defense']
        level = attacker['level']
        
        damage = (((2 * level / 5 + 2) * power * attack / defense) / 50) + 2
        return int(damage * random.uniform(0.85, 1.0))

    async def get_move_data(self, move_name: str) -> Optional[Dict]:
        if move_name in self.move_cache:
            return self.move_cache[move_name]
        
        # In a real bot, this would query an external API like PokeAPI
        # For this migration, we'll mock some data.
        mock_moves = {
            "tackle": {"power": 40, "type": "normal"},
            "ember": {"power": 40, "type": "fire"},
            "water gun": {"power": 40, "type": "water"},
            "vinewhip": {"power": 40, "type": "grass"},
        }
        if move_name.lower() in mock_moves:
            self.move_cache[move_name] = mock_moves[move_name.lower()]
            return self.move_cache[move_name]
        return None

    def calculate_hp(self, pokemon: Dict) -> int:
        # Simplified HP calculation
        return 50 + (pokemon['level'] * 5)

    async def create_tournament_battle_embed(self, interaction: discord.Interaction, battle: Dict) -> discord.Embed:
        p1_id = list(battle['players'].keys())[0]
        p2_id = list(battle['players'].keys())[1]
        p1 = battle['players'][p1_id]
        p2 = battle['players'][p2_id]
        
        p1_user = await self.bot.fetch_user(p1_id)
        p2_user = await self.bot.fetch_user(p2_id)

        embed = discord.Embed(title=f"Tournament Battle: {p1_user.name} vs {p2_user.name}", color=discord.Color.red())
        
        embed.add_field(
            name=f"{p1_user.name}'s {p1['pokemon']['nickname'] or p1['pokemon']['pokemon_name']}",
            value=f"HP: {p1['current_hp']} / {self.calculate_hp(p1['pokemon'])}",
            inline=True
        )
        embed.add_field(
            name=f"{p2_user.name}'s {p2['pokemon']['nickname'] or p2['pokemon']['pokemon_name']}",
            value=f"HP: {p2['current_hp']} / {self.calculate_hp(p2['pokemon'])}",
            inline=True
        )
        
        turn_user = await self.bot.fetch_user(battle['turn'])
        embed.set_footer(text=f"It's {turn_user.name}'s turn.")
        
        return embed

    @tournament.command(name="leaderboard", description="View tournament leaderboards")
    async def tournament_leaderboard(self, interaction: discord.Interaction):
        """View tournament leaderboards"""
        await interaction.response.defer()
        
        # For simplicity, we'll just show a server-wide leaderboard of tournament wins
        leaderboard_data = await self.bot.db.fetch(
            """SELECT u.username, SUM(tp.current_wins) as total_wins
               FROM tournament_participants tp
               JOIN users u ON tp.user_id = u.id
               JOIN pokemon_tournaments t ON tp.tournament_id = t.id
               WHERE t.guild_id = $1
               GROUP BY u.username
               ORDER BY total_wins DESC
               LIMIT 10""",
            interaction.guild.id
        )

        embed = discord.Embed(title="Tournament Win Leaderboard", color=discord.Color.gold())

        if not leaderboard_data:
            embed.description = "No tournament data available yet."
        else:
            leaderboard_text = ""
            for i, record in enumerate(leaderboard_data):
                leaderboard_text += f"{i+1}. {record['username']} - {record['total_wins']} wins\n"
            embed.description = leaderboard_text
            
        await interaction.followup.send(embed=embed)

    @tournament.command(name="history", description="View a user's tournament history")
    @app_commands.describe(user="The user to view history for (defaults to you)")
    async def tournament_history(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """View a user's tournament history"""
        await interaction.response.defer()
        target_user = user or interaction.user

        records = await self.bot.db.fetch(
            """SELECT t.name, tp.current_wins, tp.current_losses, tp.eliminated, t.status
               FROM tournament_participants tp
               JOIN pokemon_tournaments t ON tp.tournament_id = t.id
               WHERE tp.user_id = $1 AND t.guild_id = $2
               ORDER BY t.created_at DESC""",
            target_user.id, interaction.guild.id
        )

        embed = discord.Embed(title=f"Tournament History for {target_user.name}", color=discord.Color.blue())

        if not records:
            embed.description = "No tournament history found."
        else:
            history_text = ""
            for r in records:
                result = f"{r['current_wins']}W / {r['current_losses']}L"
                if r['eliminated']:
                    result += " (Eliminated)"
                history_text += f"• **{r['name']}** ({r['status']}): {result}\n"
            embed.description = history_text

        await interaction.followup.send(embed=embed)
        
    @tournament.command(name="rules", description="View rules for a tournament")
    @app_commands.describe(tournament_id="The ID of the tournament (optional)")
    async def tournament_rules(self, interaction: discord.Interaction, tournament_id: Optional[int] = None):
        """View rules for a tournament"""
        await interaction.response.defer()

        if tournament_id:
            tournament = await self.bot.db.fetchrow("SELECT * FROM pokemon_tournaments WHERE id = $1", tournament_id)
            if not tournament:
                await interaction.followup.send("Tournament not found!", ephemeral=True)
                return
            
            rules = json.loads(tournament['rules'])
            embed = discord.Embed(title=f"Rules for {tournament['name']}", color=discord.Color.blue())
            rules_text = f"**Tournament Type:** {tournament['tournament_type'].replace('_', ' ').title()}\n"
            if not rules:
                rules_text += "This tournament has no special rules."
            else:
                for key, value in rules.items():
                    rules_text += f"• **{key.replace('_', ' ').title()}:** {value}\n"
            embed.description = rules_text
        else:
            embed = discord.Embed(title="General Tournament Rules", color=discord.Color.blue())
            embed.description = "This is a general ruleset for pokemon tournaments..."
            for type_name, type_data in self.tournament_types.items():
                embed.add_field(name=type_name.replace('_',' ').title(), value=type_data['description'], inline=False)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    cog = PokemonTournament(bot)
    bot.tree.add_command(cog.tournament)
    await bot.add_cog(cog) 