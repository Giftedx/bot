"""OSRS combat system implementation."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from . import game_math
from .models import Player, SkillType


class CombatStyle(Enum):
    """Combat attack styles"""

    ACCURATE = "accurate"
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    CONTROLLED = "controlled"
    RAPID = "rapid"
    LONGRANGE = "longrange"


@dataclass
class CombatState:
    """Track combat state between players"""

    attacker: Player
    defender: Player
    style: CombatStyle
    start_time: datetime = field(default_factory=datetime.now)
    hits: List[int] = field(default_factory=list)
    total_damage: int = 0
    ended: bool = False
    winner: Optional[Player] = None


class CombatSystem:
    """Handles combat mechanics and calculations"""

    def __init__(self):
        self.active_battles: Dict[int, CombatState] = {}
        self.combat_styles = {
            CombatStyle.ACCURATE: {
                "attack_bonus": 3,
                "accuracy_multiplier": 1.1,
                "xp_type": "attack",
            },
            CombatStyle.AGGRESSIVE: {
                "strength_bonus": 3,
                "damage_multiplier": 1.1,
                "xp_type": "strength",
            },
            CombatStyle.DEFENSIVE: {
                "defence_bonus": 3,
                "defence_multiplier": 1.1,
                "xp_type": "defence",
            },
            CombatStyle.CONTROLLED: {
                "all_bonus": 1,
                "accuracy_multiplier": 1.05,
                "xp_type": "shared",
            },
        }

    def start_combat(
        self, attacker: Player, defender: Player, style: CombatStyle
    ) -> CombatState:
        """Initialize a combat session"""
        state = CombatState(attacker, defender, style)
        self.active_battles[attacker.id] = state
        return state

    def end_combat(self, attacker_id: int) -> Optional[CombatState]:
        """End combat session and return final state"""
        if attacker_id in self.active_battles:
            state = self.active_battles[attacker_id]
            state.ended = True
            del self.active_battles[attacker_id]
            return state
        return None

    def calculate_attack(
        self, attacker: Player, defender: Player, style: CombatStyle
    ) -> tuple[bool, int]:
        """Calculate hit success and damage"""
        # Get base stats
        attack_level = attacker.skills[SkillType.ATTACK].level
        strength_level = attacker.skills[SkillType.STRENGTH].level
        defence_level = defender.skills[SkillType.DEFENCE].level

        # Apply style bonuses
        style_data = self.combat_styles[style]
        attack_level += style_data.get("attack_bonus", 0)
        strength_level += style_data.get("strength_bonus", 0)

        if "all_bonus" in style_data:
            attack_level += style_data["all_bonus"]
            strength_level += style_data["all_bonus"]

        # Calculate accuracy
        accuracy = game_math.calculate_hit_chance(
            attack_level,
            attacker.combat_stats["attack_bonus"],
            defence_level,
            defender.combat_stats["defence_bonus"],
        )

        # Determine if hit lands
        hit_lands = accuracy > random.random()
        if not hit_lands:
            return False, 0

        # Calculate damage if hit lands
        max_hit = game_math.calculate_max_hit(
            strength_level, attacker.combat_stats["strength_bonus"]
        )

        damage = random.randint(0, max_hit)
        return True, damage

    def process_combat_tick(
        self, state: CombatState
    ) -> tuple[bool, int, Optional[str]]:
        """Process one combat tick, return (hit_success, damage, xp_type)"""
        # Calculate hit
        hit_lands, damage = self.calculate_attack(
            state.attacker, state.defender, state.style
        )

        if hit_lands:
            state.hits.append(damage)
            state.total_damage += damage
            xp_type = self.combat_styles[state.style]["xp_type"]
            return True, damage, xp_type

        return False, 0, None

    def award_combat_xp(
        self, player: Player, damage: int, xp_type: str
    ) -> Dict[SkillType, int]:
        """Award combat XP based on damage dealt"""
        xp_gained = {}
        base_xp = damage * 4  # 4 XP per damage point

        if xp_type == "shared":
            # Split XP between attack, strength, and defence
            shared_xp = base_xp // 3
            xp_gained[SkillType.ATTACK] = shared_xp
            xp_gained[SkillType.STRENGTH] = shared_xp
            xp_gained[SkillType.DEFENCE] = shared_xp
        else:
            # Award XP to specific skill
            skill_map = {
                "attack": SkillType.ATTACK,
                "strength": SkillType.STRENGTH,
                "defence": SkillType.DEFENCE,
            }
            if xp_type in skill_map:
                xp_gained[skill_map[xp_type]] = base_xp

        # Always give some Hitpoints XP
        xp_gained[SkillType.HITPOINTS] = int(base_xp * 1.33)

        return xp_gained


# Global instance
combat_system = CombatSystem()
