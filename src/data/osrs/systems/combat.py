from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import math


class CombatStyle(Enum):
    MELEE = "melee"
    RANGED = "ranged"
    MAGIC = "magic"
    MIXED = "mixed"


class AttackType(Enum):
    STAB = "stab"
    SLASH = "slash"
    CRUSH = "crush"
    MAGIC = "magic"
    RANGED = "ranged"


class DefenseType(Enum):
    STAB = "stab"
    SLASH = "slash"
    CRUSH = "crush"
    MAGIC = "magic"
    RANGED = "ranged"


@dataclass
class CombatStats:
    attack: int
    strength: int
    defense: int
    ranged: int
    magic: int
    hitpoints: int
    prayer: int

    def get_combat_level(self) -> int:
        """Calculate combat level."""
        base = 0.25 * (self.defense + self.hitpoints + math.floor(self.prayer / 2))
        melee = 0.325 * (self.attack + self.strength)
        range_magic = 0.325 * (math.floor(3 * self.ranged / 2) + math.floor(3 * self.magic / 2))
        return math.floor(base + max(melee, range_magic))


@dataclass
class DropTableItem:
    item_id: str
    name: str
    quantity: Tuple[int, int]  # (min, max)
    weight: int  # For weighted random selection
    rarity: float  # Drop rate (0.0 to 1.0)
    requirements: Optional[Dict[str, any]] = None


@dataclass
class DropTable:
    always: List[DropTableItem]
    common: List[DropTableItem]
    uncommon: List[DropTableItem]
    rare: List[DropTableItem]
    very_rare: List[DropTableItem]


@dataclass
class MonsterMechanic:
    name: str
    trigger_condition: str  # e.g. "hp < 50%", "every 30 ticks"
    effect: str
    damage: Tuple[int, int]  # (min, max)
    accuracy: float
    cooldown: int  # In game ticks
    protection_prayer: Optional[str] = None
    avoidance_method: Optional[str] = None


@dataclass
class Monster:
    id: str
    name: str
    combat_level: int
    stats: CombatStats
    combat_style: CombatStyle
    attack_speed: int
    max_hit: int
    aggressive: bool
    drop_table: DropTable
    mechanics: List[MonsterMechanic]
    weakness: List[AttackType]
    immune_to_poison: bool = False
    immune_to_venom: bool = False
    slayer_level: int = 1
    slayer_xp: float = 0


class DropCalculator:
    def __init__(self):
        self.ring_of_wealth: bool = False
        self.row_imbued: bool = False
        self.on_slayer_task: bool = False
        self.combat_achievements: List[str] = []

    def calculate_drop_modifiers(self, monster: Monster) -> Dict[str, float]:
        """Calculate drop rate modifiers."""
        modifiers = {
            "base": 1.0,
            "wealth": 1.0 + (0.01 if self.ring_of_wealth else 0),
            "slayer": 1.0 + (0.1 if self.on_slayer_task else 0),
            "achievements": 1.0,
        }

        # Apply combat achievement bonuses
        for achievement in self.combat_achievements:
            if achievement.startswith("elite_"):
                modifiers["achievements"] += 0.02
            elif achievement.startswith("master_"):
                modifiers["achievements"] += 0.05

        return modifiers

    def roll_drop_table(
        self, monster: Monster, modifiers: Dict[str, float] = None
    ) -> List[DropTableItem]:
        """Roll on a monster's drop table."""
        if not modifiers:
            modifiers = self.calculate_drop_modifiers(monster)

        drops = []
        total_modifier = math.prod(modifiers.values())

        # Always drops
        drops.extend(monster.drop_table.always)

        # Roll for other drops
        def roll_table(table: List[DropTableItem]) -> Optional[DropTableItem]:
            total_weight = sum(item.weight for item in table)
            roll = random.random() * total_weight
            current_weight = 0
            for item in table:
                current_weight += item.weight
                if roll < current_weight:
                    if random.random() < (item.rarity * total_modifier):
                        return item
            return None

        # Roll on each table
        tables = [
            (monster.drop_table.common, 1),
            (monster.drop_table.uncommon, 0.5),
            (monster.drop_table.rare, 0.1),
            (monster.drop_table.very_rare, 0.01),
        ]

        for table, base_chance in tables:
            if random.random() < (base_chance * total_modifier):
                drop = roll_table(table)
                if drop:
                    drops.append(drop)

        return drops


class CombatCalculator:
    def __init__(self):
        self.prayer_bonus: Dict[str, float] = {
            "piety": 1.2,
            "rigour": 1.25,
            "augury": 1.25,
            "protect_melee": 0.0,  # Complete protection in OSRS
            "protect_range": 0.0,
            "protect_magic": 0.0,
        }

    def calculate_max_hit(
        self,
        stats: CombatStats,
        equipment_bonus: int,
        style: CombatStyle,
        prayer_multiplier: float = 1.0,
        other_multipliers: Dict[str, float] = None,
    ) -> int:
        """Calculate maximum hit."""
        if not other_multipliers:
            other_multipliers = {}

        effective_level = 0
        if style == CombatStyle.MELEE:
            effective_level = stats.strength
        elif style == CombatStyle.RANGED:
            effective_level = stats.ranged
        elif style == CombatStyle.MAGIC:
            effective_level = stats.magic

        # Apply prayer bonus
        effective_level = math.floor(effective_level * prayer_multiplier)

        # Apply other multipliers
        for multiplier in other_multipliers.values():
            effective_level = math.floor(effective_level * multiplier)

        # Final max hit calculation
        max_hit = math.floor(0.5 + effective_level * (equipment_bonus + 64) / 640)
        return max_hit

    def calculate_accuracy(
        self,
        attacker_stats: CombatStats,
        defender_stats: CombatStats,
        attack_bonus: int,
        defense_bonus: int,
        style: CombatStyle,
    ) -> float:
        """Calculate hit chance."""
        # Get effective attack level
        attack_level = 0
        if style == CombatStyle.MELEE:
            attack_level = attacker_stats.attack
        elif style == CombatStyle.RANGED:
            attack_level = attacker_stats.ranged
        elif style == CombatStyle.MAGIC:
            attack_level = attacker_stats.magic

        # Get effective defense level
        defense_level = defender_stats.defense

        # Calculate attack roll
        attack_roll = attack_level * (attack_bonus + 64)

        # Calculate defense roll
        defense_roll = defense_level * (defense_bonus + 64)

        # Calculate hit chance
        if attack_roll > defense_roll:
            return 1 - (defense_roll + 2) / (2 * (attack_roll + 1))
        else:
            return attack_roll / (2 * (defense_roll + 1))

    def simulate_damage(self, max_hit: int, accuracy: float) -> int:
        """Simulate a damage roll."""
        if random.random() > accuracy:
            return 0  # Miss
        return random.randint(0, max_hit)


class MonsterMechanicsHandler:
    def __init__(self, monster: Monster):
        self.monster = monster
        self.active_mechanics: Dict[str, int] = {}  # mechanic_name -> cooldown
        self.tick_counter: int = 0

    def update(self) -> List[Tuple[MonsterMechanic, int]]:
        """Update monster mechanics and return triggered ones with damage."""
        self.tick_counter += 1
        triggered = []

        # Update cooldowns
        for mechanic_name in list(self.active_mechanics.keys()):
            self.active_mechanics[mechanic_name] -= 1
            if self.active_mechanics[mechanic_name] <= 0:
                del self.active_mechanics[mechanic_name]

        # Check for triggered mechanics
        for mechanic in self.monster.mechanics:
            if mechanic.name in self.active_mechanics:
                continue  # Still on cooldown

            # Parse and evaluate trigger condition
            should_trigger = False
            if mechanic.trigger_condition.startswith("hp <"):
                hp_percent = int(mechanic.trigger_condition.split("<")[1].strip("%"))
                # You would need to track monster HP % here
                # should_trigger = monster_hp_percent < hp_percent
            elif mechanic.trigger_condition.startswith("every"):
                ticks = int(mechanic.trigger_condition.split(" ")[1])
                should_trigger = self.tick_counter % ticks == 0

            if should_trigger:
                damage = random.randint(mechanic.damage[0], mechanic.damage[1])
                if random.random() < mechanic.accuracy:
                    triggered.append((mechanic, damage))
                self.active_mechanics[mechanic.name] = mechanic.cooldown

        return triggered

    def get_active_mechanics(self) -> List[str]:
        """Get list of currently active mechanics."""
        return list(self.active_mechanics.keys())

    def can_trigger_mechanic(self, mechanic_name: str) -> bool:
        """Check if a specific mechanic can be triggered."""
        return mechanic_name not in self.active_mechanics
