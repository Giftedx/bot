"""OSRS map utility functions."""
from typing import List, Optional, Tuple
from ...database.models import TransportLocation, TeleportLocation
from .WorldMap import WorldPoint


def world_point_to_region(point: WorldPoint) -> Tuple[int, int]:
    """Convert world point to region coordinates."""
    return (point.x >> 6, point.y >> 6)  # Divide by 64 (region size)


def region_to_world_point(region_x: int, region_y: int, plane: int = 0) -> WorldPoint:
    """Convert region coordinates to world point (returns region's base point)."""
    return WorldPoint(region_x << 6, region_y << 6, plane)


def world_point_to_local(point: WorldPoint, base_x: int, base_y: int) -> Tuple[int, int]:
    """Convert world point to local coordinates."""
    return (point.x - base_x, point.y - base_y)


def local_to_world_point(
    local_x: int, local_y: int, base_x: int, base_y: int, plane: int = 0
) -> WorldPoint:
    """Convert local coordinates to world point."""
    return WorldPoint(base_x + local_x, base_y + local_y, plane)


def get_region_id(region_x: int, region_y: int) -> int:
    """Calculate region ID from region coordinates."""
    return (region_x << 8) | region_y


def get_region_coords(region_id: int) -> Tuple[int, int]:
    """Get region coordinates from region ID."""
    return (region_id >> 8, region_id & 0xFF)


def calculate_distance(point1: WorldPoint, point2: WorldPoint) -> int:
    """Calculate Manhattan distance between two points."""
    if point1.plane != point2.plane:
        return float("inf")
    return abs(point1.x - point2.x) + abs(point1.y - point2.y)


def is_in_area(point: WorldPoint, area_x: int, area_y: int, width: int, height: int) -> bool:
    """Check if a point is within a rectangular area."""
    return (
        point.x >= area_x
        and point.x < area_x + width
        and point.y >= area_y
        and point.y < area_y + height
    )


def get_wilderness_level(y: int) -> int:
    """Calculate wilderness level from y coordinate."""
    if y < 3520:  # Below wilderness
        return 0
    return min(56, (y - 3520) // 8 + 1)


def get_scene_coordinates(point: WorldPoint) -> Tuple[int, int]:
    """Convert world point to scene coordinates."""
    # Scene coordinates are relative to the base point (0,0) of the current scene
    scene_size = 104  # Standard OSRS scene size
    scene_base_x = (point.x >> 7) << 7  # Round to nearest scene base
    scene_base_y = (point.y >> 7) << 7
    return (point.x - scene_base_x, point.y - scene_base_y)


def is_in_members_area(point: WorldPoint, locations: List[TeleportLocation]) -> bool:
    """Check if a point is in a members-only area."""
    for loc in locations:
        if (
            loc.members_only
            and abs(loc.x - point.x) <= 32
            and abs(loc.y - point.y) <= 32  # Within 32 tiles
            and loc.plane == point.plane
        ):
            return True
    return False


def find_nearest_transport(
    point: WorldPoint, transport_type: Optional[str] = None, locations: List[TransportLocation] = []
) -> Optional[TransportLocation]:
    """Find the nearest transportation of a specific type."""
    if not locations:
        return None

    nearest = None
    min_distance = float("inf")

    for loc in locations:
        if transport_type and loc.transport_type.value != transport_type:
            continue

        loc_point = WorldPoint(loc.x, loc.y, loc.plane)
        distance = calculate_distance(point, loc_point)

        if distance < min_distance:
            min_distance = distance
            nearest = loc

    return nearest


def find_teleport_to_destination(
    destination: WorldPoint,
    max_level: Optional[int] = None,
    members_only: bool = True,
    locations: List[TeleportLocation] = [],
) -> List[TeleportLocation]:
    """Find teleports that can get you close to a destination."""
    suitable_teleports = []

    for loc in locations:
        if max_level and loc.level_requirement and loc.level_requirement > max_level:
            continue

        if not members_only and loc.members_only:
            continue

        loc_point = WorldPoint(loc.x, loc.y, loc.plane)
        distance = calculate_distance(destination, loc_point)

        if distance <= 50:  # Within 50 tiles
            suitable_teleports.append(loc)

    return sorted(
        suitable_teleports,
        key=lambda x: calculate_distance(destination, WorldPoint(x.x, x.y, x.plane)),
    )


def get_path_between_points(
    start: WorldPoint,
    end: WorldPoint,
    transport_locations: List[TransportLocation] = [],
    teleport_locations: List[TeleportLocation] = [],
) -> List[Tuple[str, WorldPoint]]:
    """Find a path between two points using available transportation."""
    path = []
    current = start

    # First try direct teleports
    teleports = find_teleport_to_destination(end, locations=teleport_locations)
    if teleports:
        teleport = teleports[0]
        return [
            ("start", start),
            ("teleport", WorldPoint(teleport.x, teleport.y, teleport.plane)),
            ("walk", end),
        ]

    # Then try transportation hubs
    while calculate_distance(current, end) > 20:  # Not within walking distance
        transport = find_nearest_transport(current, locations=transport_locations)
        if not transport:
            break

        transport_point = WorldPoint(transport.x, transport.y, transport.plane)
        if calculate_distance(current, transport_point) > calculate_distance(current, end):
            break  # Transport is further than destination

        path.append(("walk", transport_point))
        if transport.destination_x and transport.destination_y:
            current = WorldPoint(
                transport.destination_x, transport.destination_y, transport.destination_plane or 0
            )
            path.append(("transport", current))
        else:
            break

    path.append(("walk", end))
    return path


def is_in_instance(point: WorldPoint) -> bool:
    """Check if a point is in an instanced area."""
    return point.plane >= 4


def get_chunk_coordinates(point: WorldPoint) -> Tuple[int, int]:
    """Convert world point to chunk coordinates."""
    chunk_size = 8  # Standard chunk size
    return (point.x >> 3, point.y >> 3)  # Divide by chunk size


def get_map_square(point: WorldPoint) -> Tuple[int, int]:
    """Get map square coordinates for a point."""
    map_square_size = 64  # Size of a map square
    return (point.x >> 6, point.y >> 6)


def is_in_multi_combat(point: WorldPoint) -> bool:
    """Check if a point is in a multi-combat area."""
    wilderness_level = get_wilderness_level(point.y)
    if wilderness_level >= 20:  # Deep wilderness is multi
        return True

    # Add checks for other known multi-combat areas
    return False
