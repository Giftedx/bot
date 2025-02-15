"""Battle system implementation for Discord bot.em implementation for Discord bot.

This module implements a unified battle system that supports three types of battles:This module implements a unified battle system that supports three types of battles:
- OSRS-style combat battlesombat battles
- Pokemon-style battles
- Pet battles

Each battle type has its own mechanics while sharing common battle managementEach battle type has its own mechanics while sharing common battle management
features like turn handling, status tracking, and rewards.d rewards.

Typical usage:
    @bot.command()
    async def fight(ctx, opponent: discord.Member):
        battle_commands = BattleCommands(bot)        battle_commands = BattleCommands(bot)
        await battle_commands.battle_osrs(ctx, opponent)        await battle_commands.battle_osrs(ctx, opponent)
"""
import asyncio
from typing import Any, Dict, Optional, Tupleimport asyncio
import discord
from discord import ButtonStyle
from discord.ext import commands
from discord.ui import Button, View
from src.core.battle_logging import BattleLoggers
from src.core.battle_manager import BattleManager, BattleType
from src.osrs.battle_system import OSRSBattleSystem
from src.pets.battle_system import PetBattleSystemer
from src.pokemon.battle_system import PokemonBattleSystemcore.battle_manager import BattleManager, BattleType
from src.osrs.battle_system import OSRSBattleSystem
class BattleCommands(commands.Cog):em
    """Cog that handles all battle-related commands and interactions.

    This cog provides commands for starting and managing battles between users,
    handling battle moves, and tracking battle status. It supports multipleg):
    battle systems through a unified interface.ated commands and interactions.

    Attributes:tarting and managing battles between users,
        bot: The Discord bot instance    handling battle moves, and tracking battle status. It supports multiple
        battle_manager: Manager for tracking active battles unified interface.
        logger: Logger for battle events
        battle_systems: Dict mapping battle types to their implementations    Attributes:
    """rd bot instance
    def __init__(self, bot: commands.Bot) -> None:king active battles
        """Initialize battle commands cog.
        ing battle types to their implementations
        Args:    """
            bot: The Discord bot instance to attach to
        """commands.Bot) -> None:
        self.bot = botcommands cog.
        self.battle_manager = BattleManager()
        self.logger = BattleLogger()        Args:
        self.battle_systems = { instance to attach to
            BattleType.OSRS: OSRSBattleSystem(),
            BattleType.POKEMON: PokemonBattleSystem(),
            BattleType.PET: PetBattleSystem(),attle_manager = BattleManager()
        }

    @commands.group(invoke_without_command=True)            BattleType.OSRS: OSRSBattleSystem(),
    async def battle(self, ctx: commands.Context) -> None:emonBattleSystem(),
        """⚔️ Battle SystemetBattleSystem(),

        Choose your battle type:
        🗡️ OSRS Combat (!battle osrs)mmand=True)
        🐲 Pokemon Battles (!battle pokemon)
        🐾 Pet Battles (!battle pet)        """⚔️ Battle System

        Start a battle with:
        !battle <type> @opponentosrs)

        During battle:        🐾 Pet Battles (!battle pet)
        !battle move <name> - Use a move
        !battle status - Check battle status
        !battle forfeit - Give up

        Example:
        !battle osrs @friendname> - Use a move
        !battle move slash"""
        await ctx.send_help(ctx.command)rfeit - Give up

    @battle.command(name="osrs")
    async def battle_osrs(
        self, ctx: commands.Context, opponent: discord.Member        !battle move slash"""
    ) -> None:help(ctx.command)
        """Start an OSRS style battle."""
        await self._start_battle(ctx, opponent, BattleType.OSRS)

    @battle.command(name="pokemon") commands.Context, opponent: discord.Member
    async def battle_pokemon(    ) -> None:
        self, ctx: commands.Context, opponent: discord.Membertyle battle."""
    ) -> None:e.OSRS)
        """Start a Pokemon battle."""
        await self._start_battle(ctx, opponent, BattleType.POKEMON)n")

    @battle.command(name="pet")
    async def battle_pet(self, ctx: commands.Context, opponent: discord.Member) -> None:    ) -> None:
        """Start a pet battle."""ttle."""
        await self._start_battle(ctx, opponent, BattleType.PET)le(ctx, opponent, BattleType.POKEMON)

    @battle.command(name="move")
    async def battle_move(self, ctx: commands.Context, *, move: str) -> None:mands.Context, opponent: discord.Member) -> None:
        """Make a move in your current battle."""""Start a pet battle."""
        # Get player's active battle        await self._start_battle(ctx, opponent, BattleType.PET)
        battle = self.battle_manager.get_player_battle(ctx.author.id)
        if not battle:")
            await ctx.send("You're not in a battle!")
            return        """Make a move in your current battle."""

        # Get appropriate battle systemt_player_battle(ctx.author.id)
        battle_system = self.battle_systems[battle.battle_type]

        # Validate moveeturn
        if not battle_system.is_valid_move(battle, move, ctx.author.id):
            moves = battle_system.get_available_moves(battle, ctx.author.id)le system
            await ctx.send(f"Invalid move! Available moves: {', '.join(moves)}")
            return

        # Process the turnmove(battle, move, ctx.author.id):
        result = battle_system.process_turn(battle, move)e, ctx.author.id)
Invalid move! Available moves: {', '.join(moves)}")
        # Record turn in historyeturn
        self.battle_manager.record_turn(battle.battle_id, move, result)
        self.logger.log_turn(battle.battle_id, ctx.author.id, move, result)
(battle, move)
        # Create battle embed
        embed = discord.Embed(        # Record turn in history
            title="⚔️ Battle Move!",ecord_turn(battle.battle_id, move, result)
            description=result["message"],tle.battle_id, ctx.author.id, move, result)
            color=discord.Color.blue(),
        )

        # Add damage field if applicable="⚔️ Battle Move!",
        if "damage" in result:lt["message"],
            embed.add_field(name="Damage", value=str(result["damage"]), inline=True)blue(),

        # Add energy/resource field if applicable
        if "attacker_energy" in result:plicable
            embed.add_field(e" in result:
                name="Energy", value=str(result["attacker_energy"]), inline=True            embed.add_field(name="Damage", value=str(result["damage"]), inline=True)
            )
 energy/resource field if applicable
        # Check for battle endergy" in result:
        if "defender_hp" in result and result["defender_hp"] <= 0:
            winner = ctx.authorr_energy"]), inline=True
            embed.add_field(
                name="🏆 Battle End!",
                value=f"{winner.mention} wins the battle!",
                inline=False, result and result["defender_hp"] <= 0:
            )
            embed.add_field(
            winner_reward, loser_reward = self.battle_manager.end_battle(!",
                battle.battle_id, winner.id                value=f"{winner.mention} wins the battle!",
            )

            if winner_reward:
                embed.add_field(tle(
                    name="Winner Rewards",.battle_id, winner.id
                    value=f"XP: {winner_reward.xp}\nCoins: {winner_reward.coins}",
                    inline=True,
                )            if winner_reward:
            if loser_reward:
                embed.add_field(
                    name="Loser Rewards",s: {winner_reward.coins}",
                    value=f"XP: {loser_reward.xp}\nCoins: {loser_reward.coins}",                    inline=True,
                    inline=True,
                )
bed.add_field(
            self.logger.log_battle_end(battle.battle_id, winner.id, battle.battle_data)                    name="Loser Rewards",
        else:: {loser_reward.xp}\nCoins: {loser_reward.coins}",
            next_id = (
                battle.opponent_id
                if ctx.author.id == battle.challenger_id
                else battle.challenger_id            self.logger.log_battle_end(battle.battle_id, winner.id, battle.battle_data)
            )
            next_player = self.bot.get_user(next_id)
            if next_player:
                embed.set_footer(text=f"{next_player.name}'s turn!")                if ctx.author.id == battle.challenger_id
challenger_id
        await ctx.send(embed=embed)

    @battle.command(name="status")            if next_player:
    async def battle_status(self, ctx: commands.Context) -> None:ooter(text=f"{next_player.name}'s turn!")
        """Check your current battle status."""
        battle = self.battle_manager.get_player_battle(ctx.author.id)end(embed=embed)
        if not battle:
            await ctx.send("You're not in a battle!")    @battle.command(name="status")
            returntx: commands.Context) -> None:
        """Check your current battle status."""
        # Get challenger and opponentr.get_player_battle(ctx.author.id)
        challenger = self.bot.get_user(battle.challenger_id)
        opponent = self.bot.get_user(battle.opponent_id)a battle!")

        if not challenger or not opponent:
            await ctx.send("Error: Could not find battle participants!")
            return = self.bot.get_user(battle.challenger_id)
        opponent = self.bot.get_user(battle.opponent_id)
        embed = discord.Embed(
            title=f"⚔️ {battle.battle_type.value.title()} Battle Status",nger or not opponent:
            color=discord.Color.blue(),ror: Could not find battle participants!")
        )

        # Add challenger statsmbed = discord.Embed(
        challenger_stats = self._format_stats(battle.battle_data["challenger_stats"])lue.title()} Battle Status",
        embed.add_field(name=challenger.name, value=challenger_stats, inline=True)ord.Color.blue(),

        # Add opponent stats
        opponent_stats = self._format_stats(battle.battle_data["opponent_stats"])        # Add challenger stats
        embed.add_field(name=opponent.name, value=opponent_stats, inline=True)ats(battle.battle_data["challenger_stats"])
 inline=True)
        # Show current turn
        current = self.bot.get_user(battle.current_turn) Add opponent stats
        if current:        opponent_stats = self._format_stats(battle.battle_data["opponent_stats"])
            embed.set_footer(text=f"Current turn: {current.name}")pponent.name, value=opponent_stats, inline=True)

        await ctx.send(embed=embed)rn

    @battle.command(name="forfeit")rent:
    async def battle_forfeit(self, ctx: commands.Context) -> None:rrent turn: {current.name}")
        """Forfeit your current battle."""
        battle = self.battle_manager.get_player_battle(ctx.author.id)        await ctx.send(embed=embed)
        if not battle:
            await ctx.send("You're not in a battle!")rfeit")
            return: commands.Context) -> None:

        # Determine winner_manager.get_player_battle(ctx.author.id)
        winner_id = (t battle:
            battle.opponent_idnd("You're not in a battle!")
            if ctx.author.id == battle.challenger_id
            else battle.challenger_id
        )
        winner = self.bot.get_user(winner_id)
        if not winner:attle.opponent_id
            await ctx.send("Error: Could not find winner!")            if ctx.author.id == battle.challenger_id
            return

        # End battle and calculate rewards        winner = self.bot.get_user(winner_id)
        winner_reward, loser_reward = self.battle_manager.end_battle(
            battle.battle_id, winner_id
        )turn

        embed = discord.Embed(lculate rewards
            title="Battle Forfeited!",oser_reward = self.battle_manager.end_battle(
            description=(
                f"{ctx.author.mention} has forfeited. " f"{winner.mention} wins!"
            ),
            color=discord.Color.red(),
        )
ption=(
        if winner_reward:                f"{ctx.author.mention} has forfeited. " f"{winner.mention} wins!"
            embed.add_field(
                name="Winner Rewards",
                value=f"XP: {winner_reward.xp}\nCoins: {winner_reward.coins}",
                inline=True,
            )
        if loser_reward:
            embed.add_field(
                name="Forfeit Rewards",P: {winner_reward.xp}\nCoins: {winner_reward.coins}",
                value=f"XP: {loser_reward.xp}\nCoins: {loser_reward.coins}",
                inline=True,
            )er_reward:

        self.logger.log_battle_end(battle.battle_id, winner_id, battle.battle_data)       name="Forfeit Rewards",
        await ctx.send(embed=embed)                value=f"XP: {loser_reward.xp}\nCoins: {loser_reward.coins}",

    async def _start_battle(
        self,
        ctx: commands.Context, battle_data)
        opponent: discord.Member, wait ctx.send(embed=embed)
        battle_type: BattleType
    ) -> None:
        """Start a new battle between two users.elf, ctx: commands.Context, opponent: discord.Member, battle_type: BattleType

        Handles battle initialization including: two users.
        - Validation checks (bot check, existing battles)
        - Battle confirmation from opponentnitialization including:
        - Initial stats loading
        - Battle state creation        - Battle confirmation from opponent
        itial stats loading
        Args:
            ctx: The command context
            opponent: The member being challenged
            battle_type: The type of battle to start

        Returns:e_type: The type of battle to start
            None. Battle state is created if accepted
        """
        # Validation checks
        if opponent.bot:
            await ctx.send("You can't battle with a bot!")        # Validation checks
            return
 can't battle with a bot!")
        if self.battle_manager.get_player_battle(ctx.author.id):
            await ctx.send("You're already in a battle!")
            return.get_player_battle(ctx.author.id):
 ctx.send("You're already in a battle!")
        if self.battle_manager.get_player_battle(opponent.id):
            await ctx.send(f"{opponent.name} is already in a battle!")
            returnyer_battle(opponent.id):
 a battle!")
        # Create battle confirmation embed
        embed = discord.Embed(
            title="⚔️ Battle Challenge!",        # Create battle confirmation embed
            description=(
                f"{ctx.author.mention} challenges {opponent.mention} "
                f"to a {battle_type.value} battle!"
            ),enges {opponent.mention} "
            color=discord.Color.gold(),e} battle!"
        )
olor=discord.Color.gold(),
        # Create confirmation buttons        )
        view = View(timeout=30.0)
        accept_button = Button(
            style=ButtonStyle.green, label="Accept", custom_id="accept"= View(timeout=30.0)
        )        accept_button = Button(
        decline_button = Button(abel="Accept", custom_id="accept"
            style=ButtonStyle.red, label="Decline", custom_id="decline"
        )
        view.add_item(accept_button)abel="Decline", custom_id="decline"
        view.add_item(decline_button)
on)
        # Send challenge
        msg = await ctx.send(content=opponent.mention, embed=embed, view=view)
ge
        try:ntion, embed=embed, view=view)
            # Wait for button interaction
            def check(interaction: discord.Interaction) -> bool:
                return ( Wait for button interaction
                    interaction.user.id == opponent.id            def check(interaction: discord.Interaction) -> bool:
                    and interaction.message.id == msg.id
                )
                    and interaction.message.id == msg.id
            interaction = await self.bot.wait_for(
                "interaction", check=check, timeout=30.0
            )ction = await self.bot.wait_for(
                "interaction", check=check, timeout=30.0
            if interaction.custom_id == "decline":
                await msg.edit(
                    content=f"{opponent.name} declined the battle challenge.",decline":
                    embed=None,
                    view=None,
                )                    embed=None,
                return

            # Get initial battle stats
            initial_stats = await self._get_initial_stats(
                ctx.author, opponent, battle_type
            ) = await self._get_initial_stats(
le_type
            # Create battle state
            battle = self.battle_manager.create_battle(
                battle_type=battle_type,            # Create battle state
                challenger_id=ctx.author.id,f.battle_manager.create_battle(
                opponent_id=opponent.id,
                initial_data=initial_stats,
            )                opponent_id=opponent.id,
itial_stats,
            self.logger.log_battle_start(            )
                battle.battle_id, battle_type.value, ctx.author.id, opponent.id
            )elf.logger.log_battle_start(
attle_type.value, ctx.author.id, opponent.id
            # Update challenge message
            await msg.edit(
                content="Battle starting!",llenge message
                embed=discord.Embed(
                    title="⚔️ Battle Start!",,
                    description=(.Embed(
                        "Type `!battle move <name>` to make your move!\n"
                        f"{ctx.author.mention}'s turn first!"
                    ),                        "Type `!battle move <name>` to make your move!\n"
                    color=discord.Color.green(),    f"{ctx.author.mention}'s turn first!"
                ),
                view=None,
            )   ),
                view=None,
        except asyncio.TimeoutError:
            await msg.edit(content="Battle challenge timed out.", embed=None, view=None)

    def _format_stats(self, stats: Dict[str, Any]) -> str:ew=None)
        """Format battle stats into a human-readable string.
        s(self, stats: Dict[str, Any]) -> str:
        Creates visual bars for HP and energy, and lists status effects.ng.

        Args:es visual bars for HP and energy, and lists status effects.
            stats: Dictionary containing battle statistics

        Returns:containing battle statistics
            Formatted string with battle stats display
        """
        lines = []            Formatted string with battle stats display

        # HP bar        lines = []
        hp_percent = stats["current_hp"] / stats["max_hp"]
        bars = "█" * int(hp_percent * 10)        # HP bar
        spaces = "░" * (10 - len(bars))        hp_percent = stats["current_hp"] / stats["max_hp"]
        lines.append(f"HP: {bars}{spaces} ({stats['current_hp']}/{stats['max_hp']})")

        # Energy/Resource bar if applicable({stats['current_hp']}/{stats['max_hp']})")
        if "current_energy" in stats:





































































    await bot.add_cog(BattleCommands(bot))    """Add BattleCommands cog to bot."""async def setup(bot: commands.Bot) -> None:        return {}            return {"challenger_pet": challenger_pet, "opponent_pet": opponent_pet}            opponent_pet = await self.bot.db.get_active_pet(opponent.id)            challenger_pet = await self.bot.db.get_active_pet(challenger.id)            # Load active pets        elif battle_type == BattleType.PET:            }                "opponent_pokemon": opponent_pokemon,                "challenger_pokemon": challenger_pokemon,            return {            opponent_pokemon = await self.bot.db.get_active_pokemon(opponent.id)            challenger_pokemon = await self.bot.db.get_active_pokemon(challenger.id)            # Load active Pokemon        elif battle_type == BattleType.POKEMON:            }                "opponent_stats": opponent_stats,                "challenger_stats": challenger_stats,            return {            opponent_stats = await self.bot.db.get_osrs_stats(opponent.id)            challenger_stats = await self.bot.db.get_osrs_stats(challenger.id)            # Load OSRS stats        if battle_type == BattleType.OSRS:        """            Dictionary containing initial stats for both participants        Returns:                        battle_type: The type of battle being started            opponent: The member being challenged            challenger: The member initiating the battle        Args:                - Pet: Active pet stats        - Pokemon: Active Pokemon stats        - OSRS: Combat stats        Loads appropriate stats based on battle type:                """Retrieve initial battle stats for both participants.    ) -> Dict[str, Any]:        battle_type: BattleType,        opponent: discord.Member,        challenger: discord.Member,        self,    async def _get_initial_stats(        return "\n".join(lines)            lines.append(f"Status: {', '.join(status_effects)}")        if status_effects := stats.get("status_effects", []):        # Status effects            )                f"({stats['current_energy']}/{stats['max_energy']})"                f"Energy: {bars}{spaces} "            lines.append(            spaces = "░" * (10 - len(bars))            bars = "█" * int(energy_percent * 10)            energy_percent = stats["current_energy"] / stats["max_energy"]        # Energy/Resource bar if applicable
        if "current_energy" in stats:
            energy_percent = stats["current_energy"] / stats["max_energy"]
            bars = "█" * int(energy_percent * 10)
            spaces = "░" * (10 - len(bars))
            lines.append(
                f"Energy: {bars}{spaces} "
                f"({stats['current_energy']}/{stats['max_energy']})"
            )

        # Status effects
        if status_effects := stats.get("status_effects", []):
            lines.append(f"Status: {', '.join(status_effects)}")

        return "\n".join(lines)

    async def _get_initial_stats(
        self,
        challenger: discord.Member,
        opponent: discord.Member,
        battle_type: BattleType,
    ) -> Dict[str, Any]:
        """Retrieve initial battle stats for both participants.

        Loads appropriate stats based on battle type:
        - OSRS: Combat stats
        - Pokemon: Active Pokemon stats
        - Pet: Active pet stats

        Args:
            challenger: The member initiating the battle
            opponent: The member being challenged
            battle_type: The type of battle being started

        Returns:
            Dictionary containing initial stats for both participants
        """
        if battle_type == BattleType.OSRS:
            # Load OSRS stats
            challenger_stats = await self.bot.db.get_osrs_stats(challenger.id)
            opponent_stats = await self.bot.db.get_osrs_stats(opponent.id)

            return {
                "challenger_stats": challenger_stats,
                "opponent_stats": opponent_stats,
            }

        elif battle_type == BattleType.POKEMON:
            # Load active Pokemon
            challenger_pokemon = await self.bot.db.get_active_pokemon(challenger.id)
            opponent_pokemon = await self.bot.db.get_active_pokemon(opponent.id)

            return {
                "challenger_pokemon": challenger_pokemon,
                "opponent_pokemon": opponent_pokemon,
            }

        elif battle_type == BattleType.PET:
            # Load active pets
            challenger_pet = await self.bot.db.get_active_pet(challenger.id)
            opponent_pet = await self.bot.db.get_active_pet(opponent.id)

            return {"challenger_pet": challenger_pet, "opponent_pet": opponent_pet}

        return {}


async def setup(bot: commands.Bot) -> None:
    """Add BattleCommands cog to bot."""
    await bot.add_cog(BattleCommands(bot))
