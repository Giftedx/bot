"""Core interfaces for battle system components."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Tuple, TypeVar

from .models import BattleMove, BattleState, StatusEffect

T = TypeVar("T", bound="IBattleSystem")


class IBattleSystem(ABC):
    """Interface for battle system implementations."""

    @abstractmethod
    def calculate_damage(
        self,
        move: BattleMove,
        attacker_stats: Dict[str, Any],
        defender_stats: Dict[str, Any],
    ) -> Tuple[int, str]:
        """Calculate damage and return amount + effect message."""
        raise NotImplementedError

    @abstractmethod
    def process_turn(self, battle_state: BattleState, move: str) -> Dict[str, Any]:
        """Process a turn and return the turn results."""
        raise NotImplementedError

    @abstractmethod
    def is_valid_move(
        self, battle_state: BattleState, move: str, player_id: int
    ) -> bool:
        """Validate if a move is legal for the current state."""
        raise NotImplementedError

    @abstractmethod
    def get_available_moves(
        self, battle_state: BattleState, player_id: int
    ) -> List[BattleMove]:
        """Get list of available moves for a player."""
        raise NotImplementedError

    @abstractmethod
    def apply_status_effects(
        self, stats: Dict[str, Any], effects: List[StatusEffect]
    ) -> Tuple[Dict[str, Any], List[str]]:
        """Apply status effects and return modified stats + messages."""
        raise NotImplementedError


class IDataProvider(Protocol):
    """Interface for data access."""

    async def get_osrs_stats(self, player_id: int) -> Dict[str, Any]:
        """Get OSRS stats for a player."""
        ...

    async def get_active_pokemon(self, player_id: int) -> Dict[str, Any]:
        """Get active Pokemon for a player."""
        ...

    async def get_active_pet(self, player_id: int) -> Dict[str, Any]:
        """Get active pet for a player."""
        ...

    async def save_battle_state(self, battle_state: BattleState) -> None:
        """Save battle state to persistent storage."""
        ...

    async def load_battle_state(self, battle_id: str) -> Optional[BattleState]:
        """Load battle state from persistent storage."""
        ...

    async def update_player_stats(
        self, player_id: int, stat_updates: Dict[str, Any]
    ) -> None:
        """Update player stats after battle."""
        ...


class IBattleLogger(Protocol):
    """Interface for battle logging."""

    def log_battle_start(self, battle_state: BattleState) -> None:
        """Log battle start event."""
        ...

    def log_turn(
        self, battle_state: BattleState, move: BattleMove, results: Dict[str, Any]
    ) -> None:
        """Log battle turn event."""
        ...

    def log_battle_end(
        self, battle_state: BattleState, final_stats: Dict[str, Any]
    ) -> None:
        """Log battle end event."""
        ...

    def log_error(
        self,
        battle_state: Optional[BattleState],
        error: Exception,
        context: Dict[str, Any],
    ) -> None:
        """Log battle system error."""
        ...


class IBattleManager(Protocol):
    """Interface for battle management."""

    def create_battle(self, battle_state: BattleState) -> None:
        """Create and initialize a new battle."""
        ...

    def end_battle(self, battle_state: BattleState, winner_id: Optional[int]) -> None:
        """End a battle and clean up resources."""
        ...

    def get_battle(self, battle_id: str) -> Optional[BattleState]:
        """Get battle state by ID."""
        ...

    def get_player_battle(self, player_id: int) -> Optional[BattleState]:
        """Get active battle for a player."""
        ...

    def validate_battle_state(self, battle_state: BattleState) -> None:
        """Validate battle state integrity."""
        ...
