"""Models for the OSRS pet system."""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime

class PetType(Enum):
    """Types/elements for pets."""
    OSRS = "osrs"
    POKEMON = "pokemon"
    CUSTOM = "custom"

class StatusEffect(Enum):
    """Status effects that can be applied to pets."""
    NONE = ""
    BURN = "🔥"
    FREEZE = "❄️"
    POISON = "☠️"
    STUN = "⚡"
    HEAL = "💚"
    SHIELD = "🛡️"

@dataclass
class PetAbility:
    """Represents a pet ability/move."""
    name: str
    description: str
    effect_type: str
    effect_value: float
    cooldown: int  # in seconds
    last_used: Optional[datetime] = None

@dataclass
class PetStats:
    """Pet statistics and levels."""
    level: int = 1
    experience: int = 0
    happiness: int = 100
    loyalty: int = 0
    last_interaction: datetime = field(default_factory=datetime.now)
    achievements: List[str] = field(default_factory=list)
    skill_levels: Dict[str, int] = field(default_factory=lambda: {
        "attack": 1,
        "defense": 1,
        "special": 1,
        "speed": 1
    })
    training_points: int = 0

    def gain_exp(self, amount: int) -> bool:
        """Add experience and return True if leveled up."""
        self.experience += amount
        old_level = self.level
        self.level = 1 + (self.experience // 1000)  # Simple leveling formula
        leveled_up = self.level > old_level
        
        if leveled_up:
            self.training_points += 1
            
        return leveled_up

    def train_skill(self, skill: str) -> bool:
        """Train a specific skill using training points."""
        if self.training_points <= 0 or skill not in self.skill_levels:
            return False
            
        self.skill_levels[skill] += 1
        self.training_points -= 1
        return True

    def calculate_power(self) -> int:
        """Calculate pet's overall power level."""
        base_power = self.level * 10
        skill_power = sum(level * 5 for level in self.skill_levels.values())
        loyalty_bonus = min(self.loyalty * 2, 100)  # Cap at 100
        happiness_multiplier = self.happiness / 100  # 0.0 to 1.0
        
        return int((base_power + skill_power + loyalty_bonus) * happiness_multiplier)

@dataclass
class Pet:
    """Base pet class."""
    id: int
    owner_id: int
    name: str
    pet_type: PetType
    stats: PetStats = field(default_factory=PetStats)
    abilities: List[PetAbility] = field(default_factory=list)
    status: StatusEffect = StatusEffect.NONE
    status_turns: int = 0
    creation_date: datetime = field(default_factory=datetime.now)
    attributes: Dict = field(default_factory=dict)

    def add_experience(self, amount: int) -> bool:
        """Add experience and return True if leveled up."""
        return self.stats.gain_exp(amount)

    def apply_status(self, effect: StatusEffect, duration: int = 3):
        """Apply a status effect."""
        self.status = effect
        self.status_turns = duration

    def update_status(self):
        """Update status effect duration."""
        if self.status_turns > 0:
            self.status_turns -= 1
            if self.status_turns == 0:
                self.status = StatusEffect.NONE

    def heal(self, amount: int) -> int:
        """Heal the pet and return amount healed."""
        old_happiness = self.stats.happiness
        self.stats.happiness = min(100, self.stats.happiness + amount)
        return self.stats.happiness - old_happiness

    def to_dict(self) -> Dict:
        """Convert pet to dictionary for storage."""
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "pet_type": self.pet_type.value,
            "stats": {
                "level": self.stats.level,
                "experience": self.stats.experience,
                "happiness": self.stats.happiness,
                "loyalty": self.stats.loyalty,
                "skill_levels": self.stats.skill_levels,
                "training_points": self.stats.training_points
            },
            "status": self.status.value,
            "status_turns": self.status_turns,
            "creation_date": self.creation_date.isoformat(),
            "attributes": self.attributes
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Pet':
        """Create pet instance from dictionary data."""
        stats = PetStats(
            level=data["stats"]["level"],
            experience=data["stats"]["experience"],
            happiness=data["stats"]["happiness"],
            loyalty=data["stats"]["loyalty"],
            skill_levels=data["stats"]["skill_levels"],
            training_points=data["stats"]["training_points"]
        )
        
        return cls(
            id=data["id"],
            owner_id=data["owner_id"],
            name=data["name"],
            pet_type=PetType(data["pet_type"]),
            stats=stats,
            status=StatusEffect(data["status"]),
            status_turns=data["status_turns"],
            creation_date=datetime.fromisoformat(data["creation_date"]),
            attributes=data["attributes"]
        ) 