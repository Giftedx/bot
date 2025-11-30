"""OSRS Combat System implementation.

This module manages combat mechanics including attack rolls, defence rolls,
max hit calculations, and the combat loop for player-versus-monster interactions.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Any
from enum import Enum
import random
import math


class CombatStyle(Enum):
    """Enumeration of combat styles."""

    ACCURATE = "accurate"
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    CONTROLLED = "controlled"
    RAPID = "rapid"
    LONGRANGE = "longrange"


class AttackType(Enum):
    """Enumeration of attack types."""

    STAB = "stab"
    SLASH = "slash"
    CRUSH = "crush"
    MAGIC = "magic"
    RANGED = "ranged"


@dataclass
class CombatStats:
    """Combat stats for a character.

    Attributes:
        attack (int): Attack skill level.
        strength (int): Strength skill level.
        defence (int): Defence skill level.
        ranged (int): Ranged skill level.
        magic (int): Magic skill level.
        prayer (int): Prayer skill level.
        hitpoints (int): Maximum hitpoints.
        current_hitpoints (int): Current hitpoints.
        prayer_points (int): Current prayer points.
    """

    attack: int
    strength: int
    defence: int
    ranged: int
    magic: int
    prayer: int
    hitpoints: int
    current_hitpoints: int
    prayer_points: int


@dataclass
class Monster:
    """Represents a monster that can be fought.

    Attributes:
        name (str): Name of the monster.
        combat_level (int): The combat level of the monster.
        hitpoints (int): Total health points.
        max_hit (int): Maximum damage the monster can deal.
        attack_level (int): Attack skill level.
        strength_level (int): Strength skill level.
        defence_level (int): Defence skill level.
        attack_bonus (int): Attack bonus stat.
        strength_bonus (int): Strength bonus stat.
        attack_type (AttackType): The type of attack used by the monster.
        aggressive (bool): Whether the monster attacks players on sight.
        drops (Dict[str, float]): Dictionary mapping item names to drop probabilities (0.0 to 1.0).
    """

    name: str
    combat_level: int
    hitpoints: int
    max_hit: int
    attack_level: int
    strength_level: int
    defence_level: int
    attack_bonus: int
    strength_bonus: int
    attack_type: AttackType
    aggressive: bool
    drops: Dict[str, float]


class CombatManager:
    """Manages combat interactions and calculations.

    Handles monster loading, combat calculations (max hit, accuracy, defence),
    and the combat processing loop.
    """

    def __init__(self) -> None:
        """Initialize the CombatManager."""
        self.monsters = self._load_monsters()
        self.active_fights: Dict[str, Monster] = {}  # player_id -> monster

    def _load_monsters(self) -> Dict[str, Monster]:
        """Load all monster definitions.

        Returns:
            Dict[str, Monster]: A dictionary mapping monster names to Monster objects.
        """
        return {
            "Goblin": Monster(
                name="Goblin",
                combat_level=2,
                hitpoints=5,
                max_hit=1,
                attack_level=1,
                strength_level=1,
                defence_level=1,
                attack_bonus=1,
                strength_bonus=1,
                attack_type=AttackType.CRUSH,
                aggressive=False,
                drops={"Bones": 1.0, "Bronze spear": 0.05, "Goblin mail": 0.1},
            ),
            "Lesser demon": Monster(
                name="Lesser demon",
                combat_level=82,
                hitpoints=79,
                max_hit=8,
                attack_level=68,
                strength_level=70,
                defence_level=71,
                attack_bonus=45,
                strength_bonus=45,
                attack_type=AttackType.SLASH,
                aggressive=True,
                drops={"Ashes": 1.0, "Black kiteshield": 0.01, "Rune med helm": 0.005},
            ),
            # Add more monsters...
        }

    def calculate_max_hit(
        self,
        strength_level: int,
        strength_bonus: int,
        style_bonus: int = 0,
        prayer_bonus: float = 1.0,
    ) -> int:
        """Calculate maximum melee hit.

        Args:
            strength_level (int): The player's strength level.
            strength_bonus (int): Equipment strength bonus.
            style_bonus (int, optional): Bonus from attack style (e.g., Aggressive gives +3). Defaults to 0.
            prayer_bonus (float, optional): Multiplier from active prayers. Defaults to 1.0.

        Returns:
            int: The calculated maximum hit.
        """
        effective = math.floor(strength_level * prayer_bonus) + style_bonus + 8
        return math.floor(0.5 + effective * (strength_bonus + 64) / 640)

    def calculate_accuracy_roll(
        self, attack_level: int, attack_bonus: int, style_bonus: int = 0, prayer_bonus: float = 1.0
    ) -> int:
        """Calculate accuracy roll for attack.

        Args:
            attack_level (int): The player's attack level.
            attack_bonus (int): Equipment attack bonus.
            style_bonus (int, optional): Bonus from attack style. Defaults to 0.
            prayer_bonus (float, optional): Multiplier from active prayers. Defaults to 1.0.

        Returns:
            int: The calculated accuracy roll.
        """
        effective = math.floor(attack_level * prayer_bonus) + style_bonus + 8
        return math.floor(effective * (attack_bonus + 64))

    def calculate_defence_roll(
        self,
        defence_level: int,
        defence_bonus: int,
        style_bonus: int = 0,
        prayer_bonus: float = 1.0,
    ) -> int:
        """Calculate defence roll against attack.

        Args:
            defence_level (int): The defender's defence level.
            defence_bonus (int): Equipment defence bonus.
            style_bonus (int, optional): Bonus from defence style. Defaults to 0.
            prayer_bonus (float, optional): Multiplier from active prayers. Defaults to 1.0.

        Returns:
            int: The calculated defence roll.
        """
        effective = math.floor(defence_level * prayer_bonus) + style_bonus + 8
        return math.floor(effective * (defence_bonus + 64))

    async def start_combat(
        self,
        player_id: str,
        monster_name: str,
        player_stats: CombatStats,
        equipment_stats: Any,
        combat_style: CombatStyle,
        attack_type: AttackType,
    ) -> Optional[Monster]:
        """Start combat with a monster.

        Args:
            player_id (str): The ID of the player initiating combat.
            monster_name (str): The name of the monster to fight.
            player_stats (CombatStats): The player's current stats.
            equipment_stats (ItemStats): The player's equipment stats.
            combat_style (CombatStyle): The chosen combat style.
            attack_type (AttackType): The chosen attack type.

        Returns:
            Optional[Monster]: The monster instance if combat starts successfully, else None.
        """
        monster = self.monsters.get(monster_name)
        if not monster:
            return None

        if player_id in self.active_fights:
            return None

        self.active_fights[player_id] = monster
        return monster

    async def process_combat_tick(
        self,
        player_id: str,
        player_stats: CombatStats,
        equipment_stats: Any,
        combat_style: CombatStyle,
        attack_type: AttackType,
    ) -> Optional[Dict[str, int]]:
        """Process one tick of combat.

        Calculates player and monster attacks for the current turn.

        Args:
            player_id (str): The player's ID.
            player_stats (CombatStats): The player's current stats.
            equipment_stats (ItemStats): The player's equipment stats.
            combat_style (CombatStyle): The chosen combat style.
            attack_type (AttackType): The chosen attack type.

        Returns:
            Optional[Dict[str, int]]: Dictionary of drops if the monster died, else None.
        """
        monster = self.active_fights.get(player_id)
        if not monster:
            return None

        # Get attack bonuses based on style
        style_attack = 0
        style_strength = 0
        style_defence = 0

        if combat_style == CombatStyle.ACCURATE:
            style_attack = 3
        elif combat_style == CombatStyle.AGGRESSIVE:
            style_strength = 3
        elif combat_style == CombatStyle.DEFENSIVE:
            style_defence = 3
        elif combat_style == CombatStyle.CONTROLLED:
            style_attack = 1
            style_strength = 1
            style_defence = 1

        # Player attack
        accuracy = self.calculate_accuracy_roll(
            player_stats.attack,
            getattr(equipment_stats, f"attack_{attack_type.value}"),
            style_attack,
        )
        defence = self.calculate_defence_roll(
            monster.defence_level, 0  # Monsters don't have equipment bonuses
        )

        hit = 0
        if random.randint(0, accuracy) > random.randint(0, defence):
            max_hit = self.calculate_max_hit(
                player_stats.strength, equipment_stats.melee_strength, style_strength
            )
            hit = random.randint(0, max_hit)
            monster.hitpoints -= hit

        # Monster attack
        monster_accuracy = self.calculate_accuracy_roll(monster.attack_level, monster.attack_bonus)
        player_defence = self.calculate_defence_roll(
            player_stats.defence,
            getattr(equipment_stats, f"defence_{monster.attack_type.value}"),
            style_defence,
        )

        monster_hit = 0
        if random.randint(0, monster_accuracy) > random.randint(0, player_defence):
            monster_hit = random.randint(0, monster.max_hit)
            player_stats.current_hitpoints -= monster_hit

        # Check for deaths
        if monster.hitpoints <= 0:
            del self.active_fights[player_id]

            # Roll for drops
            drops: Dict[str, int] = {}
            for item, rate in monster.drops.items():
                if random.random() < rate:
                    drops[item] = 1
            return drops

        if player_stats.current_hitpoints <= 0:
            del self.active_fights[player_id]
            return None

        # Return None to indicate combat continues
        return None

    def end_combat(self, player_id: str) -> None:
        """End combat with current monster.

        Args:
            player_id (str): The player's ID.
        """
        if player_id in self.active_fights:
            del self.active_fights[player_id]

    def is_in_combat(self, player_id: str) -> bool:
        """Check if player is in combat.

        Args:
            player_id (str): The player's ID.

        Returns:
            bool: True if the player is currently fighting, else False.
        """
        return player_id in self.active_fights

    def get_current_monster(self, player_id: str) -> Optional[Monster]:
        """Get monster player is fighting.

        Args:
            player_id (str): The player's ID.

        Returns:
            Optional[Monster]: The active monster instance, or None.
        """
        return self.active_fights.get(player_id)
