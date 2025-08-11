"""Combat manager for handling combat calculations and formulas."""

import math
from typing import Dict, Optional
from .data_manager import DataManager


class CombatManager(DataManager):
    """Manages combat calculations and formulas."""

    def __init__(self, data_dir: str = "src/osrs/data"):
        """Initialize the combat manager.

        Args:
            data_dir: Directory containing data files.
        """
        super().__init__(data_dir)
        self.COMBAT_FILE = "combat_formulas.json"

    def calculate_combat_level(self, stats: Dict[str, int]) -> int:
        """Calculate combat level based on stats.

        Args:
            stats: Dict containing player stats.

        Returns:
            The calculated combat level.
        """
        formulas = self.get_data(self.COMBAT_FILE, "combat_level")

        # Calculate base combat level
        base = math.floor(
            (stats["defence"] + stats["hitpoints"] + math.floor(stats["prayer"] / 2)) / 4
        )

        # Calculate attack types
        melee = math.floor(13 / 40 * (stats["attack"] + stats["strength"]))
        ranged = math.floor(13 / 40 * math.floor(3 * stats["ranged"] / 2))
        magic = math.floor(13 / 40 * math.floor(3 * stats["magic"] / 2))

        return base + max(melee, ranged, magic)

    def calculate_max_hit(
        self,
        combat_style: str,
        level: int,
        equipment_bonus: int,
        prayer_multiplier: float = 1.0,
        stance_bonus: int = 0,
    ) -> int:
        """Calculate maximum hit for given combat style.

        Args:
            combat_style: The combat style (melee/ranged/magic).
            level: The relevant combat level.
            equipment_bonus: Equipment strength bonus.
            prayer_multiplier: Prayer bonus multiplier.
            stance_bonus: Combat stance bonus.

        Returns:
            The calculated maximum hit.
        """
        formulas = self.get_data(self.COMBAT_FILE, "max_hit")
        style_data = formulas[combat_style]

        if combat_style == "magic":
            return math.floor(level * prayer_multiplier)

        effective_level = level * prayer_multiplier + stance_bonus
        max_hit = math.floor(0.5 + effective_level * (64 + equipment_bonus) / 640)

        return max_hit

    def calculate_accuracy(
        self,
        combat_style: str,
        attack_level: int,
        attack_bonus: int,
        defense_level: int,
        defense_bonus: int,
    ) -> float:
        """Calculate hit chance.

        Args:
            combat_style: The combat style (melee/ranged/magic).
            attack_level: Attacker's relevant combat level.
            attack_bonus: Attacker's equipment accuracy bonus.
            defense_level: Defender's defense level.
            defense_bonus: Defender's equipment defense bonus.

        Returns:
            The calculated hit chance (0-1).
        """
        formulas = self.get_data(self.COMBAT_FILE, "accuracy")
        style_data = formulas[combat_style]

        # Calculate attack and defense rolls
        attack_roll = math.floor((attack_level + 8) * (64 + attack_bonus) / 64)
        defense_roll = math.floor((defense_level + 8) * (64 + defense_bonus) / 64)

        # Calculate hit chance
        if attack_roll > defense_roll:
            return 1 - (defense_roll + 2) / (2 * (attack_roll + 1))
        return attack_roll / (2 * defense_roll)

    def get_special_attack(self, weapon_id: str) -> Optional[Dict]:
        """Get special attack data for a weapon.

        Args:
            weapon_id: The ID of the weapon.

        Returns:
            Dict containing special attack data or None.
        """
        special_attacks = self.get_data(self.COMBAT_FILE, "special_attacks")
        return special_attacks.get(weapon_id)

    def calculate_damage_reduction(
        self,
        damage: int,
        protection_prayer: Optional[str] = None,
        defense_level: int = 1,
        armor_bonus: int = 0,
    ) -> int:
        """Calculate reduced damage after protection.

        Args:
            damage: The initial damage.
            protection_prayer: Active protection prayer if any.
            defense_level: Defender's defense level.
            armor_bonus: Defender's armor bonus.

        Returns:
            The reduced damage amount.
        """
        formulas = self.get_data(self.COMBAT_FILE, "damage_reduction")

        # Apply protection prayer
        if protection_prayer:
            prayer_reduction = formulas["protection_prayers"].get(protection_prayer, 0)
            damage = math.floor(damage * (1 - prayer_reduction))

        # Apply defense reduction
        defense_reduction = (math.floor(defense_level * 0.3) + math.floor(armor_bonus * 0.7)) / 100
        damage = math.floor(damage * (1 - defense_reduction))

        return max(0, damage)
