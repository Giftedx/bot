"""OSRS-specific pet implementation."""
from typing import Dict, Any
import random

from .models import Pet, PetType, PetStats

class OSRSPet(Pet):
    """OSRS-specific pet implementation."""
    
    def __init__(self, id: int, owner_id: int, name: str, pet_type: str):
        """Initialize OSRS pet."""
        super().__init__(
            id=id,
            owner_id=owner_id,
            name=name,
            pet_type=PetType.OSRS,
            stats=PetStats()
        )
        self.combat_level = 1
        self.kill_count = 0
        self.boss_origin = pet_type  # The boss this pet came from
        
    def special_ability(self) -> str:
        """OSRS pets can boost skilling luck."""
        boost_chance = min(self.stats.level * 0.01, 0.15)  # Max 15% boost
        return f"Provides {boost_chance:.1%} chance of better loot/resource gathering"

    def record_kill(self, boss_name: str) -> None:
        """Record a boss kill with this pet equipped."""
        self.kill_count += 1
        self.add_experience(random.randint(10, 25))
        
    def level_combat(self) -> None:
        """Level up the pet's combat capabilities."""
        if self.combat_level < 99:  # Max combat level 99
            self.combat_level += 1
            self.add_experience(50)

    def to_dict(self) -> Dict[str, Any]:
        """Convert OSRS pet data to dictionary, including base pet data."""
        base_data = super().to_dict()
        osrs_data = {
            "combat_level": self.combat_level,
            "kill_count": self.kill_count,
            "boss_origin": self.boss_origin
        }
        return {**base_data, **osrs_data}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OSRSPet':
        """Create OSRS pet instance from dictionary data."""
        pet = cls(
            id=data["id"],
            owner_id=data["owner_id"],
            name=data["name"],
            pet_type=data["boss_origin"]
        )
        
        # Load base stats
        pet.stats = PetStats(
            level=data["stats"]["level"],
            experience=data["stats"]["experience"],
            happiness=data["stats"]["happiness"],
            loyalty=data["stats"]["loyalty"],
            skill_levels=data["stats"]["skill_levels"],
            training_points=data["stats"]["training_points"]
        )
        
        # Load OSRS-specific data
        pet.combat_level = data["combat_level"]
        pet.kill_count = data["kill_count"]
        
        return pet 