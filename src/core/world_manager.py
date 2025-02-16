"""OSRS world management system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set


class WorldType(Enum):
    """Types of game worlds"""

    REGULAR = "regular"
    PVP = "pvp"
    HIGH_RISK = "high_risk"
    MEMBERS = "members"
    SKILL_TOTAL = "skill_total"
    FRESH_START = "fresh_start"


@dataclass
class World:
    """Game world instance"""

    id: int
    name: str
    type: WorldType
    region: str
    members_only: bool = False
    pvp: bool = False
    high_risk: bool = False
    skill_total: int = 0
    max_players: int = 2000
    player_ids: Set[int] = field(default_factory=set)
    last_update: datetime = field(default_factory=datetime.now)

    @property
    def player_count(self) -> int:
        return len(self.player_ids)

    @property
    def is_full(self) -> bool:
        return self.player_count >= self.max_players


class WorldManager:
    """Manages game worlds and player world assignments"""

    def __init__(self):
        self.worlds: Dict[int, World] = {}
        self._initialize_worlds()

    def _initialize_worlds(self):
        """Initialize default game worlds"""
        self.worlds = {
            301: World(
                id=301,
                name="World 301",
                type=WorldType.REGULAR,
                region="UK",
                members_only=False,
            ),
            302: World(
                id=302,
                name="World 302",
                type=WorldType.REGULAR,
                region="US",
                members_only=False,
            ),
            325: World(
                id=325,
                name="World 325",
                type=WorldType.PVP,
                region="UK",
                members_only=True,
                pvp=True,
            ),
            416: World(
                id=416,
                name="World 416",
                type=WorldType.SKILL_TOTAL,
                region="US",
                members_only=True,
                skill_total=1500,
            ),
            477: World(
                id=477,
                name="World 477",
                type=WorldType.HIGH_RISK,
                region="US",
                members_only=True,
                high_risk=True,
            ),
        }

    def get_world(self, world_id: int) -> Optional[World]:
        """Get world by ID"""
        return self.worlds.get(world_id)

    def get_available_worlds(
        self,
        type_filter: Optional[str] = None,
        members_only: Optional[bool] = None,
        region: Optional[str] = None,
    ) -> List[World]:
        """Get available worlds matching filters"""
        worlds = self.worlds.values()

        if type_filter:
            try:
                world_type = WorldType(type_filter.lower())
                worlds = [w for w in worlds if w.type == world_type]
            except ValueError:
                pass

        if members_only is not None:
            worlds = [w for w in worlds if w.members_only == members_only]

        if region:
            worlds = [w for w in worlds if w.region.lower() == region.lower()]

        return sorted(worlds, key=lambda w: w.id)

    def join_world(self, player_id: int, world_id: int) -> bool:
        """Move player to a different world"""
        if world_id not in self.worlds:
            return False

        new_world = self.worlds[world_id]
        if new_world.is_full:
            return False

        # Remove from old world
        for world in self.worlds.values():
            if player_id in world.player_ids:
                world.player_ids.remove(player_id)

        # Add to new world
        new_world.player_ids.add(player_id)
        new_world.last_update = datetime.now()
        return True

    def get_player_world(self, player_id: int) -> Optional[World]:
        """Get the world a player is currently in"""
        for world in self.worlds.values():
            if player_id in world.player_ids:
                return world
        return None


# Global instance
world_manager = WorldManager()
