from typing import Dict, Optional
from dataclasses import dataclass
import math

@dataclass
class CombatStats:
    attack: int
    strength: int
    defence: int
    ranged: int
    magic: int
    prayer: int
    hitpoints: int

@dataclass
class EquipmentBonus:
    attack_stab: int = 0
    attack_slash: int = 0
    attack_crush: int = 0
    attack_magic: int = 0
    attack_ranged: int = 0
    defence_stab: int = 0
    defence_slash: int = 0
    defence_crush: int = 0
    defence_magic: int = 0
    defence_ranged: int = 0
    melee_strength: int = 0
    ranged_strength: int = 0
    magic_damage: int = 0
    prayer: int = 0

class CombatCalculator:
    @staticmethod
    def calculate_combat_level(stats: CombatStats) -> int:
        base = 0.25 * (stats.defence + stats.hitpoints + math.floor(stats.prayer / 2))
        melee = 0.325 * (stats.attack + stats.strength)
        ranged = 0.325 * (math.floor(3 * stats.ranged / 2))
        magic = 0.325 * (math.floor(3 * stats.magic / 2))
        
        return math.floor(base + max(melee, ranged, magic))
    
    @staticmethod
    def calculate_max_hit(
        strength_level: int,
        equipment_strength: int,
        prayer_bonus: float = 1.0,
        other_bonus: float = 1.0
    ) -> int:
        effective_strength = math.floor(strength_level * prayer_bonus) + 8
        max_hit = math.floor(0.5 + effective_strength * (equipment_strength + 64) / 640)
        return math.floor(max_hit * other_bonus)
    
    @staticmethod
    def calculate_accuracy(
        attack_level: int,
        equipment_bonus: int,
        prayer_bonus: float = 1.0,
        other_bonus: float = 1.0
    ) -> float:
        effective_level = math.floor(attack_level * prayer_bonus) + 8
        max_roll = effective_level * (equipment_bonus + 64)
        return max_roll * other_bonus
    
    @staticmethod
    def calculate_hit_chance(
        attack_roll: float,
        defence_roll: float
    ) -> float:
        if attack_roll > defence_roll:
            return 1 - (defence_roll + 2) / (2 * (attack_roll + 1))
        else:
            return attack_roll / (2 * (defence_roll + 1))
    
    @staticmethod
    def calculate_dps(
        max_hit: int,
        accuracy: float,
        attack_speed: float
    ) -> float:
        average_damage = max_hit * 0.5  # Assumes uniform distribution
        return (average_damage * accuracy) / attack_speed
    
    @classmethod
    def get_combat_style_bonus(cls, style: str) -> Dict[str, int]:
        """Returns the invisible bonus levels for each combat style."""
        bonuses = {
            'accurate': {'attack': 3},
            'aggressive': {'strength': 3},
            'defensive': {'defence': 3},
            'controlled': {'attack': 1, 'strength': 1, 'defence': 1},
            'rapid': {'ranged': 3},
            'longrange': {'defence': 3, 'ranged': 3},
        }
        return bonuses.get(style.lower(), {}) 