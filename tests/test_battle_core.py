"""Tests for core battle system components."""

from unittest.mock import Mock, patch

import pytest

from src.core.battle_config import DEFAULT_REWARD_CONFIGS, BattleSystemConfig
from src.core.battle_utils import (
    apply_stat_changes,
    calculate_accuracy,
    calculate_stat_multiplier,
    check_move_requirements,
)
from src.core.exceptions import ValidationError
from src.core.models import BattleMove, BattleState, BattleType, StatusEffect


@pytest.fixture
def battle_config():
    """Fixture for battle system configuration."""
    return BattleSystemConfig()


@pytest.fixture
def battle_move():
    """Fixture for test battle move."""
    return BattleMove(
        name="Test Move",
        move_type="normal",
        base_power=50,
        accuracy=90,
        energy_cost=10,
        hp_cost=None,
        resource_cost=None,
        status_effects=None,
        stat_changes=None,
    )


@pytest.fixture
def battle_state():
    """Fixture for test battle state."""
    return BattleState(
        battle_id="test_battle_1",
        battle_type=BattleType.OSRS,
        challenger_id=1,
        opponent_id=2,
        current_turn=1,
        battle_data={
            "challenger_stats": {
                "hp": 100,
                "current_hp": 100,
                "attack": 50,
                "defense": 50,
                "accuracy_stage": 0,
                "current_energy": 100,
            },
            "opponent_stats": {
                "hp": 100,
                "current_hp": 100,
                "attack": 50,
                "defense": 50,
                "evasion_stage": 0,
                "current_energy": 100,
            },
        },
    )


def test_calculate_stat_multiplier():
    """Test stat multiplier calculation."""
    assert calculate_stat_multiplier(0) == 1.0
    assert calculate_stat_multiplier(1) == 1.5
    assert calculate_stat_multiplier(-1) == 0.67
    assert calculate_stat_multiplier(6) == 4.0
    assert calculate_stat_multiplier(-6) == 0.25
    # Test bounds
    assert calculate_stat_multiplier(7) == 4.0
    assert calculate_stat_multiplier(-7) == 0.25


def test_apply_stat_changes():
    """Test applying stat changes."""
    stats = {"attack": 100, "attack_stage": 0, "defense": 100, "defense_stage": 0}

    changes = {"attack": 1, "defense": -1}
    modified, messages = apply_stat_changes(stats, changes)

    assert modified["attack_stage"] == 1
    assert modified["defense_stage"] == -1
    assert modified["attack"] == 150  # 1.5x multiplier
    assert modified["defense"] == 67  # 0.67x multiplier
    assert len(messages) == 2
    assert "Attack rose!" in messages
    assert "Defense fell!" in messages


def test_check_move_requirements(battle_move):
    """Test move requirement checking."""
    # Test sufficient resources
    stats = {"current_energy": 20, "current_hp": 100}
    assert check_move_requirements(stats, battle_move) is None

    # Test insufficient energy
    stats = {"current_energy": 5, "current_hp": 100}
    error = check_move_requirements(stats, battle_move)
    assert error is not None
    assert "energy" in error

    # Test move with resource cost
    move = BattleMove(
        name="Resource Move",
        move_type="normal",
        base_power=50,
        accuracy=90,
        resource_cost={"mana": 20},
    )
    stats = {"current_mana": 10}
    error = check_move_requirements(stats, move)
    assert error is not None
    assert "mana" in error


def test_calculate_accuracy(battle_move, battle_state):
    """Test accuracy calculation."""
    attacker_stats = battle_state.battle_data["challenger_stats"]
    defender_stats = battle_state.battle_data["opponent_stats"]

    # Test normal accuracy
    with patch("random.random", return_value=0.5):
        assert calculate_accuracy(battle_move, attacker_stats, defender_stats)

    # Test lowered accuracy
    attacker_stats["accuracy_stage"] = -1
    with patch("random.random", return_value=0.8):
        assert not calculate_accuracy(battle_move, attacker_stats, defender_stats)

    # Test raised evasion
    defender_stats["evasion_stage"] = 1
    with patch("random.random", return_value=0.8):
        assert not calculate_accuracy(battle_move, attacker_stats, defender_stats)

    # Test perfect accuracy move
    perfect_move = BattleMove(
        name="Perfect Move", move_type="normal", base_power=50, accuracy=None
    )
    assert calculate_accuracy(perfect_move, attacker_stats, defender_stats)


def test_battle_reward_config():
    """Test battle reward configuration."""
    osrs_config = DEFAULT_REWARD_CONFIGS[BattleType.OSRS]
    pokemon_config = DEFAULT_REWARD_CONFIGS[BattleType.POKEMON]
    pet_config = DEFAULT_REWARD_CONFIGS[BattleType.PET]

    # Test OSRS rewards
    assert osrs_config.base_xp == 100
    assert osrs_config.win_multiplier == 2.0
    assert osrs_config.rare_drop_chance == 0.01

    # Test Pokemon rewards
    assert pokemon_config.base_xp == 80
    assert pokemon_config.evolution_chance == 0.05
    assert pokemon_config.catch_bonus == 0.1

    # Test Pet rewards
    assert pet_config.base_xp == 60
    assert pet_config.loyalty_gain == 5
    assert pet_config.training_bonus == 0.15


def test_status_effect():
    """Test status effect application."""
    effect = StatusEffect(
        name="Poison",
        duration=3,
        effect_type="dot",
        magnitude=5,
        description="Deals damage over time",
        dot_damage=5,
    )

    stats = {"hp": 100, "current_hp": 100, "status_effects": []}

    # Apply effect
    stats["status_effects"].append(effect)
    assert len(stats["status_effects"]) == 1
    assert stats["status_effects"][0].name == "Poison"
    assert stats["status_effects"][0].duration == 3

    # Test max effects
    with pytest.raises(ValidationError):
        for _ in range(3):
            stats["status_effects"].append(effect)


def test_battle_state_validation(battle_state):
    """Test battle state validation."""
    # Test valid state
    assert battle_state.battle_id == "test_battle_1"
    assert battle_state.battle_type == BattleType.OSRS
    assert battle_state.challenger_id == 1
    assert battle_state.opponent_id == 2

    # Test turn tracking
    assert battle_state.current_turn == 1
    assert not battle_state.is_finished
    assert battle_state.winner_id is None

    # Test battle data
    assert "challenger_stats" in battle_state.battle_data
    assert "opponent_stats" in battle_state.battle_data
    assert battle_state.battle_data["challenger_stats"]["hp"] == 100
    assert battle_state.battle_data["opponent_stats"]["hp"] == 100
