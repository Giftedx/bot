"""OSRS world management and player interaction system."""
import json
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime

from ..models import Player
from ..database import db

logger = logging.getLogger(__name__)


@dataclass
class World:
    """Represents a game world."""
    id: int
    name: str
    type: str  # normal, pvp, deadman, etc.
    region: str  # us, uk, au, etc.
    players: Set[int] = field(default_factory=set)  # Set of player IDs
    max_players: int = 2000
    creation_time: datetime = field(default_factory=datetime.utcnow)
    last_update: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_full(self) -> bool:
        """Check if world has reached max players."""
        return len(self.players) >= self.max_players
    
    @property
    def player_count(self) -> int:
        """Get current player count."""
        return len(self.players)

    def to_dict(self) -> Dict:
        """Convert world to dictionary for storage."""
        data = asdict(self)
        data['players'] = list(self.players)
        data['creation_time'] = self.creation_time.isoformat()
        data['last_update'] = self.last_update.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'World':
        """Create world from dictionary."""
        data['players'] = set(data['players'])
        data['creation_time'] = datetime.fromisoformat(data['creation_time'])
        data['last_update'] = datetime.fromisoformat(data['last_update'])
        return cls(**data)


class WorldManager:
    """Manages game worlds and player world assignments."""
    
    def __init__(self) -> None:
        """Initialize world manager."""
        self.worlds: Dict[int, World] = {}
        self._load_worlds()
        
    def _load_worlds(self) -> None:
        """Load worlds from database or create defaults."""
        worlds_data = db.get("worlds")
        if worlds_data:
            # Load existing worlds
            worlds_dict = json.loads(worlds_data)
            self.worlds = {
                int(id_): World.from_dict(data)
                for id_, data in worlds_dict.items()
            }
        else:
            # Create default worlds
            self._setup_default_worlds()
            self._save_worlds()
        
    def _setup_default_worlds(self) -> None:
        """Create default game worlds."""
        default_worlds = [
            # Main worlds
            (301, "World 301", "normal", "us"),
            (302, "World 302", "normal", "us"),
            # PvP worlds
            (325, "World 325 (PvP)", "pvp", "us"),
            # Deadman worlds
            (345, "World 345 (Deadman)", "deadman", "us"),
            # High-Risk worlds
            (337, "World 337 (High Risk)", "high_risk", "uk"),
            # Skill Total worlds
            (353, "World 353 (1250+)", "skill_total", "us"),
            (354, "World 354 (1500+)", "skill_total", "us"),
            (355, "World 355 (2000+)", "skill_total", "us"),
        ]
        
        for world_id, name, type_, region in default_worlds:
            self.worlds[world_id] = World(
                id=world_id,
                name=name,
                type=type_,
                region=region
            )
            
    def _save_worlds(self) -> None:
        """Save worlds to database."""
        worlds_dict = {
            str(id_): world.to_dict()
            for id_, world in self.worlds.items()
        }
        db.set("worlds", json.dumps(worlds_dict))
            
    def get_world(self, world_id: int) -> Optional[World]:
        """Get world by ID."""
        return self.worlds.get(world_id)
        
    def get_available_worlds(
        self,
        type_filter: Optional[str] = None,
        region_filter: Optional[str] = None
    ) -> List[World]:
        """
        Get list of available worlds, optionally filtered.
        
        Args:
            type_filter: Filter by world type
            region_filter: Filter by region
            
        Returns:
            List[World]: List of matching worlds
        """
        worlds = self.worlds.values()
        
        if type_filter:
            worlds = [w for w in worlds if w.type == type_filter]
            
        if region_filter:
            worlds = [w for w in worlds if w.region == region_filter]
            
        return sorted(worlds, key=lambda w: w.id)
        
    def join_world(
        self,
        player: Player,
        world_id: int
    ) -> bool:
        """
        Attempt to add player to world.
        
        Args:
            player: Player to add
            world_id: World to join
            
        Returns:
            bool: True if successful, False if failed
            
        Raises:
            ValueError: If world doesn't exist
        """
        world = self.get_world(world_id)
        if not world:
            raise ValueError(f"World {world_id} does not exist")
            
        # Check world requirements
        if world.type == "skill_total":
            total_level = sum(
                level for level in player.skills.values()
            )
            if "1250+" in world.name and total_level < 1250:
                return False
            if "1500+" in world.name and total_level < 1500:
                return False
            if "2000+" in world.name and total_level < 2000:
                return False
                
        # Remove from current world if any
        self.leave_current_world(player)
        
        # Add to new world
        if not world.is_full:
            world.players.add(player.id)
            world.last_update = datetime.utcnow()
            self._save_worlds()
            return True
            
        return False
        
    def leave_current_world(self, player: Player) -> None:
        """Remove player from their current world."""
        for world in self.worlds.values():
            if player.id in world.players:
                world.players.remove(player.id)
                world.last_update = datetime.utcnow()
                self._save_worlds()
                break
                
    def get_player_world(self, player: Player) -> Optional[World]:
        """Get the world a player is currently in."""
        for world in self.worlds.values():
            if player.id in world.players:
                return world
        return None
        
    def validate_world_action(
        self,
        player: Player,
        action: str,
        target_world: Optional[World] = None
    ) -> bool:
        """
        Validate if a player can perform an action in their world.
        
        Args:
            player: Player attempting action
            action: Action being attempted
            target_world: Target world for cross-world actions
            
        Returns:
            bool: True if action is allowed
        """
        current_world = self.get_player_world(player)
        if not current_world:
            return False
            
        # Deadman mode restrictions
        if current_world.type == "deadman":
            if target_world and target_world.type != "deadman":
                return False  # Can't interact with non-deadman worlds
                
        # PvP world restrictions
        if current_world.type == "pvp":
            if action == "trade" and not target_world:
                return False  # No trading in PvP worlds
                
        # High risk world restrictions
        if current_world.type == "high_risk":
            if action == "protect_item":
                return False  # No protect item in high risk
                
        return True


# Global world manager instance
world_manager = WorldManager()
