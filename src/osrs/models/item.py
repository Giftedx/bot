"""OSRS item model implementation."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum

from ..core.constants import SkillType


class ItemType(Enum):
    """Item types."""
    EQUIPMENT = "equipment"
    CONSUMABLE = "consumable"
    MATERIAL = "material"
    CURRENCY = "currency"
    QUEST = "quest"
    OTHER = "other"


@dataclass
class ItemRequirements:
    """Item requirements."""
    skills: Dict[SkillType, int] = field(default_factory=dict)
    quests: Set[str] = field(default_factory=set)


@dataclass
class Item:
    """Represents an OSRS item."""
    id: str
    name: str
    type: ItemType
    tradeable: bool = True
    stackable: bool = False
    noted: bool = False
    noteable: bool = True
    equipable: bool = False
    high_alch: int = 0
    low_alch: int = 0
    ge_price: int = 0
    weight: float = 0.0
    buy_limit: Optional[int] = None
    requirements: ItemRequirements = field(default_factory=ItemRequirements)
    examine: str = ""
    wiki_url: str = "" 