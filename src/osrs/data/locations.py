"""OSRS location data."""
from typing import List

from ..core.map.WorldMap import WorldArea, Location, MapRegion
from ..database.models import TransportLocation, TeleportLocation, SpecialLocation
from ..database.models import TransportationType, TeleportType

# Major cities and their areas
MAJOR_CITIES = [
    Location(name="Lumbridge", area=WorldArea(3218, 3218, 30, 30), region=MapRegion.MISTHALIN),
    Location(name="Varrock", area=WorldArea(3210, 3424, 40, 40), region=MapRegion.MISTHALIN),
    Location(name="Falador", area=WorldArea(2944, 3368, 35, 35), region=MapRegion.ASGARNIA),
    Location(
        name="Ardougne",
        area=WorldArea(2648, 3296, 40, 40),
        region=MapRegion.KANDARIN,
        members_only=True,
    ),
    Location(
        name="Canifis",
        area=WorldArea(3484, 3477, 25, 25),
        region=MapRegion.MORYTANIA,
        members_only=True,
    ),
    Location(
        name="Kourend",
        area=WorldArea(1600, 3632, 50, 50),
        region=MapRegion.KOUREND,
        members_only=True,
    ),
]

# Training areas
TRAINING_AREAS = [
    Location(name="Cow Field", area=WorldArea(3242, 3291, 15, 15), region=MapRegion.MISTHALIN),
    Location(
        name="Barbarian Village", area=WorldArea(3072, 3420, 20, 20), region=MapRegion.MISTHALIN
    ),
    Location(
        name="Al Kharid Warriors", area=WorldArea(3293, 3169, 15, 15), region=MapRegion.MISTHALIN
    ),
]

# Skilling locations
SKILLING_LOCATIONS = [
    # Mining
    Location(
        name="Varrock East Mine", area=WorldArea(3280, 3360, 15, 15), region=MapRegion.MISTHALIN
    ),
    Location(
        name="Varrock West Mine", area=WorldArea(3172, 3368, 15, 15), region=MapRegion.MISTHALIN
    ),
    # Fishing
    Location(
        name="Draynor Fishing Spot", area=WorldArea(3084, 3227, 10, 10), region=MapRegion.MISTHALIN
    ),
    # Woodcutting
    Location(
        name="Draynor Willows", area=WorldArea(3084, 3238, 12, 12), region=MapRegion.MISTHALIN
    ),
]

# Quest locations
QUEST_LOCATIONS = [
    Location(
        name="Cook's Kitchen",
        area=WorldArea(3205, 3212, 5, 5),
        region=MapRegion.MISTHALIN,
        quest_required="Cook's Assistant",
    ),
    Location(
        name="Champions' Guild",
        area=WorldArea(3188, 3355, 10, 10),
        region=MapRegion.MISTHALIN,
        quest_required="Dragon Slayer",
    ),
]

# Minigame locations
MINIGAME_LOCATIONS = [
    Location(name="Duel Arena", area=WorldArea(3355, 3265, 40, 40), region=MapRegion.MISTHALIN),
    Location(
        name="Castle Wars",
        area=WorldArea(2435, 3085, 30, 30),
        region=MapRegion.KANDARIN,
        members_only=True,
    ),
]

# Wilderness locations with levels
WILDERNESS_LOCATIONS = [
    Location(
        name="Edgeville Wilderness", area=WorldArea(3091, 3498, 30, 30), region=MapRegion.WILDERNESS
    ),
    Location(
        name="Wilderness God Wars Dungeon",
        area=WorldArea(3015, 3755, 40, 40),
        region=MapRegion.WILDERNESS,
        members_only=True,
    ),
]

# Ship routes
SHIP_ROUTES: List[TransportLocation] = [
    TransportLocation(
        id=1,
        name="Port Sarim to Karamja",
        transport_type=TransportationType.SHIP,
        x=3029,
        y=3218,
        plane=0,
        destination_x=2955,
        destination_y=3144,
        members_only=False,
    ),
    TransportLocation(
        id=2,
        name="Port Sarim to Entrana",
        transport_type=TransportationType.SHIP,
        x=3046,
        y=3233,
        plane=0,
        destination_x=2833,
        destination_y=3334,
        members_only=False,
    ),
    # Add more ship routes...
]

# Minecart network
MINECART_STATIONS: List[TransportLocation] = [
    TransportLocation(
        id=100,
        name="Grand Exchange to Keldagrim",
        transport_type=TransportationType.MINECART,
        x=3139,
        y=3504,
        plane=0,
        destination_x=2908,
        destination_y=10170,
        members_only=True,
    ),
    # Add more minecart stations...
]

# Standard magic teleports
STANDARD_TELEPORTS: List[TeleportLocation] = [
    TeleportLocation(
        id=1,
        name="Varrock Teleport",
        teleport_type=TeleportType.STANDARD_MAGIC,
        x=3213,
        y=3424,
        plane=0,
        level_requirement=25,
        members_only=False,
    ),
    TeleportLocation(
        id=2,
        name="Lumbridge Teleport",
        teleport_type=TeleportType.STANDARD_MAGIC,
        x=3222,
        y=3218,
        plane=0,
        level_requirement=31,
        members_only=False,
    ),
    # Add more standard teleports...
]

# Ancient magic teleports
ANCIENT_TELEPORTS: List[TeleportLocation] = [
    TeleportLocation(
        id=50,
        name="Paddewwa Teleport",
        teleport_type=TeleportType.ANCIENT_MAGIC,
        x=3097,
        y=9880,
        plane=0,
        level_requirement=54,
        members_only=True,
    ),
    # Add more ancient teleports...
]

# Fairy ring locations
FAIRY_RINGS: List[SpecialLocation] = [
    SpecialLocation(
        id=1,
        name="Zanaris Hub",
        location_type="fairy_ring",
        x=2412,
        y=4434,
        plane=0,
        code="CIS",
        members_only=True,
        quest_requirement="Lost City",
    ),
    # Add more fairy rings...
]

# Wilderness obelisks
WILDERNESS_OBELISKS: List[SpecialLocation] = [
    SpecialLocation(
        id=100,
        name="Level 13 Obelisk",
        location_type="wilderness_obelisk",
        x=3156,
        y=3620,
        plane=0,
        members_only=False,
    ),
    # Add more obelisks...
]

# Combine all locations
ALL_LOCATIONS = (
    MAJOR_CITIES
    + TRAINING_AREAS
    + SKILLING_LOCATIONS
    + QUEST_LOCATIONS
    + MINIGAME_LOCATIONS
    + WILDERNESS_LOCATIONS
)


def initialize_world_map(world_map):
    """Initialize world map with all locations."""
    for location in ALL_LOCATIONS:
        world_map.add_location(location)


def get_all_transport_locations() -> List[TransportLocation]:
    """Get all transportation locations."""
    return (
        SHIP_ROUTES
        + MINECART_STATIONS
        # Add more transport types...
    )


def get_all_teleport_locations() -> List[TeleportLocation]:
    """Get all teleport locations."""
    return (
        STANDARD_TELEPORTS
        + ANCIENT_TELEPORTS
        # Add more teleport types...
    )


def get_all_special_locations() -> List[SpecialLocation]:
    """Get all special locations."""
    return (
        FAIRY_RINGS
        + WILDERNESS_OBELISKS
        # Add more special location types...
    )
