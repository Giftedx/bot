"""
Player models for the core system.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class Skill:
    """Skill model."""
    level: int = 1
    xp: int = 0
    
    def __post_init__(self):
        if self.level < 1:
            self.level = 1
        if self.xp < 0:
            self.xp = 0


@dataclass
class Player:
    """Basic player model."""
    id: Optional[int] = None
    discord_id: Optional[int] = None
    username: Optional[str] = None
    name: Optional[str] = None
    level: int = 1
    experience: int = 0
    coins: int = 0
    skills: Dict[str, Any] = field(default_factory=dict)
    inventory: Dict[str, int] = field(default_factory=dict)
    quests: Dict[str, str] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def combat_level(self) -> int:
        """Calculate combat level."""
        return self.level
    
    def has_item(self, item_name: str, quantity: int = 1) -> bool:
        """Check if player has an item."""
        return self.inventory.get(item_name, 0) >= quantity
    
    def remove_item_from_inventory(self, item_name: str, quantity: int) -> bool:
        """Remove item from inventory."""
        if self.has_item(item_name, quantity):
            self.inventory[item_name] = self.inventory.get(item_name, 0) - quantity
            if self.inventory[item_name] <= 0:
                del self.inventory[item_name]
            return True
        return False
    
    def get_quest_status(self, quest_id: str) -> str:
        """Get quest status."""
        return self.quests.get(quest_id, "not_started")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Player':
        """Create player from dictionary."""
        return cls(**data)