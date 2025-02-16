"""Movement system for handling player movement and pathfinding."""

import math
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import heapq

class MovementSpeed(Enum):
    """Movement speed types."""
    WALK = 1
    RUN = 2

@dataclass
class Position:
    """Represents a position in the game world."""
    x: int
    y: int
    plane: int = 0
    
    def distance_to(self, other: 'Position') -> int:
        """Calculate Manhattan distance to another position."""
        return abs(self.x - other.x) + abs(self.y - other.y)
    
    def real_distance_to(self, other: 'Position') -> float:
        """Calculate actual distance to another position."""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

class MovementSystem:
    """Handles player movement and energy calculations."""
    
    # Constants from OSRS
    GAME_TICK = 0.6  # seconds
    WALK_SPEED = 1  # tile per tick
    RUN_SPEED = 2   # tiles per tick
    BASE_RESTORE_RATE = 0.0094  # energy per tick
    WEIGHT_REDUCTION = 0.0007   # energy reduction per kg
    MAX_ENERGY = 100.0
    MIN_ENERGY = 0.0
    
    # Agility impact on energy
    AGILITY_RESTORE_BONUS = 0.01  # Per level
    AGILITY_DRAIN_REDUCTION = 0.003  # Per level
    
    def __init__(self, game_tick):
        """Initialize the movement system.
        
        Args:
            game_tick: GameTick system instance
        """
        self.game_tick = game_tick
        self.current_speed = MovementSpeed.WALK
        self.running = False
        self.weight = 0.0
        self.current_path: List[Position] = []
        self.current_position = Position(0, 0, 0)
        self.destination: Optional[Position] = None
        
        # Register movement task with game tick system
        self.game_tick.register_task(
            "movement_update",
            self._movement_tick,
            TickPriority.MOVEMENT
        )
        
    def calculate_restore_rate(self, agility_level: int) -> float:
        """Calculate energy restoration rate.
        
        Args:
            agility_level: Player's agility level (1-99)
            
        Returns:
            Energy restoration rate per tick
        """
        # Formula from OSRS wiki
        restore_rate = self.BASE_RESTORE_RATE * (1 + agility_level * self.AGILITY_RESTORE_BONUS)
        weight_penalty = max(0, self.weight * self.WEIGHT_REDUCTION)
        return max(0.0, restore_rate - weight_penalty)
        
    def calculate_drain_rate(self, agility_level: int) -> float:
        """Calculate run energy drain rate.
        
        Args:
            agility_level: Player's agility level (1-99)
            
        Returns:
            Energy drain rate per tick while running
        """
        # Formula from OSRS wiki
        base_drain = 0.67  # Base drain rate per tick
        agility_reduction = agility_level * self.AGILITY_DRAIN_REDUCTION
        weight_increase = max(0, self.weight - 0.0) * 0.0035
        
        return max(0.1, base_drain - agility_reduction + weight_increase)
        
    def update_energy(self, 
                     current_energy: float, 
                     agility_level: int,
                     running: bool,
                     ticks: int = 1) -> float:
        """Update run energy based on movement.
        
        Args:
            current_energy: Current run energy (0-100)
            agility_level: Player's agility level
            running: Whether player is running
            ticks: Number of game ticks to process
            
        Returns:
            New energy level
        """
        if running and current_energy > 0:
            drain = self.calculate_drain_rate(agility_level) * ticks
            current_energy = max(self.MIN_ENERGY, current_energy - drain)
        else:
            restore = self.calculate_restore_rate(agility_level) * ticks
            current_energy = min(self.MAX_ENERGY, current_energy + restore)
            
        return current_energy
        
    async def _movement_tick(self):
        """Process movement for current game tick."""
        if not self.current_path or not self.destination:
            return
            
        # Determine movement speed and distance for this tick
        speed = self.RUN_SPEED if self.running else self.WALK_SPEED
        
        # Move along path
        for _ in range(speed):
            if not self.current_path:
                break
                
            next_pos = self.current_path.pop(0)
            self.current_position = next_pos
            
            if next_pos.distance_to(self.destination) == 0:
                self.current_path = []
                self.destination = None
                break
                
    def calculate_path(self, 
                      start: Position,
                      end: Position,
                      collision_map: List[List[bool]],
                      max_distance: int = 100) -> List[Position]:
        """Calculate shortest path between positions using A* pathfinding.
        
        Args:
            start: Starting position
            end: Target position
            collision_map: 2D array of walkable tiles
            max_distance: Maximum pathfinding distance
            
        Returns:
            List of positions forming the path
        """
        def heuristic(pos: Position) -> float:
            return pos.real_distance_to(end)
            
        def get_neighbors(pos: Position) -> List[Position]:
            neighbors = []
            for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:  # OSRS uses 4-directional movement
                new_x, new_y = pos.x + dx, pos.y + dy
                if (0 <= new_x < len(collision_map[0]) and 
                    0 <= new_y < len(collision_map) and
                    not collision_map[new_y][new_x]):
                    neighbors.append(Position(new_x, new_y, pos.plane))
            return neighbors
            
        # A* pathfinding implementation
        open_set: List[Tuple[float, Position]] = [(0, start)]
        closed_set: Set[Position] = set()
        came_from: Dict[Position, Position] = {}
        g_score: Dict[Position, float] = {start: 0}
        f_score: Dict[Position, float] = {start: heuristic(start)}
        
        while open_set:
            current = heapq.heappop(open_set)[1]
            
            if current.distance_to(end) <= 1:  # Adjacent to target
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return list(reversed(path))
                
            closed_set.add(current)
            
            if g_score[current] > max_distance:
                continue
                
            for neighbor in get_neighbors(current):
                if neighbor in closed_set:
                    continue
                    
                tentative_g = g_score[current] + 1  # Cost is always 1 in OSRS grid
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + heuristic(neighbor)
                    f_score[neighbor] = f
                    heapq.heappush(open_set, (f, neighbor))
                
        return []  # No path found
        
    def calculate_travel_time(self,
                            path: List[Position],
                            agility_level: int,
                            starting_energy: float) -> Tuple[float, float]:
        """Calculate time and ending energy for traversing a path.
        
        Args:
            path: List of positions in the path
            agility_level: Player's agility level
            starting_energy: Starting run energy
            
        Returns:
            Tuple of (time in seconds, ending energy)
        """
        current_energy = starting_energy
        total_ticks = 0
        current_pos = 0
        
        while current_pos < len(path) - 1:
            # Determine movement speed
            running = self.running and current_energy > 0
            speed = self.RUN_SPEED if running else self.WALK_SPEED
            
            # Calculate ticks for next movement
            next_pos = min(current_pos + speed, len(path) - 1)
            ticks = 1
            
            # Update position and energy
            current_pos = next_pos
            current_energy = self.update_energy(
                current_energy,
                agility_level,
                running,
                ticks
            )
            total_ticks += ticks
            
        return (total_ticks * self.GAME_TICK, current_energy)
        
    def toggle_run(self, current_energy: float) -> bool:
        """Toggle running state if enough energy.
        
        Args:
            current_energy: Current run energy level
            
        Returns:
            New running state
        """
        if not self.running and current_energy > 0:
            self.running = True
        else:
            self.running = False
        return self.running 