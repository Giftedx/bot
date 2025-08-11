"""Combat manager for handling combat mechanics and calculations."""

import math
import random
from typing import Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum

from .game_tick import GameTick, TickPriority


class CombatStyle(Enum):
    """Combat styles available in OSRS."""

    # Melee styles
    ACCURATE = "accurate"
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    CONTROLLED = "controlled"
    # Ranged styles
    RAPID = "rapid"
    LONGRANGE = "longrange"
    # Magic styles
    STANDARD = "standard"
    DEFENSIVE_CASTING = "defensive_casting"


class AttackType(Enum):
    """Types of attacks in OSRS."""

    STAB = "stab"
    SLASH = "slash"
    CRUSH = "crush"
    MAGIC = "magic"
    RANGED = "ranged"


@dataclass
class CombatStats:
    """Combat stats for an entity."""

    attack: int
    strength: int
    defence: int
    ranged: int
    magic: int
    hitpoints: int
    prayer: int = 1
    current_hp: int = None

    def __post_init__(self):
        """Initialize current HP if not set."""
        if self.current_hp is None:
            self.current_hp = self.hitpoints


@dataclass
class CombatBonuses:
    """Equipment bonuses."""

    # Attack bonuses
    attack_stab: int = 0
    attack_slash: int = 0
    attack_crush: int = 0
    attack_magic: int = 0
    attack_ranged: int = 0
    # Defence bonuses
    defence_stab: int = 0
    defence_slash: int = 0
    defence_crush: int = 0
    defence_magic: int = 0
    defence_ranged: int = 0
    # Other bonuses
    melee_strength: int = 0
    ranged_strength: int = 0
    magic_damage: float = 0
    prayer: int = 0


@dataclass
class PrayerBonus:
    """Prayer effect on combat."""

    name: str
    attack_multiplier: float = 1.0
    strength_multiplier: float = 1.0
    defence_multiplier: float = 1.0
    damage_reduction: float = 0.0


class CombatManager:
    """Manages combat mechanics and calculations."""

    # Constants from OSRS
    GAME_TICK = 0.6  # seconds
    MAX_COMBAT_LEVEL = 126
    BASE_ATTACK_INTERVAL = 4  # ticks
    MAX_HITPOINTS = 99

    # Prayer bonuses
    PRAYERS = {
        # Melee prayers
        "burst_of_strength": PrayerBonus("Burst of Strength", strength_multiplier=1.05),
        "superhuman_strength": PrayerBonus("Superhuman Strength", strength_multiplier=1.10),
        "ultimate_strength": PrayerBonus("Ultimate Strength", strength_multiplier=1.15),
        "piety": PrayerBonus(
            "Piety", attack_multiplier=1.20, strength_multiplier=1.23, defence_multiplier=1.25
        ),
        # Ranged prayers
        "sharp_eye": PrayerBonus("Sharp Eye", attack_multiplier=1.05, strength_multiplier=1.05),
        "hawk_eye": PrayerBonus("Hawk Eye", attack_multiplier=1.10, strength_multiplier=1.10),
        "eagle_eye": PrayerBonus("Eagle Eye", attack_multiplier=1.15, strength_multiplier=1.15),
        "rigour": PrayerBonus(
            "Rigour", attack_multiplier=1.20, strength_multiplier=1.23, defence_multiplier=1.25
        ),
        # Magic prayers
        "mystic_will": PrayerBonus("Mystic Will", attack_multiplier=1.05, strength_multiplier=1.05),
        "mystic_lore": PrayerBonus("Mystic Lore", attack_multiplier=1.10, strength_multiplier=1.10),
        "mystic_might": PrayerBonus(
            "Mystic Might", attack_multiplier=1.15, strength_multiplier=1.15
        ),
        "augury": PrayerBonus("Augury", attack_multiplier=1.25, defence_multiplier=1.25),
        # Protection prayers
        "protect_from_melee": PrayerBonus("Protect from Melee", damage_reduction=0.4),
        "protect_from_missiles": PrayerBonus("Protect from Missiles", damage_reduction=0.4),
        "protect_from_magic": PrayerBonus("Protect from Magic", damage_reduction=0.4),
    }

    def __init__(self, game_tick: GameTick):
        """Initialize combat manager.

        Args:
            game_tick: GameTick system instance
        """
        self.game_tick = game_tick
        self.active_fights: Dict[int, Set[int]] = {}  # player_id: opponent_ids

        # Register combat tick task
        self.game_tick.register_task("combat_update", self._combat_tick, TickPriority.COMBAT)

    async def _combat_tick(self):
        """Process combat updates for current game tick."""
        # Process active fights
        for player_id, opponents in self.active_fights.items():
            for opponent_id in opponents:
                # Process combat between player and opponent
                pass

    def calculate_combat_level(self, stats: CombatStats) -> int:
        """Calculate combat level using OSRS formula.

        Args:
            stats: Combat stats

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
        bonuses: CombatBonuses,
        style: CombatStyle,
        attack_type: AttackType,
        prayer_bonus: Optional[PrayerBonus] = None,
        void_bonus: bool = False,
    ) -> int:
        """Calculate maximum hit.

        Args:
            stats: Attacker's combat stats
            bonuses: Equipment bonuses
            style: Combat style being used
            attack_type: Type of attack
            prayer_bonus: Active prayer bonus
            void_bonus: Whether void armor bonus applies

        Returns:
            Maximum possible hit
        """
        if attack_type in (AttackType.STAB, AttackType.SLASH, AttackType.CRUSH):
            # Melee max hit
            effective_strength = stats.strength

            # Add style bonus
            if style == CombatStyle.AGGRESSIVE:
                effective_strength += 3
            elif style == CombatStyle.CONTROLLED:
                effective_strength += 1

            # Apply prayer bonus
            if prayer_bonus:
                effective_strength = math.floor(
                    effective_strength * prayer_bonus.strength_multiplier
                )

            # Apply void bonus
            if void_bonus:
                effective_strength = math.floor(effective_strength * 1.1)

            # Calculate max hit
            max_hit = math.floor(0.5 + effective_strength * (bonuses.melee_strength + 64) / 640)

        elif attack_type == AttackType.RANGED:
            # Ranged max hit
            effective_ranged = stats.ranged

            # Add style bonus
            if style == CombatStyle.ACCURATE:
                effective_ranged += 3

            # Apply prayer bonus
            if prayer_bonus:
                effective_ranged = math.floor(effective_ranged * prayer_bonus.strength_multiplier)

            # Apply void bonus
            if void_bonus:
                effective_ranged = math.floor(effective_ranged * 1.1)

            # Calculate max hit
            max_hit = math.floor(0.5 + effective_ranged * (bonuses.ranged_strength + 64) / 640)

        else:  # Magic
            # Magic max hit depends on spell base damage
            spell_damage = stats.magic  # This would come from spell data
            max_hit = math.floor(spell_damage * (1 + bonuses.magic_damage))

            # Apply prayer bonus
            if prayer_bonus:
                max_hit = math.floor(max_hit * prayer_bonus.strength_multiplier)

        return max_hit

    def calculate_accuracy(
        self,
        attacker: CombatStats,
        defender: CombatStats,
        attacker_bonuses: CombatBonuses,
        defender_bonuses: CombatBonuses,
        style: CombatStyle,
        attack_type: AttackType,
        prayer_bonus: Optional[PrayerBonus] = None,
        void_bonus: bool = False,
    ) -> float:
        """Calculate hit chance.

        Args:
            attacker: Attacker's combat stats
            defender: Defender's combat stats
            attacker_bonuses: Attacker's equipment bonuses
            defender_bonuses: Defender's equipment bonuses
            style: Combat style being used
            attack_type: Type of attack
            prayer_bonus: Active prayer bonus
            void_bonus: Whether void armor bonus applies

        Returns:
            Hit chance (0-1)
        """
        # Calculate attack roll
        if attack_type in (AttackType.STAB, AttackType.SLASH, AttackType.CRUSH):
            effective_level = attacker.attack

            # Add style bonus
            if style == CombatStyle.ACCURATE:
                effective_level += 3
            elif style == CombatStyle.CONTROLLED:
                effective_level += 1

            # Apply prayer bonus
            if prayer_bonus:
                effective_level = math.floor(effective_level * prayer_bonus.attack_multiplier)

            # Apply void bonus
            if void_bonus:
                effective_level = math.floor(effective_level * 1.1)

            # Get equipment bonus based on style
            if attack_type == AttackType.STAB:
                equipment_bonus = attacker_bonuses.attack_stab
            elif attack_type == AttackType.SLASH:
                equipment_bonus = attacker_bonuses.attack_slash
            else:
                equipment_bonus = attacker_bonuses.attack_crush

        elif attack_type == AttackType.RANGED:
            effective_level = attacker.ranged

            # Add style bonus
            if style == CombatStyle.ACCURATE:
                effective_level += 3

            # Apply prayer bonus
            if prayer_bonus:
                effective_level = math.floor(effective_level * prayer_bonus.attack_multiplier)

            # Apply void bonus
            if void_bonus:
                effective_level = math.floor(effective_level * 1.1)

            equipment_bonus = attacker_bonuses.attack_ranged

        else:  # Magic
            effective_level = attacker.magic
            equipment_bonus = attacker_bonuses.attack_magic

            # Apply prayer bonus
            if prayer_bonus:
                effective_level = math.floor(effective_level * prayer_bonus.attack_multiplier)

        attack_roll = math.floor((effective_level + 8) * (equipment_bonus + 64))

        # Calculate defence roll
        effective_defence = defender.defence
        if attack_type == AttackType.MAGIC:
            effective_defence = math.floor(0.3 * defender.defence + 0.7 * defender.magic)

        # Apply defender's prayer bonus
        if prayer_bonus:
            effective_defence = math.floor(effective_defence * prayer_bonus.defence_multiplier)

        defence_equipment = (
            defender_bonuses.defence_stab
            if attack_type == AttackType.STAB
            else defender_bonuses.defence_slash
            if attack_type == AttackType.SLASH
            else defender_bonuses.defence_crush
            if attack_type == AttackType.CRUSH
            else defender_bonuses.defence_ranged
            if attack_type == AttackType.RANGED
            else defender_bonuses.defence_magic
        )

        defence_roll = math.floor((effective_defence + 8) * (defence_equipment + 64))

        # Calculate hit chance
        if attack_roll > defence_roll:
            return 1 - (defence_roll + 2) / (2 * (attack_roll + 1))
        else:
            return attack_roll / (2 * (defence_roll + 1))

    def calculate_damage(self, max_hit: int, accuracy: float, prayer_reduction: float = 0.0) -> int:
        """Calculate damage for a hit.

        Args:
            max_hit: Maximum possible hit
            accuracy: Hit chance
            prayer_reduction: Damage reduction from prayers

        Returns:
            Damage dealt
        """
        # Roll for hit
        if random.random() > accuracy:
            return 0

        # Roll for damage
        damage = random.randint(0, max_hit)

        # Apply prayer reduction
        if prayer_reduction > 0:
            damage = math.floor(damage * (1 - prayer_reduction))

        return max(0, damage)

    def calculate_dps(
        self,
        attacker: CombatStats,
        defender: CombatStats,
        attacker_bonuses: CombatBonuses,
        defender_bonuses: CombatBonuses,
        style: CombatStyle,
        attack_type: AttackType,
        prayer_bonus: Optional[PrayerBonus] = None,
        void_bonus: bool = False,
    ) -> float:
        """Calculate damage per second.

        Args:
            attacker: Attacker's combat stats
            defender: Defender's combat stats
            attacker_bonuses: Attacker's equipment bonuses
            defender_bonuses: Defender's equipment bonuses
            style: Combat style being used
            attack_type: Type of attack
            prayer_bonus: Active prayer bonus
            void_bonus: Whether void armor bonus applies

        Returns:
            Expected damage per second
        """
        max_hit = self.calculate_max_hit(
            attacker, attacker_bonuses, style, attack_type, prayer_bonus, void_bonus
        )

        accuracy = self.calculate_accuracy(
            attacker,
            defender,
            attacker_bonuses,
            defender_bonuses,
            style,
            attack_type,
            prayer_bonus,
            void_bonus,
        )

        # Average damage when hit lands
        avg_damage = max_hit / 2

        # Attacks per second
        attack_speed = self.BASE_ATTACK_INTERVAL * self.GAME_TICK
        attacks_per_second = 1 / attack_speed

        return accuracy * avg_damage * attacks_per_second
