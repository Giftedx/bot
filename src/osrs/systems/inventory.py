"""OSRS Inventory System"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from enum import Enum

class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    TOOL = "tool"
    CONSUMABLE = "consumable"
    MATERIAL = "material"
    CURRENCY = "currency"
    QUEST = "quest"
    PET = "pet"

class EquipmentSlot(Enum):
    HEAD = "head"
    CAPE = "cape"
    NECK = "neck"
    AMMO = "ammo"
    WEAPON = "weapon"
    SHIELD = "shield"
    BODY = "body"
    LEGS = "legs"
    HANDS = "hands"
    FEET = "feet"
    RING = "ring"

@dataclass
class ItemStats:
    """Stats for equipment items"""
    attack_stab: int = 0
    attack_slash: int = 0
    attack_crush: int = 0
    attack_magic: int = 0
    attack_range: int = 0
    defence_stab: int = 0
    defence_slash: int = 0
    defence_crush: int = 0
    defence_magic: int = 0
    defence_range: int = 0
    melee_strength: int = 0
    ranged_strength: int = 0
    magic_damage: int = 0
    prayer: int = 0

@dataclass
class ItemRequirements:
    """Requirements to use/equip an item"""
    skills: Dict[str, int] = None
    quests: List[str] = None
    achievement_points: int = 0

class Item:
    """Represents an OSRS item"""
    
    def __init__(
        self,
        name: str,
        type: ItemType,
        tradeable: bool,
        stackable: bool,
        value: int,
        equipment_slot: Optional[EquipmentSlot] = None,
        stats: Optional[ItemStats] = None,
        requirements: Optional[ItemRequirements] = None
    ):
        self.name = name
        self.type = type
        self.tradeable = tradeable
        self.stackable = stackable
        self.value = value
        self.equipment_slot = equipment_slot
        self.stats = stats or ItemStats()
        self.requirements = requirements or ItemRequirements()

class InventoryManager:
    """Manages player inventory and equipment"""
    
    def __init__(self):
        self.items = self._load_items()
        self.player_inventories: Dict[str, Dict[str, int]] = {}  # player_id -> item_name -> quantity
        self.player_equipment: Dict[str, Dict[EquipmentSlot, str]] = {}  # player_id -> slot -> item_name
        self.player_banks: Dict[str, Dict[str, int]] = {}  # player_id -> item_name -> quantity
        
    def _load_items(self) -> Dict[str, Item]:
        """Load all item definitions"""
        return {
            "Bronze sword": Item(
                name="Bronze sword",
                type=ItemType.WEAPON,
                tradeable=True,
                stackable=False,
                value=26,
                equipment_slot=EquipmentSlot.WEAPON,
                stats=ItemStats(
                    attack_stab=4,
                    attack_slash=3,
                    attack_crush=2,
                    melee_strength=5
                )
            ),
            
            "Rune platebody": Item(
                name="Rune platebody",
                type=ItemType.ARMOR,
                tradeable=True,
                stackable=False,
                value=39000,
                equipment_slot=EquipmentSlot.BODY,
                stats=ItemStats(
                    defence_stab=82,
                    defence_slash=80,
                    defence_crush=84,
                    defence_magic=-30,
                    defence_range=80
                ),
                requirements=ItemRequirements(
                    skills={"defence": 40},
                    quests=["Dragon Slayer"]
                )
            ),
            
            "Coins": Item(
                name="Coins",
                type=ItemType.CURRENCY,
                tradeable=True,
                stackable=True,
                value=1
            ),
            
            # Add more items...
        }
        
    def get_inventory(
        self,
        player_id: str
    ) -> Dict[str, int]:
        """Get player's inventory"""
        if player_id not in self.player_inventories:
            self.player_inventories[player_id] = {}
        return self.player_inventories[player_id]
        
    def get_equipment(
        self,
        player_id: str
    ) -> Dict[EquipmentSlot, str]:
        """Get player's equipped items"""
        if player_id not in self.player_equipment:
            self.player_equipment[player_id] = {}
        return self.player_equipment[player_id]
        
    def get_bank(
        self,
        player_id: str
    ) -> Dict[str, int]:
        """Get player's bank"""
        if player_id not in self.player_banks:
            self.player_banks[player_id] = {}
        return self.player_banks[player_id]
        
    def add_item(
        self,
        player_id: str,
        item_name: str,
        quantity: int,
        to_bank: bool = False
    ) -> bool:
        """Add items to inventory/bank"""
        item = self.items.get(item_name)
        if not item:
            return False
            
        target = self.get_bank(player_id) if to_bank else self.get_inventory(player_id)
        
        if not item.stackable and not to_bank:
            # Check inventory space
            current_slots = sum(
                qty for name, qty in target.items()
                if not self.items[name].stackable
            )
            if current_slots + quantity > 28:
                return False
                
        if item_name in target:
            target[item_name] += quantity
        else:
            target[item_name] = quantity
            
        return True
        
    def remove_item(
        self,
        player_id: str,
        item_name: str,
        quantity: int,
        from_bank: bool = False
    ) -> bool:
        """Remove items from inventory/bank"""
        target = self.get_bank(player_id) if from_bank else self.get_inventory(player_id)
        
        if item_name not in target or target[item_name] < quantity:
            return False
            
        target[item_name] -= quantity
        if target[item_name] == 0:
            del target[item_name]
            
        return True
        
    def can_equip(
        self,
        player_id: str,
        item_name: str,
        skills: Dict[str, int],
        completed_quests: Set[str],
        achievement_points: int
    ) -> bool:
        """Check if player can equip an item"""
        item = self.items.get(item_name)
        if not item or not item.equipment_slot:
            return False
            
        reqs = item.requirements
        
        # Check skill requirements
        if reqs.skills:
            for skill, level in reqs.skills.items():
                if skills.get(skill, 0) < level:
                    return False
                    
        # Check quest requirements
        if reqs.quests and not all(q in completed_quests for q in reqs.quests):
            return False
            
        # Check achievement points
        if achievement_points < reqs.achievement_points:
            return False
            
        return True
        
    def equip_item(
        self,
        player_id: str,
        item_name: str
    ) -> Optional[str]:
        """Equip an item from inventory, returns unequipped item if any"""
        if not self.remove_item(player_id, item_name, 1):
            return None
            
        item = self.items[item_name]
        equipment = self.get_equipment(player_id)
        
        # Unequip current item in slot
        unequipped = equipment.get(item.equipment_slot)
        if unequipped:
            self.add_item(player_id, unequipped, 1)
            
        # Equip new item
        equipment[item.equipment_slot] = item_name
        
        return unequipped
        
    def unequip_item(
        self,
        player_id: str,
        slot: EquipmentSlot
    ) -> bool:
        """Unequip an item to inventory"""
        equipment = self.get_equipment(player_id)
        
        if slot not in equipment:
            return False
            
        item_name = equipment[slot]
        if not self.add_item(player_id, item_name, 1):
            return False
            
        del equipment[slot]
        return True
        
    def get_equipment_stats(
        self,
        player_id: str
    ) -> ItemStats:
        """Get total equipment stats"""
        stats = ItemStats()
        equipment = self.get_equipment(player_id)
        
        for item_name in equipment.values():
            item = self.items[item_name]
            item_stats = item.stats
            
            stats.attack_stab += item_stats.attack_stab
            stats.attack_slash += item_stats.attack_slash
            stats.attack_crush += item_stats.attack_crush
            stats.attack_magic += item_stats.attack_magic
            stats.attack_range += item_stats.attack_range
            stats.defence_stab += item_stats.defence_stab
            stats.defence_slash += item_stats.defence_slash
            stats.defence_crush += item_stats.defence_crush
            stats.defence_magic += item_stats.defence_magic
            stats.defence_range += item_stats.defence_range
            stats.melee_strength += item_stats.melee_strength
            stats.ranged_strength += item_stats.ranged_strength
            stats.magic_damage += item_stats.magic_damage
            stats.prayer += item_stats.prayer
            
        return stats 