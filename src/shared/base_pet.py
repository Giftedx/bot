from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime


class BasePet(ABC):
    def __init__(self, pet_id: str, owner_id: str, name: str):
        self.pet_id = pet_id
        self.owner_id = owner_id
        self.name = name
        self.creation_date = datetime.now()
        self.experience = 0
        self.level = 1
        self.happiness = 100
        self.rarity = "common"

    @abstractmethod
    def special_ability(self) -> str:
        """Each pet type must implement its special ability"""
        pass

    def gain_experience(self, amount: int) -> None:
        """Generic experience gaining method"""
        self.experience += amount
        self._check_level_up()

    def _check_level_up(self) -> None:
        """Check and handle level ups"""
        exp_needed = self.level * 100
        if self.experience >= exp_needed:
            self.level += 1
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert pet data to dictionary for storage"""
        return {
            "pet_id": self.pet_id,
            "owner_id": self.owner_id,
            "name": self.name,
            "creation_date": self.creation_date.isoformat(),
            "experience": self.experience,
            "level": self.level,
            "happiness": self.happiness,
            "rarity": self.rarity,
            "type": self.__class__.__name__,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BasePet":
        """Create pet instance from dictionary data"""
        pet = cls(data["pet_id"], data["owner_id"], data["name"])
        pet.creation_date = datetime.fromisoformat(data["creation_date"])
        pet.experience = data["experience"]
        pet.level = data["level"]
        pet.happiness = data["happiness"]
        pet.rarity = data["rarity"]
        return pet
