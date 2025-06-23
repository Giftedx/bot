from typing import Optional, List, Dict, Tuple, Set
import random
import asyncio
from dataclasses import dataclass
from datetime import datetime

from .combat_calculator import CombatCalculator, CombatStats, EquipmentBonus


@dataclass
class SpecialAttack:
    name: str
    energy_cost: int
    accuracy_multiplier: float
    damage_multiplier: float
    effects: List[str]
    max_hits: int = 1


@dataclass
class CombatStyle:
    name: str
    attack_type: str  # stab, slash, crush, ranged, magic
    attack_style: str  # accurate, aggressive, defensive, controlled, rapid
    experience: str  # attack, strength, defence, shared
    bonuses: Dict[str, int]


@dataclass
class CombatEntity:
    id: int
    name: str
    stats: CombatStats
    equipment: EquipmentBonus
    current_hp: int
    max_hp: int
    combat_level: int
    is_player: bool = False
    special_attack_energy: float = 100.0
    combat_style: Optional[CombatStyle] = None
    status_effects: Set[str] = None

    @property
    def is_alive(self) -> bool:
        return self.current_hp > 0


@dataclass
class CombatState:
    attacker: CombatEntity
    defender: CombatEntity
    start_time: datetime
    last_hit_time: datetime
    hits: List[Dict[str, any]]
    is_finished: bool = False
    winner: Optional[CombatEntity] = None
    is_special_attack: bool = False
    multi_combat: bool = False
    area_targets: List[CombatEntity] = None


@dataclass
class WeaponRequirement:
    attack_level: int = 1
    strength_level: int = 1
    ranged_level: int = 1
    magic_level: int = 1
    quest_requirements: List[str] = None


@dataclass
class WeaponStats:
    requirements: WeaponRequirement
    attack_speed: float
    weapon_type: str
    is_two_handed: bool = False
    can_poison: bool = False
    can_venom: bool = False


class CombatManager:
    def __init__(self):
        self.calculator = CombatCalculator()
        self.active_fights: Dict[int, CombatState] = {}

        # Define weapon combat styles
        self.weapon_styles = {
            "sword": [
                CombatStyle("Chop", "slash", "accurate", "attack", {"attack": 3}),
                CombatStyle("Slash", "slash", "aggressive", "strength", {"strength": 3}),
                CombatStyle("Block", "slash", "defensive", "defence", {"defence": 3}),
            ],
            "scimitar": [
                CombatStyle("Slash", "slash", "accurate", "attack", {"attack": 3}),
                CombatStyle("Lunge", "stab", "aggressive", "strength", {"strength": 3}),
                CombatStyle("Block", "slash", "defensive", "defence", {"defence": 3}),
            ],
            "battleaxe": [
                CombatStyle("Chop", "slash", "accurate", "attack", {"attack": 3}),
                CombatStyle("Hack", "slash", "aggressive", "strength", {"strength": 3}),
                CombatStyle("Smash", "crush", "aggressive", "strength", {"strength": 3}),
                CombatStyle("Block", "slash", "defensive", "defence", {"defence": 3}),
            ],
            "bow": [
                CombatStyle("Accurate", "ranged", "accurate", "ranged", {"ranged": 3}),
                CombatStyle("Rapid", "ranged", "rapid", "ranged", {"ranged": 1}),
                CombatStyle(
                    "Longrange", "ranged", "longrange", "shared", {"ranged": 1, "defence": 2}
                ),
            ],
        }

        # Define special attacks
        self.special_attacks = {
            "dragon_dagger": SpecialAttack(
                name="Dragon Dagger Spec",
                energy_cost=25,
                accuracy_multiplier=1.15,
                damage_multiplier=1.15,
                effects=[],
                max_hits=2,
            ),
            "granite_maul": SpecialAttack(
                name="Granite Maul Spec",
                energy_cost=50,
                accuracy_multiplier=1.0,
                damage_multiplier=1.1,
                effects=["instant"],
                max_hits=1,
            ),
            "dragon_claws": SpecialAttack(
                name="Dragon Claws Spec",
                energy_cost=50,
                accuracy_multiplier=1.25,
                damage_multiplier=1.0,
                effects=["decreasing"],
                max_hits=4,
            ),
        }

        # Define weapon stats
        self.weapon_stats = {
            "bronze_sword": WeaponStats(
                requirements=WeaponRequirement(attack_level=1),
                attack_speed=2.4,
                weapon_type="sword",
            ),
            "rune_scimitar": WeaponStats(
                requirements=WeaponRequirement(attack_level=40),
                attack_speed=2.4,
                weapon_type="scimitar",
            ),
            "dragon_dagger": WeaponStats(
                requirements=WeaponRequirement(attack_level=60, quest_requirements=["Lost City"]),
                attack_speed=2.4,
                weapon_type="dagger",
                can_poison=True,
            ),
            "abyssal_whip": WeaponStats(
                requirements=WeaponRequirement(attack_level=70),
                attack_speed=2.4,
                weapon_type="whip",
            ),
            "toxic_blowpipe": WeaponStats(
                requirements=WeaponRequirement(ranged_level=75),
                attack_speed=1.8,
                weapon_type="dart",
                can_venom=True,
            ),
        }

        # Enhanced status effects
        self.status_effects = {
            "poison": {
                "damage": 2,
                "tick_rate": 18,  # Ticks between damage
                "duration": -1,  # -1 for infinite until cured
                "stacks": False,
            },
            "venom": {
                "damage": 6,
                "tick_rate": 18,
                "duration": -1,
                "stacks": True,
                "stack_increase": 2,
            },
            "frozen": {
                "duration": 20,  # Ticks
                "can_attack": True,
                "can_move": False,
                "immune_duration": 30,  # Ticks of immunity after effect ends
            },
            "stunned": {
                "duration": 3,
                "can_attack": False,
                "can_move": False,
                "immune_duration": 10,
            },
            "berserker": {"damage_multiplier": 1.2, "defence_multiplier": 0.8, "duration": 30},
        }

        # Critical hit system
        self.critical_hit = {
            "base_chance": 0.05,  # 5% base chance
            "damage_multiplier": 1.5,
            "accuracy_bonus": 1.2,
        }

    async def start_combat(
        self, attacker: CombatEntity, defender: CombatEntity, multi_combat: bool = False
    ) -> CombatState:
        """Start a new combat encounter between two entities."""
        now = datetime.utcnow()
        state = CombatState(
            attacker=attacker,
            defender=defender,
            start_time=now,
            last_hit_time=now,
            hits=[],
            multi_combat=multi_combat,
            area_targets=[] if not multi_combat else [defender],
        )

        # Store the combat state
        fight_id = hash((attacker.id, defender.id, now.timestamp()))
        self.active_fights[fight_id] = state

        return state

    def calculate_hit(
        self, attacker: CombatEntity, defender: CombatEntity, is_special: bool = False
    ) -> Tuple[bool, int, bool]:  # Returns (hit_lands, damage, is_critical)
        """Calculate if a hit lands and its damage."""
        # Get combat style bonuses
        style_bonuses = {}
        if attacker.combat_style:
            style_bonuses = attacker.combat_style.bonuses

        # Check for critical hit
        is_critical = random.random() < self.critical_hit["base_chance"]
        crit_multiplier = self.critical_hit["damage_multiplier"] if is_critical else 1.0
        accuracy_bonus = self.critical_hit["accuracy_bonus"] if is_critical else 1.0

        # Get special attack multipliers
        accuracy_multiplier = 1.0
        damage_multiplier = 1.0
        if is_special:
            weapon_name = "dragon_dagger"  # TODO: Get from equipment
            if weapon_name in self.special_attacks:
                special = self.special_attacks[weapon_name]
                accuracy_multiplier = special.accuracy_multiplier
                damage_multiplier = special.damage_multiplier

        # Calculate accuracy with critical bonus
        attack_level = attacker.stats.attack + style_bonuses.get("attack", 0)
        attack_roll = self.calculator.calculate_accuracy(
            attack_level,
            attacker.equipment.attack_slash,
            prayer_bonus=1.0,
            other_bonus=accuracy_multiplier * accuracy_bonus,
        )

        defence_level = defender.stats.defence + style_bonuses.get("defence", 0)
        defence_roll = self.calculator.calculate_accuracy(
            defence_level, defender.equipment.defence_slash
        )

        hit_chance = self.calculator.calculate_hit_chance(attack_roll, defence_roll)

        # Determine if hit lands
        hit_lands = random.random() < hit_chance

        if not hit_lands:
            return False, 0, False

        # Calculate damage with critical multiplier
        strength_level = attacker.stats.strength + style_bonuses.get("strength", 0)
        max_hit = self.calculator.calculate_max_hit(
            strength_level,
            attacker.equipment.melee_strength,
            other_bonus=damage_multiplier * crit_multiplier,
        )

        damage = random.randint(0, max_hit)

        # Apply status effects
        if attacker.status_effects:
            for effect in attacker.status_effects:
                if effect in self.status_effects:
                    effect_data = self.status_effects[effect]
                    if "damage_multiplier" in effect_data:
                        damage = int(damage * effect_data["damage_multiplier"])

        # Apply weapon effects
        weapon_name = "dragon_dagger"  # TODO: Get from equipment
        if weapon_name in self.weapon_stats:
            weapon = self.weapon_stats[weapon_name]
            if weapon.can_poison and random.random() < 0.25:  # 25% chance to poison
                if "poison" not in defender.status_effects:
                    defender.status_effects.add("poison")
            if weapon.can_venom and random.random() < 0.25:
                if "venom" not in defender.status_effects:
                    defender.status_effects.add("venom")

        return hit_lands, damage, is_critical

    async def process_combat_tick(self, state: CombatState) -> Optional[CombatEntity]:
        """Process one tick of combat, returns winner if combat is finished."""
        if state.is_finished:
            return state.winner

        # Handle special attacks
        is_special = False
        if state.is_special_attack:
            weapon_name = "dragon_dagger"  # TODO: Get from equipment
            if weapon_name in self.special_attacks:
                special = self.special_attacks[weapon_name]
                if state.attacker.special_attack_energy >= special.energy_cost:
                    is_special = True
                    state.attacker.special_attack_energy -= special.energy_cost

                    # Handle multi-hit special attacks
                    for _ in range(special.max_hits):
                        hit_lands, damage, is_critical = self.calculate_hit(
                            state.attacker, state.defender, is_special=True
                        )

                        # Record hit
                        hit_data = {
                            "attacker": state.attacker.name,
                            "defender": state.defender.name,
                            "hit_lands": hit_lands,
                            "damage": damage,
                            "is_special": True,
                            "is_critical": is_critical,
                            "time": datetime.utcnow(),
                        }
                        state.hits.append(hit_data)

                        # Apply damage
                        if hit_lands:
                            state.defender.current_hp = max(0, state.defender.current_hp - damage)

                            # Check if combat is finished
                            if not state.defender.is_alive:
                                state.is_finished = True
                                state.winner = state.attacker
                                return state.winner

                    state.is_special_attack = False
                    return None

        # Normal attack
        hit_lands, damage, is_critical = self.calculate_hit(
            state.attacker, state.defender, is_special=is_special
        )

        # Record hit
        hit_data = {
            "attacker": state.attacker.name,
            "defender": state.defender.name,
            "hit_lands": hit_lands,
            "damage": damage,
            "is_special": is_special,
            "is_critical": is_critical,
            "time": datetime.utcnow(),
        }
        state.hits.append(hit_data)

        # Apply damage
        if hit_lands:
            state.defender.current_hp = max(0, state.defender.current_hp - damage)

            # Check if combat is finished
            if not state.defender.is_alive:
                state.is_finished = True
                state.winner = state.attacker
                return state.winner

            # Handle multi-combat
            if state.multi_combat and state.area_targets:
                splash_damage = int(damage * 0.5)
                for target in state.area_targets:
                    if target != state.defender and target.is_alive:
                        target.current_hp = max(0, target.current_hp - splash_damage)
                        state.hits.append(
                            {
                                "attacker": state.attacker.name,
                                "defender": target.name,
                                "hit_lands": True,
                                "damage": splash_damage,
                                "is_special": False,
                                "is_splash": True,
                                "time": datetime.utcnow(),
                            }
                        )

        # Swap attacker and defender
        state.attacker, state.defender = state.defender, state.attacker
        state.last_hit_time = datetime.utcnow()

        # Regenerate special attack energy
        if state.attacker.is_player:
            state.attacker.special_attack_energy = min(
                100.0, state.attacker.special_attack_energy + 10
            )

        return None

    async def run_combat(self, state: CombatState, tick_duration: float = 1.8) -> CombatEntity:
        """Run combat until one entity dies."""
        while not state.is_finished:
            winner = await self.process_combat_tick(state)
            if winner:
                return winner
            await asyncio.sleep(tick_duration)

        return state.winner

    def get_combat_log(self, state: CombatState) -> List[str]:
        """Generate a readable combat log from the combat state."""
        log = []
        for hit in state.hits:
            if hit.get("is_special"):
                if hit["hit_lands"]:
                    log.append(
                        f"{hit['attacker']} hits {hit['defender']} with a special "
                        f"attack for {hit['damage']} damage!"
                    )
                else:
                    log.append(f"{hit['attacker']} misses {hit['defender']} with a special attack!")
            elif hit.get("is_splash"):
                log.append(
                    f"{hit['attacker']}'s attack splashes onto {hit['defender']} "
                    f"for {hit['damage']} damage!"
                )
            else:
                if hit["hit_lands"]:
                    log.append(
                        f"{hit['attacker']} hits {hit['defender']} for {hit['damage']} damage!"
                    )
                else:
                    log.append(f"{hit['attacker']} misses {hit['defender']}!")
        return log

    def process_status_effects(self, entity: CombatEntity, ticks: int = 1):
        """Process status effects on an entity."""
        if not entity.status_effects:
            return

        for effect in list(entity.status_effects):
            effect_data = self.status_effects.get(effect)
            if not effect_data:
                continue

            # Handle damage over time effects
            if "damage" in effect_data and "tick_rate" in effect_data:
                if ticks % effect_data["tick_rate"] == 0:
                    damage = effect_data["damage"]
                    if effect == "venom" and effect_data["stacks"]:
                        # Increase venom damage
                        damage += effect_data["stack_increase"]
                    entity.current_hp = max(0, entity.current_hp - damage)

            # Handle effect duration
            if effect_data["duration"] > 0:
                effect_data["duration"] -= ticks
                if effect_data["duration"] <= 0:
                    entity.status_effects.remove(effect)
                    # Add immunity if specified
                    if "immune_duration" in effect_data:
                        entity.status_effects.add(f"{effect}_immune")
                        effect_data["immune_duration"] = effect_data["immune_duration"]
