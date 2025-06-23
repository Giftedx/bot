"""
Canonical Player model for the bot.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
from src.core.models.quest import QuestStatus

class EquipmentSlot(Enum):
    HEAD = "head"
    CAPE = "cape"
    NECK = "neck"
    AMMUNITION = "ammunition"
    WEAPON = "weapon"
    SHIELD = "shield"
    BODY = "body"
    LEGS = "legs"
    HANDS = "hands"
    FEET = "feet"
    RING = "ring"

@dataclass
class Item:
    id: int
    name: str
    quantity: int = 1

@dataclass
class Skill:
    level: int = 1
    xp: int = 0

@dataclass
class Player:
    """Represents a player in the game."""
    user_id: int
    username: str
    skills: Dict[str, Skill] = field(default_factory=dict)
    combat_level: int = 3
    inventory: List[Item] = field(default_factory=list)
    bank: List[Item] = field(default_factory=list)
    equipment: Dict[EquipmentSlot, Item] = field(default_factory=dict)
    quest_progress: Dict[int, QuestStatus] = field(default_factory=dict)
    completed_achievements: List[int] = field(default_factory=list)
    collection_log: Dict[str, int] = field(default_factory=dict)

    def add_item_to_inventory(self, item_name: str, quantity: int = 1):
        """Adds an item to the player's inventory, stacking if possible."""
        # This is a simplified implementation. A real one would need an item ID system.
        for item in self.inventory:
            if item.name == item_name:
                item.quantity += quantity
                return
        
        # If item not found, add a new one.
        # We're using a placeholder ID of 0.
        self.inventory.append(Item(id=0, name=item_name, quantity=quantity))

    def has_item(self, item_name: str, quantity: int = 1) -> bool:
        """Checks if the player has a specific item in their inventory."""
        for item in self.inventory:
            if item.name == item_name and item.quantity >= quantity:
                return True
        return False

    def remove_item_from_inventory(self, item_name: str, quantity: int = 1) -> bool:
        """Removes an item from the player's inventory."""
        for item in self.inventory:
            if item.name == item_name:
                if item.quantity > quantity:
                    item.quantity -= quantity
                else:
                    self.inventory.remove(item)
                return True
        return False

    def get_quest_status(self, quest_id: int) -> QuestStatus:
        """Gets the status of a specific quest."""
        return self.quest_progress.get(quest_id, QuestStatus.NOT_STARTED)

    def start_quest(self, quest_id: int):
        """Marks a quest as in progress."""
        if self.get_quest_status(quest_id) == QuestStatus.NOT_STARTED:
            self.quest_progress[quest_id] = QuestStatus.IN_PROGRESS

    def complete_quest(self, quest_id: int):
        """Marks a quest as completed."""
        self.quest_progress[quest_id] = QuestStatus.COMPLETED

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        """Creates a Player object from a dictionary."""
        # The data from the DB is a JSON string, so it needs to be loaded.
        import json
        player_data = json.loads(data.get("data", "{}"))
        
        skills = {name: Skill(**stats) for name, stats in player_data.get("skills", {}).items()}
        inventory = [Item(**item) for item in player_data.get("inventory", [])]
        bank = [Item(**item) for item in player_data.get("bank", [])]
        equipment_data = data.get("equipment", {})
        equipment = {
            EquipmentSlot(slot): Item.from_dict(item_data)
            for slot, item_data in equipment_data.items()
        }
        quest_progress_data = data.get("quest_progress", {})
        quest_progress = {int(k): QuestStatus(v) for k, v in quest_progress_data.items()}
        
        return cls(
            user_id=data["player_id"],
            username=data["username"],
            skills=skills,
            combat_level=player_data.get("combat_level", 3),
            inventory=inventory,
            bank=bank,
            equipment=equipment,
            quest_progress=quest_progress,
            completed_achievements=data.get("completed_achievements", []),
            collection_log=data.get("collection_log", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Player object to a dictionary."""
        return {
            "skills": {name: {"level": s.level, "xp": s.xp} for name, s in self.skills.items()},
            "combat_level": self.combat_level,
            "inventory": [item.__dict__ for item in self.inventory],
            "bank": [item.__dict__ for item in self.bank],
            "equipment": {slot.value: item.to_dict() for slot, item in self.equipment.items()},
            "quest_progress": {str(k): v.value for k, v in self.quest_progress.items()},
            "completed_achievements": self.completed_achievements,
            "collection_log": self.collection_log,
        }

    def add_to_collection_log(self, item_name: str):
        """Adds an item to the player's collection log."""
        self.collection_log[item_name] = self.collection_log.get(item_name, 0) + 1 