"""Player state management for OSRS."""
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class StatusEffect:
    """Represents a temporary status effect on a player."""

    type: str
    value: float
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        """Check if the effect has expired."""
        return datetime.now() > self.expires_at


class PlayerState:
    """Manages player state and status effects."""

    def __init__(self, player_id: int):
        self.player_id = player_id
        self.status_effects: List[StatusEffect] = []
        self.active_prayers: Set[str] = set()
        self.run_energy: float = 100.0
        self.special_attack: float = 100.0
        self.is_running: bool = False
        self.last_action: Optional[datetime] = None
        self.combat_target: Optional[int] = None
        self.last_hit_taken: Optional[datetime] = None
        self.last_hit_dealt: Optional[datetime] = None
        self.current_action: Optional[str] = None
        self.action_started: Optional[datetime] = None
        self.current_location: str = "lumbridge"
        self.is_in_combat: bool = False
        self.is_teleblocked: bool = False
        self.poison_damage: int = 0
        self.venom_damage: int = 0
        self.disease_damage: int = 0
        self.prayer_points: float = 1.0
        self.boosted_stats: Dict[str, int] = {}
        self.reduced_stats: Dict[str, int] = {}

    def add_status_effect(self, effect_type: str, value: float, duration: timedelta) -> None:
        """Add a temporary status effect."""
        effect = StatusEffect(type=effect_type, value=value, expires_at=datetime.now() + duration)
        self.status_effects.append(effect)

    def remove_status_effect(self, effect_type: str) -> None:
        """Remove a status effect."""
        self.status_effects = [
            effect for effect in self.status_effects if effect.type != effect_type
        ]

    def get_status_effect(self, effect_type: str) -> Optional[StatusEffect]:
        """Get a specific status effect if active."""
        self._clean_expired_effects()
        return next((effect for effect in self.status_effects if effect.type == effect_type), None)

    def _clean_expired_effects(self) -> None:
        """Remove expired status effects."""
        self.status_effects = [effect for effect in self.status_effects if not effect.is_expired]

    def toggle_prayer(self, prayer_name: str) -> bool:
        """Toggle a prayer on/off."""
        if prayer_name in self.active_prayers:
            self.active_prayers.remove(prayer_name)
            return False
        else:
            self.active_prayers.add(prayer_name)
            return True

    def clear_prayers(self) -> None:
        """Turn off all active prayers."""
        self.active_prayers.clear()

    def modify_run_energy(self, amount: float) -> None:
        """Modify run energy level."""
        self.run_energy = max(0.0, min(100.0, self.run_energy + amount))
        if self.run_energy == 0:
            self.is_running = False

    def modify_special_attack(self, amount: float) -> None:
        """Modify special attack energy."""
        self.special_attack = max(0.0, min(100.0, self.special_attack + amount))

    def start_action(self, action: str) -> None:
        """Start a new action."""
        self.current_action = action
        self.action_started = datetime.now()

    def stop_action(self) -> None:
        """Stop the current action."""
        self.current_action = None
        self.action_started = None

    def apply_poison(self, damage: int) -> None:
        """Apply poison effect."""
        if self.poison_damage < damage:
            self.poison_damage = damage

    def apply_venom(self, damage: int) -> None:
        """Apply venom effect."""
        if self.venom_damage < damage:
            self.venom_damage = damage

    def apply_disease(self, damage: int) -> None:
        """Apply disease effect."""
        if self.disease_damage < damage:
            self.disease_damage = damage

    def cure_poison(self) -> None:
        """Cure poison effect."""
        self.poison_damage = 0

    def cure_venom(self) -> None:
        """Cure venom effect."""
        self.venom_damage = 0

    def cure_disease(self) -> None:
        """Cure disease effect."""
        self.disease_damage = 0

    def boost_stat(self, stat: str, amount: int) -> None:
        """Apply a temporary stat boost."""
        self.boosted_stats[stat] = amount

    def reduce_stat(self, stat: str, amount: int) -> None:
        """Apply a temporary stat reduction."""
        self.reduced_stats[stat] = amount

    def clear_stat_changes(self) -> None:
        """Clear all temporary stat changes."""
        self.boosted_stats.clear()
        self.reduced_stats.clear()

    def get_effective_stat(self, stat: str, base_value: int) -> int:
        """Get effective stat value including boosts/reductions."""
        boost = self.boosted_stats.get(stat, 0)
        reduction = self.reduced_stats.get(stat, 0)
        return max(1, base_value + boost - reduction)

    def start_combat(self, target_id: int) -> None:
        """Enter combat with a target."""
        self.combat_target = target_id
        self.is_in_combat = True
        self.last_hit_taken = None
        self.last_hit_dealt = None

    def end_combat(self) -> None:
        """End combat state."""
        self.combat_target = None
        self.is_in_combat = False
        self.last_hit_taken = None
        self.last_hit_dealt = None

    def apply_teleblock(self, duration: timedelta) -> None:
        """Apply teleblock effect."""
        self.is_teleblocked = True
        self.add_status_effect("teleblock", 1.0, duration)

    def update_location(self, new_location: str) -> None:
        """Update player location."""
        self.current_location = new_location

    def is_idle(self) -> bool:
        """Check if player is currently idle."""
        return not self.is_in_combat and not self.current_action and not self.combat_target

    def can_teleport(self) -> bool:
        """Check if player can currently teleport."""
        return not self.is_teleblocked and not self.is_in_combat and self.wilderness_level() <= 20

    def wilderness_level(self) -> int:
        """Get current wilderness level or 0 if not in wilderness."""
        if not self.current_location.startswith("wilderness_"):
            return 0
        try:
            return int(self.current_location.split("_")[1])
        except (IndexError, ValueError):
            return 0

    def tick(self) -> None:
        """Process one game tick for the player."""
        self._clean_expired_effects()

        # Handle poison damage
        if self.poison_damage > 0:
            self.poison_damage = max(0, self.poison_damage - 1)

        # Handle venom damage
        if self.venom_damage > 0:
            self.venom_damage += 2

        # Handle disease damage
        if self.disease_damage > 0:
            self.disease_damage = max(0, self.disease_damage - 1)

        # Regenerate run energy
        if not self.is_running:
            self.modify_run_energy(0.6)  # Regenerate 0.6% per tick

        # Regenerate special attack
        if self.special_attack < 100:
            self.modify_special_attack(10)  # 10% per tick

        # Check teleblock expiry
        if self.is_teleblocked:
            teleblock = self.get_status_effect("teleblock")
            if not teleblock:
                self.is_teleblocked = False
