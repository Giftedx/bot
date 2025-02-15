"""OSRS User model implementation."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from enum import Enum
import math

from ..core.bank import Bank
from ..core.skills import SkillType, SkillLevel
from ..core.gear import Gear, GearSetup, GearBank
from ..core.constants import BitField


class AttackStyle(Enum):
    """Combat attack styles."""
    ACCURATE = "accurate"
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    CONTROLLED = "controlled"
    RAPID = "rapid"
    LONGRANGE = "longrange"


@dataclass
class User:
    """Represents an OSRS user/player."""
    id: str
    username: str
    minion_ironman: bool = False
    GP: int = 0
    bank: Dict[str, int] = field(default_factory=dict)
    collection_log: Dict[str, int] = field(default_factory=dict)
    gear_melee: Optional[GearSetup] = None
    gear_mage: Optional[GearSetup] = None
    gear_range: Optional[GearSetup] = None
    gear_misc: Optional[GearSetup] = None
    gear_skilling: Optional[GearSetup] = None
    gear_wildy: Optional[GearSetup] = None
    gear_fashion: Optional[GearSetup] = None
    gear_other: Optional[GearSetup] = None
    skills: Dict[SkillType, SkillLevel] = field(default_factory=dict)
    bitfield: List[BitField] = field(default_factory=list)
    badges: List[str] = field(default_factory=list)
    attack_style: List[AttackStyle] = field(default_factory=list)
    combat_options: List[str] = field(default_factory=list)
    bank_sort_method: Optional[str] = None
    favorite_alchables: List[int] = field(default_factory=list)

    def __post_init__(self):
        """Initialize default values and create Bank instances."""
        self._bank = Bank(self.bank)
        self._bank_with_gp = Bank(self.bank)
        self._bank_with_gp.add('Coins', self.GP)
        self._collection_log = Bank(self.collection_log)
        
        # Initialize gear if not provided
        default_gear = {}
        self.gear_melee = self.gear_melee or default_gear
        self.gear_mage = self.gear_mage or default_gear
        self.gear_range = self.gear_range or default_gear
        self.gear_misc = self.gear_misc or default_gear
        self.gear_skilling = self.gear_skilling or default_gear
        self.gear_wildy = self.gear_wildy or default_gear
        self.gear_fashion = self.gear_fashion or default_gear
        self.gear_other = self.gear_other or default_gear
        
        # Initialize skills if empty
        if not self.skills:
            self.skills = {
                skill_type: SkillLevel() 
                for skill_type in SkillType
            }
            # Set Hitpoints to 10
            self.skills[SkillType.HITPOINTS].level = 10
            self.skills[SkillType.HITPOINTS].xp = self._xp_for_level(10)

    @property
    def bank(self) -> Bank:
        """Get the user's bank."""
        return self._bank

    @property
    def bank_with_gp(self) -> Bank:
        """Get the user's bank including GP."""
        return self._bank_with_gp

    @property
    def collection_log(self) -> Bank:
        """Get the user's collection log."""
        return self._collection_log

    @property
    def gear(self) -> Dict[str, Gear]:
        """Get all gear setups."""
        return {
            'melee': Gear(self.gear_melee),
            'mage': Gear(self.gear_mage),
            'range': Gear(self.gear_range),
            'misc': Gear(self.gear_misc),
            'skilling': Gear(self.gear_skilling),
            'wildy': Gear(self.gear_wildy),
            'fashion': Gear(self.gear_fashion),
            'other': Gear(self.gear_other)
        }

    @property
    def gear_bank(self) -> GearBank:
        """Get a GearBank instance for this user."""
        return GearBank(
            gear=self.gear,
            bank=self.bank,
            skills=self.skills
        )

    @property
    def combat_level(self) -> int:
        """Calculate combat level using OSRS formula."""
        defence = self.skills[SkillType.DEFENCE].level
        hitpoints = self.skills[SkillType.HITPOINTS].level
        prayer = self.skills[SkillType.PRAYER].level
        attack = self.skills[SkillType.ATTACK].level
        strength = self.skills[SkillType.STRENGTH].level
        ranged = self.skills[SkillType.RANGED].level
        magic = self.skills[SkillType.MAGIC].level

        base = 0.25 * (defence + hitpoints + math.floor(prayer / 2))
        melee = 0.325 * (attack + strength)
        range_val = 0.325 * (math.floor(ranged / 2) + ranged)
        mage = 0.325 * (math.floor(magic / 2) + magic)
        return math.floor(base + max(melee, range_val, mage))

    @property
    def total_level(self) -> int:
        """Get total skill level."""
        return sum(skill.level for skill in self.skills.values())

    def skill_level(self, skill: SkillType) -> int:
        """Get level for a specific skill."""
        return self.skills[skill].level

    def has_skill_requirements(self, requirements: Dict[SkillType, int]) -> bool:
        """Check if user meets skill requirements."""
        return all(
            self.skill_level(skill) >= level
            for skill, level in requirements.items()
        )

    @staticmethod
    def _xp_for_level(level: int) -> int:
        """Calculate XP required for a given level using OSRS formula."""
        total = 0
        for i in range(1, level):
            total += int(i + 300 * (2 ** (i / 7.0)))
        return int(total / 4)

    def count_skills_at_least_99(self) -> int:
        """Count number of skills at level 99 or higher."""
        return sum(1 for skill in self.skills.values() if skill.level >= 99)

    def has_equipped(self, items: Union[int, str, List[int], List[str]], every: bool = False) -> bool:
        """Check if user has item(s) equipped in any gear setup."""
        if isinstance(items, (int, str)):
            items = [items]
        
        for gear_setup in self.gear.values():
            equipped = gear_setup.equipped_items()
            if every:
                if all(item in equipped for item in items):
                    return True
            else:
                if any(item in equipped for item in items):
                    return True
        return False

    def has_equipped_or_in_bank(self, items: Union[int, str, List[int], List[str]], every: bool = False) -> bool:
        """Check if user has item(s) equipped or in bank."""
        if isinstance(items, (int, str)):
            items = [items]
        
        # Check equipped items
        if self.has_equipped(items, every):
            return True
            
        # Check bank
        for item in items:
            if every:
                if not self.bank.has(item):
                    return False
            else:
                if self.bank.has(item):
                    return True
                    
        return every 