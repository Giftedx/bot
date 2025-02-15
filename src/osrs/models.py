"""OSRS game models and data structures"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class SkillType(Enum):
    """OSRS skill types"""
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


@dataclass
class Skill:
    """Represents a trainable skill"""
    type: SkillType
    level: int = 1
    xp: int = 0
    
    def add_xp(self, amount: int) -> bool:
        """Add XP to the skill and return True if leveled up"""
        self.xp += amount
        old_level = self.level
        self.level = self._xp_to_level(self.xp)
        return self.level > old_level
        
    @staticmethod
    def _xp_to_level(xp: int) -> int:
        """Convert XP to level using OSRS formula"""
        for level in range(1, 100):
            if xp < Player.xp_for_level(level):
                return level - 1
        return 99


@dataclass 
class Item:
    """Represents an in-game item"""
    id: int
    name: str
    description: str
    tradeable: bool = True
    stackable: bool = False
    equipable: bool = False
    value: int = 0


@dataclass
class InventoryItem:
    """Represents an item in an inventory"""
    item: Item
    quantity: int = 1


@dataclass
class Equipment:
    """Represents equipped items"""
    weapon: Optional[Item] = None
    shield: Optional[Item] = None
    helmet: Optional[Item] = None
    body: Optional[Item] = None
    legs: Optional[Item] = None
    boots: Optional[Item] = None
    gloves: Optional[Item] = None
    amulet: Optional[Item] = None
    ring: Optional[Item] = None
    cape: Optional[Item] = None


@dataclass
class Player:
    """Represents a player character"""
    id: int
    name: str
    skills: Dict[SkillType, Skill] = field(default_factory=dict)
    inventory: List[InventoryItem] = field(default_factory=list)
    equipment: Equipment = field(default_factory=Equipment)
    gold: int = 0

    def __post_init__(self) -> None:
        # Initialize all skills at level 1
        if not self.skills:
            self.skills = {
                skill_type: Skill(type=skill_type)
                for skill_type in SkillType
            }
            # Set Hitpoints to 10
            self.skills[SkillType.HITPOINTS].level = 10
            self.skills[SkillType.HITPOINTS].xp = self.xp_for_level(10)

    @staticmethod
    def xp_for_level(level: int) -> int:
        """Calculate XP required for a given level using OSRS formula"""
        total = 0
        for i in range(1, level):
            total += int(i + 300 * (2 ** (i / 7.0)))
        return int(total / 4)

    def get_combat_level(self) -> int:
        """Calculate combat level using OSRS formula"""
        base = 0.25 * (
            self.skills[SkillType.DEFENCE].level + 
            self.skills[SkillType.HITPOINTS].level +
            (self.skills[SkillType.PRAYER].level // 2)
        )
        
        melee = 0.325 * (
            self.skills[SkillType.ATTACK].level +
            self.skills[SkillType.STRENGTH].level
        )
        
        ranged = 0.325 * (
            (self.skills[SkillType.RANGED].level * 3) // 2
        )
        
        magic = 0.325 * (
            (self.skills[SkillType.MAGIC].level * 3) // 2
        )
        
        return int(base + max(melee, ranged, magic))

    def add_item(self, item: Item, quantity: int = 1) -> bool:
        """Add item to inventory. Returns False if inventory is full."""
        if len(self.inventory) >= 28 and not item.stackable:
            return False
            
        for inv_item in self.inventory:
            if inv_item.item.id == item.id and item.stackable:
                inv_item.quantity += quantity
                return True
                
        if len(self.inventory) < 28:
            self.inventory.append(InventoryItem(item, quantity))
            return True
            
        return False
