"""OSRS gear and equipment implementation."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Union
from enum import Enum, auto

from .bank import Bank
from .skills import SkillType


class EquipmentSlot(Enum):
    """Equipment slot types."""
    HEAD = auto()
    CAPE = auto()
    NECK = auto()
    AMMO = auto()
    WEAPON = auto()
    BODY = auto()
    SHIELD = auto()
    LEGS = auto()
    HANDS = auto()
    FEET = auto()
    RING = auto()


@dataclass
class GearStats:
    """Equipment stats."""
    attack_stab: int = 0
    attack_slash: int = 0
    attack_crush: int = 0
    attack_magic: int = 0
    attack_ranged: int = 0
    defence_stab: int = 0
    defence_slash: int = 0
    defence_crush: int = 0
    defence_magic: int = 0
    defence_ranged: int = 0
    melee_strength: int = 0
    ranged_strength: int = 0
    magic_damage: int = 0
    prayer: int = 0
    speed: int = 4  # Default attack speed

    def __add__(self, other: 'GearStats') -> 'GearStats':
        """Add two GearStats objects together."""
        return GearStats(
            attack_stab=self.attack_stab + other.attack_stab,
            attack_slash=self.attack_slash + other.attack_slash,
            attack_crush=self.attack_crush + other.attack_crush,
            attack_magic=self.attack_magic + other.attack_magic,
            attack_ranged=self.attack_ranged + other.attack_ranged,
            defence_stab=self.defence_stab + other.defence_stab,
            defence_slash=self.defence_slash + other.defence_slash,
            defence_crush=self.defence_crush + other.defence_crush,
            defence_magic=self.defence_magic + other.defence_magic,
            defence_ranged=self.defence_ranged + other.defence_ranged,
            melee_strength=self.melee_strength + other.melee_strength,
            ranged_strength=self.ranged_strength + other.ranged_strength,
            magic_damage=self.magic_damage + other.magic_damage,
            prayer=self.prayer + other.prayer,
            speed=max(self.speed, other.speed)
        )


@dataclass
class GearRequirements:
    """Equipment requirements."""
    skills: Dict[SkillType, int] = field(default_factory=dict)
    quests: Set[str] = field(default_factory=set)


@dataclass
class GearItem:
    """Individual equipment item."""
    id: Union[str, int]
    name: str
    slot: EquipmentSlot
    stats: GearStats = field(default_factory=GearStats)
    requirements: GearRequirements = field(default_factory=GearRequirements)
    two_handed: bool = False


class GearSetup:
    """Equipment setup for a specific combat style."""

    def __init__(self):
        """Initialize empty gear setup."""
        self._slots: Dict[EquipmentSlot, Optional[GearItem]] = {
            slot: None for slot in EquipmentSlot
        }

    def equip(self, item: GearItem) -> List[GearItem]:
        """
        Equip an item and return any unequipped items.
        Handles two-handed weapons appropriately.
        """
        unequipped = []
        
        # Handle two-handed weapons
        if item.two_handed and item.slot == EquipmentSlot.WEAPON:
            shield = self._slots[EquipmentSlot.SHIELD]
            if shield:
                unequipped.append(shield)
                self._slots[EquipmentSlot.SHIELD] = None
        
        # Handle equipping shield with two-handed weapon
        if (item.slot == EquipmentSlot.SHIELD and 
            self._slots[EquipmentSlot.WEAPON] and 
            self._slots[EquipmentSlot.WEAPON].two_handed):
            unequipped.append(self._slots[EquipmentSlot.WEAPON])
            self._slots[EquipmentSlot.WEAPON] = None
        
        # Unequip current item in slot
        current = self._slots[item.slot]
        if current:
            unequipped.append(current)
        
        # Equip new item
        self._slots[item.slot] = item
        
        return unequipped

    def unequip(self, slot: EquipmentSlot) -> Optional[GearItem]:
        """Unequip item from slot."""
        item = self._slots[slot]
        self._slots[slot] = None
        return item

    def get(self, slot: EquipmentSlot) -> Optional[GearItem]:
        """Get item in slot."""
        return self._slots[slot]

    def clear(self) -> List[GearItem]:
        """Remove all equipment and return unequipped items."""
        unequipped = []
        for slot in EquipmentSlot:
            item = self._slots[slot]
            if item:
                unequipped.append(item)
                self._slots[slot] = None
        return unequipped

    def stats(self) -> GearStats:
        """Calculate total stats of equipped items."""
        total = GearStats()
        for item in self._slots.values():
            if item:
                total = total + item.stats
        return total

    def equipped_items(self) -> Set[Union[str, int]]:
        """Get set of equipped item IDs."""
        return {
            item.id for item in self._slots.values() 
            if item is not None
        }

    def meets_requirements(self, 
                         skills: Dict[SkillType, int],
                         completed_quests: Set[str]) -> bool:
        """Check if all equipped items' requirements are met."""
        for item in self._slots.values():
            if not item:
                continue
                
            # Check skill requirements
            for skill, level in item.requirements.skills.items():
                if skills.get(skill, 1) < level:
                    return False
                    
            # Check quest requirements
            if not item.requirements.quests.issubset(completed_quests):
                return False
                
        return True


class GearBank:
    """Manages gear setups and bank integration."""

    def __init__(self,
                 gear: Dict[str, GearSetup],
                 bank: Bank,
                 skills: Dict[SkillType, int]):
        """Initialize with gear setups, bank and skills."""
        self.gear = gear
        self.bank = bank
        self.skills = skills

    def equip(self, 
              setup: str,
              item: GearItem,
              auto_unequip_to_bank: bool = True) -> bool:
        """
        Equip item to specified setup.
        Returns True if successful, False if requirements not met.
        """
        if setup not in self.gear:
            return False
            
        # Check requirements
        if not self.gear[setup].meets_requirements(self.skills, set()):
            return False
            
        # Remove from bank
        if not self.bank.remove(item.id):
            return False
            
        # Equip and handle unequipped items
        unequipped = self.gear[setup].equip(item)
        
        if auto_unequip_to_bank:
            for unequipped_item in unequipped:
                self.bank.add(unequipped_item.id)
                
        return True

    def unequip(self,
                setup: str,
                slot: EquipmentSlot,
                to_bank: bool = True) -> bool:
        """
        Unequip item from specified setup.
        Returns True if successful.
        """
        if setup not in self.gear:
            return False
            
        item = self.gear[setup].unequip(slot)
        if item and to_bank:
            self.bank.add(item.id)
            
        return True

    def clear_setup(self,
                   setup: str,
                   to_bank: bool = True) -> bool:
        """
        Clear all equipment from specified setup.
        Returns True if successful.
        """
        if setup not in self.gear:
            return False
            
        unequipped = self.gear[setup].clear()
        
        if to_bank:
            for item in unequipped:
                self.bank.add(item.id)
                
        return True 