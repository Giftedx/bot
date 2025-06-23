"""Combat system implementing exact OSRS combat mechanics."""

import math
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class CombatStyle(Enum):
    """Combat styles available in OSRS."""

    ACCURATE = "accurate"
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    CONTROLLED = "controlled"
    RAPID = "rapid"
    LONGRANGE = "longrange"


class AttackType(Enum):
    """Types of attacks in OSRS."""

    MELEE = "melee"
    RANGED = "ranged"
    MAGIC = "magic"


@dataclass
class CombatStats:
    """Combat stats for a character."""

    attack: int
    strength: int
    defence: int
    ranged: int
    magic: int
    hitpoints: int
    prayer: int


@dataclass
class Equipment:
    """Equipment bonuses."""

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
    magic_damage: float = 0
    prayer: int = 0


class CombatSystem:
    """Implements OSRS combat mechanics."""

    # Constants from OSRS
    GAME_TICK = 0.6  # seconds
    MAX_COMBAT_LEVEL = 126
    BASE_ATTACK_INTERVAL = 4  # ticks
    MAX_HIT_POINTS = 99

    def __init__(self):
        """Initialize the combat system."""
        pass

    def calculate_combat_level(self, stats: CombatStats) -> int:
        """Calculate combat level using OSRS formula.

        Args:
            stats: Character's combat stats

        Returns:
            Combat level (1-126)
        """
        # Base combat level
        base = math.floor((stats.defence + stats.hitpoints + math.floor(stats.prayer / 2)) / 4)

        # Attack types
        melee = math.floor(13 / 40 * (stats.attack + stats.strength))
        ranged = math.floor(13 / 40 * math.floor(3 * stats.ranged / 2))
        magic = math.floor(13 / 40 * math.floor(3 * stats.magic / 2))

        return base + max(melee, ranged, magic)

    def calculate_max_hit(
        self,
        stats: CombatStats,
        equipment: Equipment,
        style: CombatStyle,
        attack_type: AttackType,
        prayer_multiplier: float = 1.0,
        other_bonus: float = 1.0,
    ) -> int:
        """Calculate maximum hit using OSRS formulas.

        Args:
            stats: Character's combat stats
            equipment: Equipment bonuses
            style: Combat style being used
            attack_type: Type of attack
            prayer_multiplier: Prayer bonus multiplier
            other_bonus: Other damage multipliers

        Returns:
            Maximum possible hit
        """
        if attack_type == AttackType.MELEE:
            effective_level = stats.strength

            # Add style bonus
            if style == CombatStyle.AGGRESSIVE:
                effective_level += 3
            elif style == CombatStyle.CONTROLLED:
                effective_level += 1

            # Apply prayer
            effective_level = math.floor(effective_level * prayer_multiplier)

            # Calculate max hit
            max_hit = math.floor(0.5 + effective_level * (equipment.melee_strength + 64) / 640)

        elif attack_type == AttackType.RANGED:
            effective_level = stats.ranged

            # Add style bonus
            if style == CombatStyle.ACCURATE:
                effective_level += 3

            # Apply prayer
            effective_level = math.floor(effective_level * prayer_multiplier)

            # Calculate max hit
            max_hit = math.floor(0.5 + effective_level * (equipment.ranged_strength + 64) / 640)

        else:  # Magic
            spell_damage = stats.magic  # This would come from spell data
            max_hit = math.floor(spell_damage * (1 + equipment.magic_damage))

        return math.floor(max_hit * other_bonus)

    def calculate_accuracy(
        self,
        attacker: CombatStats,
        defender: CombatStats,
        attacker_equipment: Equipment,
        defender_equipment: Equipment,
        style: CombatStyle,
        attack_type: AttackType,
        prayer_multiplier: float = 1.0,
    ) -> float:
        """Calculate hit chance using OSRS formulas.

        Args:
            attacker: Attacker's combat stats
            defender: Defender's combat stats
            attacker_equipment: Attacker's equipment
            defender_equipment: Defender's equipment
            style: Combat style being used
            attack_type: Type of attack
            prayer_multiplier: Prayer bonus multiplier

        Returns:
            Hit chance (0-1)
        """
        # Calculate attack roll
        if attack_type == AttackType.MELEE:
            effective_level = attacker.attack

            # Add style bonus
            if style == CombatStyle.ACCURATE:
                effective_level += 3
            elif style == CombatStyle.CONTROLLED:
                effective_level += 1

            # Apply prayer
            effective_level = math.floor(effective_level * prayer_multiplier)

            # Get equipment bonus based on style
            if style == CombatStyle.ACCURATE:
                equipment_bonus = attacker_equipment.attack_stab
            elif style == CombatStyle.AGGRESSIVE:
                equipment_bonus = attacker_equipment.attack_slash
            else:
                equipment_bonus = attacker_equipment.attack_crush

        elif attack_type == AttackType.RANGED:
            effective_level = attacker.ranged

            # Add style bonus
            if style == CombatStyle.ACCURATE:
                effective_level += 3

            # Apply prayer
            effective_level = math.floor(effective_level * prayer_multiplier)

            equipment_bonus = attacker_equipment.attack_ranged

        else:  # Magic
            effective_level = attacker.magic
            equipment_bonus = attacker_equipment.attack_magic

        attack_roll = math.floor((effective_level + 8) * (equipment_bonus + 64))

        # Calculate defence roll
        effective_defence = defender.defence
        if attack_type == AttackType.MAGIC:
            effective_defence = math.floor(0.3 * defender.defence + 0.7 * defender.magic)

        defence_equipment = (
            defender_equipment.defence_stab
            if attack_type == AttackType.MELEE
            else defender_equipment.defence_ranged
            if attack_type == AttackType.RANGED
            else defender_equipment.defence_magic
        )

        defence_roll = math.floor((effective_defence + 8) * (defence_equipment + 64))

        # Calculate hit chance
        if attack_roll > defence_roll:
            return 1 - (defence_roll + 2) / (2 * (attack_roll + 1))
        else:
            return attack_roll / (2 * (defence_roll + 1))

    def process_hit(
        self,
        attacker: CombatStats,
        defender: CombatStats,
        attacker_equipment: Equipment,
        defender_equipment: Equipment,
        style: CombatStyle,
        attack_type: AttackType,
        prayer_multiplier: float = 1.0,
        other_bonus: float = 1.0,
    ) -> Tuple[bool, int]:
        """Process a single hit in combat.

        Args:
            attacker: Attacker's combat stats
            defender: Defender's combat stats
            attacker_equipment: Attacker's equipment
            defender_equipment: Defender's equipment
            style: Combat style being used
            attack_type: Type of attack
            prayer_multiplier: Prayer bonus multiplier
            other_bonus: Other damage multipliers

        Returns:
            Tuple of (hit successful, damage dealt)
        """
        # Calculate accuracy
        accuracy = self.calculate_accuracy(
            attacker,
            defender,
            attacker_equipment,
            defender_equipment,
            style,
            attack_type,
            prayer_multiplier,
        )

        # Roll for hit
        if random.random() > accuracy:
            return (False, 0)

        # Calculate damage
        max_hit = self.calculate_max_hit(
            attacker, attacker_equipment, style, attack_type, prayer_multiplier, other_bonus
        )

        damage = random.randint(0, max_hit)
        return (True, damage)

    def calculate_dps(
        self,
        attacker: CombatStats,
        defender: CombatStats,
        attacker_equipment: Equipment,
        defender_equipment: Equipment,
        style: CombatStyle,
        attack_type: AttackType,
        prayer_multiplier: float = 1.0,
        other_bonus: float = 1.0,
    ) -> float:
        """Calculate damage per second.

        Args:
            attacker: Attacker's combat stats
            defender: Defender's combat stats
            attacker_equipment: Attacker's equipment
            defender_equipment: Defender's equipment
            style: Combat style being used
            attack_type: Type of attack
            prayer_multiplier: Prayer bonus multiplier
            other_bonus: Other damage multipliers

        Returns:
            Expected damage per second
        """
        accuracy = self.calculate_accuracy(
            attacker,
            defender,
            attacker_equipment,
            defender_equipment,
            style,
            attack_type,
            prayer_multiplier,
        )

        max_hit = self.calculate_max_hit(
            attacker, attacker_equipment, style, attack_type, prayer_multiplier, other_bonus
        )

        # Average damage when hit lands
        avg_damage = max_hit / 2

        # Attacks per second
        attack_speed = self.BASE_ATTACK_INTERVAL * self.GAME_TICK
        attacks_per_second = 1 / attack_speed

        return accuracy * avg_damage * attacks_per_second
