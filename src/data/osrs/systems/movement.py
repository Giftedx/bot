from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum
import math
import heapq

class TileType(Enum):
    WALKABLE = "walkable"
    BLOCKED = "blocked"
    AGILITY_OBSTACLE = "agility_obstacle"
    DOOR = "door"
    GATE = "gate"
    WATER = "water"
    LADDER = "ladder"
    STAIRS = "stairs"

@dataclass
class Tile:
    x: int
    y: int
    z: int  # Floor/level
    type: TileType
    agility_level: int = 1  # Required agility level if obstacle
    requirements: Dict[str, any] = None
    interaction_text: str = ""

@dataclass
class Area:
    name: str
    tiles: List[List[Tile]]  # 2D grid of tiles
    connections: Dict[str, 'Area']  # Connected areas and their requirements
    wilderness_level: int = 0
    is_pvp: bool = False
    is_multicombat: bool = False

class MovementSystem:
    def __init__(self):
        self.current_area: Optional[Area] = None
        self.current_position: Tuple[int, int, int] = (0, 0, 0)  # x, y, z
        self.run_energy: float = 100.0
        self.weight: float = 0.0
        self.agility_level: int = 1

    def can_access_tile(self, tile: Tile) -> Tuple[bool, str]:
        """Check if a tile can be accessed based on requirements."""
        if tile.type == TileType.BLOCKED:
            return False, "This tile is blocked."
            
        if tile.type == TileType.AGILITY_OBSTACLE:
            if self.agility_level < tile.agility_level:
                return False, f"You need {tile.agility_level} Agility to use this obstacle."

        if tile.requirements:
            # Check other requirements (quests, items, etc.)
            for req_type, req_value in tile.requirements.items():
                # Implementation for checking various requirement types
                pass

        return True, ""

    def calculate_run_energy_drain(self, distance: float, weight: float) -> float:
        """Calculate run energy drain based on distance and weight."""
        base_drain = distance * 0.67  # Base drain per tile
        weight_multiplier = 1 + (weight / 64)  # Weight affects drain rate
        return base_drain * weight_multiplier

    def restore_run_energy(self, amount: float):
        """Restore run energy."""
        self.run_energy = min(100.0, self.run_energy + amount)

    def get_available_shortcuts(self, current_pos: Tuple[int, int, int]) -> List[Tuple[Tile, str]]:
        """Get available agility shortcuts from current position."""
        shortcuts = []
        x, y, z = current_pos
        
        # Check adjacent tiles for obstacles
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < len(self.current_area.tiles[0]) and 0 <= new_y < len(self.current_area.tiles):
                tile = self.current_area.tiles[new_y][new_x]
                if tile.type == TileType.AGILITY_OBSTACLE:
                    can_use, reason = self.can_access_tile(tile)
                    if can_use:
                        shortcuts.append((tile, tile.interaction_text))

        return shortcuts

class PathFinder:
    def __init__(self, movement_system: MovementSystem):
        self.movement = movement_system

    def find_path(self, start: Tuple[int, int, int], end: Tuple[int, int, int]) -> Optional[List[Tuple[int, int, int]]]:
        """Find path using A* algorithm with agility shortcuts."""
        def heuristic(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
            return math.sqrt((b[0] - a[0])**2 + (b[1] - a[1])**2)

        def get_neighbors(pos: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
            x, y, z = pos
            neighbors = []
            
            # Regular movement
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < len(self.movement.current_area.tiles[0]) and 0 <= new_y < len(self.movement.current_area.tiles):
                    tile = self.movement.current_area.tiles[new_y][new_x]
                    can_move, _ = self.movement.can_access_tile(tile)
                    if can_move:
                        neighbors.append((new_x, new_y, z))
            
            # Agility shortcuts
            shortcuts = self.movement.get_available_shortcuts((x, y, z))
            for tile, _ in shortcuts:
                neighbors.append((tile.x, tile.y, tile.z))

            return neighbors

        # A* implementation
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}

        while frontier:
            current = heapq.heappop(frontier)[1]

            if current == end:
                # Reconstruct path
                path = []
                while current is not None:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            for next_pos in get_neighbors(current):
                new_cost = cost_so_far[current] + 1  # Could be adjusted for different movement types
                if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                    cost_so_far[next_pos] = new_cost
                    priority = new_cost + heuristic(next_pos, end)
                    heapq.heappush(frontier, (priority, next_pos))
                    came_from[next_pos] = current

        return None  # No path found

class MovementHandler:
    def __init__(self, movement_system: MovementSystem, pathfinder: PathFinder):
        self.movement = movement_system
        self.pathfinder = pathfinder
        self.current_path: Optional[List[Tuple[int, int, int]]] = None
        self.is_running: bool = False

    async def move_to(self, destination: Tuple[int, int, int]):
        """Handle movement to a destination, including pathfinding and energy management."""
        self.current_path = self.pathfinder.find_path(self.movement.current_position, destination)
        
        if not self.current_path:
            return False, "No valid path found."

        for next_pos in self.current_path:
            # Calculate distance
            current_x, current_y, _ = self.movement.current_position
            next_x, next_y, _ = next_pos
            distance = math.sqrt((next_x - current_x)**2 + (next_y - current_y)**2)

            # Handle run energy
            if self.is_running:
                energy_drain = self.movement.calculate_run_energy_drain(distance, self.movement.weight)
                if self.movement.run_energy < energy_drain:
                    self.is_running = False
                else:
                    self.movement.run_energy -= energy_drain

            # Move to next position
            self.movement.current_position = next_pos

            # Add delay based on running/walking
            await asyncio.sleep(0.6 if not self.is_running else 0.3)

        return True, "Destination reached."

    def toggle_run(self):
        """Toggle running on/off."""
        if not self.is_running and self.movement.run_energy <= 0:
            return False, "Not enough run energy."
        
        self.is_running = not self.is_running
        return True, f"Running {'enabled' if self.is_running else 'disabled'}." 