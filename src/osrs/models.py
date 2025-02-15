"""OSRS game models and data structures"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime


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
    SHARED = "shared"  # For shared XP gains


class QuestStatus(Enum):
    """Quest completion status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TradeStatus(Enum):
    """Trade offer status."""
    PENDING = "pending"
    COMPLETED = "completed"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


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
    id: str
    name: str
    description: str
    category: str
    tradeable: bool = True
    stackable: bool = False
    equipable: bool = False
    high_alch_value: int = 0
    low_alch_value: int = 0
    ge_price: Optional[int] = None


@dataclass
class InventoryItem:
    """Represents an item in an inventory"""
    item: Item
    quantity: int = 1


@dataclass
class Equipment:
    """Represents equipped items"""
    head: Optional[Item] = None
    cape: Optional[Item] = None
    neck: Optional[Item] = None
    weapon: Optional[Item] = None
    body: Optional[Item] = None
    shield: Optional[Item] = None
    legs: Optional[Item] = None
    hands: Optional[Item] = None
    feet: Optional[Item] = None
    ring: Optional[Item] = None
    ammo: Optional[Item] = None
    
    def get_attack_bonus(self) -> int:
        """Calculate total attack bonus from equipment."""
        bonus = 0
        for slot in self.__dict__.values():
            if slot and hasattr(slot, 'attack_bonus'):
                bonus += slot.attack_bonus
        return bonus
    
    def get_strength_bonus(self) -> int:
        """Calculate total strength bonus from equipment."""
        bonus = 0
        for slot in self.__dict__.values():
            if slot and hasattr(slot, 'strength_bonus'):
                bonus += slot.strength_bonus
        return bonus
    
    def get_defence_bonus(self) -> int:
        """Calculate total defence bonus from equipment."""
        bonus = 0
        for slot in self.__dict__.values():
            if slot and hasattr(slot, 'defence_bonus'):
                bonus += slot.defence_bonus
        return bonus


@dataclass
class Bank:
    """Represents a player's bank"""
    items: Dict[str, int] = field(default_factory=dict)  # item_id -> quantity
    max_slots: int = 800  # Default max bank slots
    
    def add_item(self, item_id: str, quantity: int = 1) -> bool:
        """Add items to bank. Returns True if successful."""
        if len(self.items) >= self.max_slots and item_id not in self.items:
            return False
        
        self.items[item_id] = self.items.get(item_id, 0) + quantity
        return True
    
    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        """Remove items from bank. Returns True if successful."""
        if item_id not in self.items or self.items[item_id] < quantity:
            return False
            
        self.items[item_id] -= quantity
        if self.items[item_id] == 0:
            del self.items[item_id]
        return True
    
    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        """Check if bank has enough of an item"""
        return item_id in self.items and self.items[item_id] >= quantity
    
    def get_item_quantity(self, item_id: str) -> int:
        """Get quantity of an item in bank"""
        return self.items.get(item_id, 0)
    
    def get_total_items(self) -> int:
        """Get total number of unique items in bank"""
        return len(self.items)


@dataclass
class Player:
    """Represents a player character"""
    id: int
    name: str
    skills: Dict[SkillType, Skill] = field(default_factory=dict)
    inventory: List[InventoryItem] = field(default_factory=list)
    equipment: Equipment = field(default_factory=Equipment)
    bank: Bank = field(default_factory=Bank)
    quests: Dict[str, QuestStatus] = field(default_factory=dict)
    quest_points: int = 0
    gold: int = 0
    current_world: int = 301

    def __post_init__(self) -> None:
        # Initialize all skills at level 1
        if not self.skills:
            self.skills = {
                skill_type: Skill(type=skill_type)
                for skill_type in SkillType
                if skill_type != SkillType.SHARED
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

    def get_quest_status(self, quest_id: str) -> QuestStatus:
        """Get the status of a quest."""
        return self.quests.get(quest_id, QuestStatus.NOT_STARTED)
    
    def start_quest(self, quest_id: str) -> None:
        """Start a quest."""
        if quest_id not in self.quests:
            self.quests[quest_id] = QuestStatus.IN_PROGRESS
    
    def complete_quest(self, quest_id: str, quest_points: int = 1) -> None:
        """Complete a quest and award quest points."""
        self.quests[quest_id] = QuestStatus.COMPLETED
        self.quest_points += quest_points
