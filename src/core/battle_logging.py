"""Battle system exceptions and logging."""

import logging
from typing import Any, Dict, Optional


class BattleError(Exception):
    """Base class for battle-related errors."""


class BattleNotFoundError(BattleError):
    """Raised when trying to access a non-existent battle."""


class InvalidMoveError(BattleError):
    """Raised when an invalid move is attempted."""


class InvalidBattleStateError(BattleError):
    """Raised when battle is in an invalid state."""


class BattleLogger:
    """Handles battle system logging."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("battle_system")
        self.logger.setLevel(logging.INFO)

        # File handler for battle logs
        fh = logging.FileHandler("logs/battles.log")
        fh.setLevel(logging.INFO)

        # Console handler for errors
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)

        # Formatters
        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - Battle %(battle_id)s: %(message)s"
        )
        console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        fh.setFormatter(file_formatter)
        ch.setFormatter(console_formatter)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def log_battle_start(
        self, battle_id: str, battle_type: str, challenger_id: int, opponent_id: int
    ) -> None:
        """Log battle start."""
        self.logger.info(
            f"Battle started - Type: {battle_type}",
            extra={
                "battle_id": battle_id,
                "data": {
                    "type": battle_type,
                    "challenger": challenger_id,
                    "opponent": opponent_id,
                },
            },
        )

    def log_turn(
        self, battle_id: str, player_id: int, move: str, turn_data: Dict[str, Any]
    ) -> None:
        """Log a battle turn."""
        self.logger.info(
            f"Turn completed - Player {player_id} used {move}",
            extra={
                "battle_id": battle_id,
                "data": {"player": player_id, "move": move, "results": turn_data},
            },
        )

    def log_battle_end(
        self, battle_id: str, winner_id: Optional[int], battle_data: Dict[str, Any]
    ) -> None:
        """Log battle completion."""
        outcome = f"won by {winner_id}" if winner_id else "ended in draw"
        self.logger.info(
            f"Battle {outcome}",
            extra={
                "battle_id": battle_id,
                "data": {"winner": winner_id, "final_state": battle_data},
            },
        )

    def log_error(self, battle_id: str, error: Exception, context: Dict[str, Any]) -> None:
        """Log battle error."""
        self.logger.error(
            f"Battle error: {str(error)}",
            extra={
                "battle_id": battle_id,
                "data": {"error_type": type(error).__name__, "context": context},
            },
            exc_info=True,
        )

    def log_reward(self, battle_id: str, player_id: int, rewards: Dict[str, Any]) -> None:
        """Log battle rewards."""
        self.logger.info(
            f"Rewards given to player {player_id}",
            extra={
                "battle_id": battle_id,
                "data": {"player": player_id, "rewards": rewards},
            },
        )

    def log_achievement(self, battle_id: str, player_id: int, achievement: Dict[str, Any]) -> None:
        """Log achievement unlock."""
        self.logger.info(
            f"Achievement unlocked: {achievement['name']}",
            extra={
                "battle_id": battle_id,
                "data": {"player": player_id, "achievement": achievement},
            },
        )
