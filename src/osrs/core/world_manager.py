"""OSRS world system implementation."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import logging

from ..models import User
from .map.WorldMap import WorldPoint, WorldArea, Location, MapRegion
from ..database.models import (
    Database,
    TransportLocation,
    TeleportLocation,
    SpecialLocation
)
from .map.map_utils import (
    calculate_distance,
    get_wilderness_level,
    is_in_multi_combat
)


logger = logging.getLogger('WorldManager')


@dataclass
class World:
    """Represents an OSRS world."""
    id: int
    name: str
    description: str
    type: str  # regular, pvp, skill, minigame
    region: str  # us, uk, de, au
    members_only: bool = False
    pvp: bool = False
    skill_total: int = 0
    players: Set[int] = field(default_factory=set)  # Set of player IDs
    max_players: int = 2000


class WorldManager:
    """Manages the game world and its regions."""
    
    def __init__(self, database: Database):
        """Initialize world manager."""
        self.db = database
        self.worlds: Dict[int, World] = self._initialize_worlds()
        self.regions: Dict[MapRegion, Set[WorldArea]] = {
            region: set() for region in MapRegion
        }
        self.locations: Dict[str, Location] = {}
        self.transport_locations: List[TransportLocation] = []
        self.teleport_locations: List[TeleportLocation] = []
        self.special_locations: List[SpecialLocation] = []
        self.multi_combat_areas: Set[WorldArea] = set()
        self.members_areas: Set[WorldArea] = set()
        self.load_world_data()
    
    def _initialize_worlds(self) -> Dict[int, World]:
        """Initialize default worlds."""
        worlds = {}
        
        # Free-to-play worlds
        worlds[301] = World(
            id=301,
            name="301",
            description="Free-to-play world",
            type="regular",
            region="us"
        )
        
        worlds[308] = World(
            id=308,
            name="308",
            description="Free-to-play PvP world",
            type="pvp",
            region="us",
            pvp=True
        )
        
        # Members worlds
        worlds[302] = World(
            id=302,
            name="302",
            description="Members world",
            type="regular",
            region="us",
            members_only=True
        )
        
        worlds[325] = World(
            id=325,
            name="325",
            description="High Risk PvP world",
            type="pvp",
            region="uk",
            members_only=True,
            pvp=True
        )
        
        worlds[349] = World(
            id=349,
            name="349",
            description="Skill Total (1500)",
            type="skill",
            region="uk",
            members_only=True,
            skill_total=1500
        )
        
        worlds[361] = World(
            id=361,
            name="361",
            description="High Risk PvP world",
            type="pvp",
            region="au",
            members_only=True,
            pvp=True
        )
        
        return worlds
    
    def get_world(self, world_id: int) -> Optional[World]:
        """Get a world by its ID."""
        return self.worlds.get(world_id)
    
    def get_player_world(self, player: User) -> Optional[World]:
        """Get the world a player is in."""
        return self.worlds.get(player.current_world)
    
    def join_world(self, player: User, world_id: int) -> bool:
        """
        Move a player to a different world.
        Returns True if successful.
        """
        # Check if world exists
        world = self.worlds.get(world_id)
        if not world:
            return False
        
        # Check world requirements
        if world.members_only and not self._is_member(player):
            return False
        
        if world.skill_total > 0 and not self._meets_skill_total(player, world.skill_total):
            return False
        
        # Remove from current world
        current_world = self.worlds.get(player.current_world)
        if current_world:
            current_world.players.discard(player.id)
        
        # Check world capacity
        if len(world.players) >= world.max_players:
            return False
        
        # Add to new world
        world.players.add(player.id)
        player.current_world = world_id
        
        return True
    
    def leave_world(self, player: User) -> None:
        """Remove a player from their current world."""
        world = self.worlds.get(player.current_world)
        if world:
            world.players.discard(player.id)
    
    def are_players_in_same_world(self, player1: User, player2: User) -> bool:
        """Check if two players are in the same world."""
        return player1.current_world == player2.current_world
    
    def is_pvp_enabled(self, player: User) -> bool:
        """Check if a player is in a PvP world."""
        world = self.worlds.get(player.current_world)
        return world is not None and world.pvp
    
    def get_world_players(self, world_id: int) -> Set[int]:
        """Get all players in a world."""
        world = self.worlds.get(world_id)
        return world.players if world else set()
    
    def get_available_worlds(self, player: User) -> List[World]:
        """Get all worlds available to a player."""
        is_member = self._is_member(player)
        total_level = self._get_total_level(player)
        
        return [
            world for world in self.worlds.values()
            if (not world.members_only or is_member)
            and (world.skill_total == 0 or total_level >= world.skill_total)
        ]
    
    def _is_member(self, player: User) -> bool:
        """Check if a player is a member."""
        # TODO: Implement membership check
        return True
    
    def _meets_skill_total(self, player: User, required_total: int) -> bool:
        """Check if a player meets the total level requirement."""
        return self._get_total_level(player) >= required_total
    
    def _get_total_level(self, player: User) -> int:
        """Calculate a player's total level."""
        return sum(skill.level for skill in player.skills.values())
    
    def load_world_data(self) -> None:
        """Load world data from database."""
        with self.db.conn:
            cursor = self.db.conn.cursor()
            
            # Load transport locations
            cursor.execute("SELECT * FROM transport_locations")
            for row in cursor.fetchall():
                location = TransportLocation(**row)
                self.transport_locations.append(location)
                if location.members_only:
                    self.members_areas.add(
                        WorldArea(
                            location.x - 32,
                            location.y - 32,
                            64, 64
                        )
                    )
                    
            # Load teleport locations
            cursor.execute("SELECT * FROM teleport_locations")
            for row in cursor.fetchall():
                location = TeleportLocation(**row)
                self.teleport_locations.append(location)
                if location.members_only:
                    self.members_areas.add(
                        WorldArea(
                            location.x - 32,
                            location.y - 32,
                            64, 64
                        )
                    )
                    
            # Load special locations
            cursor.execute("SELECT * FROM special_locations")
            for row in cursor.fetchall():
                location = SpecialLocation(**row)
                self.special_locations.append(location)
                if location.members_only:
                    self.members_areas.add(
                        WorldArea(
                            location.x - 32,
                            location.y - 32,
                            64, 64
                        )
                    )
                    
    def add_location(self, location: Location) -> None:
        """Add a location to the world."""
        self.locations[location.name] = location
        self.regions[location.region].add(location.area)
        
        if location.members_only:
            self.members_areas.add(location.area)
            
    def get_location(self, name: str) -> Optional[Location]:
        """Get a location by name."""
        return self.locations.get(name)
        
    def get_locations_in_region(self, region: MapRegion) -> List[Location]:
        """Get all locations in a region."""
        return [
            loc for loc in self.locations.values()
            if loc.region == region
        ]
        
    def get_locations_in_area(self, area: WorldArea) -> List[Location]:
        """Get all locations within an area."""
        return [
            loc for loc in self.locations.values()
            if loc.area.overlaps(area)
        ]
        
    def get_nearest_location(
        self,
        point: WorldPoint,
        max_distance: Optional[int] = None
    ) -> Optional[Location]:
        """Get the nearest location to a point."""
        nearest = None
        min_distance = float('inf')
        
        for location in self.locations.values():
            distance = location.area.distance_to(point)
            if distance < min_distance and (
                max_distance is None or
                distance <= max_distance
            ):
                min_distance = distance
                nearest = location
                
        return nearest
        
    def is_in_members_area(self, point: WorldPoint) -> bool:
        """Check if a point is in a members-only area."""
        return any(
            area.contains(point)
            for area in self.members_areas
        )
        
    def is_in_multi_combat(self, point: WorldPoint) -> bool:
        """Check if a point is in a multi-combat area."""
        # Check wilderness level first
        wilderness_level = get_wilderness_level(point.y)
        if wilderness_level >= 20:
            return True
            
        # Then check defined multi-combat areas
        return any(
            area.contains(point)
            for area in self.multi_combat_areas
        )
        
    def add_multi_combat_area(self, area: WorldArea) -> None:
        """Add a multi-combat area."""
        self.multi_combat_areas.add(area)
        
    def get_region_at_point(self, point: WorldPoint) -> Optional[MapRegion]:
        """Get the region at a point."""
        for region, areas in self.regions.items():
            if any(area.contains(point) for area in areas):
                return region
        return None
        
    def get_available_transport(
        self,
        point: WorldPoint,
        max_distance: int = 50
    ) -> List[TransportLocation]:
        """Get available transportation methods near a point."""
        return [
            transport for transport in self.transport_locations
            if calculate_distance(
                point,
                WorldPoint(transport.x, transport.y, transport.plane)
            ) <= max_distance
        ]
        
    def get_available_teleports(
        self,
        point: WorldPoint,
        max_distance: int = 50
    ) -> List[TeleportLocation]:
        """Get available teleport locations near a point."""
        return [
            teleport for teleport in self.teleport_locations
            if calculate_distance(
                point,
                WorldPoint(teleport.x, teleport.y, teleport.plane)
            ) <= max_distance
        ]
        
    def get_special_locations_in_area(
        self,
        area: WorldArea,
        location_type: Optional[str] = None
    ) -> List[SpecialLocation]:
        """Get special locations within an area."""
        return [
            loc for loc in self.special_locations
            if (location_type is None or loc.location_type == location_type)
            and area.contains(WorldPoint(loc.x, loc.y, loc.plane))
        ]
        
    def get_path_between_points(
        self,
        start: WorldPoint,
        end: WorldPoint,
        allow_teleports: bool = True,
        allow_transport: bool = True,
        max_distance: Optional[int] = None
    ) -> List[Tuple[str, WorldPoint]]:
        """Find a path between two points."""
        path = []
        current = start
        
        # If points are close enough, just walk
        if max_distance is None or calculate_distance(start, end) <= max_distance:
            return [("walk", end)]
            
        # Try teleports first if allowed
        if allow_teleports:
            teleports = [
                t for t in self.teleport_locations
                if calculate_distance(
                    WorldPoint(t.x, t.y, t.plane),
                    end
                ) <= (max_distance or 50)
            ]
            if teleports:
                teleport = min(
                    teleports,
                    key=lambda t: calculate_distance(
                        WorldPoint(t.x, t.y, t.plane),
                        end
                    )
                )
                return [
                    ("start", start),
                    (
                        "teleport",
                        WorldPoint(teleport.x, teleport.y, teleport.plane)
                    ),
                    ("walk", end)
                ]
                
        # Then try transportation if allowed
        if allow_transport:
            while calculate_distance(current, end) > (max_distance or 20):
                transports = self.get_available_transport(current)
                if not transports:
                    break
                    
                transport = min(
                    transports,
                    key=lambda t: calculate_distance(
                        WorldPoint(
                            t.destination_x or t.x,
                            t.destination_y or t.y,
                            t.destination_plane or t.plane
                        ),
                        end
                    )
                )
                
                transport_point = WorldPoint(
                    transport.x,
                    transport.y,
                    transport.plane
                )
                if calculate_distance(current, transport_point) > calculate_distance(current, end):
                    break
                    
                path.append(("walk", transport_point))
                if transport.destination_x and transport.destination_y:
                    current = WorldPoint(
                        transport.destination_x,
                        transport.destination_y,
                        transport.destination_plane or 0
                    )
                    path.append(("transport", current))
                else:
                    break
                    
        path.append(("walk", end))
        return path
