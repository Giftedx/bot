from typing import Dict, Any
from ....shared.base_pet import BasePet
import random

class OSRSPet(BasePet):
    def __init__(self, pet_id: str, owner_id: str, name: str, pet_type: str):
        super().__init__(pet_id, owner_id, name)
        self.pet_type = pet_type  # e.g., "Baby Mole", "Prince Black Dragon"
        self.combat_level = 1
        self.kill_count = 0
        self.boss_origin = ""  # The boss this pet came from
        
    def special_ability(self) -> str:
        """OSRS pets can boost skilling luck"""
        boost_chance = min(self.level * 0.01, 0.15)  # Max 15% boost
        return f"Provides {boost_chance:.1%} chance of better loot/resource gathering"

    def record_kill(self, boss_name: str) -> None:
        """Record a boss kill with this pet equipped"""
        self.kill_count += 1
        self.gain_experience(random.randint(10, 25))
        
    def level_combat(self) -> None:
        """Level up the pet's combat capabilities"""
        if self.combat_level < 99:  # Max combat level 99
            self.combat_level += 1
            self.gain_experience(50)

    def to_dict(self) -> Dict[str, Any]:
        """Convert OSRS pet data to dictionary, including base pet data"""
        base_data = super().to_dict()
        osrs_data = {
            "pet_type": self.pet_type,
            "combat_level": self.combat_level,
            "kill_count": self.kill_count,
            "boss_origin": self.boss_origin
        }
        return {**base_data, **osrs_data}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OSRSPet':
        """Create OSRS pet instance from dictionary data"""
        pet = super().from_dict(cls, data)
        pet.pet_type = data["pet_type"]
        pet.combat_level = data["combat_level"]
        pet.kill_count = data["kill_count"]
        pet.boss_origin = data["boss_origin"]
        return pet 