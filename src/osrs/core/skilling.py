from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
import random
import math

from .skills import SkillType, SkillManager


class ResourceType(Enum):
    # Woodcutting
    NORMAL_TREE = auto()
    OAK_TREE = auto()
    WILLOW_TREE = auto()
    MAPLE_TREE = auto()
    YEW_TREE = auto()
    MAGIC_TREE = auto()

    # Mining
    COPPER_ORE = auto()
    TIN_ORE = auto()
    IRON_ORE = auto()
    COAL = auto()
    MITHRIL_ORE = auto()
    ADAMANTITE_ORE = auto()
    RUNITE_ORE = auto()

    # Fishing
    SHRIMP = auto()
    SARDINE = auto()
    HERRING = auto()
    TROUT = auto()
    SALMON = auto()
    LOBSTER = auto()
    SWORDFISH = auto()
    SHARK = auto()


@dataclass
class Resource:
    type: ResourceType
    required_level: int
    base_xp: float
    success_chance: float
    respawn_time: int  # in seconds


class SkillingManager:
    """Manages skilling activities and resources"""

    def __init__(self):
        self.resources: Dict[ResourceType, Resource] = self._initialize_resources()

    def _initialize_resources(self) -> Dict[ResourceType, Resource]:
        """Initialize all resource data"""
        resources = {}

        # Woodcutting resources
        resources[ResourceType.NORMAL_TREE] = Resource(
            type=ResourceType.NORMAL_TREE,
            required_level=1,
            base_xp=25.0,
            success_chance=0.5,
            respawn_time=5,
        )
        resources[ResourceType.OAK_TREE] = Resource(
            type=ResourceType.OAK_TREE,
            required_level=15,
            base_xp=37.5,
            success_chance=0.4,
            respawn_time=8,
        )
        resources[ResourceType.WILLOW_TREE] = Resource(
            type=ResourceType.WILLOW_TREE,
            required_level=30,
            base_xp=67.5,
            success_chance=0.35,
            respawn_time=10,
        )

        # Mining resources
        resources[ResourceType.COPPER_ORE] = Resource(
            type=ResourceType.COPPER_ORE,
            required_level=1,
            base_xp=17.5,
            success_chance=0.5,
            respawn_time=4,
        )
        resources[ResourceType.TIN_ORE] = Resource(
            type=ResourceType.TIN_ORE,
            required_level=1,
            base_xp=17.5,
            success_chance=0.5,
            respawn_time=4,
        )
        resources[ResourceType.IRON_ORE] = Resource(
            type=ResourceType.IRON_ORE,
            required_level=15,
            base_xp=35.0,
            success_chance=0.4,
            respawn_time=6,
        )

        # Fishing resources
        resources[ResourceType.SHRIMP] = Resource(
            type=ResourceType.SHRIMP,
            required_level=1,
            base_xp=10.0,
            success_chance=0.5,
            respawn_time=3,
        )
        resources[ResourceType.SARDINE] = Resource(
            type=ResourceType.SARDINE,
            required_level=5,
            base_xp=20.0,
            success_chance=0.45,
            respawn_time=4,
        )
        resources[ResourceType.TROUT] = Resource(
            type=ResourceType.TROUT,
            required_level=20,
            base_xp=50.0,
            success_chance=0.4,
            respawn_time=5,
        )

        return resources

    def get_resource(self, resource_type: ResourceType) -> Optional[Resource]:
        """Get resource data by type"""
        return self.resources.get(resource_type)

    def attempt_gather(
        self, resource_type: ResourceType, skill_manager: SkillManager
    ) -> Tuple[bool, float]:
        """
        Attempt to gather a resource
        Returns (success, xp_gained)
        """
        resource = self.get_resource(resource_type)
        if not resource:
            return (False, 0.0)

        # Get the corresponding skill type
        skill_type = self._get_skill_for_resource(resource_type)
        if not skill_type:
            return (False, 0.0)

        # Check level requirement
        if not skill_manager.meets_requirement(skill_type, resource.required_level):
            return (False, 0.0)

        # Calculate success chance based on level
        level_bonus = (skill_manager.get_level(skill_type) - resource.required_level) * 0.01
        adjusted_chance = min(0.95, resource.success_chance + level_bonus)

        # Attempt gather
        success = random.random() < adjusted_chance
        xp_gained = resource.base_xp if success else 0.0

        if success:
            skill_manager.add_xp(skill_type, xp_gained)

        return (success, xp_gained)

    def _get_skill_for_resource(self, resource_type: ResourceType) -> Optional[SkillType]:
        """Get the corresponding skill type for a resource"""
        if resource_type.name.endswith("_TREE"):
            return SkillType.WOODCUTTING
        elif resource_type.name.endswith("_ORE") or resource_type == ResourceType.COAL:
            return SkillType.MINING
        elif resource_type in [
            ResourceType.SHRIMP,
            ResourceType.SARDINE,
            ResourceType.HERRING,
            ResourceType.TROUT,
            ResourceType.SALMON,
            ResourceType.LOBSTER,
            ResourceType.SWORDFISH,
            ResourceType.SHARK,
        ]:
            return SkillType.FISHING
        return None
