"""Type effectiveness and status effect system."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ElementType(Enum):
    """Unified element types across game systems."""

    # OSRS Combat Types
    MELEE = "melee"
    RANGED = "ranged"
    MAGIC = "magic"

    # Pokemon/Pet Elements
    NORMAL = "normal"
    FIRE = "fire"
    WATER = "water"
    ELECTRIC = "electric"
    GRASS = "grass"
    ICE = "ice"
    FIGHTING = "fighting"
    POISON = "poison"
    GROUND = "ground"
    FLYING = "flying"
    PSYCHIC = "psychic"
    BUG = "bug"
    ROCK = "rock"
    GHOST = "ghost"
    DRAGON = "dragon"
    DARK = "dark"
    STEEL = "steel"
    FAIRY = "fairy"


@dataclass
class StatusEffect:
    """Status effect definition."""

    name: str
    duration: int
    damage_per_turn: int = 0
    stat_multipliers: Dict[str, float] = None
    skip_turn_chance: float = 0
    cure_chance: float = 0


class TypeSystem:
    """Unified type effectiveness system."""

    def __init__(self):
        # OSRS Combat Triangle
        self.osrs_effectiveness = {
            ElementType.MELEE: {ElementType.RANGED: 1.5, ElementType.MAGIC: 0.5},
            ElementType.RANGED: {ElementType.MAGIC: 1.5, ElementType.MELEE: 0.5},
            ElementType.MAGIC: {ElementType.MELEE: 1.5, ElementType.RANGED: 0.5},
        }

        # Pokemon/Pet Type Chart (simplified version)
        self.pokemon_effectiveness = {
            ElementType.FIRE: {
                ElementType.GRASS: 2.0,
                ElementType.ICE: 2.0,
                ElementType.BUG: 2.0,
                ElementType.STEEL: 2.0,
                ElementType.WATER: 0.5,
                ElementType.ROCK: 0.5,
                ElementType.DRAGON: 0.5,
            },
            # ...existing type effectiveness mappings...
        }

        # Status Effects
        self.status_effects = {
            "poison": StatusEffect(
                name="poison",
                duration=5,
                damage_per_turn=5,
                stat_multipliers={"attack": 0.8},
            ),
            "burn": StatusEffect(
                name="burn",
                duration=3,
                damage_per_turn=10,
                stat_multipliers={"attack": 0.7},
            ),
            "freeze": StatusEffect(
                name="freeze", duration=2, skip_turn_chance=0.5, cure_chance=0.2
            ),
            "stun": StatusEffect(name="stun", duration=1, skip_turn_chance=1.0),
            "prayer_drain": StatusEffect(  # OSRS specific
                name="prayer_drain", duration=3, stat_multipliers={"prayer": 0.5}
            ),
            "confusion": StatusEffect(  # Pokemon specific
                name="confusion", duration=4, skip_turn_chance=0.33, cure_chance=0.25
            ),
        }

    def get_effectiveness(
        self, attacker_type: ElementType, defender_type: ElementType, game_type: str
    ) -> float:
        """Get type effectiveness multiplier."""
        if game_type == "osrs":
            return self.osrs_effectiveness.get(attacker_type, {}).get(
                defender_type, 1.0
            )
        else:
            return self.pokemon_effectiveness.get(attacker_type, {}).get(
                defender_type, 1.0
            )

    def apply_status_effect(
        self, effect_name: str, target_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a status effect to target stats."""
        if effect_name not in self.status_effects:
            return target_stats

        effect = self.status_effects[effect_name]
        modified_stats = target_stats.copy()

        # Apply stat multipliers
        if effect.stat_multipliers:
            for stat, multiplier in effect.stat_multipliers.items():
                if stat in modified_stats:
                    modified_stats[stat] *= multiplier

        # Add effect duration
        modified_stats["status_effect"] = effect_name
        modified_stats["status_duration"] = effect.duration
        modified_stats["status_damage"] = effect.damage_per_turn
        modified_stats["skip_turn_chance"] = effect.skip_turn_chance
        modified_stats["cure_chance"] = effect.cure_chance

        return modified_stats

    def process_status_effects(
        self, stats: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Process active status effects."""
        if "status_effect" not in stats:
            return stats, None

        effect_name = stats["status_effect"]
        if effect_name not in self.status_effects:
            return stats, None

        modified_stats = stats.copy()
        message = None

        # Try curing
        if (
            "cure_chance" in modified_stats
            and random.random() < modified_stats["cure_chance"]
        ):
            del modified_stats["status_effect"]
            del modified_stats["status_duration"]
            message = f"Status effect {effect_name} was cured!"
            return modified_stats, message

        # Apply damage
        if "status_damage" in modified_stats:
            if "current_hp" in modified_stats:
                modified_stats["current_hp"] -= modified_stats["status_damage"]
                message = (
                    f"{effect_name} dealt {modified_stats['status_damage']} damage!"
                )

        # Reduce duration
        modified_stats["status_duration"] -= 1
        if modified_stats["status_duration"] <= 0:
            message = f"Status effect {effect_name} wore off!"
            del modified_stats["status_effect"]
            del modified_stats["status_duration"]

        return modified_stats, message
