"""Resource manager for handling gathering resources and respawn timers."""

import time
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from .game_tick import GameTick, TickPriority
from .movement import Position

class ResourceType(Enum):
    """Types of gatherable resources."""
    TREE = "tree"
    ROCK = "rock"
    FISHING_SPOT = "fishing_spot"
    FARMING_PATCH = "farming_patch"
    HUNTER_SPOT = "hunter_spot"

@dataclass
class Resource:
    """Represents a gatherable resource."""
    type: ResourceType
    id: str
    position: Position
    level_required: int
    respawn_ticks: int
    depletion_chance: float
    tool_required: Optional[str] = None
    
@dataclass
class ResourceState:
    """Current state of a resource."""
    resource: Resource
    depleted: bool = False
    depleted_at: int = 0  # Tick when depleted
    players_gathering: Set[int] = None  # Set of player IDs
    
    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.players_gathering is None:
            self.players_gathering = set()

class ResourceManager:
    """Manages resource gathering and respawning."""
    
    def __init__(self, game_tick: GameTick):
        """Initialize resource manager.
        
        Args:
            game_tick: GameTick system instance
        """
        self.game_tick = game_tick
        self.resources: Dict[str, Resource] = {}
        self.resource_states: Dict[str, ResourceState] = {}
        
        # Register resource tick task
        self.game_tick.register_task(
            "resource_update",
            self._resource_tick,
            TickPriority.WORLD
        )
        
    def add_resource(self, resource: Resource):
        """Add a resource to the world.
        
        Args:
            resource: Resource to add
        """
        self.resources[resource.id] = resource
        self.resource_states[resource.id] = ResourceState(resource)
        
    def remove_resource(self, resource_id: str):
        """Remove a resource from the world.
        
        Args:
            resource_id: ID of resource to remove
        """
        self.resources.pop(resource_id, None)
        self.resource_states.pop(resource_id, None)
        
    async def _resource_tick(self):
        """Process resource updates for current game tick."""
        current_tick = self.game_tick.get_tick_count()
        
        # Check for respawns
        for state in self.resource_states.values():
            if state.depleted:
                if current_tick - state.depleted_at >= state.resource.respawn_ticks:
                    state.depleted = False
                    state.depleted_at = 0
                    
    def start_gathering(self, 
                       player_id: int,
                       resource_id: str) -> Tuple[bool, Optional[str]]:
        """Start gathering a resource.
        
        Args:
            player_id: Player's ID
            resource_id: Resource to gather
            
        Returns:
            Tuple of (success, error message if failed)
        """
        if resource_id not in self.resource_states:
            return (False, "Resource not found")
            
        state = self.resource_states[resource_id]
        
        if state.depleted:
            return (False, "Resource is depleted")
            
        state.players_gathering.add(player_id)
        return (True, None)
        
    def stop_gathering(self,
                      player_id: int,
                      resource_id: str):
        """Stop gathering a resource.
        
        Args:
            player_id: Player's ID
            resource_id: Resource being gathered
        """
        if resource_id in self.resource_states:
            self.resource_states[resource_id].players_gathering.discard(player_id)
            
    def attempt_gather(self,
                      player_id: int,
                      resource_id: str) -> Tuple[bool, Optional[str]]:
        """Attempt to gather from a resource.
        
        Args:
            player_id: Player's ID
            resource_id: Resource to gather from
            
        Returns:
            Tuple of (success, error message if failed)
        """
        if resource_id not in self.resource_states:
            return (False, "Resource not found")
            
        state = self.resource_states[resource_id]
        
        if state.depleted:
            return (False, "Resource is depleted")
            
        if player_id not in state.players_gathering:
            return (False, "Not gathering this resource")
            
        # Check for depletion
        if state.resource.depletion_chance > 0:
            import random
            if random.random() < state.resource.depletion_chance:
                state.depleted = True
                state.depleted_at = self.game_tick.get_tick_count()
                state.players_gathering.clear()
                return (True, "Resource depleted")
                
        return (True, None)
        
    def get_resource(self, resource_id: str) -> Optional[Resource]:
        """Get resource by ID.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Resource if found, None otherwise
        """
        return self.resources.get(resource_id)
        
    def get_resources_in_range(self,
                             position: Position,
                             max_distance: float) -> List[Resource]:
        """Get resources within range of a position.
        
        Args:
            position: Center position
            max_distance: Maximum distance to search
            
        Returns:
            List of resources within range
        """
        return [
            resource for resource in self.resources.values()
            if resource.position.real_distance_to(position) <= max_distance
        ]
        
    def get_nearest_resource(self,
                           position: Position,
                           resource_type: Optional[ResourceType] = None) -> Optional[Resource]:
        """Find nearest resource to a position.
        
        Args:
            position: Position to search from
            resource_type: Optional type filter
            
        Returns:
            Nearest matching resource if found
        """
        resources = self.resources.values()
        if resource_type:
            resources = [r for r in resources if r.type == resource_type]
            
        if not resources:
            return None
            
        return min(
            resources,
            key=lambda r: r.position.real_distance_to(position)
        )
        
    def is_resource_available(self, resource_id: str) -> bool:
        """Check if a resource is available for gathering.
        
        Args:
            resource_id: Resource to check
            
        Returns:
            True if resource is available
        """
        if resource_id not in self.resource_states:
            return False
            
        return not self.resource_states[resource_id].depleted
        
    def get_respawn_time(self, resource_id: str) -> Optional[int]:
        """Get ticks until resource respawns.
        
        Args:
            resource_id: Resource to check
            
        Returns:
            Ticks until respawn if depleted, None if not depleted
        """
        if resource_id not in self.resource_states:
            return None
            
        state = self.resource_states[resource_id]
        if not state.depleted:
            return None
            
        current_tick = self.game_tick.get_tick_count()
        ticks_depleted = current_tick - state.depleted_at
        return max(0, state.resource.respawn_ticks - ticks_depleted)
        
    def get_players_gathering(self, resource_id: str) -> Set[int]:
        """Get players currently gathering from a resource.
        
        Args:
            resource_id: Resource to check
            
        Returns:
            Set of player IDs
        """
        if resource_id not in self.resource_states:
            return set()
            
        return self.resource_states[resource_id].players_gathering.copy() 