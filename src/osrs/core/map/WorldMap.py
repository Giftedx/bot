"""OSRS world map implementation."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


class MapRegion(Enum):
    """Map region types."""
    MISTHALIN = "misthalin"
    ASGARNIA = "asgarnia"
    KANDARIN = "kandarin"
    MORYTANIA = "morytania"
    KARAMJA = "karamja"
    WILDERNESS = "wilderness"
    KOUREND = "kourend"
    KEBOS = "kebos"
    FELDIP_HILLS = "feldip_hills"
    TIRANNWN = "tirannwn"
    PISCATORIS = "piscatoris"
    DESERT = "desert"
    FREMENNIK = "fremennik"
    TROLL_LANDS = "troll_lands"
    FOSSIL_ISLAND = "fossil_island"
    VARLAMORE = "varlamore"


@dataclass
class WorldPoint:
    """Represents a point in the game world."""
    x: int
    y: int
    plane: int = 0

    def distance_to(self, other: 'WorldPoint') -> int:
        """Calculate Manhattan distance to another point."""
        if self.plane != other.plane:
            return float('inf')
        return abs(self.x - other.x) + abs(self.y - other.y)

    def is_in_scene(self, scene_base_x: int, scene_base_y: int) -> bool:
        """Check if point is in the current scene."""
        scene_size = 104  # Standard OSRS scene size
        max_x = scene_base_x + scene_size
        max_y = scene_base_y + scene_size
        return (
            self.x >= scene_base_x and 
            self.x < max_x and 
            self.y >= scene_base_y and 
            self.y < max_y
        )


@dataclass
class WorldArea:
    """Represents a rectangular area in the game world."""
    x: int
    y: int
    width: int
    height: int
    plane: int = 0

    def contains(self, point: WorldPoint) -> bool:
        """Check if area contains a point."""
        return (
            point.plane == self.plane and
            point.x >= self.x and
            point.x < self.x + self.width and
            point.y >= self.y and
            point.y < self.y + self.height
        )

    def overlaps(self, other: 'WorldArea') -> bool:
        """Check if area overlaps with another area."""
        return (
            self.plane == other.plane and
            self.x < other.x + other.width and
            self.x + self.width > other.x and
            self.y < other.y + other.height and
            self.y + self.height > other.y
        )


@dataclass
class Location:
    """Represents a named location on the map."""
    name: str
    area: WorldArea
    region: MapRegion
    members_only: bool = False
    quest_required: Optional[str] = None
    achievement_diary_required: Optional[str] = None


class WorldMap:
    """OSRS world map manager."""

    REGION_SIZE = 64  # Size of a region in tiles

    def __init__(self):
        """Initialize world map."""
        self.locations: Dict[str, Location] = {}
        self.regions: Dict[MapRegion, Set[Tuple[int, int]]] = {
            region: set() for region in MapRegion
        }
        self._initialize_regions()

    def _initialize_regions(self):
        """Initialize region data."""
        # Misthalin regions
        self._add_region_coords(MapRegion.MISTHALIN, [
            (12850, 12851),  # Lumbridge
            (12598, 12597),  # Varrock
            (12342, 12343),  # Al Kharid
            (12854, 12855)   # Draynor
        ])

        # Asgarnia regions
        self._add_region_coords(MapRegion.ASGARNIA, [
            (11828, 11829),  # Falador
            (11572, 11573),  # Port Sarim
            (11316, 11317)   # Rimmington
        ])

        # Add more regions as needed...

    def _add_region_coords(self, region: MapRegion, coords: List[Tuple[int, int]]):
        """Add region coordinates."""
        self.regions[region].update(coords)

    def add_location(self, location: Location):
        """Add a location to the map."""
        self.locations[location.name] = location

    def get_region_at(self, point: WorldPoint) -> Optional[MapRegion]:
        """Get the region at a specific point."""
        region_x = point.x >> 6  # Divide by REGION_SIZE
        region_y = point.y >> 6
        region_id = (region_x << 8) | region_y

        for region_type, region_coords in self.regions.items():
            if (region_x, region_y) in region_coords:
                return region_type
        return None

    def get_locations_in_area(self, area: WorldArea) -> List[Location]:
        """Get all locations within an area."""
        return [
            loc for loc in self.locations.values()
            if loc.area.overlaps(area)
        ]

    def get_locations_in_region(self, region: MapRegion) -> List[Location]:
        """Get all locations in a region."""
        return [
            loc for loc in self.locations.values()
            if loc.region == region
        ]

    def get_nearest_location(self, point: WorldPoint) -> Optional[Location]:
        """Get the nearest location to a point."""
        if not self.locations:
            return None

        nearest = None
        min_distance = float('inf')

        for location in self.locations.values():
            # Use center point of location area
            loc_point = WorldPoint(
                location.area.x + location.area.width // 2,
                location.area.y + location.area.height // 2,
                location.area.plane
            )
            distance = point.distance_to(loc_point)
            if distance < min_distance:
                min_distance = distance
                nearest = location

        return nearest

    def is_in_members_area(self, point: WorldPoint) -> bool:
        """Check if a point is in a members-only area."""
        for location in self.locations.values():
            if location.members_only and location.area.contains(point):
                return True
        return False

    def is_in_wilderness(self, point: WorldPoint) -> bool:
        """Check if a point is in the wilderness."""
        return self.get_region_at(point) == MapRegion.WILDERNESS

    def get_wilderness_level(self, point: WorldPoint) -> int:
        """Get wilderness level at a point."""
        if not self.is_in_wilderness(point):
            return 0
        return (point.y - 3520) // 8 + 1  # Standard wilderness level formula 