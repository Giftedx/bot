from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import math


class OSRSSkill(Enum):
    ATTACK = "attack"
    STRENGTH = "strength"
    DEFENCE = "defence"
    RANGED = "ranged"
    PRAYER = "prayer"
    MAGIC = "magic"
    RUNECRAFT = "runecraft"
    HITPOINTS = "hitpoints"
    CRAFTING = "crafting"
    MINING = "mining"
    SMITHING = "smithing"
    FISHING = "fishing"
    COOKING = "cooking"
    FIREMAKING = "firemaking"
    WOODCUTTING = "woodcutting"
    AGILITY = "agility"
    HERBLORE = "herblore"
    THIEVING = "thieving"
    FLETCHING = "fletching"
    SLAYER = "slayer"
    FARMING = "farming"
    CONSTRUCTION = "construction"
    HUNTER = "hunter"


class OSRSCombatStyle(Enum):
    MELEE = "melee"
    RANGED = "ranged"
    MAGIC = "magic"
    MIXED = "mixed"


class OSRSPetSource(Enum):
    BOSS = "boss"
    SKILLING = "skilling"
    MINIGAME = "minigame"
    QUEST = "quest"
    OTHER = "other"


class OSRSPetRarity(Enum):
    COMMON = "common"  # 1/1000 or more common
    UNCOMMON = "uncommon"  # 1/1000 to 1/5000
    RARE = "rare"  # 1/5000 to 1/10000
    VERY_RARE = "very_rare"  # Less than 1/10000
    GUARANTEED = "guaranteed"  # 100% drop rate (quest rewards etc)


@dataclass
class OSRSStats:
    attack: int = 1
    strength: int = 1
    defence: int = 1
    ranged: int = 1
    prayer: int = 1
    magic: int = 1
    runecraft: int = 1
    hitpoints: int = 10
    crafting: int = 1
    mining: int = 1
    smithing: int = 1
    fishing: int = 1
    cooking: int = 1
    firemaking: int = 1
    woodcutting: int = 1
    agility: int = 1
    herblore: int = 1
    thieving: int = 1
    fletching: int = 1
    slayer: int = 1
    farming: int = 1
    construction: int = 1
    hunter: int = 1

    def get_combat_level(self) -> int:
        """Calculate combat level based on stats"""
        base = 0.25 * (defence + hitpoints + math.floor(prayer / 2))
        melee = 0.325 * (attack + strength)
        range_magic = 0.325 * (math.floor(3 * ranged / 2) + math.floor(3 * magic / 2))
        return math.floor(base + max(melee, range_magic))


@dataclass
class OSRSCombatStats:
    attack_level: int
    strength_level: int
    defence_level: int
    hitpoints_level: int
    ranged_level: int
    magic_level: int
    prayer_level: int
    combat_level: int
    attack_bonus: Dict[str, int]
    defence_bonus: Dict[str, int]
    other_bonuses: Dict[str, int]


@dataclass
class OSRSMonster:
    id: str
    name: str
    combat_level: int
    hitpoints: int
    combat_style: OSRSCombatStyle
    stats: OSRSCombatStats
    aggressive: bool
    poisonous: bool
    immune_to_poison: bool
    immune_to_venom: bool
    attributes: List[str]
    weakness: List[str]
    attack_speed: int
    max_hit: int
    experience_per_hit: float
    slayer_level: int = 1
    slayer_xp: float = 0
    examine_text: str = ""
    wiki_url: str = ""


@dataclass
class OSRSLocation:
    name: str
    region: str
    coordinates: Optional[tuple[int, int]] = None
    wilderness_level: int = 0
    requirements: Dict[str, Any] = None
    description: str = ""


@dataclass
class OSRSPetAbility:
    name: str
    description: str
    effect_type: str
    effect_value: float
    passive: bool = False
    cooldown: int = 0
    requirements: Dict[str, Any] = None


@dataclass
class OSRSPetVariant:
    name: str
    examine_text: str
    metamorphic: bool = False
    requirements: Dict[str, Any] = None


@dataclass
class OSRSPet:
    id: str
    name: str
    release_date: datetime
    source: OSRSPetSource
    rarity: OSRSPetRarity
    base_stats: OSRSCombatStats
    abilities: List[OSRSPetAbility]
    variants: List[OSRSPetVariant]
    obtainable_from: List[str]
    drop_rate: Optional[float] = None
    requirements: Dict[OSRSSkill, int] = None
    quest_requirements: List[str] = None
    item_requirements: List[str] = None
    locations: List[OSRSLocation] = None
    examine_text: str = ""
    trivia: List[str] = None
    wiki_url: str = ""

    def calculate_effective_drop_rate(
        self, player_stats: OSRSStats, modifiers: Dict[str, float] = None
    ) -> float:
        """Calculate effective drop rate with player stats and modifiers"""
        if not self.drop_rate:
            return 0.0

        base_rate = self.drop_rate
        if not modifiers:
            modifiers = {}

        # Apply skill-based modifiers
        if self.requirements:
            for skill, required_level in self.requirements.items():
                player_level = getattr(player_stats, skill.value)
                if player_level > required_level:
                    # Small bonus for exceeding requirements
                    bonus = min((player_level - required_level) * 0.001, 0.1)
                    base_rate *= 1 + bonus

        # Apply external modifiers
        for modifier_name, modifier_value in modifiers.items():
            base_rate *= modifier_value

        return min(base_rate, 1.0)  # Cap at 100%

    def meets_requirements(
        self,
        player_stats: OSRSStats,
        completed_quests: List[str] = None,
        owned_items: List[str] = None,
    ) -> tuple[bool, List[str]]:
        """Check if player meets requirements for pet"""
        if not completed_quests:
            completed_quests = []
        if not owned_items:
            owned_items = []

        missing_reqs = []

        # Check skill requirements
        if self.requirements:
            for skill, required_level in self.requirements.items():
                player_level = getattr(player_stats, skill.value)
                if player_level < required_level:
                    missing_reqs.append(
                        f"{skill.value.title()} level {required_level} required "
                        f"(current: {player_level})"
                    )

        # Check quest requirements
        if self.quest_requirements:
            for quest in self.quest_requirements:
                if quest not in completed_quests:
                    missing_reqs.append(f"Quest required: {quest}")

        # Check item requirements
        if self.item_requirements:
            for item in self.item_requirements:
                if item not in owned_items:
                    missing_reqs.append(f"Item required: {item}")

        return len(missing_reqs) == 0, missing_reqs


@dataclass
class OSRSBoss(OSRSMonster):
    pet_drop: Optional[OSRSPet] = None
    mechanics: List[str] = None
    recommended_stats: Dict[OSRSSkill, int] = None
    recommended_items: List[str] = None
    protection_prayers: List[str] = None
    special_attacks: List[str] = None


@dataclass
class OSRSSkillingActivity:
    skill: OSRSSkill
    name: str
    level_required: int
    experience: float
    pet_chance: Optional[float] = None
    requirements: Dict[str, Any] = None
    recommended_items: List[str] = None
    locations: List[OSRSLocation] = None


@dataclass
class OSRSMinigame:
    name: str
    description: str
    requirements: Dict[str, Any]
    rewards: List[str]
    pet_rewards: List[OSRSPet]
    locations: List[OSRSLocation]
    team_based: bool = False
    combat_based: bool = False
    skill_based: bool = False
