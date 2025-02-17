"""Core interfaces for battle system components."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Tuple, TypeVar
import json
from dataclasses import dataclass
from datetime import datetime

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


@dataclass
class DisplayState:
    """Current state of the game display"""
    mode: str = "text"  # text or graphical
    content: str = ""
    graphics_data: Dict[str, Any] = None
    last_update: datetime = None


class GameDisplay:
    """Handles both text and graphical display modes for the game"""
    
    def __init__(self):
        self.state = DisplayState()
        
    def update_text(self, content: str):
        """Update text display content"""
        self.state.content = content
        self.state.last_update = datetime.now()
        
    def update_graphics(self, player_state: Any):
        """Update graphical display state"""
        # Convert player state to graphics data
        graphics_data = {
            "location": player_state.location,
            "stats": {
                "combat": player_state.combat_stats.calculate_combat_level(),
                "skills": player_state.skills
            },
            "equipment": player_state.equipment.__dict__,
            "inventory": player_state.inventory
        }
        
        self.state.graphics_data = graphics_data
        self.state.last_update = datetime.now()
        
    def get_display_data(self) -> Dict[str, Any]:
        """Get current display data in format suitable for Discord embed or iframe"""
        if self.state.mode == "text":
            return {
                "type": "text",
                "content": self.state.content,
                "timestamp": self.state.last_update.isoformat()
            }
        else:
            return {
                "type": "graphical",
                "data": self.state.graphics_data,
                "timestamp": self.state.last_update.isoformat()
            }
            
    def get_iframe_html(self) -> str:
        """Generate HTML for iframe display"""
        if self.state.mode != "graphical":
            return ""
            
        data = json.dumps(self.state.graphics_data)
        return f"""
        <iframe id="game-display" 
                src="about:blank"
                style="width: 100%; height: 500px; border: none;">
        <script>
            const gameData = {data};
            // Render game display using graphics data
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            function render() {{
                // Clear canvas
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                // Draw player location
                ctx.fillText(`Location: ${{gameData.location}}`, 10, 20);
                
                // Draw stats
                let y = 50;
                for (const [skill, level] of Object.entries(gameData.stats.skills)) {{
                    ctx.fillText(`${{skill}}: ${{level}}`, 10, y);
                    y += 20;
                }}
                
                // Draw equipment
                y = 50;
                ctx.fillText("Equipment:", 200, 30);
                for (const [slot, item] of Object.entries(gameData.equipment)) {{
                    if (item) {{
                        ctx.fillText(`${{slot}}: ${{item}}`, 200, y);
                        y += 20;
                    }}
                }}
                
                // Draw inventory
                y = 50;
                ctx.fillText("Inventory:", 400, 30);
                for (const [item, count] of Object.entries(gameData.inventory)) {{
                    ctx.fillText(`${{item}} x${{count}}`, 400, y);
                    y += 20;
                }}
            }}
            
            // Initial render
            render();
            
            // Update every second
            setInterval(render, 1000);
        </script>
        </iframe>
        """
