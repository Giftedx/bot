from typing import Dict, Set, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
from .movement_system import Tile


class TransportType(Enum):
    TELEPORT = "teleport"
    FAIRY_RING = "fairy_ring"
    SPIRIT_TREE = "spirit_tree"
    GNOME_GLIDER = "gnome_glider"
    CHARTER_SHIP = "charter_ship"
    MAGIC_CARPET = "magic_carpet"
    MINIGAME = "minigame"
    JEWELRY = "jewelry"
    WILDERNESS_OBELISK = "wilderness_obelisk"
    ANCIENT_OBELISK = "ancient_obelisk"
    PORTAL_NEXUS = "portal_nexus"
    POH_PORTAL = "poh_portal"
    ACHIEVEMENT_DIARY = "achievement_diary"
    QUEST = "quest"


class LocationType(Enum):
    BANK = "bank"
    GE = "grand_exchange"
    SHOP = "shop"
    ALTAR = "altar"
    SLAYER_MASTER = "slayer_master"
    FARMING_PATCH = "farming_patch"
    FISHING_SPOT = "fishing_spot"
    MINING_SITE = "mining_site"
    ANVIL = "anvil"
    FURNACE = "furnace"
    RANGE = "range"
    WELL = "well"
    AGILITY_COURSE = "agility_course"
    THIEVING_SPOT = "thieving_spot"
    BOSS_LAIR = "boss_lair"
    DUNGEON = "dungeon"
    QUEST_START = "quest_start"
    MINIGAME_AREA = "minigame_area"


class RegionType(Enum):
    CITY = "city"
    DUNGEON = "dungeon"
    WILDERNESS = "wilderness"
    GUILD = "guild"
    MINIGAME = "minigame"
    SLAYER = "slayer"


class TravelMethod(Enum):
    WALK = "walk"
    TELEPORT = "teleport"
    FAIRY_RING = "fairy_ring"
    SPIRIT_TREE = "spirit_tree"
    BOAT = "boat"
    AGILITY = "agility"
    UNDERGROUND = "underground"


@dataclass
class TransportNode:
    """Represents a transportation method in OSRS."""

    type: TransportType
    source: Tile
    destinations: List[Tuple[Tile, Dict[str, any]]]  # (destination, requirements)
    cost: int = 0
    cooldown: int = 0  # In game ticks
    requirements: Dict[str, any] = None
    interaction_text: str = ""


@dataclass
class LocationNode:
    """Represents a point of interest in OSRS."""

    type: LocationType
    tile: Tile
    name: str
    requirements: Dict[str, any] = None
    features: Set[str] = None  # Special features like "deposit_box", "poll_booth", etc.


@dataclass
class LocationRequirements:
    """Requirements to access a location"""

    quests: List[str] = None
    skills: Dict[str, int] = None
    items: List[str] = None
    achievement_diary: Dict[str, str] = None  # region -> tier
    combat_level: Optional[int] = None


@dataclass
class TravelRequirements:
    """Requirements for a travel method"""

    quests: List[str] = None
    skills: Dict[str, int] = None
    items: List[str] = None
    cost: Optional[int] = None
    energy_cost: Optional[float] = None


@dataclass
class Connection:
    """Connection between two locations"""

    destination: str
    method: TravelMethod
    requirements: TravelRequirements
    distance: int  # In tiles
    wilderness_level: Optional[int] = None


class TeleportGroups:
    """Groups of teleport locations by type."""

    STANDARD_SPELLBOOK = {
        "varrock": (3213, 3424, 0),
        "lumbridge": (3222, 3218, 0),
        "falador": (2964, 3379, 0),
        "camelot": (2757, 3477, 0),
        "ardougne": (2661, 3300, 0),
        "watchtower": (2931, 4717, 2),
        "trollheim": (2888, 3674, 0),
        "ape_atoll": (2796, 2799, 0),
        "house": None,  # Varies by house location
    }

    ANCIENT_SPELLBOOK = {
        "paddewwa": (3099, 9882, 0),
        "senntisten": (3322, 3336, 0),
        "kharyrll": (3492, 3471, 0),
        "lassar": (3006, 3471, 0),
        "dareeyak": (2990, 3696, 0),
        "carrallangar": (3156, 3666, 0),
        "annakarl": (3288, 3886, 0),
        "ghorrock": (2977, 3873, 0),
    }

    LUNAR_SPELLBOOK = {
        "moonclan": (2114, 3915, 0),
        "ourania": (2468, 3246, 0),
        "waterbirth": (2546, 3755, 0),
        "barbarian": (2544, 3572, 0),
        "khazard": (2636, 3167, 0),
        "fishing_guild": (2611, 3393, 0),
        "catherby": (2802, 3449, 0),
        "ice_plateau": (2973, 3939, 0),
    }

    ARCEUUS_SPELLBOOK = {
        "arceuus_library": (1632, 3838, 0),
        "draynor_manor": (3108, 3352, 0),
        "mind_altar": (2979, 3509, 0),
        "salve_graveyard": (3432, 3460, 0),
        "fenkenstrain": (3548, 3528, 0),
        "west_ardougne": (2500, 3291, 0),
        "harmony": (3799, 2867, 0),
        "cemetery": (2978, 3763, 0),
    }


class FairyRings:
    """All fairy ring locations and codes."""

    LOCATIONS = {
        "AIQ": ((2996, 3114, 0), "Asgarnia: Mudskipper Point"),
        "AIR": ((2700, 3247, 0), "Islands: South of Witchaven"),
        "AJQ": ((2735, 3353, 0), "Dungeons: Dark cave south of Dorgesh-Kaan"),
        "AJR": ((2780, 3613, 0), "Kandarin: Slayer cave south-east of Rellekka"),
        "AJS": ((2500, 3896, 0), "Islands: Penguins near Miscellania"),
        "AKQ": ((2319, 3619, 0), "Kandarin: Piscatoris Hunter area"),
        "AKS": ((2571, 2956, 0), "Feldip Hills: Jungle Hunter area"),
        "ALP": ((2468, 3411, 0), "Islands: Lighthouse"),
        "ALQ": ((3597, 3495, 0), "Morytania: Haunted Woods"),
        "ALR": ((3059, 4875, 0), "Other realms: Abyss"),
        "ALS": ((2644, 3495, 0), "Kandarin: McGrubor's Wood"),
        "BIP": ((3410, 3324, 0), "Islands: River Salve"),
        "BIQ": ((3251, 3095, 0), "Kharidian Desert: Near Kalphite hive"),
        "BIS": ((2635, 3266, 0), "Kandarin: Ardougne Zoo unicorns"),
        "BJR": ((2650, 4730, 0), "Other realms: Realm of the Fisher King"),
        "BJS": ((2147, 3070, 0), "Islands: Near Zul-Andra"),
        "BKP": ((2385, 3035, 0), "Feldip Hills: South of Castle Wars"),
        "BKQ": ((3041, 4532, 0), "Other realms: Enchanted Valley"),
        "BKR": ((3469, 3431, 0), "Morytania: Mort Myre, south of Canifis"),
        "BLP": ((2437, 3090, 0), "Islands: TzHaar area"),
        "BLR": ((2740, 3351, 0), "Kandarin: Legends' Guild"),
        "CIP": ((2513, 3884, 0), "Islands: Miscellania"),
        "CIQ": ((2528, 3127, 0), "Kandarin: North-west of Yanille"),
        "CJR": ((2705, 3576, 0), "Kandarin: Sinclair Mansion"),
        "CKP": ((2075, 4848, 0), "Other realms: Cosmic Entity's plane"),
        "CKR": ((2801, 3003, 0), "Karamja: South of Tai Bwo Wannai"),
        "CKS": ((3447, 3470, 0), "Morytania: Canifis"),
        "CLP": ((3082, 3206, 0), "Misthalin: South of Draynor Village"),
        "CLR": ((2740, 2738, 0), "Ape Atoll"),
        "DIS": ((3108, 3149, 0), "Misthalin: Wizards' Tower"),
        "DJP": ((2658, 3230, 0), "Kandarin: Tower of Life"),
        "DJR": ((2676, 3587, 0), "Kandarin: Sinclair Mansion (west)"),
        "DKP": ((2900, 3111, 0), "Karamja: South of Musa Point"),
        "DKR": ((3129, 3496, 0), "Misthalin: Edgeville"),
        "DKS": ((2744, 3719, 0), "Kandarin: Snowy Hunter area"),
        "DLQ": ((3423, 3016, 0), "Kharidian Desert: North of Nardah"),
        "DLR": ((2213, 3099, 0), "Islands: Poison Waste"),
    }


class SpiritTrees:
    """All spirit tree locations."""

    LOCATIONS = {
        "tree_gnome_village": (2542, 3170, 0),
        "tree_gnome_stronghold": (2461, 3444, 0),
        "battlefield_of_khazard": (2555, 3259, 0),
        "grand_exchange": (3183, 3508, 0),
        "poh": None,  # Varies by house location
    }


class GnomeGliders:
    """All gnome glider locations."""

    LOCATIONS = {
        "ta_quir_priw": (2465, 3501, 3),  # Grand Tree
        "kar_hewo": (3284, 3213, 0),  # Al Kharid
        "lemanto_andra": (3321, 3427, 0),  # White Wolf Mountain
        "sindarpos": (2850, 3498, 0),  # Crashed Grand Tree
        "gandius": (2894, 2729, 0),  # Karamja
        "lemantolly_undri": (2544, 2970, 0),  # Feldip Hills
    }


class MinigameTeleports:
    """All minigame teleport locations."""

    LOCATIONS = {
        "barbarian_assault": (2531, 3577, 0),
        "blast_furnace": (1948, 4959, 0),
        "burthorpe_games_room": (2207, 4934, 0),
        "castle_wars": (2440, 3092, 0),
        "clan_wars": (3388, 3158, 0),
        "fishing_trawler": (2667, 3161, 0),
        "nightmare_zone": (2611, 3177, 0),
        "pest_control": (2657, 2639, 0),
        "rat_pits": (3266, 3401, 0),
        "shades_of_mortton": (3499, 3298, 0),
        "soul_wars": (2210, 2858, 0),
        "trouble_brewing": (3811, 3021, 0),
        "tzhaar_fight_pit": (2399, 5177, 0),
    }


class Location:
    """Represents an OSRS location"""

    def __init__(
        self,
        name: str,
        region_type: RegionType,
        coordinates: Tuple[int, int, int],  # x, y, z
        requirements: LocationRequirements,
        connections: Dict[str, Connection],
        bank: bool = False,
        altar: bool = False,
        shops: List[str] = None,
        monsters: List[str] = None,
        resources: List[str] = None,
    ):
        self.name = name
        self.region_type = region_type
        self.coordinates = coordinates
        self.requirements = requirements
        self.connections = connections
        self.bank = bank
        self.altar = altar
        self.shops = shops or []
        self.monsters = monsters or []
        self.resources = resources or []


class LocationManager:
    """Manages game locations and travel"""

    def __init__(self):
        self.locations = self._load_locations()

    def _load_locations(self) -> Dict[str, Location]:
        """Load all location definitions"""
        return {
            "Lumbridge": Location(
                name="Lumbridge",
                region_type=RegionType.CITY,
                coordinates=(3222, 3218, 0),
                requirements=LocationRequirements(),
                connections={
                    "Al Kharid": Connection(
                        destination="Al Kharid",
                        method=TravelMethod.WALK,
                        requirements=TravelRequirements(cost=10),
                        distance=30,
                    ),
                    "Draynor Village": Connection(
                        destination="Draynor Village",
                        method=TravelMethod.WALK,
                        requirements=TravelRequirements(),
                        distance=50,
                    ),
                    "Varrock": Connection(
                        destination="Varrock",
                        method=TravelMethod.TELEPORT,
                        requirements=TravelRequirements(
                            skills={"magic": 25}, items=["Air rune", "Law rune", "Fire rune"]
                        ),
                        distance=0,
                    ),
                },
                bank=True,
                altar=True,
                shops=["General Store", "Combat Shop"],
                monsters=["Goblin", "Giant rat", "Spider"],
                resources=["Oak tree", "Copper ore", "Tin ore"],
            ),
            "Varrock": Location(
                name="Varrock",
                region_type=RegionType.CITY,
                coordinates=(3213, 3424, 0),
                requirements=LocationRequirements(),
                connections={
                    "Grand Exchange": Connection(
                        destination="Grand Exchange",
                        method=TravelMethod.WALK,
                        requirements=TravelRequirements(),
                        distance=20,
                    ),
                    "Wilderness": Connection(
                        destination="Wilderness",
                        method=TravelMethod.WALK,
                        requirements=TravelRequirements(),
                        distance=10,
                        wilderness_level=1,
                    ),
                    "Lumbridge": Connection(
                        destination="Lumbridge",
                        method=TravelMethod.TELEPORT,
                        requirements=TravelRequirements(
                            skills={"magic": 25}, items=["Air rune", "Law rune", "Earth rune"]
                        ),
                        distance=0,
                    ),
                },
                bank=True,
                altar=True,
                shops=["General Store", "Sword Shop", "Staff Shop", "Armor Shop", "Rune Shop"],
                monsters=["Guard", "Dark wizard"],
                resources=["Willow tree", "Iron ore", "Clay"],
            ),
            "Warriors' Guild": Location(
                name="Warriors' Guild",
                region_type=RegionType.GUILD,
                coordinates=(2855, 3543, 0),
                requirements=LocationRequirements(skills={"attack": 65, "strength": 65}),
                connections={
                    "Burthorpe": Connection(
                        destination="Burthorpe",
                        method=TravelMethod.WALK,
                        requirements=TravelRequirements(),
                        distance=15,
                    )
                },
                bank=True,
                shops=["Equipment Shop"],
                monsters=["Animated armor"],
            ),
            # Add more locations...
        }

    def get_location(self, name: str) -> Optional[Location]:
        """Get location by name"""
        return self.locations.get(name)

    def can_access_location(
        self,
        location: Location,
        player_quests: Set[str],
        player_skills: Dict[str, int],
        player_items: Set[str],
        player_achievements: Dict[str, Dict[str, bool]],
        combat_level: int,
    ) -> bool:
        """Check if player can access a location"""
        reqs = location.requirements

        # Check quest requirements
        if reqs.quests and not all(q in player_quests for q in reqs.quests):
            return False

        # Check skill requirements
        if reqs.skills:
            for skill, level in reqs.skills.items():
                if player_skills.get(skill, 0) < level:
                    return False

        # Check item requirements
        if reqs.items and not all(i in player_items for i in reqs.items):
            return False

        # Check achievement diary requirements
        if reqs.achievement_diary:
            for region, tier in reqs.achievement_diary.items():
                if not player_achievements.get(region, {}).get(tier, False):
                    return False

        # Check combat level
        if reqs.combat_level and combat_level < reqs.combat_level:
            return False

        return True

    def can_use_travel_method(
        self,
        connection: Connection,
        player_quests: Set[str],
        player_skills: Dict[str, int],
        player_items: Set[str],
        player_coins: int,
        player_energy: float,
    ) -> bool:
        """Check if player can use a travel method"""
        reqs = connection.requirements

        # Check quest requirements
        if reqs.quests and not all(q in player_quests for q in reqs.quests):
            return False

        # Check skill requirements
        if reqs.skills:
            for skill, level in reqs.skills.items():
                if player_skills.get(skill, 0) < level:
                    return False

        # Check item requirements
        if reqs.items and not all(i in player_items for i in reqs.items):
            return False

        # Check cost
        if reqs.cost and player_coins < reqs.cost:
            return False

        # Check energy
        if reqs.energy_cost and player_energy < reqs.energy_cost:
            return False

        return True

    def get_available_destinations(
        self,
        current_location: str,
        player_quests: Set[str],
        player_skills: Dict[str, int],
        player_items: Set[str],
        player_coins: int,
        player_energy: float,
    ) -> List[Tuple[str, TravelMethod]]:
        """Get list of available destinations from current location"""
        location = self.get_location(current_location)
        if not location:
            return []

        available = []
        for dest, conn in location.connections.items():
            if self.can_use_travel_method(
                conn, player_quests, player_skills, player_items, player_coins, player_energy
            ):
                available.append((dest, conn.method))

        return available

    def find_path(
        self,
        start: str,
        end: str,
        player_quests: Set[str],
        player_skills: Dict[str, int],
        player_items: Set[str],
        player_coins: int,
        player_energy: float,
        avoid_wilderness: bool = True,
    ) -> Optional[List[Tuple[str, Connection]]]:
        """Find shortest path between locations"""
        if start not in self.locations or end not in self.locations:
            return None

        # Dijkstra's algorithm
        distances = {loc: float("inf") for loc in self.locations}
        distances[start] = 0
        previous = {loc: None for loc in self.locations}
        unvisited = set(self.locations.keys())

        while unvisited:
            # Get closest unvisited location
            current = min(unvisited, key=lambda x: distances[x])
            if current == end:
                break

            unvisited.remove(current)

            # Check each connection
            location = self.locations[current]
            for dest, conn in location.connections.items():
                if dest not in unvisited:
                    continue

                # Skip wilderness if avoiding
                if avoid_wilderness and conn.wilderness_level:
                    continue

                # Check if can use connection
                if not self.can_use_travel_method(
                    conn, player_quests, player_skills, player_items, player_coins, player_energy
                ):
                    continue

                # Update distance
                distance = distances[current] + conn.distance
                if distance < distances[dest]:
                    distances[dest] = distance
                    previous[dest] = (current, conn)

        # Build path
        if distances[end] == float("inf"):
            return None

        path = []
        current = end
        while current != start:
            prev, conn = previous[current]
            path.append((prev, conn))
            current = prev

        return list(reversed(path))
