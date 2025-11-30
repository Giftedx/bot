from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
import random

from .constants import SkillType
from .skill_manager import SkillManager
from .skilling import ResourceType


class ProcessedItemType(Enum):
    # Cooking products
    COOKED_SHRIMP = auto()
    COOKED_SARDINE = auto()
    COOKED_HERRING = auto()
    COOKED_TROUT = auto()
    COOKED_SALMON = auto()
    COOKED_LOBSTER = auto()
    COOKED_SWORDFISH = auto()
    COOKED_SHARK = auto()

    # Smithing products
    BRONZE_BAR = auto()
    IRON_BAR = auto()
    STEEL_BAR = auto()
    MITHRIL_BAR = auto()
    ADAMANT_BAR = auto()
    RUNE_BAR = auto()


@dataclass
class ProcessingRecipe:
    result: ProcessedItemType
    required_level: int
    base_xp: float
    success_chance: float
    ingredients: List[ResourceType]


class ProcessingManager:
    """Manages processing activities like cooking and smithing"""

    def __init__(self):
        self.recipes: Dict[ProcessedItemType, ProcessingRecipe] = self._initialize_recipes()

    def _initialize_recipes(self) -> Dict[ProcessedItemType, ProcessingRecipe]:
        """Initialize all processing recipes"""
        recipes = {}

        # Cooking recipes
        recipes[ProcessedItemType.COOKED_SHRIMP] = ProcessingRecipe(
            result=ProcessedItemType.COOKED_SHRIMP,
            required_level=1,
            base_xp=30.0,
            success_chance=0.5,
            ingredients=[ResourceType.SHRIMP],
        )
        recipes[ProcessedItemType.COOKED_SARDINE] = ProcessingRecipe(
            result=ProcessedItemType.COOKED_SARDINE,
            required_level=1,
            base_xp=40.0,
            success_chance=0.45,
            ingredients=[ResourceType.SARDINE],
        )
        recipes[ProcessedItemType.COOKED_TROUT] = ProcessingRecipe(
            result=ProcessedItemType.COOKED_TROUT,
            required_level=15,
            base_xp=70.0,
            success_chance=0.4,
            ingredients=[ResourceType.TROUT],
        )

        # Smithing recipes
        recipes[ProcessedItemType.BRONZE_BAR] = ProcessingRecipe(
            result=ProcessedItemType.BRONZE_BAR,
            required_level=1,
            base_xp=6.2,
            success_chance=1.0,  # Smithing always succeeds
            ingredients=[ResourceType.COPPER_ORE, ResourceType.TIN_ORE],
        )
        recipes[ProcessedItemType.IRON_BAR] = ProcessingRecipe(
            result=ProcessedItemType.IRON_BAR,
            required_level=15,
            base_xp=12.5,
            success_chance=1.0,
            ingredients=[ResourceType.IRON_ORE],
        )
        recipes[ProcessedItemType.STEEL_BAR] = ProcessingRecipe(
            result=ProcessedItemType.STEEL_BAR,
            required_level=30,
            base_xp=17.5,
            success_chance=1.0,
            ingredients=[ResourceType.IRON_ORE, ResourceType.COAL],
        )

        return recipes

    def get_recipe(self, item_type: ProcessedItemType) -> Optional[ProcessingRecipe]:
        """Get recipe data by result type"""
        return self.recipes.get(item_type)

    def attempt_process(
        self,
        item_type: ProcessedItemType,
        skill_manager: SkillManager,
        has_ingredients: bool = True,
    ) -> Tuple[bool, float]:
        """
        Attempt to process items (cook or smith)
        Returns (success, xp_gained)
        """
        recipe = self.get_recipe(item_type)
        if not recipe:
            return (False, 0.0)

        # Get the corresponding skill type
        skill_type = self._get_skill_for_recipe(item_type)
        if not skill_type:
            return (False, 0.0)

        # Check level requirement
        if not skill_manager.meets_requirement(skill_type, recipe.required_level):
            return (False, 0.0)

        # Check ingredients
        if not has_ingredients:
            return (False, 0.0)

        # Calculate success chance based on level for cooking
        if skill_type == SkillType.COOKING:
            level_bonus = (skill_manager.get_level(skill_type) - recipe.required_level) * 0.01
            adjusted_chance = min(0.95, recipe.success_chance + level_bonus)
            success = random.random() < adjusted_chance
        else:  # Smithing always succeeds
            success = True

        xp_gained = recipe.base_xp if success else 0.0

        if success:
            skill_manager.add_xp(skill_type, xp_gained)

        return (success, xp_gained)

    def _get_skill_for_recipe(self, item_type: ProcessedItemType) -> Optional[SkillType]:
        """Get the corresponding skill type for a recipe"""
        if item_type.name.startswith("COOKED_"):
            return SkillType.COOKING
        elif item_type.name.endswith("_BAR"):
            return SkillType.SMITHING
        return None

    def get_required_ingredients(self, item_type: ProcessedItemType) -> List[ResourceType]:
        """Get the required ingredients for a recipe"""
        recipe = self.get_recipe(item_type)
        return recipe.ingredients if recipe else []
