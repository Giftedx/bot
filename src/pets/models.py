"""Models for the pet system including pets, battles, and status effects."""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime

class PetType(Enum):
    """Types/elements for pets."""
    FIRE = "🔥"
    WATER = "💧" 
    EARTH = "🌍"
    AIR = "💨"
    LIGHT = "✨"
    DARK = "🌑"

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
class PetMove:
    """Represents a move/ability that a pet can use."""
    name: str
    damage: int
    element: PetType
    status_effect: Optional[StatusEffect] = None
    status_duration: int = 0
    cooldown: int = 0
    emoji: str = "⚔️"

@dataclass 
class Pet:
    """Represents a pet with stats and battle info."""
    name: str
    element: PetType
    level: int = 1
    experience: int = 0
    health: int = 100
    max_health: int = 100
    status: StatusEffect = StatusEffect.NONE
    status_turns: int = 0
    moves: List[PetMove] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Initialize default moves if none provided."""
        if self.moves is None:
            self.moves = [
                PetMove(
                    "Basic Attack",
                    10,
                    self.element
                ),
                PetMove(
                    f"{self.element.name} Strike",
                    20,
                    self.element,
                    emoji=self.element.value
                )
            ]

    def apply_status(self, effect: StatusEffect, duration: int = 3):
        """Apply a status effect to the pet."""
        self.status = effect
        self.status_turns = duration

    def update_status(self):
        """Update status effect duration and clear if expired."""
        if self.status_turns > 0:
            self.status_turns -= 1
            if self.status_turns == 0:
                self.status = StatusEffect.NONE

    def add_experience(self, amount: int) -> bool:
        """Add experience to the pet.
        
        Args:
            amount: Amount of XP to add
            
        Returns:
            bool: True if pet leveled up
        """
        self.experience += amount
        if self.experience >= self.level * 100:
            self.level_up()
            return True
        return False

    def level_up(self) -> None:
        """Level up the pet, updating its stats."""
        self.level += 1
        self.experience = 0
        old_max = self.max_health
        self.max_health = int(self.max_health * 1.1)  # 10% increase
        self.health += (self.max_health - old_max)  # Heal by the HP increase

    def heal(self, amount: int) -> int:
        """Heal the pet.
        
        Args:
            amount: Amount to heal
            
        Returns:
            int: Actual amount healed
        """
        old_health = self.health
        self.health = min(self.max_health, self.health + amount)
        return self.health - old_health

    def take_damage(self, amount: int) -> int:
        """Apply damage to the pet.
        
        Args:
            amount: Amount of damage to take
            
        Returns:
            int: Actual damage taken
        """
        old_health = self.health
        self.health = max(0, self.health - amount)
        return old_health - self.health

    def is_defeated(self) -> bool:
        """Check if pet is defeated (HP = 0)."""
        return self.health <= 0

@dataclass
class Battle:
    """Represents an active battle between two pets."""
    battle_id: str
    pet1: Pet
    pet2: Pet
    current_turn: int = 1
    last_move: Optional[str] = None
    status: str = "active"

    def get_current_pet(self) -> Pet:
        """Get the pet whose turn it currently is."""
        return self.pet1 if self.current_turn % 2 == 1 else self.pet2

    def get_opponent_pet(self) -> Pet:
        """Get the pet waiting for their turn."""
        return self.pet2 if self.current_turn % 2 == 1 else self.pet1

    def next_turn(self):
        """Advance to the next turn."""
        self.current_turn += 1
        current_pet = self.get_current_pet()
        current_pet.update_status()

class BattleSystem:
    """Manages pet battles including turns and damage calculation."""
    
    def __init__(self):
        self.active_battles: Dict[str, Battle] = {}
        self.battle_counter = 0

    async def start_battle(self, pet1: Pet, pet2: Pet) -> Battle:
        """Start a new battle between two pets."""
        self.battle_counter += 1
        battle_id = f"battle_{self.battle_counter}"
        
        battle = Battle(
            battle_id=battle_id,
            pet1=pet1,
            pet2=pet2
        )
        self.active_battles[battle_id] = battle
        return battle

    def end_battle(self, battle_id: str):
        """End a battle and clean up."""
        if battle_id in self.active_battles:
            del self.active_battles[battle_id]

    def get_battle(self, battle_id: str) -> Optional[Battle]:
        """Get a battle by ID."""
        return self.active_battles.get(battle_id)