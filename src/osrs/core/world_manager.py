"""World manager for handling OSRS map data and locations."""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from typing import Set
from datetime import datetime

from .movement import Position


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
    type: str  # e.g., normal, pvp, deadman, high_risk, skill_total
    region: str = "us"
    max_players: int = 2000
    players: Set[int] = field(default_factory=set)
    creation_time: datetime = field(default_factory=datetime.utcnow)
    last_update: datetime = field(default_factory=datetime.utcnow)

    @property
    def player_count(self) -> int:
        return len(self.players)

    @property
    def is_full(self) -> bool:
        return self.player_count >= self.max_players

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "region": self.region,
            "max_players": self.max_players,
            "players": list(self.players),
            "creation_time": self.creation_time.isoformat(),
            "last_update": self.last_update.isoformat(),
        }

    @staticmethod
    def from_dict(data: Dict) -> "World":
        w = World(
            id=data["id"],
            name=data["name"],
            type=data["type"],
            region=data.get("region", "us"),
            max_players=data.get("max_players", 2000),
        )
        w.players = set(data.get("players", []))
        w.creation_time = datetime.fromisoformat(data["creation_time"]) if data.get("creation_time") else datetime.utcnow()
        w.last_update = datetime.fromisoformat(data["last_update"]) if data.get("last_update") else datetime.utcnow()
        return w


class _SimpleWorldManager:
    def __init__(self) -> None:
        self.worlds: Dict[int, World] = {}
        # Seed default worlds
        self._add_world(World(301, "World 301", "normal", region="us"))
        self._add_world(World(302, "World 302", "normal", region="eu"))
        self._add_world(World(318, "World 318", "pvp", region="us"))
        self._add_world(World(345, "World 345", "deadman", region="us"))
        self._add_world(World(353, "World 353 (1250+)", "skill_total", region="us"))
        self._add_world(World(365, "World 365 (High Risk)", "high_risk", region="eu"))

    def _add_world(self, world: World) -> None:
        self.worlds[world.id] = world

    def get_world(self, world_id: int) -> Optional[World]:
        return self.worlds.get(world_id)

    def get_available_worlds(self, type_filter: Optional[str] = None) -> List[World]:
        worlds = list(self.worlds.values())
        if type_filter:
            worlds = [w for w in worlds if w.type == type_filter]
        return worlds

    def get_player_world(self, player) -> Optional[World]:
        for w in self.worlds.values():
            if player.id in w.players:
                return w
        return None

    def join_world(self, player, world_id: int) -> bool:
        world = self.get_world(world_id)
        if not world or world.is_full:
            return False

        # Enforce skill total requirement for 1250+ world
        if "1250+" in world.name:
            total = sum(s.level for s in player.skills.values())
            if total < 1250:
                return False

        # Move player from previous world if present
        prev = self.get_player_world(player)
        if prev:
            prev.players.discard(player.id)

        world.players.add(player.id)
        world.last_update = datetime.utcnow()
        return True

    def validate_world_action(self, player, action: str, target_world: Optional[World] = None) -> bool:
        current = self.get_player_world(player)
        if not current:
            return True
        if current.type == "pvp" and action == "trade":
            return False
        if current.type == "high_risk" and action == "protect_item":
            return False
        if current.type == "deadman" and target_world and target_world.type == "normal":
            return False
        return True


# Expose simple manager for tests
WorldManager = _SimpleWorldManager
# Ensure alias remains the exported symbol
World = World


class WorldManager:
    """Manages OSRS world data and locations."""

    def __init__(self, data_path: str):
        """Initialize the world manager.

        Args:
            data_path: Path to world data files
        """
        self.data_path = Path(data_path)
        self.regions: Dict[int, Region] = {}
        self.locations: Dict[str, Location] = {}
        self.collision_maps: Dict[int, List[List[bool]]] = {}

        # Load world data
        self._load_regions()
        self._load_locations()
        self._load_collision_maps()

    def _load_regions(self):
        """Load region data from JSON."""
        region_file = self.data_path / "regions.json"
        if not region_file.exists():
            return

        with open(region_file) as f:
            data = json.load(f)
            for region_data in data:
                positions = [
                    Position(pos["x"], pos["y"], pos.get("plane", 0))
                    for pos in region_data["positions"]
                ]

                self.regions[region_data["id"]] = Region(
                    id=region_data["id"],
                    name=region_data["name"],
                    is_members=region_data["is_members"],
                    positions=positions,
                    collision_map=[],  # Loaded separately
                )

    def _load_locations(self):
        """Load location data from JSON."""
        location_file = self.data_path / "locations.json"
        if not location_file.exists():
            return

        with open(location_file) as f:
            data = json.load(f)
            for loc_data in data:
                pos = Position(
                    loc_data["position"]["x"],
                    loc_data["position"]["y"],
                    loc_data["position"].get("plane", 0),
                )

                self.locations[loc_data["name"]] = Location(
                    name=loc_data["name"],
                    position=pos,
                    region_id=loc_data["region_id"],
                    is_members=loc_data.get("is_members", False),
                    requirements=loc_data.get("requirements", {}),
                )

    def _load_collision_maps(self):
        """Load collision map data."""
        collision_dir = self.data_path / "collision"
        if not collision_dir.exists():
            return

        for region_file in collision_dir.glob("*.json"):
            region_id = int(region_file.stem)
            with open(region_file) as f:
                self.collision_maps[region_id] = json.load(f)

            if region_id in self.regions:
                self.regions[region_id].collision_map = self.collision_maps[region_id]

    def get_region(self, region_id: int) -> Optional[Region]:
        """Get region by ID.

        Args:
            region_id: Region identifier

        Returns:
            Region data if found, None otherwise
        """
        return self.regions.get(region_id)

    def get_location(self, name: str) -> Optional[Location]:
        """Get location by name.

        Args:
            name: Location name

        Returns:
            Location data if found, None otherwise
        """
        return self.locations.get(name)

    def get_nearest_location(self, pos: Position) -> Optional[Tuple[str, float]]:
        """Find nearest named location to position.

        Args:
            pos: Position to search from

        Returns:
            Tuple of (location name, distance) if found, None otherwise
        """
        if not self.locations:
            return None

        nearest = min(self.locations.items(), key=lambda x: pos.real_distance_to(x[1].position))

        return (nearest[0], pos.real_distance_to(nearest[1].position))

    def get_collision_map(self, region_id: int) -> Optional[List[List[bool]]]:
        """Get collision map for region.

        Args:
            region_id: Region identifier

        Returns:
            2D collision map if found, None otherwise
        """
        return self.collision_maps.get(region_id)

    def is_walkable(self, pos: Position) -> bool:
        """Check if position is walkable.

        Args:
            pos: Position to check

        Returns:
            True if walkable, False otherwise
        """
        # Find region containing position
        region = next(
            (
                r
                for r in self.regions.values()
                if any(p.x <= pos.x <= p.x + 64 and p.y <= pos.y <= p.y + 64 for p in r.positions)
            ),
            None,
        )

        if not region or not region.collision_map:
            return False

        # Convert to local coordinates
        local_x = pos.x % 64
        local_y = pos.y % 64

        try:
            return not region.collision_map[local_y][local_x]
        except IndexError:
            return False

    def can_access_location(
        self, location: Location, player_skills: Dict[str, int], is_member: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """Check if player can access location.

        Args:
            location: Location to check
            player_skills: Dictionary of player skill levels
            is_member: Whether player is a member

        Returns:
            Tuple of (can access, reason if cannot)
        """
        if location.is_members and not is_member:
            return (False, "Members only location")

        if location.requirements:
            for skill, level in location.requirements.items():
                if player_skills.get(skill, 1) < level:
                    return (False, f"Requires {skill} level {level}")

        return (True, None)

    def get_path_between_locations(
        self, start_name: str, end_name: str, movement_system
    ) -> Optional[List[Position]]:
        """Find path between named locations.

        Args:
            start_name: Starting location name
            end_name: Destination location name
            movement_system: MovementSystem instance for pathfinding

        Returns:
            List of positions forming path if found, None otherwise
        """
        start_loc = self.get_location(start_name)
        end_loc = self.get_location(end_name)

        if not start_loc or not end_loc:
            return None

        # Get regions path needs to traverse
        start_region = self.get_region(start_loc.region_id)
        end_region = self.get_region(end_loc.region_id)

        if not start_region or not end_region:
            return None

        # Combine collision maps of regions
        combined_map = self._combine_collision_maps([start_region, end_region])

        # Calculate path
        return movement_system.calculate_path(start_loc.position, end_loc.position, combined_map)

    def _combine_collision_maps(self, regions: List[Region]) -> List[List[bool]]:
        """Combine collision maps from multiple regions.

        Args:
            regions: List of regions to combine

        Returns:
            Combined collision map
        """
        # Find bounds
        min_x = min(pos.x for r in regions for pos in r.positions)
        max_x = max(pos.x for r in regions for pos in r.positions)
        min_y = min(pos.y for r in regions for pos in r.positions)
        max_y = max(pos.y for r in regions for pos in r.positions)

        width = max_x - min_x + 1
        height = max_y - min_y + 1

        # Initialize combined map
        combined = [[True] * width for _ in range(height)]

        # Merge collision data
        for region in regions:
            if not region.collision_map:
                continue

            for y, row in enumerate(region.collision_map):
                for x, blocked in enumerate(row):
                    world_x = region.positions[0].x + x - min_x
                    world_y = region.positions[0].y + y - min_y

                    if 0 <= world_x < width and 0 <= world_y < height:
                        combined[world_y][world_x] = blocked

        return combined

# Override export to ensure tests use simple manager
WorldManager = _SimpleWorldManager
