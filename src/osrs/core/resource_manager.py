"""Resource management for OSRS."""
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import random

@dataclass
class Resource:
    """Represents a game resource."""
    id: int
    type: str
    level_required: int
    xp_granted: float
    depletion_chance: float
    respawn_time: timedelta
    depleted: bool = False
    last_depleted: Optional[datetime] = None
    
    @property
    def is_available(self) -> bool:
        """Check if resource is available."""
        if not self.depleted:
            return True
        if not self.last_depleted:
            return True
        return datetime.now() >= self.last_depleted + self.respawn_time

class ResourceNode:
    """Represents a resource gathering node."""
    
    def __init__(
        self,
        node_id: int,
        location: str,
        resource_type: str,
        max_resources: int = 1
    ):
        self.node_id = node_id
        self.location = location
        self.resource_type = resource_type
        self.max_resources = max_resources
        self.current_resources = max_resources
        self.last_depleted: Optional[datetime] = None
        self.being_used_by: Set[int] = set()

class ResourceManager:
    """Manages game resources and their states."""
    
    def __init__(self):
        self.resources: Dict[int, Resource] = {}
        self.nodes: Dict[int, ResourceNode] = {}
        self.resource_definitions: Dict[str, Dict] = {
            'trees': {
                'normal': {
                    'level': 1,
                    'xp': 25.0,
                    'depletion': 0.5,
                    'respawn': timedelta(seconds=30)
                },
                'oak': {
                    'level': 15,
                    'xp': 37.5,
                    'depletion': 0.4,
                    'respawn': timedelta(seconds=45)
                },
                'willow': {
                    'level': 30,
                    'xp': 67.5,
                    'depletion': 0.3,
                    'respawn': timedelta(seconds=60)
                },
                'maple': {
                    'level': 45,
                    'xp': 100.0,
                    'depletion': 0.25,
                    'respawn': timedelta(seconds=90)
                },
                'yew': {
                    'level': 60,
                    'xp': 175.0,
                    'depletion': 0.15,
                    'respawn': timedelta(minutes=2)
                },
                'magic': {
                    'level': 75,
                    'xp': 250.0,
                    'depletion': 0.1,
                    'respawn': timedelta(minutes=3)
                }
            },
            'rocks': {
                'copper': {
                    'level': 1,
                    'xp': 17.5,
                    'depletion': 0.5,
                    'respawn': timedelta(seconds=30)
                },
                'tin': {
                    'level': 1,
                    'xp': 17.5,
                    'depletion': 0.5,
                    'respawn': timedelta(seconds=30)
                },
                'iron': {
                    'level': 15,
                    'xp': 35.0,
                    'depletion': 0.4,
                    'respawn': timedelta(seconds=45)
                },
                'coal': {
                    'level': 30,
                    'xp': 50.0,
                    'depletion': 0.3,
                    'respawn': timedelta(seconds=60)
                },
                'gold': {
                    'level': 40,
                    'xp': 65.0,
                    'depletion': 0.25,
                    'respawn': timedelta(seconds=90)
                },
                'mithril': {
                    'level': 55,
                    'xp': 80.0,
                    'depletion': 0.2,
                    'respawn': timedelta(minutes=2)
                },
                'adamantite': {
                    'level': 70,
                    'xp': 95.0,
                    'depletion': 0.15,
                    'respawn': timedelta(minutes=3)
                },
                'runite': {
                    'level': 85,
                    'xp': 125.0,
                    'depletion': 0.1,
                    'respawn': timedelta(minutes=5)
                }
            },
            'fishing_spots': {
                'shrimp': {
                    'level': 1,
                    'xp': 10.0,
                    'depletion': 0.2,
                    'respawn': timedelta(seconds=15)
                },
                'trout': {
                    'level': 20,
                    'xp': 50.0,
                    'depletion': 0.15,
                    'respawn': timedelta(seconds=20)
                },
                'salmon': {
                    'level': 30,
                    'xp': 70.0,
                    'depletion': 0.15,
                    'respawn': timedelta(seconds=20)
                },
                'lobster': {
                    'level': 40,
                    'xp': 90.0,
                    'depletion': 0.1,
                    'respawn': timedelta(seconds=30)
                },
                'swordfish': {
                    'level': 50,
                    'xp': 100.0,
                    'depletion': 0.1,
                    'respawn': timedelta(seconds=30)
                },
                'shark': {
                    'level': 76,
                    'xp': 110.0,
                    'depletion': 0.05,
                    'respawn': timedelta(seconds=45)
                }
            }
        }
        
    def add_resource(
        self,
        resource_id: int,
        resource_type: str,
        subtype: str
    ) -> None:
        """Add a new resource to the manager."""
        if resource_type not in self.resource_definitions:
            raise ValueError(f"Unknown resource type: {resource_type}")
            
        if subtype not in self.resource_definitions[resource_type]:
            raise ValueError(f"Unknown {resource_type} subtype: {subtype}")
            
        definition = self.resource_definitions[resource_type][subtype]
        
        self.resources[resource_id] = Resource(
            id=resource_id,
            type=f"{resource_type}_{subtype}",
            level_required=definition['level'],
            xp_granted=definition['xp'],
            depletion_chance=definition['depletion'],
            respawn_time=definition['respawn']
        )
        
    def add_node(
        self,
        node_id: int,
        location: str,
        resource_type: str,
        max_resources: int = 1
    ) -> None:
        """Add a new resource node."""
        self.nodes[node_id] = ResourceNode(
            node_id=node_id,
            location=location,
            resource_type=resource_type,
            max_resources=max_resources
        )
        
    def get_resource(self, resource_id: int) -> Optional[Resource]:
        """Get a resource by ID."""
        return self.resources.get(resource_id)
        
    def get_node(self, node_id: int) -> Optional[ResourceNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
        
    def attempt_resource_gather(
        self,
        resource_id: int,
        player_id: int,
        skill_level: int,
        tool_bonus: float = 0
    ) -> bool:
        """Attempt to gather from a resource."""
        resource = self.get_resource(resource_id)
        if not resource:
            return False
            
        if not resource.is_available:
            return False
            
        if skill_level < resource.level_required:
            return False
            
        # Calculate depletion chance
        base_chance = resource.depletion_chance
        level_bonus = skill_level * 0.01
        final_chance = base_chance * (1 - level_bonus - tool_bonus)
        
        # Check for depletion
        if random.random() < final_chance:
            resource.depleted = True
            resource.last_depleted = datetime.now()
            return False
            
        return True
        
    def start_gathering(
        self,
        node_id: int,
        player_id: int
    ) -> bool:
        """Start gathering at a node."""
        node = self.get_node(node_id)
        if not node:
            return False
            
        if node.current_resources <= 0:
            return False
            
        node.being_used_by.add(player_id)
        return True
        
    def stop_gathering(
        self,
        node_id: int,
        player_id: int
    ) -> None:
        """Stop gathering at a node."""
        node = self.get_node(node_id)
        if node:
            node.being_used_by.discard(player_id)
            
    def deplete_node(self, node_id: int) -> None:
        """Deplete a resource node."""
        node = self.get_node(node_id)
        if node:
            node.current_resources = max(0, node.current_resources - 1)
            if node.current_resources == 0:
                node.last_depleted = datetime.now()
                node.being_used_by.clear()
                
    def respawn_nodes(self) -> None:
        """Check and respawn depleted nodes."""
        current_time = datetime.now()
        
        for node in self.nodes.values():
            if node.current_resources < node.max_resources:
                if node.last_depleted:
                    resource = next(
                        (r for r in self.resources.values() if r.type == node.resource_type),
                        None
                    )
                    if resource and current_time >= node.last_depleted + resource.respawn_time:
                        node.current_resources = node.max_resources
                        node.last_depleted = None
                        
    def get_available_nodes(
        self,
        location: str,
        resource_type: Optional[str] = None
    ) -> List[ResourceNode]:
        """Get available nodes in a location."""
        nodes = [
            node for node in self.nodes.values()
            if node.location == location and node.current_resources > 0
        ]
        
        if resource_type:
            nodes = [
                node for node in nodes
                if node.resource_type == resource_type
            ]
            
        return nodes
        
    def get_nearest_node(
        self,
        location: str,
        resource_type: str
    ) -> Optional[ResourceNode]:
        """Get nearest available node of a type."""
        available = self.get_available_nodes(location, resource_type)
        return available[0] if available else None 