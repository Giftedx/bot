import asyncio
import random
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

import discord
from discord.ext import commands

from src.core.battle_manager import BattleManager, BattleType
from src.osrs.battle_system import OSRSBattleSystem
from src.pets.battle_system import PetBattleSystem
from src.pokemon.battle_system import PokemonBattleSystem


class BattleCommands(commands.Cog):
    """Unified battle command system."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.battle_manager = BattleManager()
        self.battle_systems = {
            BattleType.OSRS: OSRSBattleSystem(),
            BattleType.POKEMON: PokemonBattleSystem(),
            BattleType.PET: PetBattleSystem(),
        }

    @commands.group(invoke_without_command=True)
    async def battle(self, ctx: commands.Context):
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
        !battle osrs @friend
        !battle move slash"""
        await ctx.send_help(ctx.command)

    @battle.command(name="move")
    async def battle_move(self, ctx: commands.Context, *, move: str):
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
            embed.add_field(
                name="Energy", value=str(result["attacker_energy"]), inline=True
            )

        # Check for battle end
        battle_end, winner_id = battle_system.check_battle_end(battle)
        if battle_end:
            if winner_id:
                winner = self.bot.get_user(winner_id)
                embed.add_field(
                    name="🏆 Battle End!",
                    value=f"{winner.name} wins the battle!",
                    inline=False,
                )
            self.battle_manager.end_battle(battle.battle_id, winner_id)
        else:
            # Switch turns
            next_id = self.battle_manager.next_turn(battle.battle_id)
            next_player = self.bot.get_user(next_id)
            embed.set_footer(text=f"{next_player.name}'s turn!")

        await ctx.send(embed=embed)

    @battle.command(name="status")
    async def battle_status(self, ctx: commands.Context):
        """Check your current battle status."""
        battle = self.battle_manager.get_player_battle(ctx.author.id)
        if not battle:
            await ctx.send("You're not in a battle!")
            return

        # Get challenger and opponent
        challenger = self.bot.get_user(battle.challenger_id)
        opponent = self.bot.get_user(battle.opponent_id)

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

        # Show current turn
        current = self.bot.get_user(battle.current_turn)
        embed.set_footer(text=f"Current turn: {current.name}")

        await ctx.send(embed=embed)

    @battle.command(name="forfeit")
    async def battle_forfeit(self, ctx: commands.Context):
        """Forfeit your current battle."""
        battle = self.battle_manager.get_player_battle(ctx.author.id)
        if not battle:
            await ctx.send("You're not in a battle!")
            return

        # Get winner (other player)
        winner_id = (
            battle.opponent_id
            if ctx.author.id == battle.challenger_id
            else battle.challenger_id
        )
        winner = self.bot.get_user(winner_id)

        # End battle
        self.battle_manager.end_battle(battle.battle_id, winner_id)

        embed = discord.Embed(
            title="🏳️ Battle Forfeited!",
            description=f"{ctx.author.name} has forfeited the battle!",
            color=discord.Color.red(),
        )
        embed.add_field(name="Winner", value=winner.name)
        await ctx.send(embed=embed)

    def _format_stats(self, stats: Dict[str, Any]) -> str:
        """Format battle stats for display."""
        lines = []

        if "current_hp" in stats:
            lines.append(f"HP: {stats['current_hp']}/{stats['max_hp']}")
        elif "hitpoints" in stats:
            lines.append(f"HP: {stats['hitpoints']}")

        if "current_energy" in stats:
            lines.append(f"Energy: {stats['current_energy']}/{stats['max_energy']}")

        if "status_effects" in stats and stats["status_effects"]:
            effects = ", ".join(stats["status_effects"].keys())
            lines.append(f"Status: {effects}")

        return "\n".join(lines) if lines else "No stats available"


async def setup(bot: commands.Bot):
    """Add BattleCommands cog to bot."""
    await bot.add_cog(BattleCommands(bot))
