"""Battle system logging and monitoring."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import LoggingError
from .models import BattleMove, BattleState


class BattleLogger:
    """Handles battle system logging and monitoring."""

    def __init__(
        self, log_dir: str = "logs/battles", log_level: int = logging.INFO
    ) -> None:
        """Initialize battle logger.

        Args:
            log_dir: Directory to store log files
            log_level: Logging level to use
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Set up file handler
        self.logger = logging.getLogger("battle_system")
        self.logger.setLevel(log_level)

        # Create handlers
        file_handler = logging.FileHandler(self.log_dir / "battle_system.log")
        file_handler.setLevel(log_level)

        # Create formatters
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        # Add handlers
        self.logger.addHandler(file_handler)

    def log_battle_start(self, battle_state: BattleState) -> None:
        """Log battle start event.

        Args:
            battle_state: Initial battle state

        Raises:
            LoggingError: If logging fails
        """
        try:
            # Log to system log
            self.logger.info(
                f"Battle started - ID: {battle_state.battle_id}, "
                f"Type: {battle_state.battle_type.value}, "
                f"Challenger: {battle_state.challenger_id}, "
                f"Opponent: {battle_state.opponent_id}"
            )

            # Save detailed battle start state
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = (
                self.log_dir / f"battle_{battle_state.battle_id}_{timestamp}.json"
            )

            battle_data = {
                "event": "battle_start",
                "timestamp": timestamp,
                "battle_state": {
                    "battle_id": battle_state.battle_id,
                    "battle_type": battle_state.battle_type.value,
                    "challenger_id": battle_state.challenger_id,
                    "opponent_id": battle_state.opponent_id,
                    "initial_data": battle_state.battle_data,
                },
            }

            with open(file_path, "w") as f:
                json.dump(battle_data, f, indent=2)

        except Exception as e:
            raise LoggingError(f"Failed to log battle start: {e}")

    def log_turn(
        self, battle_state: BattleState, move: BattleMove, results: Dict[str, Any]
    ) -> None:
        """Log battle turn event.

        Args:
            battle_state: Current battle state
            move: Move that was used
            results: Results of the turn

        Raises:
            LoggingError: If logging fails
        """
        try:
            # Log to system log
            self.logger.info(
                f"Turn processed - Battle: {battle_state.battle_id}, "
                f"Round: {battle_state.round_number}, "
                f"Player: {battle_state.current_turn}, "
                f"Move: {move.name}"
            )

            # Save detailed turn data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = (
                self.log_dir
                / f"battle_{battle_state.battle_id}_turn_{battle_state.round_number}.json"
            )

            turn_data = {
                "event": "battle_turn",
                "timestamp": timestamp,
                "battle_id": battle_state.battle_id,
                "round": battle_state.round_number,
                "player_id": battle_state.current_turn,
                "move": {
                    "name": move.name,
                    "move_type": move.move_type,
                    "base_power": move.base_power,
                },
                "results": results,
            }

            with open(file_path, "w") as f:
                json.dump(turn_data, f, indent=2)

        except Exception as e:
            raise LoggingError(f"Failed to log battle turn: {e}")

    def log_battle_end(
        self, battle_state: BattleState, final_stats: Dict[str, Any]
    ) -> None:
        """Log battle end event.

        Args:
            battle_state: Final battle state
            final_stats: Final battle statistics

        Raises:
            LoggingError: If logging fails
        """
        try:
            # Log to system log
            self.logger.info(
                f"Battle ended - ID: {battle_state.battle_id}, "
                f"Winner: {battle_state.winner_id}, "
                f"Rounds: {battle_state.round_number}"
            )

            # Save detailed end state
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = self.log_dir / f"battle_{battle_state.battle_id}_end.json"

            end_data = {
                "event": "battle_end",
                "timestamp": timestamp,
                "battle_id": battle_state.battle_id,
                "winner_id": battle_state.winner_id,
                "total_rounds": battle_state.round_number,
                "final_stats": final_stats,
            }

            with open(file_path, "w") as f:
                json.dump(end_data, f, indent=2)

        except Exception as e:
            raise LoggingError(f"Failed to log battle end: {e}")

    def log_error(
        self,
        battle_state: Optional[BattleState],
        error: Exception,
        context: Dict[str, Any],
    ) -> None:
        """Log battle system error.

        Args:
            battle_state: Current battle state if available
            error: The error that occurred
            context: Additional context about the error

        Raises:
            LoggingError: If logging fails
        """
        try:
            # Log to system log
            self.logger.error(
                f"Battle error - Type: {type(error).__name__}, "
                f"Message: {str(error)}, "
                f"Battle ID: {battle_state.battle_id if battle_state else 'N/A'}"
            )

            # Save detailed error data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = self.log_dir / f"error_{timestamp}.json"

            error_data = {
                "event": "battle_error",
                "timestamp": timestamp,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "battle_state": (
                    {
                        "battle_id": battle_state.battle_id,
                        "round": battle_state.round_number,
                        "current_turn": battle_state.current_turn,
                    }
                    if battle_state
                    else None
                ),
                "context": context,
            }

            with open(file_path, "w") as f:
                json.dump(error_data, f, indent=2)

        except Exception as e:
            raise LoggingError(f"Failed to log error: {e}")

    def get_battle_history(self, battle_id: str) -> Dict[str, Any]:
        """Get complete history for a battle.

        Args:
            battle_id: ID of battle to get history for

        Returns:
            Dict containing complete battle history

        Raises:
            LoggingError: If history retrieval fails
        """
        try:
            history = {"battle_id": battle_id, "events": []}

            # Collect all log files for this battle
            battle_files = sorted(self.log_dir.glob(f"battle_{battle_id}_*.json"))

            for file_path in battle_files:
                with open(file_path, "r") as f:
                    event_data = json.load(f)
                    history["events"].append(event_data)

            return history

        except Exception as e:
            raise LoggingError(f"Failed to get battle history: {e}")
