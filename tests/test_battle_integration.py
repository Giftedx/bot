"""Integration tests for battle system."""

from unittest.mock import AsyncMock, Mock

import discord
import pytest
from discord.ext import commands

from cogs.battle_system import BattleCommands
from src.core.battle_database import BattleDatabase
from src.core.battle_manager import BattleManager, BattleType


@pytest.fixture
async def bot():
    """Create test bot instance."""
    bot = Mock(spec=commands.Bot)
    bot.db = AsyncMock(spec=BattleDatabase)
    return bot


@pytest.fixture
def battle_cog(bot):
    """Create battle commands cog."""
    return BattleCommands(bot)


@pytest.mark.asyncio
class TestBattleIntegration:
    """Integration tests for battle system."""

    async def test_battle_command_flow(self, battle_cog):
        """Test complete battle command flow."""
        ctx = Mock(spec=commands.Context)
        ctx.author = Mock(spec=discord.Member, id=1)
        ctx.send = AsyncMock()

        opponent = Mock(spec=discord.Member, id=2)
        opponent.bot = False

        # Mock database methods
        battle_cog.bot.db.get_osrs_stats = AsyncMock(
            return_value={
                "skills": {
                    "attack": 60,
                    "strength": 55,
                    "defence": 50,
                    "hitpoints": 50,
                },
                "equipment": {"weapon_type": "sword", "bonus": 10},
            }
        )

        # Test battle start
        await battle_cog.battle_osrs(ctx, opponent)
        ctx.send.assert_called_once()
        assert battle_cog.battle_manager.get_player_battle(ctx.author.id) is not None

        # Test move command
        ctx.send.reset_mock()
        await battle_cog.battle_move(ctx, move="slash")
        ctx.send.assert_called_once()

        # Verify battle state updated
        battle = battle_cog.battle_manager.get_player_battle(ctx.author.id)
        assert len(battle.turn_history) == 1

    async def test_battle_database_integration(self, battle_cog):
        """Test battle database operations."""
        ctx = Mock(spec=commands.Context)
        ctx.author = Mock(spec=discord.Member, id=1)
        opponent = Mock(spec=discord.Member, id=2)

        # Create test battle
        battle = battle_cog.battle_manager.create_battle(
            battle_type=BattleType.POKEMON,
            challenger_id=ctx.author.id,
            opponent_id=opponent.id,
            initial_data={
                "challenger_pokemon": {"name": "Pikachu", "stats": {"hp": 50}},
                "opponent_pokemon": {"name": "Squirtle", "stats": {"hp": 44}},
            },
        )

        # Mock database calls
        battle_cog.bot.db.record_battle = AsyncMock()
        battle_cog.bot.db.record_rewards = AsyncMock()
        battle_cog.bot.db.update_ratings = AsyncMock()
        battle_cog.bot.db.check_achievements = AsyncMock(return_value=[])

        # End battle and verify database calls
        battle_cog.battle_manager.end_battle(battle.battle_id, ctx.author.id)

        battle_cog.bot.db.record_battle.assert_called_once()
        battle_cog.bot.db.record_rewards.assert_called()
        battle_cog.bot.db.update_ratings.assert_called_once()
        battle_cog.bot.db.check_achievements.assert_called()

    async def test_battle_reward_system(self, battle_cog):
        """Test battle reward calculation and distribution."""
        ctx = Mock(spec=commands.Context)
        ctx.author = Mock(spec=discord.Member, id=1)
        ctx.send = AsyncMock()

        # Create test battle
        battle = battle_cog.battle_manager.create_battle(
            battle_type=BattleType.PET,
            challenger_id=ctx.author.id,
            opponent_id=2,
            initial_data={
                "challenger_pet": {
                    "name": "TestPet",
                    "stats": {"hp": 100},
                    "loyalty": 50,
                }
            },
        )

        # Mock database stats
        battle_cog.bot.db.get_player_stats = AsyncMock(
            return_value={"total_battles": 10, "win_streak": 2}
        )

        # End battle and check rewards
        winner_reward, loser_reward = battle_cog.battle_manager.end_battle(
            battle.battle_id, ctx.author.id
        )

        assert winner_reward.xp > 0
        assert winner_reward.coins > 0
        assert "loyalty_gain" in winner_reward.special_rewards

    @pytest.mark.parametrize(
        "battle_type", [BattleType.OSRS, BattleType.POKEMON, BattleType.PET]
    )
    async def test_battle_type_specific_features(self, battle_cog, battle_type):
        """Test features specific to each battle type."""
        ctx = Mock(spec=commands.Context)
        ctx.author = Mock(spec=discord.Member, id=1)
        ctx.send = AsyncMock()

        # Get appropriate battle system
        battle_system = battle_cog.battle_systems[battle_type]

        # Test battle system specific features
        if battle_type == BattleType.OSRS:
            # Test prayer effects
            attacker_stats = {
                "skills": {"attack": 60, "strength": 55},
                "active_prayers": ["piety"],
            }
            modified = battle_system._apply_combat_effects(attacker_stats)
            assert modified["skills"]["attack"] > attacker_stats["skills"]["attack"]

        elif battle_type == BattleType.POKEMON:
            # Test type effectiveness
            effectiveness = battle_system._calculate_effectiveness(
                "water", ["fire", "ground"]
            )
            assert effectiveness > 1.0  # Should be super effective

        elif battle_type == BattleType.PET:
            # Test loyalty bonus
            attacker_stats = {
                "loyalty": 100,
                "stats": {"attack": 50},
                "moves": {"test": {"power": 40}},
            }
            defender_stats = {"stats": {"defense": 30}}
            damage, _ = battle_system.calculate_damage(
                "test", attacker_stats, defender_stats
            )
            assert damage > 0  # Loyalty should increase damage

    async def test_error_handling(self, battle_cog):
        """Test battle system error handling."""
        ctx = Mock(spec=commands.Context)
        ctx.author = Mock(spec=discord.Member, id=1)
        ctx.send = AsyncMock()

        # Test invalid move
        await battle_cog.battle_move(ctx, move="invalid_move")
        ctx.send.assert_called_with("You're not in a battle!")

        # Test battle with bot
        bot_opponent = Mock(spec=discord.Member, id=2)
        bot_opponent.bot = True
        await battle_cog.battle_osrs(ctx, bot_opponent)
        ctx.send.assert_called_with("You can't battle with a bot!")

        # Test double battle start
        opponent = Mock(spec=discord.Member, id=3)
        opponent.bot = False

        # Create first battle
        battle = battle_cog.battle_manager.create_battle(
            battle_type=BattleType.OSRS,
            challenger_id=ctx.author.id,
            opponent_id=opponent.id,
            initial_data={},
        )

        # Try to start second battle
        await battle_cog.battle_osrs(ctx, opponent)
        ctx.send.assert_called_with("You're already in a battle!")
