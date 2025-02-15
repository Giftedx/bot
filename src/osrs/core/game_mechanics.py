"""Core game mechanics for OSRS."""
from typing import Dict, Optional, Tuple
import math
import random

class GameMechanics:
    """Handles core OSRS game mechanics."""
    
    @staticmethod
    def xp_for_level(level: int) -> int:
        """Calculate XP required for a specific level."""
        if level < 1:
            return 0
        return int(sum(math.floor(i + 300 * (2 ** (i / 7))) for i in range(1, level)) / 4)

    @staticmethod
    def level_for_xp(xp: int) -> int:
        """Calculate level for a given amount of XP."""
        if xp < 0:
            return 1
            
        level = 1
        while GameMechanics.xp_for_level(level + 1) <= xp:
            level += 1
        return level

    @staticmethod
    def calculate_combat_level(stats: Dict[str, int]) -> int:
        """Calculate combat level based on combat stats."""
        base = 0.25 * (stats.get('defence', 1) + stats.get('hitpoints', 10) + math.floor(stats.get('prayer', 1) / 2))
        
        melee = 0.325 * (stats.get('attack', 1) + stats.get('strength', 1))
        ranged = 0.325 * (stats.get('ranged', 1) * 1.5)
        magic = 0.325 * (stats.get('magic', 1) * 1.5)
        
        return math.floor(base + max(melee, ranged, magic))

    @staticmethod
    def calculate_max_hit(
        base_level: int,
        equipment_bonus: int,
        prayer_bonus: float = 1.0,
        other_bonus: float = 1.0,
        void_bonus: bool = False
    ) -> int:
        """Calculate maximum hit for a combat style."""
        effective_level = math.floor(base_level * prayer_bonus)
        if void_bonus:
            effective_level = math.floor(effective_level * 1.1)
            
        max_hit = math.floor(0.5 + effective_level * (equipment_bonus + 64) / 640)
        max_hit = math.floor(max_hit * other_bonus)
        
        return max_hit

    @staticmethod
    def calculate_accuracy(
        attack_level: int,
        equipment_bonus: int,
        target_defence: int,
        target_bonus: int,
        prayer_bonus: float = 1.0,
        void_bonus: bool = False
    ) -> float:
        """Calculate hit chance against target."""
        effective_attack = math.floor(attack_level * prayer_bonus)
        if void_bonus:
            effective_attack = math.floor(effective_attack * 1.1)
            
        attack_roll = effective_attack * (equipment_bonus + 64)
        defence_roll = target_defence * (target_bonus + 64)
        
        if attack_roll > defence_roll:
            return 1 - (defence_roll + 2) / (2 * (attack_roll + 1))
        else:
            return attack_roll / (2 * (defence_roll + 1))

    @staticmethod
    def calculate_damage_reduction(
        defence_level: int,
        equipment_bonus: int,
        prayer_bonus: float = 1.0
    ) -> float:
        """Calculate damage reduction from defence and equipment."""
        effective_defence = math.floor(defence_level * prayer_bonus)
        return min(0.95, (effective_defence * equipment_bonus) / 10000)

    @staticmethod
    def calculate_prayer_drain(
        points: int,
        prayer_bonus: int,
        active_prayers: Dict[str, float]
    ) -> float:
        """Calculate prayer point drain rate."""
        if not active_prayers:
            return 0.0
            
        total_drain = sum(drain for drain in active_prayers.values())
        drain_rate = total_drain * (1 - (prayer_bonus / 30))
        return max(0.1, drain_rate)

    @staticmethod
    def calculate_run_energy_drain(
        weight: float,
        agility_level: int
    ) -> float:
        """Calculate run energy drain rate."""
        base_drain = 0.67
        weight_factor = max(0, weight) * 0.025
        agility_bonus = agility_level * 0.01
        
        return max(0.1, base_drain + weight_factor - agility_bonus)

    @staticmethod
    def calculate_special_attack_damage(
        base_damage: int,
        spec_bonus: float,
        accuracy_modifier: float = 1.0,
        damage_modifier: float = 1.0
    ) -> Tuple[bool, int]:
        """Calculate special attack hit and damage."""
        accuracy_roll = random.random() * accuracy_modifier
        if accuracy_roll > spec_bonus:
            return False, 0
            
        damage = math.floor(base_damage * damage_modifier)
        return True, damage

    @staticmethod
    def calculate_skill_xp(
        base_xp: float,
        level: int,
        bonus_multiplier: float = 1.0
    ) -> int:
        """Calculate skill XP gain with bonuses."""
        level_scaling = 1 + (level / 100)  # Small bonus for higher levels
        xp = base_xp * level_scaling * bonus_multiplier
        return math.floor(xp)

    @staticmethod
    def calculate_drop_chance(
        base_chance: float,
        luck_bonus: float = 0,
        ring_of_wealth: bool = False
    ) -> float:
        """Calculate drop chance with modifiers."""
        chance = base_chance * (1 + luck_bonus)
        if ring_of_wealth:
            chance *= 1.1
        return min(1.0, chance)

    @staticmethod
    def calculate_resource_depletion(
        base_chance: float,
        skill_level: int,
        tool_bonus: float = 0
    ) -> float:
        """Calculate resource depletion chance."""
        level_bonus = skill_level * 0.01
        chance = base_chance * (1 - level_bonus - tool_bonus)
        return max(0.1, min(1.0, chance))

    @staticmethod
    def calculate_burn_chance(
        cooking_level: int,
        food_level: int,
        cooking_gauntlets: bool = False
    ) -> float:
        """Calculate chance to burn food."""
        level_diff = cooking_level - food_level
        base_chance = max(0, 60 - level_diff) / 100
        
        if cooking_gauntlets:
            base_chance *= 0.75
            
        return max(0, min(1.0, base_chance))

    @staticmethod
    def calculate_agility_success(
        agility_level: int,
        obstacle_level: int,
        graceful_bonus: bool = False
    ) -> float:
        """Calculate agility obstacle success chance."""
        level_diff = agility_level - obstacle_level
        base_chance = min(0.95, 0.5 + (level_diff * 0.03))
        
        if graceful_bonus:
            base_chance = min(0.95, base_chance * 1.1)
            
        return max(0.05, base_chance)

    @staticmethod
    def calculate_thieving_success(
        thieving_level: int,
        target_level: int,
        ardougne_bonus: bool = False
    ) -> float:
        """Calculate pickpocket success chance."""
        level_diff = thieving_level - target_level
        base_chance = min(0.95, 0.3 + (level_diff * 0.025))
        
        if ardougne_bonus:
            base_chance = min(0.95, base_chance * 1.1)
            
        return max(0.05, base_chance)

    @staticmethod
    def calculate_mining_speed(
        mining_level: int,
        rock_level: int,
        pickaxe_bonus: float
    ) -> float:
        """Calculate mining speed in ticks."""
        level_factor = 1 + ((mining_level - rock_level) * 0.01)
        base_ticks = max(1, 8 - math.floor(pickaxe_bonus))
        return max(1, base_ticks / level_factor)

    @staticmethod
    def calculate_woodcutting_speed(
        woodcutting_level: int,
        tree_level: int,
        axe_bonus: float
    ) -> float:
        """Calculate woodcutting speed in ticks."""
        level_factor = 1 + ((woodcutting_level - tree_level) * 0.01)
        base_ticks = max(1, 8 - math.floor(axe_bonus))
        return max(1, base_ticks / level_factor)

    @staticmethod
    def calculate_fishing_speed(
        fishing_level: int,
        fish_level: int,
        tool_bonus: float
    ) -> float:
        """Calculate fishing speed in ticks."""
        level_factor = 1 + ((fishing_level - fish_level) * 0.01)
        base_ticks = max(1, 5 - math.floor(tool_bonus))
        return max(1, base_ticks / level_factor) 