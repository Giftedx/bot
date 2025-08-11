from __future__ import annotations

"""World manager for handling OSRS map data and locations."""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Set, List

from .movement import Position
from ..models.user import User as Player  # alias for tests


@dataclass
class Location:
    """Represents a named location in the game world."""

    name: str
    position: Position
    region_id: int
    is_members: bool = False
    requirements: Dict[str, int] = None  # Skill requirements to access


@dataclass
class Region:
    """Represents a region in the game world."""

    id: int
    name: str
    is_members: bool
    positions: List[Position]  # Boundary positions
    collision_map: List[List[bool]]  # True = blocked


@dataclass
class World:
    id: int
    name: str
    type: str
    region: str
    max_players: int = 2000
    player_count: int = 0
    is_full: bool = False
    players: Set[int] = field(default_factory=set)
    creation_time: datetime = field(default_factory=datetime.utcnow)
    last_update: Optional[datetime] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "region": self.region,
            "max_players": self.max_players,
            "player_count": self.player_count,
            "is_full": self.is_full,
            "players": list(self.players),
            "creation_time": self.creation_time.isoformat(),
            "last_update": self.last_update.isoformat() if self.last_update else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> World:
        w = cls(
            id=int(data["id"]),
            name=str(data["name"]),
            type=str(data["type"]),
            region=str(data["region"]),
            max_players=int(data.get("max_players", 2000)),
        )
        w.player_count = int(data.get("player_count", 0))
        w.is_full = bool(data.get("is_full", False))
        w.players = set(int(x) for x in data.get("players", []))
        ct = data.get("creation_time")
        if isinstance(ct, str):
            w.creation_time = datetime.fromisoformat(ct)
        lt = data.get("last_update")
        if isinstance(lt, str):
            w.last_update = datetime.fromisoformat(lt)
        return w


class WorldManager:
    """Manages OSRS world data and locations."""

    def __init__(self) -> None:
        self.worlds: Dict[int, World] = {}
        self.player_world: Dict[int, int] = {}
        self._init_defaults()

    def _init_defaults(self) -> None:
        # Minimal set of worlds to satisfy tests
        defaults: List[World] = [
            World(301, "World 301", "normal", "us"),
            World(302, "World 302", "normal", "eu"),
            World(353, "World 353 (1250+)", "skill_total", "us"),
            World(318, "World 318", "pvp", "us"),
            World(365, "World 365", "deadman", "us"),
            World(392, "World 392", "high_risk", "us"),
        ]
        for w in defaults:
            self.worlds[w.id] = w

    def get_world(self, world_id: int) -> Optional[World]:
        return self.worlds.get(world_id)

    def get_available_worlds(self, type_filter: Optional[str] = None) -> List[World]:
        worlds = list(self.worlds.values())
        if type_filter:
            worlds = [w for w in worlds if w.type == type_filter]
        return worlds

    def _meets_requirements(self, player: Player, world: World) -> bool:
        if world.type == "skill_total":
            return getattr(player, "total_level", 0) >= 1250
        return True

    def join_world(self, player: Player, world_id: int) -> bool:
        world = self.get_world(world_id)
        if not world:
            return False
        if not self._meets_requirements(player, world):
            return False
        # Remove from previous world
        prev = self.player_world.get(player.id)
        if prev and prev in self.worlds:
            self.worlds[prev].players.discard(player.id)
        # Add to new world
        world.players.add(player.id)
        self.player_world[player.id] = world.id
        return True

    def get_player_world(self, player: Player) -> Optional[World]:
        world_id = self.player_world.get(player.id)
        return self.worlds.get(world_id) if world_id else None

    def validate_world_action(self, player: Player, action: str, other_world: Optional[World] = None) -> bool:
        current = self.get_player_world(player)
        if not current:
            return False
        if current.type == "pvp" and action == "trade":
            return False
        if current.type == "high_risk" and action == "protect_item":
            return False
        if current.type == "deadman" and other_world and other_world.type == "normal":
            return False
        return True
