"""World manager for handling OSRS map data and locations."""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

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
