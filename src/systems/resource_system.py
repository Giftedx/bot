"""Cross-game resource system for shared item pools."""

import logging
import random
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime

from src.core.database import DatabaseManager
from src.cache.factory import CacheFactory
from .unified_xp import XPSystem, ActivityType

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """Types of resources that can be collected."""
    
    # OSRS Resources
    OSRS_ORE = "osrs_ore"
    OSRS_HERB = "osrs_herb"
    OSRS_RUNE = "osrs_rune"
    
    # Pokemon Resources
    POKEMON_BERRY = "pokemon_berry"
    POKEMON_STONE = "pokemon_stone"
    POKEMON_FOSSIL = "pokemon_fossil"
    
    # Universal Resources
    ENERGY = "energy"
    ESSENCE = "essence"
    CRYSTAL = "crystal"

class ResourceNode:
    """Represents a resource that can be harvested."""
    
    def __init__(
        self,
        node_type: ResourceType,
        base_xp: float,
        primary_rewards: Dict[str, float],
        cross_rewards: Dict[str, float]
    ):
        """Initialize resource node.
        
        Args:
            node_type: Type of resource
            base_xp: Base XP for harvesting
            primary_rewards: Primary resource rewards
            cross_rewards: Cross-system resource rewards
        """
        self.type = node_type
        self.base_xp = base_xp
        self.primary_rewards = primary_rewards
        self.cross_rewards = cross_rewards

class ResourceSystem:
    """Manages resource collection and distribution."""
    
    def __init__(
        self,
        db: DatabaseManager,
        cache_url: str,
        xp_system: XPSystem
    ):
        """Initialize resource system.
        
        Args:
            db: Database manager instance
            cache_url: Redis cache URL
            xp_system: XP system instance
        """
        self.db = db
        self.cache = CacheFactory.get_redis_cache(cache_url)
        self.xp_system = xp_system
        
        # Initialize resource nodes
        self.nodes = self._initialize_nodes()
        
    def _initialize_nodes(self) -> Dict[ResourceType, ResourceNode]:
        """Initialize all resource nodes with rewards."""
        nodes = {}
        
        # OSRS Nodes
        nodes[ResourceType.OSRS_ORE] = ResourceNode(
            ResourceType.OSRS_ORE,
            base_xp=50.0,
            primary_rewards={"iron": 0.8, "coal": 0.6, "mithril": 0.3},
            cross_rewards={
                "pokemon_stone": 0.05,  # Small chance for evolution stone
                "energy": 0.2  # Universal resource
            }
        )
        
        # Pokemon Nodes
        nodes[ResourceType.POKEMON_BERRY] = ResourceNode(
            ResourceType.POKEMON_BERRY,
            base_xp=30.0,
            primary_rewards={"oran": 0.8, "sitrus": 0.4, "leppa": 0.3},
            cross_rewards={
                "osrs_herb": 0.05,  # Small chance for herb
                "essence": 0.2  # Universal resource
            }
        )
        
        return nodes
        
    async def harvest_resource(
        self,
        player_id: int,
        node_type: ResourceType,
        skill_level: int,
        metadata: Optional[Dict] = None
    ) -> Dict[str, List[str]]:
        """Harvest resources from a node.
        
        Args:
            player_id: Player's Discord ID
            node_type: Type of resource to harvest
            skill_level: Player's relevant skill level
            metadata: Additional harvest data
            
        Returns:
            Dictionary of resources obtained
        """
        try:
            node = self.nodes[node_type]
            
            # Calculate success chances based on skill
            success_modifier = min(1.5, 1 + (skill_level / 100))
            
            # Get primary rewards
            rewards = {"primary": [], "cross": [], "universal": []}
            
            for resource, chance in node.primary_rewards.items():
                if random.random() < (chance * success_modifier):
                    rewards["primary"].append(resource)
                    
            # Get cross-system rewards
            for resource, chance in node.cross_rewards.items():
                if random.random() < (chance * success_modifier):
                    if resource in ["energy", "essence", "crystal"]:
                        rewards["universal"].append(resource)
                    else:
                        rewards["cross"].append(resource)
                        
            # Award XP
            await self.xp_system.award_xp(
                player_id,
                ActivityType.COLLECTION,
                node.base_xp * success_modifier,
                metadata
            )
            
            # Update database
            async with self.db.get_session() as session:
                await self._save_rewards(session, player_id, rewards)
                
            return rewards
            
        except Exception as e:
            logger.error(f"Error harvesting resource: {e}")
            return {"primary": [], "cross": [], "universal": []}
            
    async def _save_rewards(
        self,
        session,
        player_id: int,
        rewards: Dict[str, List[str]]
    ) -> None:
        """Save obtained rewards to appropriate systems.
        
        Args:
            session: Database session
            player_id: Player's Discord ID
            rewards: Dictionary of obtained rewards
        """
        # Implementation depends on database schema
        pass 