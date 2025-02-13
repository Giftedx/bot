# TODO: Refactor and integrate functionality from master.py
from enum import Enum
from dataclasses import dataclass, field
from typing import List

class PetType(Enum):
    FIRE = "🔥"
    WATER = "💧"
    EARTH = "🌍"
    AIR = "💨"
    LIGHT = "✨"
    DARK = "🌑"

class StatusEffect(Enum):
    BURN = "🔥"
    POISON = "🤢"
    PARALYZE = "⚡"
    SLEEP = "💤"
    NONE = ""

@dataclass
class PetMove:
    name: str
    damage: int
    element: PetType
    accuracy: int
    cooldown: int
    emoji: str
    status_effect: StatusEffect = StatusEffect.NONE
    status_chance: int = 0
    current_cooldown: int = 0

@dataclass
class BattlePet:
    pet: 'Pet'
    moves: List[PetMove]
    current_hp: int
    max_hp: int
    element: PetType
    status: StatusEffect = StatusEffect.NONE
    status_turns: int = 0

    def apply_status(self, effect: StatusEffect, turns: int = 3):
        self.status = effect
        self.status_turns = turns

    def update_status(self):
        if self.status_turns > 0:
            self.status_turns -= 1
            if self.status_turns == 0:
                self.status = StatusEffect.NONE

@dataclass
class Pet:
    name: str
    element: PetType
    level: int = 1
    experience: int = 0
    moves: List[PetMove] = field(default_factory=list)
    health: int = 100
    max_health: int = 100

    def __post_init__(self):
      pass #Was calling generate_moves, which needs refactoring
      #   if not self.moves:
      #       self.moves = generate_moves_for_element(self.element)

    def add_experience(self, amount: int) -> bool:
        """Returns True if leveled up"""
        self.experience += amount
        if self.experience >= self.level * 100:
            self.level_up()
            return True
        return False

    def level_up(self):
        self.level += 1
        self.experience = 0
        self.max_health += 10
        self.health = self.max_health