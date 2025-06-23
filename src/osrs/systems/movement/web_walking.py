"""OSRS Web Walking System"""
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
import math
import heapq
from .movement_system import MovementSystem, Tile, TileType
import asyncio
import random
from datetime import datetime

from .locations import LocationManager, Location, Connection, TravelMethod, RegionType


@dataclass
class WebNode:
    """Represents a node in the web walking network."""

    tile: Tile
    connections: Set[Tuple[int, int, int]]  # Connected node coordinates (x, y, z)
    flags: Set[str]  # Special flags like "bank", "ge", "fairy_ring", etc.


@dataclass
class PathNode:
    """Node in a movement path"""

    location: str
    connection: Connection
    next_node: Optional["PathNode"] = None


class MovementState:
    """Current state of player movement"""

    def __init__(self):
        self.is_moving = False
        self.current_path: Optional[PathNode] = None
        self.start_time: Optional[datetime] = None
        self.energy: float = 100.0
        self.weight: float = 0.0
        self.run_enabled: bool = False

    def update_energy(self, elapsed_seconds: float):
        """Update run energy"""
        if self.is_moving and self.run_enabled:
            # Drain energy while running
            energy_drain = (0.67 + self.weight * 0.0067) * elapsed_seconds
            self.energy = max(0.0, self.energy - energy_drain)
        elif not self.is_moving:
            # Restore energy while standing still
            energy_restore = 0.45 * elapsed_seconds
            self.energy = min(100.0, self.energy + energy_restore)


class WebWalking:
    def __init__(self, movement_system: MovementSystem):
        self.movement = movement_system
        self.web_nodes: Dict[Tuple[int, int, int], WebNode] = {}
        self.cached_paths: Dict[Tuple[Tuple[int, int, int], Tuple[int, int, int]], List[Tile]] = {}

    def add_node(self, tile: Tile, flags: Set[str] = None):
        """Add a node to the web walking network."""
        coord = (tile.x, tile.y, tile.z)
        self.web_nodes[coord] = WebNode(tile=tile, connections=set(), flags=flags or set())

    def connect_nodes(self, node1_coord: Tuple[int, int, int], node2_coord: Tuple[int, int, int]):
        """Connect two nodes in the network."""
        if node1_coord in self.web_nodes and node2_coord in self.web_nodes:
            self.web_nodes[node1_coord].connections.add(node2_coord)
            self.web_nodes[node2_coord].connections.add(node1_coord)

    def calculate_distance(self, start: Tile, end: Tile, distance_type: str = "manhattan") -> float:
        """Calculate distance between two tiles."""
        if distance_type == "manhattan":
            return abs(end.x - start.x) + abs(end.y - start.y)
        elif distance_type == "chebyshev":
            return max(abs(end.x - start.x), abs(end.y - start.y))
        else:  # Euclidean
            return math.sqrt((end.x - start.x) ** 2 + (end.y - start.y) ** 2)

    def find_nearest_node(self, tile: Tile) -> Optional[Tuple[int, int, int]]:
        """Find the nearest web node to a given tile."""
        if not self.web_nodes:
            return None

        nearest = None
        min_distance = float("inf")

        for coord, node in self.web_nodes.items():
            distance = self.calculate_distance(tile, node.tile)
            if distance < min_distance:
                min_distance = distance
                nearest = coord

        return nearest

    def find_path(self, start: Tile, end: Tile) -> Optional[List[Tile]]:
        """Find a path between two points using the web walking network."""
        # Check cache first
        cache_key = ((start.x, start.y, start.z), (end.x, end.y, end.z))
        if cache_key in self.cached_paths:
            return self.cached_paths[cache_key]

        # Find nearest nodes to start and end points
        start_node = self.find_nearest_node(start)
        end_node = self.find_nearest_node(end)

        if not start_node or not end_node:
            return None

        # Use A* to find path between nodes
        def heuristic(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
            return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)

        frontier = []
        heapq.heappush(frontier, (0, start_node))
        came_from = {start_node: None}
        cost_so_far = {start_node: 0}

        while frontier:
            current = heapq.heappop(frontier)[1]

            if current == end_node:
                # Reconstruct path
                path = []
                while current is not None:
                    path.append(self.web_nodes[current].tile)
                    current = came_from[current]
                path.reverse()

                # Cache the result
                self.cached_paths[cache_key] = path
                return path

            for next_coord in self.web_nodes[current].connections:
                new_cost = cost_so_far[current] + self.calculate_distance(
                    self.web_nodes[current].tile, self.web_nodes[next_coord].tile
                )

                if next_coord not in cost_so_far or new_cost < cost_so_far[next_coord]:
                    cost_so_far[next_coord] = new_cost
                    priority = new_cost + heuristic(next_coord, end_node)
                    heapq.heappush(frontier, (priority, next_coord))
                    came_from[next_coord] = current

        return None

    def find_nearest_flag(self, tile: Tile, flag: str) -> Optional[Tile]:
        """Find the nearest node with a specific flag."""
        nearest = None
        min_distance = float("inf")

        for node in self.web_nodes.values():
            if flag in node.flags:
                distance = self.calculate_distance(tile, node.tile)
                if distance < min_distance:
                    min_distance = distance
                    nearest = node.tile

        return nearest

    def optimize_path(self, path: List[Tile]) -> List[Tile]:
        """Optimize a path by removing unnecessary nodes."""
        if len(path) <= 2:
            return path

        optimized = [path[0]]
        current_idx = 0

        while current_idx < len(path) - 1:
            # Look ahead for furthest visible node
            for i in range(len(path) - 1, current_idx, -1):
                if self.is_path_clear(path[current_idx], path[i]):
                    optimized.append(path[i])
                    current_idx = i
                    break
            else:
                current_idx += 1
                optimized.append(path[current_idx])

        return optimized

    def is_path_clear(self, start: Tile, end: Tile) -> bool:
        """Check if there's a clear line of sight between two tiles."""
        # Bresenham's line algorithm
        x1, y1 = start.x, start.y
        x2, y2 = end.x, end.y
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        n = 1 + dx + dy
        x_inc = 1 if x2 > x1 else -1
        y_inc = 1 if y2 > y1 else -1
        error = dx - dy
        dx *= 2
        dy *= 2

        for _ in range(n):
            if not self.is_tile_walkable(Tile(x, y, start.z, TileType.WALKABLE)):
                return False

            if error > 0:
                x += x_inc
                error -= dy
            else:
                y += y_inc
                error += dx

        return True

    def is_tile_walkable(self, tile: Tile) -> bool:
        """Check if a tile is walkable."""
        if not self.movement.current_area:
            return False

        if not (
            0 <= tile.x < len(self.movement.current_area.tiles[0])
            and 0 <= tile.y < len(self.movement.current_area.tiles)
        ):
            return False

        area_tile = self.movement.current_area.tiles[tile.y][tile.x]
        return area_tile.type != TileType.BLOCKED


class WebWalker:
    """Handles pathfinding and movement"""

    def __init__(self, location_manager: LocationManager):
        self.locations = location_manager
        self.player_states: Dict[str, MovementState] = {}

    def get_player_state(self, player_id: str) -> MovementState:
        """Get movement state for a player"""
        if player_id not in self.player_states:
            self.player_states[player_id] = MovementState()
        return self.player_states[player_id]

    async def move_to_location(
        self,
        player_id: str,
        current_location: str,
        destination: str,
        player_quests: Set[str],
        player_skills: Dict[str, int],
        player_items: Set[str],
        player_coins: int,
        avoid_wilderness: bool = True,
    ) -> Optional[str]:
        """Start moving to a destination"""
        state = self.get_player_state(player_id)

        if state.is_moving:
            return "You are already moving!"

        # Find path
        path = self.locations.find_path(
            current_location,
            destination,
            player_quests,
            player_skills,
            player_items,
            player_coins,
            state.energy,
            avoid_wilderness,
        )

        if not path:
            return f"Could not find path to {destination}"

        # Convert path to nodes
        current_node = None
        for location, connection in reversed(path):
            node = PathNode(location=location, connection=connection)
            node.next_node = current_node
            current_node = node

        # Start movement
        state.is_moving = True
        state.current_path = current_node
        state.start_time = datetime.now()

        return f"Starting journey to {destination}"

    async def process_movement_tick(
        self, player_id: str, current_location: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Process one tick of movement
        Returns (new_location, message) if location changed
        """
        state = self.get_player_state(player_id)

        if not state.is_moving or not state.current_path:
            return None, None

        # Update energy
        elapsed = (datetime.now() - state.start_time).total_seconds()
        state.update_energy(elapsed)

        # Check if reached next location
        if state.current_path.location == current_location:
            # Move to next node
            state.current_path = state.current_path.next_node
            if not state.current_path:
                # Reached destination
                state.is_moving = False
                return None, "You have reached your destination!"

        # Calculate progress to next location
        connection = state.current_path.connection
        ticks_per_tile = 2 if state.run_enabled and state.energy > 0 else 4
        tiles_per_tick = 1 / ticks_per_tile

        # Apply movement
        if connection.method == TravelMethod.WALK:
            # Regular walking/running
            tiles_moved = tiles_per_tick
            if random.random() < 0.1:  # 10% chance of obstacle
                tiles_moved *= 0.5

        elif connection.method == TravelMethod.TELEPORT:
            # Instant teleport
            return state.current_path.location, "You teleport to your destination!"

        elif connection.method == TravelMethod.BOAT:
            # Boat travel
            tiles_moved = tiles_per_tick * 2

        elif connection.method == TravelMethod.AGILITY:
            # Agility shortcut
            tiles_moved = tiles_per_tick * 1.5

        # Check if reached next location
        if tiles_moved >= connection.distance:
            new_location = state.current_path.location
            message = f"You arrive at {new_location}"

            # Update path
            state.current_path = state.current_path.next_node
            if not state.current_path:
                state.is_moving = False
                message += " - your final destination!"

            return new_location, message

        return None, None

    def toggle_run(self, player_id: str) -> str:
        """Toggle run mode"""
        state = self.get_player_state(player_id)

        if state.energy <= 0:
            return "You don't have enough energy to run!"

        state.run_enabled = not state.run_enabled
        return "Run mode " + ("enabled" if state.run_enabled else "disabled")

    def update_weight(self, player_id: str, new_weight: float):
        """Update carried weight"""
        state = self.get_player_state(player_id)
        state.weight = new_weight

    def stop_movement(self, player_id: str):
        """Stop current movement"""
        state = self.get_player_state(player_id)
        state.is_moving = False
        state.current_path = None

    def get_minimap_destination(
        self, player_id: str, current_location: str
    ) -> Optional[Tuple[int, int]]:
        """Get coordinates for next destination on minimap"""
        state = self.get_player_state(player_id)

        if not state.is_moving or not state.current_path:
            return None

        if state.current_path.location == current_location:
            if state.current_path.next_node:
                next_loc = self.locations.get_location(state.current_path.next_node.location)
                if next_loc:
                    return next_loc.coordinates[:2]
            return None

        next_loc = self.locations.get_location(state.current_path.location)
        if next_loc:
            return next_loc.coordinates[:2]

        return None
