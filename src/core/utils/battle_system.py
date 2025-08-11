"""
Battle system commands for the bot.

This cog defines the commands for initiating and managing battles, which can be
of different types like OSRS, Pokemon, or Pets. Each battle type has its own
mechanics while sharing common battle management features like turn handling,
status tracking, and rewards.

Typical usage:
    @bot.command()
    async def fight(ctx, opponent: discord.Member):
        battle_commands = BattleCommands(bot)
        await battle_commands.battle_osrs(ctx, opponent)
"""
from typing import Any, Dict

import discord
from discord import ButtonStyle
from discord.ext import commands
from discord.ui import Button, View

from src.core.battle_logging import BattleLogger
from src.core.battle_manager import BattleManager, BattleType
from src.osrs.battle_system import OSRSBattleSystem
from src.pets.battle_system import PetBattleSystem
from src.pokemon.battle_system import PokemonBattleSystem


class BattleCommands(commands.Cog):
    """Cog that handles all battle-related commands and interactions.
    This cog provides commands for starting and managing battles between users,
    handling battle moves, and tracking battle status. It supports multiple
    battle systems through a unified interface.
    Attributes:
        bot: The Discord bot instance
        battle_manager: Manager for tracking active battles
        logger: Logger for battle events
        battle_systems: Dict mapping battle types to their implementations
    """

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize battle commands cog.
        Args:
            bot: The Discord bot instance to attach to
        """
        self.bot = bot
        self.battle_manager = BattleManager()
        self.logger = BattleLogger()
        self.battle_systems = {
            BattleType.OSRS: OSRSBattleSystem(),
            BattleType.POKEMON: PokemonBattleSystem(),
            BattleType.PET: PetBattleSystem(),
        }

    @commands.group(invoke_without_command=True)
    async def battle(self, ctx: commands.Context) -> None:
        """⚔️ Battle System
        Choose your battle type:
        🗡️ OSRS Combat (!battle osrs)
        🐲 Pokemon Battles (!battle pokemon)
        🐾 Pet Battles (!battle pet)
        Start a battle with:
        !battle <type> @opponent
        During battle:
        !battle move <name> - Use a move
        !battle status - Check battle status
        !battle forfeit - Give up
        Example:
        !battle osrs @friendname
        !battle move slash"""
        await ctx.send_help(ctx.command)

    @battle.command(name="osrs")
    async def battle_osrs(self, ctx: commands.Context, opponent: discord.Member) -> None:
        """Start an OSRS style battle."""
        await self._start_battle(ctx, opponent, BattleType.OSRS)

    @battle.command(name="pokemon")
    async def battle_pokemon(self, ctx: commands.Context, opponent: discord.Member) -> None:
        """Start a Pokemon battle."""
        await self._start_battle(ctx, opponent, BattleType.POKEMON)

    @battle.command(name="pet")
    async def battle_pet(self, ctx: commands.Context, opponent: discord.Member) -> None:
        """Start a pet battle."""
        await self._start_battle(ctx, opponent, BattleType.PET)

    @battle.command(name="move")
    async def battle_move(self, ctx: commands.Context, *, move: str) -> None:
        """Make a move in your current battle."""
        # Get player's active battle
        battle = self.battle_manager.get_player_battle(ctx.author.id)
        if not battle:
            await ctx.send("You're not in a battle!")
            return

        # Get appropriate battle system
        battle_system = self.battle_systems[battle.battle_type]

        # Validate move
        if not battle_system.is_valid_move(battle, move, ctx.author.id):
            moves = battle_system.get_available_moves(battle, ctx.author.id)
            await ctx.send(f"Invalid move! Available moves: {', '.join(moves)}")
            return

        # Process the turn
        result = battle_system.process_turn(battle, move)

        # Record turn in history
        self.battle_manager.record_turn(battle.battle_id, move, result)
        self.logger.log_turn(battle.battle_id, ctx.author.id, move, result)

        # Create battle embed
        embed = discord.Embed(
            title="⚔️ Battle Move!",
            description=result["message"],
            color=discord.Color.blue(),
        )

        # Add damage field if applicable
        if "damage" in result:
            embed.add_field(name="Damage", value=str(result["damage"]), inline=True)

        # Add energy/resource field if applicable
        if "attacker_energy" in result:
            embed.add_field(name="Energy", value=str(result["attacker_energy"]), inline=True)

        # Check for battle end
        if "defender_hp" in result and result["defender_hp"] <= 0:
            winner = ctx.author
            embed.add_field(
                name="🏆 Battle End!",
                value=f"{winner.mention} wins the battle!",
                inline=False,
            )
            winner_reward, loser_reward = self.battle_manager.end_battle(
                battle.battle_id, winner.id
            )

            if winner_reward:
                embed.add_field(
                    name="Winner Rewards",
                    value=f"XP: {winner_reward.xp}\nCoins: {winner_reward.coins}",
                    inline=True,
                )
            if loser_reward:
                embed.add_field(
                    name="Loser Rewards",
                    value=f"XP: {loser_reward.xp}\nCoins: {loser_reward.coins}",
                    inline=True,
                )
            self.logger.log_battle_end(battle.battle_id, winner.id, battle.battle_data)
        else:
            next_id = (
                battle.opponent_id
                if ctx.author.id == battle.challenger_id
                else battle.challenger_id
            )
            next_player = self.bot.get_user(next_id)
            if next_player:
                embed.set_footer(text=f"{next_player.name}'s turn!")

        await ctx.send(embed=embed)

    @battle.command(name="status")
    async def battle_status(self, ctx: commands.Context) -> None:
        """Check your current battle status."""
        battle = self.battle_manager.get_player_battle(ctx.author.id)
        if not battle:
            await ctx.send("You're not in a battle!")
            return

        # Get challenger and opponent
        challenger = self.bot.get_user(battle.challenger_id)
        opponent = self.bot.get_user(battle.opponent_id)

        if not challenger or not opponent:
            await ctx.send("Error: Could not find battle participants!")
            return
        embed = discord.Embed(
            title=f"⚔️ {battle.battle_type.value.title()} Battle Status",
            color=discord.Color.blue(),
        )

        # Add challenger stats
        challenger_stats = self._format_stats(battle.battle_data["challenger_stats"])
        embed.add_field(name=challenger.name, value=challenger_stats, inline=True)

        # Add opponent stats
        opponent_stats = self._format_stats(battle.battle_data["opponent_stats"])
        embed.add_field(name=opponent.name, value=opponent_stats, inline=True)

        # Add battle history
        history = self.battle_manager.get_battle_history(battle.battle_id)
        if history:
            history_text = "\n".join(
                [f"**{turn['move']}**: {turn['result']['message']}" for turn in history]
            )
            embed.add_field(name="📜 History", value=history_text, inline=False)

        await ctx.send(embed=embed)

    @battle.command(name="forfeit")
    async def battle_forfeit(self, ctx: commands.Context) -> None:
        """Forfeit your current battle."""
        battle = self.battle_manager.get_player_battle(ctx.author.id)
        if not battle:
            await ctx.send("You're not in a battle!")
            return

        winner_id = (
            battle.opponent_id if ctx.author.id == battle.challenger_id else battle.challenger_id
        )
        winner = self.bot.get_user(winner_id)

        embed = discord.Embed(
            title="🏳️ Battle Forfeited!",
            description=f"{ctx.author.mention} has forfeited!",
            color=discord.Color.orange(),
        )
        if winner:
            embed.add_field(name="🏆 Winner", value=winner.mention, inline=False)

        self.battle_manager.end_battle(battle.battle_id, winner_id)
        self.logger.log_battle_end(battle.battle_id, winner_id, battle.battle_data, forfeited=True)

        await ctx.send(embed=embed)

    async def _start_battle(
        self, ctx: commands.Context, opponent: discord.Member, battle_type: BattleType
    ) -> None:
        """Generic method to start a battle of a given type."""
        if opponent.bot:
            await ctx.send("You can't battle a bot!")
            return
        if ctx.author.id == opponent.id:
            await ctx.send("You can't battle yourself!")
            return
        if self.battle_manager.is_in_battle(ctx.author.id) or self.battle_manager.is_in_battle(
            opponent.id
        ):
            await ctx.send("One of you is already in a battle!")
            return

        # Create battle and get initial data
        battle_system = self.battle_systems[battle_type]
        initial_data = battle_system.initialize_battle(ctx.author.id, opponent.id)
        battle = self.battle_manager.start_battle(
            ctx.author.id, opponent.id, battle_type, initial_data
        )
        self.logger.log_battle_start(battle.battle_id, ctx.author.id, opponent.id, battle_type)

        # Send initial battle message
        embed = discord.Embed(
            title=f"⚔️ New {battle_type.value.title()} Battle!",
            description=f"{ctx.author.mention} vs {opponent.mention}",
            color=discord.Color.green(),
        )
        embed.add_field(name="Turn", value=f"{ctx.author.name}'s turn!", inline=False)
        embed.set_footer(text=f"Battle ID: {battle.battle_id}")

        view = await self._create_battle_view(battle.battle_id)
        await ctx.send(embed=embed, view=view)

    async def _handle_battle_error(self, ctx: commands.Context, error_msg: str) -> None:
        """Send a standardized error message for battle commands."""
        embed = discord.Embed(
            title="Battle Error",
            description=error_msg,
            color=discord.Color.red(),
        )

        await ctx.send(embed=embed)

    async def _create_battle_view(self, battle_id: str) -> View:
        """Create a view with buttons for battle actions."""
        view = View()
        view.add_item(
            Button(style=ButtonStyle.primary, label="Move", custom_id=f"move_{battle_id}")
        )
        view.add_item(
            Button(style=ButtonStyle.secondary, label="Status", custom_id=f"status_{battle_id}")
        )
        view.add_item(
            Button(style=ButtonStyle.danger, label="Forfeit", custom_id=f"forfeit_{battle_id}")
        )
        return view

    def _format_stats(self, stats: Dict[str, Any]) -> str:
        """Format player stats for display."""
        return "\n".join([f"**{key.title()}**: {value}" for key, value in stats.items()])
