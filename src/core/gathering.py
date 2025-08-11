"""OSRS gathering skills implementation."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from . import game_math
from .models import SkillType


class Tool(Enum):
    """Gathering tool types"""

    BRONZE_PICKAXE = ("pickaxe", 1, 1)
    IRON_PICKAXE = ("pickaxe", 1, 2)
    STEEL_PICKAXE = ("pickaxe", 5, 3)
    BLACK_PICKAXE = ("pickaxe", 10, 4)
    MITHRIL_PICKAXE = ("pickaxe", 20, 5)
    ADAMANT_PICKAXE = ("pickaxe", 30, 7)
    RUNE_PICKAXE = ("pickaxe", 40, 10)
    DRAGON_PICKAXE = ("pickaxe", 60, 15)

    BRONZE_AXE = ("axe", 1, 1)
    IRON_AXE = ("axe", 1, 2)
    STEEL_AXE = ("axe", 5, 3)
    BLACK_AXE = ("axe", 10, 4)
    MITHRIL_AXE = ("axe", 20, 5)
    ADAMANT_AXE = ("axe", 30, 7)
    RUNE_AXE = ("axe", 40, 10)
    DRAGON_AXE = ("axe", 60, 15)

    def __init__(self, tool_type: str, level_req: int, bonus: int):
        self.tool_type = tool_type
        self.level_req = level_req
        self.bonus = bonus


@dataclass
class Resource:
    """Gatherable resource"""

    name: str
    skill: SkillType
    level: int
    base_xp: float
    min_yield: int
    max_yield: int
    tool_type: str
    depletion_chance: float = 0.0
    respawn_time: int = 0


class GatheringSystem:
    """Handles resource gathering mechanics"""

    def __init__(self):
        self.resources = {
            # Mining resources
            "copper": Resource("Copper ore", SkillType.MINING, 1, 17.5, 1, 1, "pickaxe"),
            "tin": Resource("Tin ore", SkillType.MINING, 1, 17.5, 1, 1, "pickaxe"),
            "iron": Resource("Iron ore", SkillType.MINING, 15, 35.0, 1, 1, "pickaxe", 0.5, 3),
            "coal": Resource("Coal", SkillType.MINING, 30, 50.0, 1, 1, "pickaxe", 0.4, 10),
            "mithril": Resource(
                "Mithril ore", SkillType.MINING, 55, 80.0, 1, 1, "pickaxe", 0.3, 20
            ),
            # Woodcutting resources
            "normal": Resource("Logs", SkillType.WOODCUTTING, 1, 25.0, 1, 1, "axe"),
            "oak": Resource("Oak logs", SkillType.WOODCUTTING, 15, 37.5, 1, 1, "axe", 0.4, 4),
            "willow": Resource("Willow logs", SkillType.WOODCUTTING, 30, 67.5, 1, 1, "axe", 0.3, 8),
            "maple": Resource(
                "Maple logs", SkillType.WOODCUTTING, 45, 100.0, 1, 1, "axe", 0.25, 12
            ),
            "yew": Resource("Yew logs", SkillType.WOODCUTTING, 60, 175.0, 1, 1, "axe", 0.2, 20),
        }

    def get_best_tool(self, tool_type: str, skill_level: int) -> Optional[Tool]:
        """Get best usable tool for skill level"""
        best_tool = None
        for tool in Tool:
            if (
                tool.tool_type == tool_type
                and tool.level_req <= skill_level
                and (not best_tool or tool.bonus > best_tool.bonus)
            ):
                best_tool = tool
        return best_tool

    def gather_resource(
        self, resource_name: str, skill_level: int, tool: Optional[Tool] = None
    ) -> tuple[int, float]:
        """
        Attempt to gather a resource
        Returns (amount gathered, xp gained)
        """
        if resource_name not in self.resources:
            return 0, 0.0

        resource = self.resources[resource_name]
        if skill_level < resource.level:
            return 0, 0.0

        # Use best available tool if none provided
        if not tool:
            tool = self.get_best_tool(resource.tool_type, skill_level)
        if not tool or tool.tool_type != resource.tool_type:
            return 0, 0.0

        # Calculate success chance
        success_chance = game_math.calculate_success_chance(
            resource.skill, skill_level, resource.level, tool.bonus
        )

        # Check for success
        if random.random() > success_chance:
            return 0, 0.0

        # Calculate yield and XP
        amount = random.randint(resource.min_yield, resource.max_yield)
        xp = resource.base_xp * amount

        return amount, xp


# Global instance
gathering_system = GatheringSystem()
