import discord
from discord.ext import commands
import asyncio
import random
import math
from typing import Dict, List, Optional
from datetime import datetime, timezone
import json
import aiohttp

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
            'single_elimination': {
                'description': 'Standard single elimination bracket tournament',
                'requires_power_of_two': True,
                'rules': {}
            },
            'double_elimination': {
                'description': 'Double elimination with winners and losers brackets',
                'requires_power_of_two': True,
                'rules': {}
            },
            'round_robin': {
                'description': 'Everyone plays against everyone',
                'requires_power_of_two': False,
                'rules': {}
            },
            'type_restricted': {
                'description': 'Pokemon must be of specific type(s)',
                'requires_power_of_two': True,
                'rules': {
                    'allowed_types': []  # Set during tournament creation
                }
            },
            'level_cap': {
                'description': 'Pokemon levels are capped and scaled',
                'requires_power_of_two': True,
                'rules': {
                    'level_cap': 50,  # Set during tournament creation
                    'scale_to_cap': True
                }
            }
        }

    @commands.group(invoke_without_command=True)
    async def tournament(self, ctx):
        """Pokemon tournament commands"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Pokemon Tournaments",
                description="Use these commands to participate in tournaments:",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Commands",
                value="• `!tournament create` - Create a new tournament\n"
                      "• `!tournament list` - List active tournaments\n"
                      "• `!tournament info <id>` - Get tournament information\n"
                      "• `!tournament join <id>` - Join a tournament\n"
                      "• `!tournament leave <id>` - Leave a tournament\n"
                      "• `!tournament start <id>` - Start a tournament (admin only)\n"
                      "• `!tournament bracket <id>` - View tournament bracket\n"
                      "• `!tournament matches` - View your upcoming matches",
                inline=False
            )
            await ctx.send(embed=embed)

    @tournament.command(name='create')
    @commands.has_permissions(administrator=True)
    async def create_tournament(self, ctx):
        """Create a new tournament"""
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            # Get tournament name
            await ctx.send("What would you like to name this tournament?")
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
            name = msg.content

            # Get tournament type
            type_list = "\n".join(f"• {t}: {data['description']}" for t, data in self.tournament_types.items())
            await ctx.send(f"What type of tournament? Available types:\n{type_list}")
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
            tournament_type = msg.content.lower()
            
            if tournament_type not in self.tournament_types:
                return await ctx.send("Invalid tournament type!")

            # Get special rules based on tournament type
            rules = {}
            if tournament_type == 'type_restricted':
                await ctx.send("Enter allowed Pokemon types (comma-separated):")
                msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                allowed_types = [t.strip().lower() for t in msg.content.split(',')]
                rules['allowed_types'] = allowed_types

            elif tournament_type == 'level_cap':
                await ctx.send("Enter level cap (1-100):")
                msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                try:
                    level_cap = max(1, min(100, int(msg.content)))
                    rules['level_cap'] = level_cap
                except ValueError:
                    return await ctx.send("Invalid level cap!")

                await ctx.send("Scale Pokemon to cap? (yes/no)")
                msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                rules['scale_to_cap'] = msg.content.lower() == 'yes'

            # Get participant limit
            await ctx.send("What's the maximum number of participants?")
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
            try:
                max_participants = int(msg.content)
                if self.tournament_types[tournament_type]['requires_power_of_two']:
                    if not math.log2(max_participants).is_integer():
                        return await ctx.send("Participant count must be a power of 2 for this tournament type!")
            except ValueError:
                return await ctx.send("Invalid number!")

            # Get level range
            await ctx.send("What's the minimum Pokemon level required? (1-100)")
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
            try:
                min_level = max(1, min(100, int(msg.content)))
            except ValueError:
                return await ctx.send("Invalid level!")

            await ctx.send("What's the maximum Pokemon level allowed? (1-100)")
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
            try:
                max_level = max(min_level, min(100, int(msg.content)))
            except ValueError:
                return await ctx.send("Invalid level!")

            # Get entry fee
            await ctx.send("What's the entry fee? (in coins, 0 for free)")
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
            try:
                entry_fee = max(0, int(msg.content))
            except ValueError:
                return await ctx.send("Invalid amount!")

            # Create tournament
            tournament_id = await self.bot.db.fetchval(
                '''INSERT INTO pokemon_tournaments 
                   (name, tournament_type, max_participants, min_level, max_level, 
                    entry_fee, prize_pool, rules)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                   RETURNING id''',
                name, tournament_type, max_participants, min_level, max_level, 
                entry_fee, entry_fee * max_participants, json.dumps(rules)
            )

            embed = discord.Embed(
                title="Tournament Created!",
                description=f"Tournament **{name}** has been created!",
                color=discord.Color.green()
            )
            embed.add_field(name="ID", value=str(tournament_id), inline=True)
            embed.add_field(name="Type", value=tournament_type.replace('_', ' ').title(), inline=True)
            embed.add_field(name="Max Participants", value=str(max_participants), inline=True)
            embed.add_field(name="Level Range", value=f"{min_level}-{max_level}", inline=True)
            embed.add_field(name="Entry Fee", value=f"{entry_fee} coins", inline=True)
            embed.add_field(name="Prize Pool", value=f"{entry_fee * max_participants} coins", inline=True)
            
            if rules:
                rules_text = "\n".join(f"• {k}: {v}" for k, v in rules.items())
                embed.add_field(name="Special Rules", value=rules_text, inline=False)
            
            embed.add_field(
                name="How to Join",
                value=f"Use `!tournament join {tournament_id}` to participate!",
                inline=False
            )
            await ctx.send(embed=embed)

        except asyncio.TimeoutError:
            await ctx.send("Tournament creation cancelled - you took too long to respond!")

    @tournament.command(name='list')
    async def list_tournaments(self, ctx):
        """List active tournaments"""
        tournaments = await self.bot.db.fetch(
            '''SELECT * FROM pokemon_tournaments 
               WHERE status != 'completed' 
               ORDER BY created_at DESC'''
        )

        if not tournaments:
            return await ctx.send("No active tournaments found!")

        embed = discord.Embed(
            title="Active Pokemon Tournaments",
            color=discord.Color.blue()
        )

        for t in tournaments:
            participants = await self.bot.db.fetchval(
                'SELECT COUNT(*) FROM tournament_participants WHERE tournament_id = $1',
                t['id']
            )
            
            embed.add_field(
                name=f"{t['name']} (ID: {t['id']})",
                value=f"Type: {t['tournament_type'].replace('_', ' ').title()}\n"
                      f"Status: {t['status'].replace('_', ' ').title()}\n"
                      f"Participants: {participants}/{t['max_participants']}\n"
                      f"Level Range: {t['min_level']}-{t['max_level']}\n"
                      f"Entry Fee: {t['entry_fee']} coins\n"
                      f"Prize Pool: {t['prize_pool']} coins",
                inline=False
            )

        await ctx.send(embed=embed)

    @tournament.command(name='info')
    async def tournament_info(self, ctx, tournament_id: int):
        """Get detailed information about a tournament"""
        tournament = await self.bot.db.fetchrow(
            'SELECT * FROM pokemon_tournaments WHERE id = $1',
            tournament_id
        )

        if not tournament:
            return await ctx.send("Tournament not found!")

        participants = await self.bot.db.fetch(
            '''SELECT u.username, tp.current_wins, tp.current_losses, tp.eliminated
               FROM tournament_participants tp
               JOIN users u ON tp.user_id = u.id
               WHERE tp.tournament_id = $1
               ORDER BY tp.current_wins DESC''',
            tournament_id
        )

        embed = discord.Embed(
            title=f"Tournament: {tournament['name']}",
            color=discord.Color.blue()
        )

        embed.add_field(name="ID", value=str(tournament['id']), inline=True)
        embed.add_field(name="Type", value=tournament['tournament_type'].replace('_', ' ').title(), inline=True)
        embed.add_field(name="Status", value=tournament['status'].replace('_', ' ').title(), inline=True)
        embed.add_field(name="Level Range", value=f"{tournament['min_level']}-{tournament['max_level']}", inline=True)
        embed.add_field(name="Entry Fee", value=f"{tournament['entry_fee']} coins", inline=True)
        embed.add_field(name="Prize Pool", value=f"{tournament['prize_pool']} coins", inline=True)
        
        if participants:
            participant_list = []
            for p in participants:
                status = "🏆" if p['current_wins'] > 0 else "❌" if p['eliminated'] else "⏳"
                participant_list.append(
                    f"{status} {p['username']} (W: {p['current_wins']} L: {p['current_losses']})"
                )
            
            embed.add_field(
                name=f"Participants ({len(participants)}/{tournament['max_participants']})",
                value="\n".join(participant_list) if len(participant_list) <= 10 
                      else "\n".join(participant_list[:10]) + f"\n...and {len(participant_list)-10} more",
                inline=False
            )
        else:
            embed.add_field(
                name="Participants (0/{}})".format(tournament['max_participants']),
                value="No participants yet!",
                inline=False
            )

        await ctx.send(embed=embed)

    @tournament.command(name='join')
    async def join_tournament(self, ctx, tournament_id: int):
        """Join a tournament"""
        # Check if tournament exists and is accepting registrations
        tournament = await self.bot.db.fetchrow(
            '''SELECT * FROM pokemon_tournaments 
               WHERE id = $1 AND status = 'registering' ''',
            tournament_id
        )

        if not tournament:
            return await ctx.send("Tournament not found or not accepting registrations!")

        # Check if already registered
        existing = await self.bot.db.fetchrow(
            '''SELECT * FROM tournament_participants 
               WHERE tournament_id = $1 AND user_id = $2''',
            tournament_id, ctx.author.id
        )

        if existing:
            return await ctx.send("You're already registered for this tournament!")

        # Check participant limit
        participant_count = await self.bot.db.fetchval(
            'SELECT COUNT(*) FROM tournament_participants WHERE tournament_id = $1',
            tournament_id
        )

        if participant_count >= tournament['max_participants']:
            return await ctx.send("This tournament is full!")

        # Get user's eligible Pokemon based on tournament rules
        query = '''SELECT * FROM pokemon 
                  WHERE user_id = $1 
                  AND level BETWEEN $2 AND $3'''
        params = [ctx.author.id, tournament['min_level'], tournament['max_level']]

        # Apply special rules
        rules = json.loads(tournament['rules']) if tournament['rules'] else {}
        
        if tournament['tournament_type'] == 'type_restricted' and 'allowed_types' in rules:
            allowed_types = rules['allowed_types']
            # Note: This assumes Pokemon types are stored in the stats JSONB field
            query += " AND stats->>'types' ?| $4::text[]"
            params.append(allowed_types)

        elif tournament['tournament_type'] == 'level_cap' and 'level_cap' in rules:
            # Adjust query to respect level cap
            params[2] = min(tournament['max_level'], rules['level_cap'])

        pokemon = await self.bot.db.fetch(query, *params)

        if len(pokemon) < 6:
            type_restriction = ""
            if tournament['tournament_type'] == 'type_restricted':
                type_restriction = f" of type(s): {', '.join(rules['allowed_types'])}"
            
            level_range = f"{params[1]}-{params[2]}"
            return await ctx.send(
                f"You need 6 Pokemon{type_restriction} between levels {level_range} to participate!"
            )

        # Check if user has enough coins for entry fee
        if tournament['entry_fee'] > 0:
            user_coins = await self.bot.db.fetchval(
                'SELECT currency FROM users WHERE id = $1',
                ctx.author.id
            )

            if user_coins < tournament['entry_fee']:
                return await ctx.send(
                    f"You need {tournament['entry_fee']} coins to enter this tournament!"
                )

            # Deduct entry fee
            await self.bot.db.execute(
                'UPDATE users SET currency = currency - $1 WHERE id = $2',
                tournament['entry_fee'], ctx.author.id
            )

        # Show user's eligible Pokemon and let them choose their team
        pokemon_list = []
        for i, p in enumerate(pokemon[:12], 1):  # Show up to 12 Pokemon
            # Get Pokemon types from stats
            stats = json.loads(p['stats'])
            types = stats.get('types', ['Normal'])
            types_str = '/'.join(t.title() for t in types)
            
            pokemon_list.append(
                f"{i}. Level {p['level']} {p['name'].title()} ({types_str})"
            )

        embed = discord.Embed(
            title="Choose Your Tournament Team",
            description="Select 6 Pokemon by number (comma-separated):\n" + "\n".join(pokemon_list),
            color=discord.Color.blue()
        )

        if rules:
            rules_text = []
            if 'level_cap' in rules:
                rules_text.append(f"Level Cap: {rules['level_cap']}")
                if rules.get('scale_to_cap'):
                    rules_text.append("Pokemon will be scaled to level cap")
            if 'allowed_types' in rules:
                rules_text.append(f"Allowed Types: {', '.join(rules['allowed_types'])}")
            
            embed.add_field(
                name="Tournament Rules",
                value="\n".join(rules_text),
                inline=False
            )

        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', timeout=60.0, check=check)
            choices = [int(x.strip()) for x in msg.content.split(',')]
            
            if len(choices) != 6 or not all(1 <= x <= len(pokemon_list) for x in choices):
                await self.bot.db.execute(
                    'UPDATE users SET currency = currency + $1 WHERE id = $2',
                    tournament['entry_fee'], ctx.author.id
                )
                return await ctx.send("Invalid selection! Registration cancelled.")

            # Get chosen Pokemon
            chosen_pokemon = [pokemon[i-1] for i in choices]

            # Apply level cap scaling if needed
            if (tournament['tournament_type'] == 'level_cap' and 
                rules.get('scale_to_cap') and 
                'level_cap' in rules):
                level_cap = rules['level_cap']
                for p in chosen_pokemon:
                    if p['level'] > level_cap:
                        # Scale stats to level cap
                        stats = json.loads(p['stats'])
                        scale_factor = level_cap / p['level']
                        for stat in ['hp', 'attack', 'defense', 'special-attack', 'special-defense', 'speed']:
                            if stat in stats:
                                stats[stat] = int(stats[stat] * scale_factor)
                        p['stats'] = json.dumps(stats)
                        p['level'] = level_cap

            # Register for tournament
            chosen_pokemon_ids = [p['id'] for p in chosen_pokemon]
            await self.bot.db.execute(
                '''INSERT INTO tournament_participants 
                   (tournament_id, user_id, pokemon_ids)
                   VALUES ($1, $2, $3)''',
                tournament_id, ctx.author.id, chosen_pokemon_ids
            )

            # Create confirmation embed
            embed = discord.Embed(
                title="Tournament Registration Complete!",
                description=f"You've successfully registered for {tournament['name']}!",
                color=discord.Color.green()
            )

            team_list = []
            for p in chosen_pokemon:
                stats = json.loads(p['stats'])
                types = stats.get('types', ['Normal'])
                types_str = '/'.join(t.title() for t in types)
                team_list.append(f"• Level {p['level']} {p['name'].title()} ({types_str})")

            embed.add_field(
                name="Your Team",
                value="\n".join(team_list),
                inline=False
            )

            await ctx.send(embed=embed)

        except asyncio.TimeoutError:
            await self.bot.db.execute(
                'UPDATE users SET currency = currency + $1 WHERE id = $2',
                tournament['entry_fee'], ctx.author.id
            )
            await ctx.send("Registration cancelled - you took too long to choose your team!")

    @tournament.command(name='leave')
    async def leave_tournament(self, ctx, tournament_id: int):
        """Leave a tournament"""
        # Check if tournament exists and is still in registration
        tournament = await self.bot.db.fetchrow(
            '''SELECT * FROM pokemon_tournaments 
               WHERE id = $1 AND status = 'registering' ''',
            tournament_id
        )

        if not tournament:
            return await ctx.send("Tournament not found or already in progress!")

        # Check if registered
        participant = await self.bot.db.fetchrow(
            '''SELECT * FROM tournament_participants 
               WHERE tournament_id = $1 AND user_id = $2''',
            tournament_id, ctx.author.id
        )

        if not participant:
            return await ctx.send("You're not registered for this tournament!")

        # Remove from tournament
        await self.bot.db.execute(
            '''DELETE FROM tournament_participants 
               WHERE tournament_id = $1 AND user_id = $2''',
            tournament_id, ctx.author.id
        )

        # Refund entry fee
        if tournament['entry_fee'] > 0:
            await self.bot.db.execute(
                'UPDATE users SET currency = currency + $1 WHERE id = $2',
                tournament['entry_fee'], ctx.author.id
            )

        await ctx.send("You've successfully left the tournament and received a refund of the entry fee!")

    @tournament.command(name='start')
    @commands.has_permissions(administrator=True)
    async def start_tournament(self, ctx, tournament_id: int):
        """Start a tournament"""
        # Check if tournament exists and is in registration
        tournament = await self.bot.db.fetchrow(
            '''SELECT * FROM pokemon_tournaments 
               WHERE id = $1 AND status = 'registering' ''',
            tournament_id
        )

        if not tournament:
            return await ctx.send("Tournament not found or already in progress!")

        # Get participants
        participants = await self.bot.db.fetch(
            'SELECT user_id FROM tournament_participants WHERE tournament_id = $1',
            tournament_id
        )

        if not participants:
            return await ctx.send("Can't start tournament - no participants!")

        if tournament['tournament_type'] in ['single_elimination', 'double_elimination']:
            if not math.log2(len(participants)).is_integer():
                return await ctx.send(
                    f"Need a power of 2 participants for elimination tournament! "
                    f"Current: {len(participants)}"
                )

        # Generate first round matches
        participant_ids = [p['user_id'] for p in participants]
        random.shuffle(participant_ids)

        # Create matches
        match_number = 1
        for i in range(0, len(participant_ids), 2):
            await self.bot.db.execute(
                '''INSERT INTO tournament_matches 
                   (tournament_id, round, match_number, player1_id, player2_id)
                   VALUES ($1, 1, $2, $3, $4)''',
                tournament_id, match_number,
                participant_ids[i],
                participant_ids[i+1] if i+1 < len(participant_ids) else None
            )
            match_number += 1

        # Update tournament status
        await self.bot.db.execute(
            '''UPDATE pokemon_tournaments 
               SET status = 'in_progress', started_at = CURRENT_TIMESTAMP
               WHERE id = $1''',
            tournament_id
        )

        # Announce tournament start
        embed = discord.Embed(
            title=f"Tournament {tournament['name']} has begun!",
            description="The first round matches have been generated.",
            color=discord.Color.green()
        )
        
        matches = await self.bot.db.fetch(
            '''SELECT m.*, u1.username as player1_name, u2.username as player2_name
               FROM tournament_matches m
               LEFT JOIN users u1 ON m.player1_id = u1.id
               LEFT JOIN users u2 ON m.player2_id = u2.id
               WHERE m.tournament_id = $1 AND m.round = 1
               ORDER BY m.match_number''',
            tournament_id
        )

        match_list = []
        for match in matches:
            if match['player2_id']:
                match_list.append(
                    f"Match {match['match_number']}: "
                    f"{match['player1_name']} vs {match['player2_name']}"
                )
            else:
                match_list.append(
                    f"Match {match['match_number']}: "
                    f"{match['player1_name']} receives a bye"
                )

        embed.add_field(
            name="First Round Matches",
            value="\n".join(match_list),
            inline=False
        )

        await ctx.send(embed=embed)

    @tournament.command(name='bracket')
    async def view_bracket(self, ctx, tournament_id: int):
        """View the tournament bracket"""
        tournament = await self.bot.db.fetchrow(
            'SELECT * FROM pokemon_tournaments WHERE id = $1',
            tournament_id
        )

        if not tournament:
            return await ctx.send("Tournament not found!")

        matches = await self.bot.db.fetch(
            '''SELECT m.*, 
                      u1.username as player1_name, 
                      u2.username as player2_name,
                      u3.username as winner_name
               FROM tournament_matches m
               LEFT JOIN users u1 ON m.player1_id = u1.id
               LEFT JOIN users u2 ON m.player2_id = u2.id
               LEFT JOIN users u3 ON m.winner_id = u3.id
               WHERE m.tournament_id = $1
               ORDER BY m.round, m.match_number''',
            tournament_id
        )

        if not matches:
            return await ctx.send("No matches found for this tournament!")

        embed = discord.Embed(
            title=f"Tournament Bracket: {tournament['name']}",
            color=discord.Color.blue()
        )

        current_round = 0
        match_list = []
        for match in matches:
            if match['round'] != current_round:
                if match_list:
                    embed.add_field(
                        name=f"Round {current_round}",
                        value="\n".join(match_list),
                        inline=False
                    )
                current_round = match['round']
                match_list = []

            status = "🏆" if match['winner_id'] else "⏳"
            if match['player2_id']:
                match_list.append(
                    f"Match {match['match_number']}: {status} "
                    f"{match['player1_name']} vs {match['player2_name']}"
                    f"{' → ' + match['winner_name'] if match['winner_id'] else ''}"
                )
            else:
                match_list.append(
                    f"Match {match['match_number']}: {status} "
                    f"{match['player1_name']} (bye)"
                )

        if match_list:
            embed.add_field(
                name=f"Round {current_round}",
                value="\n".join(match_list),
                inline=False
            )

        await ctx.send(embed=embed)

    @tournament.command(name='matches')
    async def view_matches(self, ctx):
        """View your upcoming tournament matches"""
        matches = await self.bot.db.fetch(
            '''SELECT m.*, t.name as tournament_name,
                      u1.username as player1_name, 
                      u2.username as player2_name
               FROM tournament_matches m
               JOIN pokemon_tournaments t ON m.tournament_id = t.id
               LEFT JOIN users u1 ON m.player1_id = u1.id
               LEFT JOIN users u2 ON m.player2_id = u2.id
               WHERE (m.player1_id = $1 OR m.player2_id = $1)
                     AND m.winner_id IS NULL
                     AND t.status = 'in_progress'
               ORDER BY t.id, m.round, m.match_number''',
            ctx.author.id
        )

        if not matches:
            return await ctx.send("You have no upcoming tournament matches!")

        embed = discord.Embed(
            title="Your Tournament Matches",
            color=discord.Color.blue()
        )

        for match in matches:
            embed.add_field(
                name=f"{match['tournament_name']} - Round {match['round']}",
                value=f"Match {match['match_number']}: "
                      f"{match['player1_name']} vs {match['player2_name']}",
                inline=False
            )

        await ctx.send(embed=embed)

    @tournament.command(name='battle')
    async def tournament_battle(self, ctx, tournament_id: int, match_number: int):
        """Start a tournament match battle"""
        # Check if match exists and user is part of it
        match = await self.bot.db.fetchrow(
            '''SELECT m.*, t.name as tournament_name,
                      u1.username as player1_name, 
                      u2.username as player2_name,
                      tp1.pokemon_ids as player1_pokemon,
                      tp2.pokemon_ids as player2_pokemon
               FROM tournament_matches m
               JOIN pokemon_tournaments t ON m.tournament_id = t.id
               LEFT JOIN users u1 ON m.player1_id = u1.id
               LEFT JOIN users u2 ON m.player2_id = u2.id
               LEFT JOIN tournament_participants tp1 ON (tp1.tournament_id = m.tournament_id AND tp1.user_id = m.player1_id)
               LEFT JOIN tournament_participants tp2 ON (tp2.tournament_id = m.tournament_id AND tp2.user_id = m.player2_id)
               WHERE m.tournament_id = $1 
                     AND m.match_number = $2
                     AND m.winner_id IS NULL
                     AND t.status = 'in_progress' ''',
            tournament_id, match_number
        )

        if not match:
            return await ctx.send("Match not found or already completed!")

        if ctx.author.id not in [match['player1_id'], match['player2_id']]:
            return await ctx.send("You're not part of this match!")

        if match['status'] == 'in_progress':
            return await ctx.send("This match is already in progress!")

        # Get opponent
        opponent_id = match['player2_id'] if ctx.author.id == match['player1_id'] else match['player1_id']
        opponent = ctx.guild.get_member(opponent_id)
        if not opponent:
            return await ctx.send("Couldn't find opponent!")

        # Update match status
        await self.bot.db.execute(
            '''UPDATE tournament_matches 
               SET status = 'in_progress', started_at = CURRENT_TIMESTAMP
               WHERE tournament_id = $1 AND match_number = $2''',
            tournament_id, match_number
        )

        # Get Pokemon teams
        player_pokemon = await self.bot.db.fetch(
            'SELECT * FROM pokemon WHERE id = ANY($1)',
            match['player1_pokemon'] if ctx.author.id == match['player1_id'] else match['player2_pokemon']
        )
        opponent_pokemon = await self.bot.db.fetch(
            'SELECT * FROM pokemon WHERE id = ANY($1)',
            match['player2_pokemon'] if ctx.author.id == match['player1_id'] else match['player1_pokemon']
        )

        # Create battle data
        battle_data = {
            'tournament_id': tournament_id,
            'match_number': match_number,
            'trainers': {
                ctx.author.id: {
                    'pokemon': player_pokemon,
                    'current_pokemon': 0,
                    'current_hp': self.calculate_hp(player_pokemon[0]),
                    'fainted_pokemon': []
                },
                opponent.id: {
                    'pokemon': opponent_pokemon,
                    'current_pokemon': 0,
                    'current_hp': self.calculate_hp(opponent_pokemon[0]),
                    'fainted_pokemon': []
                }
            },
            'current_turn': ctx.author.id,
            'message': None
        }

        self.active_tournament_battles[ctx.channel.id] = battle_data

        # Send initial battle message
        embed = await self.create_tournament_battle_embed(ctx, battle_data)
        battle_data['message'] = await ctx.send(embed=embed)

        await ctx.send(
            f"Tournament battle between {ctx.author.mention} and {opponent.mention} has begun!\n"
            f"Use `!tournament attack <move>` to use a move!"
        )

    @tournament.command(name='attack')
    async def tournament_attack(self, ctx, move_name: str):
        """Use a move in a tournament battle"""
        if ctx.channel.id not in self.active_tournament_battles:
            return await ctx.send("No active tournament battle in this channel!")

        battle = self.active_tournament_battles[ctx.channel.id]
        if ctx.author.id != battle['current_turn']:
            return await ctx.send("It's not your turn!")

        try:
            # Get attacker and defender data
            attacker = battle['trainers'][ctx.author.id]
            defender = battle['trainers'][
                next(uid for uid in battle['trainers'] if uid != ctx.author.id)
            ]

            # Get current Pokemon
            attacker_pokemon = attacker['pokemon'][attacker['current_pokemon']]
            defender_pokemon = defender['pokemon'][defender['current_pokemon']]

            # Get move data
            move_data = await self.get_move_data(move_name.lower())
            if not move_data:
                return await ctx.send("Invalid move!")

            # Calculate damage
            damage = self.calculate_tournament_damage(attacker_pokemon, defender_pokemon, move_data)
            
            # Apply damage
            defender['current_hp'] = max(0, defender['current_hp'] - damage)

            # Create move result message
            await ctx.send(f"{attacker_pokemon['name'].title()} used {move_name.title()}!")
            if damage > 0:
                await ctx.send(f"Dealt {damage} damage!")

            # Update battle display
            await self.update_tournament_battle_embed(ctx)

            # Check if defender's Pokemon fainted
            if defender['current_hp'] == 0:
                await ctx.send(f"{defender_pokemon['name'].title()} fainted!")
                defender['fainted_pokemon'].append(defender['current_pokemon'])

                # Check if all Pokemon have fainted
                if len(defender['fainted_pokemon']) == len(defender['pokemon']):
                    await self.handle_tournament_victory(ctx, ctx.author.id)
                    return

                # Switch to next Pokemon
                for i in range(len(defender['pokemon'])):
                    if i not in defender['fainted_pokemon']:
                        defender['current_pokemon'] = i
                        defender['current_hp'] = self.calculate_hp(defender['pokemon'][i])
                        break

                await ctx.send(
                    f"Opponent sends out {defender['pokemon'][defender['current_pokemon']]['name'].title()}!"
                )
                await self.update_tournament_battle_embed(ctx)

            # Switch turns
            battle['current_turn'] = next(uid for uid in battle['trainers'] if uid != ctx.author.id)
            trainer = ctx.guild.get_member(battle['current_turn'])
            await ctx.send(f"{trainer.mention}'s turn!")

        except Exception as e:
            await ctx.send(f"Error processing move: {e}")

    async def handle_tournament_victory(self, ctx, winner_id):
        """Handle tournament battle victory"""
        battle = self.active_tournament_battles[ctx.channel.id]
        
        # Update match result
        await self.bot.db.execute(
            '''UPDATE tournament_matches 
               SET winner_id = $1, 
                   status = 'completed',
                   completed_at = CURRENT_TIMESTAMP
               WHERE tournament_id = $1 AND match_number = $2''',
            winner_id, battle['tournament_id'], battle['match_number']
        )

        # Update participant stats
        await self.bot.db.execute(
            '''UPDATE tournament_participants 
               SET current_wins = current_wins + 1
               WHERE tournament_id = $1 AND user_id = $2''',
            battle['tournament_id'], winner_id
        )

        loser_id = next(uid for uid in battle['trainers'] if uid != winner_id)
        await self.bot.db.execute(
            '''UPDATE tournament_participants 
               SET current_losses = current_losses + 1,
                   eliminated = $3
               WHERE tournament_id = $1 AND user_id = $2''',
            battle['tournament_id'], loser_id,
            True  # Eliminated in single/double elimination tournaments
        )

        # Get tournament info
        tournament = await self.bot.db.fetchrow(
            'SELECT * FROM pokemon_tournaments WHERE id = $1',
            battle['tournament_id']
        )

        # Check if tournament is complete
        remaining_matches = await self.bot.db.fetchval(
            '''SELECT COUNT(*) FROM tournament_matches 
               WHERE tournament_id = $1 AND winner_id IS NULL''',
            battle['tournament_id']
        )

        if remaining_matches == 0:
            # Tournament complete
            await self.bot.db.execute(
                '''UPDATE pokemon_tournaments 
                   SET status = 'completed',
                       completed_at = CURRENT_TIMESTAMP
                   WHERE id = $1''',
                battle['tournament_id']
            )

            # Award prize money
            await self.bot.db.execute(
                'UPDATE users SET currency = currency + $1 WHERE id = $2',
                tournament['prize_pool'], winner_id
            )

            winner = ctx.guild.get_member(winner_id)
            embed = discord.Embed(
                title="🏆 Tournament Complete! 🏆",
                description=f"Congratulations to {winner.mention} for winning {tournament['name']}!",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="Prize",
                value=f"{tournament['prize_pool']} coins",
                inline=False
            )
            await ctx.send(embed=embed)
        else:
            # Generate next round matches if needed
            await self.generate_next_round_matches(ctx, battle['tournament_id'])

            winner = ctx.guild.get_member(winner_id)
            await ctx.send(f"🎉 {winner.mention} wins the match!")

        # Clean up battle data
        del self.active_tournament_battles[ctx.channel.id]

    async def generate_next_round_matches(self, ctx, tournament_id: int):
        """Generate matches for the next tournament round"""
        # Get current round number
        current_round = await self.bot.db.fetchval(
            'SELECT MAX(round) FROM tournament_matches WHERE tournament_id = $1',
            tournament_id
        )

        # Get winners from current round
        winners = await self.bot.db.fetch(
            '''SELECT winner_id, match_number 
               FROM tournament_matches 
               WHERE tournament_id = $1 AND round = $2
               ORDER BY match_number''',
            tournament_id, current_round
        )

        # Check if all matches in current round are complete
        if len(winners) % 2 == 0 and all(w['winner_id'] for w in winners):
            # Create next round matches
            next_round = current_round + 1
            match_number = await self.bot.db.fetchval(
                'SELECT MAX(match_number) FROM tournament_matches WHERE tournament_id = $1',
                tournament_id
            ) + 1

            for i in range(0, len(winners), 2):
                await self.bot.db.execute(
                    '''INSERT INTO tournament_matches 
                       (tournament_id, round, match_number, player1_id, player2_id)
                       VALUES ($1, $2, $3, $4, $5)''',
                    tournament_id, next_round, match_number,
                    winners[i]['winner_id'],
                    winners[i+1]['winner_id'] if i+1 < len(winners) else None
                )
                match_number += 1

            # Announce next round
            embed = discord.Embed(
                title=f"Round {next_round} Matches",
                color=discord.Color.blue()
            )

            matches = await self.bot.db.fetch(
                '''SELECT m.*, u1.username as player1_name, u2.username as player2_name
                   FROM tournament_matches m
                   LEFT JOIN users u1 ON m.player1_id = u1.id
                   LEFT JOIN users u2 ON m.player2_id = u2.id
                   WHERE m.tournament_id = $1 AND m.round = $2
                   ORDER BY m.match_number''',
                tournament_id, next_round
            )

            for match in matches:
                if match['player2_id']:
                    embed.add_field(
                        name=f"Match {match['match_number']}",
                        value=f"{match['player1_name']} vs {match['player2_name']}",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"Match {match['match_number']}",
                        value=f"{match['player1_name']} receives a bye",
                        inline=False
                    )

            await ctx.send(embed=embed)

    async def create_tournament_battle_embed(self, ctx, battle: Dict) -> discord.Embed:
        """Create the tournament battle status embed"""
        embed = discord.Embed(
            title="Tournament Battle",
            color=discord.Color.blue()
        )

        for trainer_id, data in battle['trainers'].items():
            if data:  # Skip if trainer hasn't chosen Pokemon yet
                trainer = ctx.guild.get_member(trainer_id)
                pokemon = data['pokemon'][data['current_pokemon']]
                
                hp_percent = int(data['current_hp'] / self.calculate_hp(pokemon) * 100)
                hp_bar = '█' * (hp_percent // 10) + '░' * (10 - hp_percent // 10)
                
                pokemon_list = []
                for i, p in enumerate(data['pokemon']):
                    status = "💀" if i in data['fainted_pokemon'] else "⚔️" if i == data['current_pokemon'] else "⏳"
                    pokemon_list.append(f"{status} {p['name'].title()} (Lv.{p['level']})")
                
                embed.add_field(
                    name=f"{trainer.display_name}'s Team",
                    value=f"**Active: {pokemon['name'].title()} (Lv.{pokemon['level']})**\n"
                          f"HP: {data['current_hp']}/{self.calculate_hp(pokemon)} [{hp_bar}]\n"
                          f"Team:\n" + "\n".join(pokemon_list),
                    inline=False
                )

        return embed

    async def update_tournament_battle_embed(self, ctx):
        """Update the tournament battle status embed"""
        battle = self.active_tournament_battles.get(ctx.channel.id)
        if not battle:
            return

        embed = await self.create_tournament_battle_embed(ctx, battle)
        
        # Update for players
        if battle['message']:
            await battle['message'].edit(embed=embed)
        
        # Update for spectators
        if ctx.channel.id in self.spectators:
            for spectator_id in self.spectators[ctx.channel.id]:
                spectator = ctx.guild.get_member(spectator_id)
                if spectator:
                    try:
                        # Send update to spectator's DM
                        await spectator.send(embed=embed)
                    except discord.Forbidden:
                        # Remove spectator if we can't DM them
                        self.spectators[ctx.channel.id].remove(spectator_id)

    def calculate_tournament_damage(self, attacker: Dict, defender: Dict, move: Dict) -> int:
        """Calculate damage for a tournament battle move"""
        # Base damage calculation
        level = attacker['level']
        if move['power'] is None:
            return 0
        
        # Get attack and defense stats
        attacker_stats = json.loads(attacker['stats'])
        defender_stats = json.loads(defender['stats'])
        
        if move['damage_class']['name'] == 'physical':
            attack = attacker_stats.get('attack', 50)
            defense = defender_stats.get('defense', 50)
        else:
            attack = attacker_stats.get('special-attack', 50)
            defense = defender_stats.get('special-defense', 50)
        
        # Calculate base damage
        damage = ((2 * level / 5 + 2) * move['power'] * attack / defense / 50) + 2
        
        # Apply random factor (85-100%)
        damage *= random.uniform(0.85, 1.0)
        
        return int(damage)

    async def get_move_data(self, move_name: str) -> Optional[Dict]:
        """Get move data from PokeAPI"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://pokeapi.co/api/v2/move/{move_name}') as resp:
                if resp.status == 200:
                    return await resp.json()
                return None

    def calculate_hp(self, pokemon: Dict) -> int:
        """Calculate max HP for a Pokemon"""
        base_hp = 50  # Default base HP
        if isinstance(pokemon.get('stats'), str):
            stats = json.loads(pokemon['stats'])
            base_hp = stats.get('hp', 50)
        elif isinstance(pokemon.get('stats'), dict):
            base_hp = pokemon['stats'].get('hp', 50)
        
        return int((2 * base_hp * pokemon['level']) / 100 + pokemon['level'] + 10)

    @tournament.command(name='leaderboard')
    async def tournament_leaderboard(self, ctx):
        """View tournament leaderboard"""
        # Get tournament statistics for all users
        leaderboard = await self.bot.db.fetch(
            '''WITH tournament_stats AS (
                   SELECT user_id,
                          COUNT(*) as tournaments_entered,
                          COUNT(*) FILTER (WHERE eliminated = false) as tournaments_won,
                          SUM(current_wins) as total_wins,
                          SUM(current_losses) as total_losses
                   FROM tournament_participants
                   GROUP BY user_id
               )
               SELECT u.username,
                      ts.tournaments_entered,
                      ts.tournaments_won,
                      ts.total_wins,
                      ts.total_losses,
                      CASE WHEN ts.total_wins + ts.total_losses > 0
                           THEN ROUND(ts.total_wins::numeric / (ts.total_wins + ts.total_losses) * 100, 1)
                           ELSE 0
                      END as win_rate
               FROM tournament_stats ts
               JOIN users u ON ts.user_id = u.id
               ORDER BY tournaments_won DESC, win_rate DESC
               LIMIT 10'''
        )

        if not leaderboard:
            return await ctx.send("No tournament data available!")

        embed = discord.Embed(
            title="Tournament Leaderboard",
            color=discord.Color.gold()
        )

        for i, stats in enumerate(leaderboard, 1):
            embed.add_field(
                name=f"{i}. {stats['username']}",
                value=f"🏆 Tournaments Won: {stats['tournaments_won']}\n"
                      f"🎮 Tournaments Entered: {stats['tournaments_entered']}\n"
                      f"✨ Total Wins: {stats['total_wins']}\n"
                      f"💢 Total Losses: {stats['total_losses']}\n"
                      f"📊 Win Rate: {stats['win_rate']}%",
                inline=False
            )

        await ctx.send(embed=embed)

    @tournament.command(name='history')
    async def tournament_history(self, ctx, user: discord.Member = None):
        """View tournament history for a user"""
        target_user = user or ctx.author

        # Get user's tournament history
        history = await self.bot.db.fetch(
            '''SELECT t.name, t.tournament_type, t.completed_at,
                      tp.current_wins, tp.current_losses, tp.eliminated
               FROM tournament_participants tp
               JOIN pokemon_tournaments t ON tp.tournament_id = t.id
               WHERE tp.user_id = $1 AND t.status = 'completed'
               ORDER BY t.completed_at DESC
               LIMIT 10''',
            target_user.id
        )

        if not history:
            return await ctx.send(f"No tournament history found for {target_user.display_name}!")

        embed = discord.Embed(
            title=f"Tournament History - {target_user.display_name}",
            color=discord.Color.blue()
        )

        for entry in history:
            result = "🏆 Winner!" if not entry['eliminated'] else "❌ Eliminated"
            embed.add_field(
                name=f"{entry['name']} ({entry['tournament_type'].replace('_', ' ').title()})",
                value=f"Result: {result}\n"
                      f"Record: {entry['current_wins']}W - {entry['current_losses']}L\n"
                      f"Date: {entry['completed_at'].strftime('%Y-%m-%d')}",
                inline=False
            )

        await ctx.send(embed=embed)

    @tournament.command(name='rules')
    async def tournament_rules(self, ctx, tournament_id: int = None):
        """View tournament rules and types"""
        if tournament_id:
            # Show rules for specific tournament
            tournament = await self.bot.db.fetchrow(
                'SELECT * FROM pokemon_tournaments WHERE id = $1',
                tournament_id
            )

            if not tournament:
                return await ctx.send("Tournament not found!")

            embed = discord.Embed(
                title=f"Rules - {tournament['name']}",
                description=f"Type: {tournament['tournament_type'].replace('_', ' ').title()}",
                color=discord.Color.blue()
            )

            embed.add_field(
                name="Level Range",
                value=f"Min: {tournament['min_level']}\nMax: {tournament['max_level']}",
                inline=True
            )

            embed.add_field(
                name="Entry Fee",
                value=f"{tournament['entry_fee']} coins",
                inline=True
            )

            embed.add_field(
                name="Prize Pool",
                value=f"{tournament['prize_pool']} coins",
                inline=True
            )

            if tournament['rules']:
                rules = json.loads(tournament['rules'])
                for rule, value in rules.items():
                    embed.add_field(
                        name=rule.replace('_', ' ').title(),
                        value=str(value),
                        inline=False
                    )

        else:
            # Show all tournament types and their rules
            embed = discord.Embed(
                title="Tournament Types and Rules",
                color=discord.Color.blue()
            )

            for t_type, data in self.tournament_types.items():
                rules_text = "\n".join(f"• {k}: {v}" for k, v in data['rules'].items()) if data['rules'] else "No special rules"
                embed.add_field(
                    name=t_type.replace('_', ' ').title(),
                    value=f"{data['description']}\n\nRules:\n{rules_text}",
                    inline=False
                )

        await ctx.send(embed=embed)

    @tournament.command(name='spectate')
    async def spectate_match(self, ctx, tournament_id: int, match_number: int):
        """Spectate an ongoing tournament match"""
        try:
            # Check if match exists and is in progress
            match = await self.bot.db.fetchrow(
                '''SELECT * FROM tournament_matches 
                   WHERE tournament_id = $1 AND match_number = $2 
                   AND status = 'in_progress' ''',
                tournament_id, match_number
            )
            if not match:
                return await ctx.send("No active match found with those details!")

            # Add spectator to the match
            if ctx.channel.id not in self.spectators:
                self.spectators[ctx.channel.id] = set()
            
            self.spectators[ctx.channel.id].add(ctx.author.id)
            
            # Get battle data
            battle = self.active_battles.get(ctx.channel.id)
            if battle:
                # Send current battle state to new spectator
                embed = await self.create_tournament_battle_embed(ctx, battle)
                await ctx.author.send(embed=embed)
                await ctx.send(f"{ctx.author.mention} is now spectating the match!")
            
        except Exception as e:
            await ctx.send(f"Error starting spectator mode: {e}")

    @tournament.command(name='leave_spectate')
    async def leave_spectate(self, ctx):
        """Leave spectator mode for the current match"""
        if ctx.channel.id in self.spectators and ctx.author.id in self.spectators[ctx.channel.id]:
            self.spectators[ctx.channel.id].remove(ctx.author.id)
            await ctx.send(f"{ctx.author.mention} is no longer spectating.")
        else:
            await ctx.send("You are not spectating any match in this channel!")

    @tournament.command(name='spectators')
    async def list_spectators(self, ctx, tournament_id: int, match_number: int):
        """List all spectators for a specific match"""
        try:
            # Check if match exists
            match = await self.bot.db.fetchrow(
                'SELECT * FROM tournament_matches WHERE tournament_id = $1 AND match_number = $2',
                tournament_id, match_number
            )
            if not match:
                return await ctx.send("Match not found!")

            if ctx.channel.id not in self.spectators or not self.spectators[ctx.channel.id]:
                return await ctx.send("No spectators for this match!")

            # Create spectator list
            spectator_list = []
            for spectator_id in self.spectators[ctx.channel.id]:
                spectator = ctx.guild.get_member(spectator_id)
                if spectator:
                    spectator_list.append(spectator.display_name)

            # Create embed
            embed = discord.Embed(
                title=f"Match Spectators",
                description=f"Tournament ID: {tournament_id}\nMatch Number: {match_number}",
                color=discord.Color.blue()
            )
            embed.add_field(
                name=f"Spectators ({len(spectator_list)})",
                value="\n".join(spectator_list) if spectator_list else "No spectators",
                inline=False
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error listing spectators: {e}")

async def setup(bot):
    await bot.add_cog(PokemonTournament(bot)) 