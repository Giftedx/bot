"""Test configuration and fixtures."""

import os
import sys
from pathlib import Path

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.battle_config import BattleSystemConfig
from src.core.models import BattleMove, BattleState, BattleType, StatusEffect


@pytest.fixture
def battle_config():
    """Fixture for battle system configuration."""
    return BattleSystemConfig()


@pytest.fixture
def basic_move():
    """Fixture for basic battle move."""
    return BattleMove(
        name="Basic Attack", move_type="normal", base_power=50, accuracy=90
    )


@pytest.fixture
def perfect_move():
    """Fixture for move that always hits."""
    return BattleMove(
        name="Perfect Strike", move_type="normal", base_power=40, accuracy=None
    )


@pytest.fixture
def resource_move():
    """Fixture for move with resource cost."""
    return BattleMove(
        name="Energy Blast",
        move_type="special",
        base_power=80,
        accuracy=95,
        energy_cost=20,
    )


@pytest.fixture
def status_move():
    """Fixture for move with status effect."""
    effect = StatusEffect(
        name="Poison",
        duration=3,
        effect_type="dot",
        magnitude=5,
        description="Deals damage over time",
        dot_damage=5,
    )
    return BattleMove(
        name="Poison Strike",
        move_type="poison",
        base_power=30,
        accuracy=100,
        status_effects=[effect],
    )


@pytest.fixture
def battle_state():
    """Fixture for battle state."""
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


@pytest.fixture
def mock_random():
    """Fixture for consistent random numbers in tests."""
    return 0.5


@pytest.fixture
def test_data_dir(tmp_path):
    """Fixture for test data directory."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def test_log_dir(tmp_path):
    """Fixture for test log directory."""
    log_dir = tmp_path / "test_logs"
    log_dir.mkdir()
    return log_dir


def pytest_configure(config):
    """Configure test environment."""
    os.environ["TESTING"] = "1"

    # Create test directories if they don't exist
    Path("tests/data").mkdir(exist_ok=True)
    Path("tests/logs").mkdir(exist_ok=True)


def pytest_unconfigure(config):
    """Clean up test environment."""
    os.environ.pop("TESTING", None)
