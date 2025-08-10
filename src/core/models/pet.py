"""
Pet models for the core system.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class PetType(Enum):
    """Pet types."""
    FIRE = "fire"
    WATER = "water"
    EARTH = "earth"
    AIR = "air"
    LIGHT = "light"
    DARK = "dark"


@dataclass
class Pet:
    """Basic pet model."""
    id: Optional[int] = None
    name: str = ""
    owner_id: Optional[int] = None
    element: PetType = PetType.FIRE
    level: int = 1
    experience: int = 0
    health: int = 100
    max_health: int = 100
    data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}