"""OSRS equipment and inventory models."""
from dataclasses import dataclass
from typing import Optional

from .item import Item
from ..core.gear import EquipmentSlot


@dataclass
class Equipment:
    """Represents an equipped item."""
    item: Item
    slot: EquipmentSlot
    degradation: Optional[int] = None  # For degradable items
    charges: Optional[int] = None  # For chargeable items


@dataclass
class InventoryItem:
    """Represents an item in inventory."""
    item: Item
    quantity: int = 1
    noted: bool = False 