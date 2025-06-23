"""Tests for battle logger functionality."""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.core.models import BattleState, BattleType
from src.core.battle_logger import BattleLogger
from src.core.battle_storage import BattleStorage
from src.core.exceptions import LoggingError


@pytest.fixture
def battle_logger(tmp_path):
    """Fixture for battle logger."""
    log_dir = tmp_path / "logs"
    logger = BattleLogger(log_dir=str(log_dir))
    return logger


def test_log_battle_start(battle_logger):
    """Test logging battle start."""
    battle_state = BattleState(
        battle_id="test_battle_1",
        battle_type=BattleType.OSRS,
        challenger_id=1,
        opponent_id=2,
        current_turn=1,
        is_finished=False,
    )

    battle_logger.log_battle_start(battle_state)

    log_file = battle_logger.log_dir / "battle_system.log"
    assert log_file.exists()

    with open(log_file, "r") as f:
        logs = f.readlines()

    assert any("Battle started" in log for log in logs)


def test_log_turn(battle_logger):
    """Test logging battle turn."""
    battle_state = BattleState(
        battle_id="test_battle_1",
        battle_type=BattleType.OSRS,
        challenger_id=1,
        opponent_id=2,
        current_turn=1,
        is_finished=False,
    )

    move = MagicMock(name="Test Move")
    results = {"damage": 20, "message": "Hit!"}

    battle_logger.log_turn(battle_state, move, results)

    log_file = battle_logger.log_dir / "battle_system.log"
    assert log_file.exists()

    with open(log_file, "r") as f:
        logs = f.readlines()

    assert any("Turn processed" in log for log in logs)


def test_log_battle_end(battle_logger):
    """Test logging battle end."""
    battle_state = BattleState(
        battle_id="test_battle_1",
        battle_type=BattleType.OSRS,
        challenger_id=1,
        opponent_id=2,
        current_turn=1,
        is_finished=True,
        winner_id=1,
    )

    final_stats = {"challenger": {"xp": 100}, "opponent": {"xp": 50}}

    battle_logger.log_battle_end(battle_state, final_stats)

    log_file = battle_logger.log_dir / "battle_system.log"
    assert log_file.exists()

    with open(log_file, "r") as f:
        logs = f.readlines()

    assert any("Battle ended" in log for log in logs)


def test_log_error(battle_logger):
    """Test logging an error."""
    error_message = "An error occurred"

    with pytest.raises(LoggingError):
        battle_logger.log_error(None, Exception(error_message), {"context": "test"})

    log_file = battle_logger.log_dir / "battle_system.log"
    assert log_file.exists()

    with open(log_file, "r") as f:
        logs = f.readlines()

    assert any("Battle error" in log for log in logs)
