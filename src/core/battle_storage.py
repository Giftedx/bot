"""Battle state persistence and storage operations."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import DatabaseError
from .models import BattleState, BattleType


class BattleStorage:
    """Handles battle state persistence and storage."""

    def __init__(self, storage_dir: str = "data/battles") -> None:
        """Initialize battle storage.

        Args:
            storage_dir: Directory to store battle data
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def save_battle(self, battle_state: BattleState) -> None:
        """Save battle state to storage.

        Args:
            battle_state: Battle state to save

        Raises:
            DatabaseError: If save operation fails
        """
        try:
            # Convert battle state to serializable dict
            battle_data = {
                "battle_id": battle_state.battle_id,
                "battle_type": battle_state.battle_type.value,
                "challenger_id": battle_state.challenger_id,
                "opponent_id": battle_state.opponent_id,
                "current_turn": battle_state.current_turn,
                "is_finished": battle_state.is_finished,
                "winner_id": battle_state.winner_id,
                "battle_data": battle_state.battle_data,
                "turn_history": battle_state.turn_history,
                "round_number": battle_state.round_number,
            }

            # Save to file
            file_path = self.storage_dir / f"{battle_state.battle_id}.json"
            with open(file_path, "w") as f:
                json.dump(battle_data, f, indent=2)

        except Exception as e:
            raise DatabaseError(f"Failed to save battle state: {e}")

    async def load_battle(self, battle_id: str) -> Optional[BattleState]:
        """Load battle state from storage.

        Args:
            battle_id: ID of battle to load

        Returns:
            BattleState if found, None otherwise

        Raises:
            DatabaseError: If load operation fails
        """
        try:
            file_path = self.storage_dir / f"{battle_id}.json"
            if not file_path.exists():
                return None

            # Load from file
            with open(file_path, "r") as f:
                battle_data = json.load(f)

            # Convert back to BattleState
            return BattleState(
                battle_id=battle_data["battle_id"],
                battle_type=BattleType(battle_data["battle_type"]),
                challenger_id=battle_data["challenger_id"],
                opponent_id=battle_data["opponent_id"],
                current_turn=battle_data["current_turn"],
                is_finished=battle_data["is_finished"],
                winner_id=battle_data["winner_id"],
                battle_data=battle_data["battle_data"],
                turn_history=battle_data["turn_history"],
                round_number=battle_data["round_number"],
            )

        except Exception as e:
            raise DatabaseError(f"Failed to load battle state: {e}")

    async def delete_battle(self, battle_id: str) -> None:
        """Delete battle state from storage.

        Args:
            battle_id: ID of battle to delete

        Raises:
            DatabaseError: If delete operation fails
        """
        try:
            file_path = self.storage_dir / f"{battle_id}.json"
            if file_path.exists():
                file_path.unlink()

        except Exception as e:
            raise DatabaseError(f"Failed to delete battle state: {e}")

    async def list_active_battles(self) -> Dict[str, Any]:
        """List all active battles.

        Returns:
            Dict mapping battle IDs to basic battle info

        Raises:
            DatabaseError: If listing operation fails
        """
        try:
            active_battles = {}

            for file_path in self.storage_dir.glob("*.json"):
                with open(file_path, "r") as f:
                    battle_data = json.load(f)

                if not battle_data.get("is_finished", True):
                    battle_id = battle_data["battle_id"]
                    active_battles[battle_id] = {
                        "battle_type": battle_data["battle_type"],
                        "challenger_id": battle_data["challenger_id"],
                        "opponent_id": battle_data["opponent_id"],
                        "current_turn": battle_data["current_turn"],
                        "round_number": battle_data["round_number"],
                    }

            return active_battles

        except Exception as e:
            raise DatabaseError(f"Failed to list active battles: {e}")

    async def cleanup_finished_battles(self, max_age_hours: int = 24) -> None:
        """Clean up old finished battles.

        Args:
            max_age_hours: Maximum age in hours before deleting

        Raises:
            DatabaseError: If cleanup operation fails
        """
        try:
            from datetime import datetime, timedelta

            cutoff = datetime.now() - timedelta(hours=max_age_hours)

            for file_path in self.storage_dir.glob("*.json"):
                if file_path.stat().st_mtime < cutoff.timestamp():
                    with open(file_path, "r") as f:
                        battle_data = json.load(f)

                    if battle_data.get("is_finished", False):
                        file_path.unlink()

        except Exception as e:
            raise DatabaseError(f"Failed to cleanup battles: {e}")
