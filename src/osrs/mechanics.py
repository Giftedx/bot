from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set
import math

# Combat Styles
class CombatStyle(Enum):
    ACCURATE = "accurate"
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    CONTROLLED = "controlled"
    RAPID = "rapid"
    LONGRANGE = "longrange"

# Attack Types
class AttackType(Enum):
    STAB = "stab"
    SLASH = "slash"
    CRUSH = "crush"
    MAGIC = "magic"
    RANGED = "ranged"

@dataclass
class CombatStats:
    """OSRS combat stats using real formulas"""
    attack: int
    strength: int
    defence: int
    ranged: int
    magic: int
    hitpoints: int
    prayer: int
    
    def calculate_combat_level(self) -> int:
        """
        Calculate combat level using the actual OSRS formula
        """
        base = 0.25 * (defence + hitpoints + math.floor(prayer/2))
        melee = 0.325 * (attack + strength)
        range_level = 0.325 * (math.floor(ranged/2) + ranged)
        mage_level = 0.325 * (math.floor(magic/2) + magic)
        
        return math.floor(base + max(melee, range_level, mage_level))

@dataclass
class Equipment:
    """Equipment bonuses using real OSRS stats"""
    # Attack bonuses
    stab_attack: int = 0
    slash_attack: int = 0
    crush_attack: int = 0
    magic_attack: int = 0
    range_attack: int = 0
    
    # Defence bonuses
    stab_defence: int = 0
    slash_defence: int = 0
    crush_defence: int = 0
    magic_defence: int = 0
    range_defence: int = 0
    
    # Other bonuses
    melee_strength: int = 0
    ranged_strength: int = 0
    magic_strength: int = 0
    prayer: int = 0

class CombatFormulas:
    """
    Actual OSRS combat formulas for accuracy and damage
    """
    @staticmethod
    def calculate_max_hit(base_level: int, effective_level: int, strength_bonus: int, void_bonus: float = 1.0) -> int:
        """
        Calculate maximum hit using OSRS formula
        base_level: Base strength/ranged level
        effective_level: Level after prayers/potions
        strength_bonus: Equipment strength bonus
        void_bonus: Void armor bonus if applicable
        """
        a = effective_level * (strength_bonus + 64)
        b = math.floor(a / 640)
        return math.floor(b * void_bonus)
    
    @staticmethod
    def calculate_accuracy_roll(attack_level: int, equipment_bonus: int) -> int:
        """
        Calculate accuracy roll using OSRS formula
        """
        return attack_level * (equipment_bonus + 64)
    
    @staticmethod
    def calculate_defence_roll(defence_level: int, equipment_bonus: int) -> int:
        """
        Calculate defence roll using OSRS formula
        """
        return defence_level * (equipment_bonus + 64)
    
    @staticmethod
    def calculate_hit_chance(attack_roll: int, defence_roll: int) -> float:
        """
        Calculate hit chance using OSRS formula
        """
        if attack_roll > defence_roll:
            return 1 - (defence_roll + 2) / (2 * (attack_roll + 1))
        return attack_roll / (2 * (defence_roll + 1))

class PrayerMultipliers:
    """
    Actual OSRS prayer multipliers
    """
    ATTACK_PRAYERS = {
        "Clarity of Thought": 1.05,
        "Improved Reflexes": 1.10,
        "Incredible Reflexes": 1.15,
        "Chivalry": 1.15,
        "Piety": 1.20
    }
    
    STRENGTH_PRAYERS = {
        "Burst of Strength": 1.05,
        "Superhuman Strength": 1.10,
        "Ultimate Strength": 1.15,
        "Chivalry": 1.18,
        "Piety": 1.23
    }
    
    DEFENCE_PRAYERS = {
        "Thick Skin": 1.05,
        "Rock Skin": 1.10,
        "Steel Skin": 1.15,
        "Chivalry": 1.20,
        "Piety": 1.25
    }
    
    RANGED_PRAYERS = {
        "Sharp Eye": 1.05,
        "Hawk Eye": 1.10,
        "Eagle Eye": 1.15,
        "Rigour": 1.20
    }
    
    MAGIC_PRAYERS = {
        "Mystic Will": 1.05,
        "Mystic Lore": 1.10,
        "Mystic Might": 1.15,
        "Augury": 1.25
    }

@dataclass
class ExperienceTable:
    """
    OSRS experience table and calculations
    """
    @staticmethod
    def level_to_xp(level: int) -> int:
        """Convert level to total XP required"""
        total = 0
        for i in range(1, level):
            total += math.floor(i + 300 * 2 ** (i / 7))
        return math.floor(total / 4)
    
    @staticmethod
    def xp_to_level(xp: int) -> int:
        """Convert XP to level"""
        level = 1
        while ExperienceTable.level_to_xp(level + 1) <= xp:
            level += 1
        return level

class DropRates:
    """
    Actual OSRS drop rates and calculations
    """
    @staticmethod
    def calculate_drop_chance(base_chance: int, ring_of_wealth: bool = False) -> float:
        """
        Calculate drop chance with Ring of Wealth modifier
        """
        if ring_of_wealth:
            # RoW removes empty drops from rare drop table
            return base_chance * 1.01
        return base_chance
    
    @staticmethod
    def calculate_pet_chance(base_chance: int, kc: int) -> float:
        """
        Calculate pet chance using OSRS formula
        threshold: Number of kills that halves the pet rate
        """
        threshold = 3000  # Standard threshold for most bosses
        threshold_reductions = kc // threshold
        if threshold_reductions == 0:
            return 1/base_chance
        
        modified_rate = base_chance
        for _ in range(threshold_reductions):
            modified_rate = modified_rate // 2
        return 1/modified_rate

@dataclass
class AgilityCourse:
    """
    OSRS Agility course with real XP rates and requirements
    """
    name: str
    level_required: int
    obstacles: List[Tuple[str, float]]  # (obstacle_name, xp)
    lap_bonus: float
    mark_of_grace_chance: float
    
    def calculate_lap_xp(self) -> float:
        """Calculate total XP for completing a lap"""
        return sum(xp for _, xp in self.obstacles) + self.lap_bonus

# Real OSRS Agility Courses
AGILITY_COURSES = {
    "Gnome Stronghold": AgilityCourse(
        name="Gnome Stronghold",
        level_required=1,
        obstacles=[
            ("Log balance", 7.5),
            ("Obstacle net", 7.5),
            ("Tree branch", 5.0),
            ("Balancing rope", 7.5),
            ("Tree branch", 5.0),
            ("Obstacle net", 7.5),
            ("Pipes", 7.5)
        ],
        lap_bonus=39.0,
        mark_of_grace_chance=0
    ),
    "Draynor Village": AgilityCourse(
        name="Draynor Village",
        level_required=10,
        obstacles=[
            ("Rough wall", 8.0),
            ("Tightrope", 7.5),
            ("Tightrope", 7.5),
            ("Narrow wall", 7.5),
            ("Wall", 7.5),
            ("Gap", 7.5),
            ("Crate", 8.0)
        ],
        lap_bonus=120.0,
        mark_of_grace_chance=0.1
    ),
    # Add more courses as needed
}

# Real OSRS Agility Courses
AGILITY_COURSES.update({
    "Al Kharid": AgilityCourse(
        name="Al Kharid",
        level_required=20,
        obstacles=[
            ("Rough wall", 10.0),
            ("Tightrope", 30.0),
            ("Cable", 40.0),
            ("Zip line", 40.0),
            ("Tropical tree", 10.0),
            ("Roof top beams", 15.0),
            ("Tightrope", 15.0),
            ("Gap", 15.0)
        ],
        lap_bonus=180.0,
        mark_of_grace_chance=0.12
    ),
    "Varrock": AgilityCourse(
        name="Varrock",
        level_required=30,
        obstacles=[
            ("Rough wall", 15.0),
            ("Clothes line", 20.0),
            ("Gap", 30.0),
            ("Wall", 35.0),
            ("Gap", 30.0),
            ("Gap", 30.0),
            ("Gap", 30.0),
            ("Ledge", 25.0),
            ("Edge", 23.0)
        ],
        lap_bonus=238.0,
        mark_of_grace_chance=0.15
    ),
    "Canifis": AgilityCourse(
        name="Canifis",
        level_required=40,
        obstacles=[
            ("Tall tree", 45.0),
            ("Gap", 20.0),
            ("Gap", 40.0),
            ("Gap", 40.0),
            ("Gap", 40.0),
            ("Pole-vault", 40.0),
            ("Gap", 40.0),
            ("Gap", 40.0)
        ],
        lap_bonus=240.0,
        mark_of_grace_chance=0.20
    ),
    "Seers Village": AgilityCourse(
        name="Seers Village",
        level_required=60,
        obstacles=[
            ("Wall", 20.0),
            ("Gap", 60.0),
            ("Tightrope", 50.0),
            ("Gap", 55.0),
            ("Gap", 55.0),
            ("Edge", 55.0)
        ],
        lap_bonus=570.0,
        mark_of_grace_chance=0.25
    ),
    "Pollnivneach": AgilityCourse(
        name="Pollnivneach",
        level_required=70,
        obstacles=[
            ("Basket", 40.0),
            ("Market stall", 50.0),
            ("Banner", 50.0),
            ("Gap", 60.0),
            ("Tree", 50.0),
            ("Rough wall", 50.0),
            ("Monkeybars", 60.0),
            ("Tree", 50.0),
            ("Drying line", 50.0)
        ],
        lap_bonus=890.0,
        mark_of_grace_chance=0.28
    ),
    "Rellekka": AgilityCourse(
        name="Rellekka",
        level_required=80,
        obstacles=[
            ("Rough wall", 95.0),
            ("Gap", 75.0),
            ("Tightrope", 80.0),
            ("Gap", 85.0),
            ("Gap", 85.0),
            ("Tightrope", 85.0),
            ("Pile of fish", 95.0)
        ],
        lap_bonus=780.0,
        mark_of_grace_chance=0.30
    ),
    "Ardougne": AgilityCourse(
        name="Ardougne",
        level_required=90,
        obstacles=[
            ("Wooden beams", 100.0),
            ("Gap", 100.0),
            ("Plank", 100.0),
            ("Gap", 100.0),
            ("Gap", 100.0),
            ("Steep roof", 100.0),
            ("Gap", 100.0)
        ],
        lap_bonus=1320.0,
        mark_of_grace_chance=0.35
    )
})

# Real OSRS run energy restoration
def calculate_run_energy_restore(agility_level: int) -> float:
    """
    Calculate run energy restoration rate per tick
    Higher agility = faster restoration
    """
    return 0.096 + (agility_level * 0.00448)

# Add real OSRS run energy drain rates
def calculate_run_energy_drain(weight: float, agility_level: int) -> float:
    """
    Calculate run energy drain per tick
    Based on weight and agility level
    """
    base_drain = 0.67
    weight_factor = max(0, weight - 64) * 0.0035
    agility_reduction = min(0.5, agility_level * 0.0065)
    
    return base_drain * (1 + weight_factor) * (1 - agility_reduction)

class PotionBoosts:
    """
    Real OSRS potion boost formulas and values
    """
    COMBAT_POTIONS = {
        "Super combat": {
            "attack": lambda level: math.floor(level * 0.15) + 5,
            "strength": lambda level: math.floor(level * 0.15) + 5,
            "defence": lambda level: math.floor(level * 0.15) + 5
        },
        "Super attack": {
            "attack": lambda level: math.floor(level * 0.15) + 5
        },
        "Super strength": {
            "strength": lambda level: math.floor(level * 0.15) + 5
        },
        "Super defence": {
            "defence": lambda level: math.floor(level * 0.15) + 5
        },
        "Combat": {
            "attack": lambda level: math.floor(level * 0.10) + 3,
            "strength": lambda level: math.floor(level * 0.10) + 3
        },
        "Zamorak brew": {
            "attack": lambda level: math.floor(level * 0.20) + 2,
            "strength": lambda level: math.floor(level * 0.12) + 2,
            "defence": lambda level: -math.floor(level * 0.10) - 2,
            "hitpoints": lambda level: -math.floor(level * 0.10)
        }
    }

    RANGED_POTIONS = {
        "Ranging": {
            "ranged": lambda level: math.floor(level * 0.10) + 4
        },
        "Bastion": {
            "ranged": lambda level: math.floor(level * 0.10) + 4,
            "defence": lambda level: math.floor(level * 0.15) + 5
        }
    }

    MAGIC_POTIONS = {
        "Magic": {
            "magic": lambda level: math.floor(level * 0.10) + 4
        },
        "Battlemage": {
            "magic": lambda level: math.floor(level * 0.10) + 4,
            "defence": lambda level: math.floor(level * 0.15) + 5
        },
        "Imbued heart": {
            "magic": lambda level: math.floor(level * 0.10) + 1
        }
    }

    RESTORE_POTIONS = {
        "Super restore": {
            "all": lambda level: math.floor(level * 0.25) + 8,
            "prayer": lambda level: math.floor(level * 0.25) + 8
        },
        "Prayer": {
            "prayer": lambda level: math.floor(level * 0.25) + 7
        }
    }

class SpecialAttacks:
    """
    Real OSRS special attack effects and calculations
    """
    SPECIAL_ATTACKS = {
        "Dragon dagger": {
            "drain": 25,
            "hits": 2,
            "accuracy_multiplier": 1.15,
            "damage_multiplier": 1.15,
            "effect": None
        },
        "Abyssal whip": {
            "drain": 50,
            "hits": 1,
            "accuracy_multiplier": 1.25,
            "damage_multiplier": 1.0,
            "effect": "drain_run"
        },
        "Armadyl godsword": {
            "drain": 50,
            "hits": 1,
            "accuracy_multiplier": 2.0,
            "damage_multiplier": 1.375,
            "effect": None
        },
        "Dragon claws": {
            "drain": 50,
            "hits": 4,
            "accuracy_multiplier": 1.0,
            "damage_multiplier": [1.0, 0.5, 0.25, 0.25],
            "effect": "guaranteed_hits"
        },
        "Granite maul": {
            "drain": 50,
            "hits": 1,
            "accuracy_multiplier": 1.0,
            "damage_multiplier": 1.0,
            "effect": "instant_hit"
        },
        "Toxic blowpipe": {
            "drain": 50,
            "hits": 1,
            "accuracy_multiplier": 2.0,
            "damage_multiplier": 1.5,
            "effect": "heal"
        }
    }

    @staticmethod
    def calculate_special_damage(base_damage: int, spec_weapon: str, hit_number: int = 0) -> int:
        """Calculate special attack damage"""
        spec = SpecialAttacks.SPECIAL_ATTACKS[spec_weapon]
        if isinstance(spec["damage_multiplier"], list):
            multiplier = spec["damage_multiplier"][hit_number]
        else:
            multiplier = spec["damage_multiplier"]
        return math.floor(base_damage * multiplier)

    @staticmethod
    def calculate_special_accuracy(base_accuracy: float, spec_weapon: str) -> float:
        """Calculate special attack accuracy"""
        return base_accuracy * SpecialAttacks.SPECIAL_ATTACKS[spec_weapon]["accuracy_multiplier"]

class BarrowsSystem:
    """
    Real OSRS Barrows mechanics and calculations
    """
    BROTHERS = {
        "Ahrim": {
            "combat_level": 98,
            "hitpoints": 100,
            "max_hit": 25,
            "attack_style": "magic",
            "weakness": "ranged",
            "special": "Magic damage reduction effect"
        },
        "Dharok": {
            "combat_level": 115,
            "hitpoints": 100,
            "max_hit": 57,  # Can be higher with lower HP
            "attack_style": "melee",
            "weakness": "magic",
            "special": "Lower HP = higher max hit"
        },
        "Guthan": {
            "combat_level": 115,
            "hitpoints": 100,
            "max_hit": 24,
            "attack_style": "melee",
            "weakness": "magic",
            "special": "Heal for damage dealt"
        },
        "Karil": {
            "combat_level": 98,
            "hitpoints": 100,
            "max_hit": 20,
            "attack_style": "ranged",
            "weakness": "melee",
            "special": "Agility level reduction"
        },
        "Torag": {
            "combat_level": 115,
            "hitpoints": 100,
            "max_hit": 23,
            "attack_style": "melee",
            "weakness": "magic",
            "special": "Run energy reduction"
        },
        "Verac": {
            "combat_level": 115,
            "hitpoints": 100,
            "max_hit": 23,
            "attack_style": "melee",
            "weakness": "magic",
            "special": "Hit through prayer"
        }
    }

    REWARDS = {
        "Ahrim's hood": {"rarity": 1/392, "set": "Ahrim"},
        "Ahrim's staff": {"rarity": 1/392, "set": "Ahrim"},
        "Ahrim's robetop": {"rarity": 1/392, "set": "Ahrim"},
        "Ahrim's robeskirt": {"rarity": 1/392, "set": "Ahrim"},
        "Dharok's helm": {"rarity": 1/392, "set": "Dharok"},
        "Dharok's greataxe": {"rarity": 1/392, "set": "Dharok"},
        "Dharok's platebody": {"rarity": 1/392, "set": "Dharok"},
        "Dharok's platelegs": {"rarity": 1/392, "set": "Dharok"}
        # ... other items
    }

    @staticmethod
    def calculate_reward_potential(brothers_killed: int, monsters_killed: int) -> float:
        """Calculate reward potential percentage"""
        brother_points = brothers_killed * 2.5
        monster_points = min(monsters_killed * 0.1, 1.0)
        return min(100.0, brother_points + monster_points)

    @staticmethod
    def calculate_dharok_max_hit(base_max: int, current_hp: int, max_hp: int) -> int:
        """Calculate Dharok's max hit based on missing HP"""
        hp_modifier = (max_hp - current_hp) / 100
        return math.floor(base_max * (1 + hp_modifier))

class GodwarsDungeon:
    """
    Real OSRS God Wars Dungeon mechanics
    """
    BOSSES = {
        "General Graardor": {
            "combat_level": 624,
            "hitpoints": 255,
            "max_hit": 60,
            "attack_styles": ["melee", "ranged"],
            "minions": [
                "Sergeant Strongstack",
                "Sergeant Steelwill",
                "Sergeant Grimspike"
            ],
            "weakness": "stab",
            "killcount": 40,
            "respawn_time": 90  # seconds
        },
        "Commander Zilyana": {
            "combat_level": 596,
            "hitpoints": 255,
            "max_hit": 31,
            "attack_styles": ["melee", "magic"],
            "minions": [
                "Starlight",
                "Bree",
                "Growler"
            ],
            "weakness": "ranged",
            "killcount": 40,
            "respawn_time": 90
        },
        "Kree'arra": {
            "combat_level": 580,
            "hitpoints": 255,
            "max_hit": 71,
            "attack_styles": ["ranged", "magic"],
            "minions": [
                "Flight Kilisa",
                "Wingman Skree",
                "Flockleader Geerin"
            ],
            "weakness": "crossbow",
            "killcount": 40,
            "respawn_time": 90
        },
        "K'ril Tsutsaroth": {
            "combat_level": 650,
            "hitpoints": 255,
            "max_hit": 47,
            "attack_styles": ["melee", "magic"],
            "minions": [
                "Balfrug Kreeyath",
                "Tstanon Karlak",
                "Zakl'n Gritch"
            ],
            "weakness": "slash",
            "killcount": 40,
            "respawn_time": 90
        }
    }

    UNIQUE_DROPS = {
        "General Graardor": {
            "Bandos chestplate": 1/381,
            "Bandos tassets": 1/381,
            "Bandos boots": 1/381,
            "Bandos hilt": 1/508
        },
        "Commander Zilyana": {
            "Saradomin sword": 1/508,
            "Armadyl crossbow": 1/508,
            "Saradomin hilt": 1/508
        },
        "Kree'arra": {
            "Armadyl helmet": 1/381,
            "Armadyl chestplate": 1/381,
            "Armadyl chainskirt": 1/381,
            "Armadyl hilt": 1/508
        },
        "K'ril Tsutsaroth": {
            "Zamorak spear": 1/508,
            "Staff of the dead": 1/508,
            "Zamorak hilt": 1/508
        }
    }

    @staticmethod
    def calculate_killcount_chance(kc: int, item_rate: float) -> float:
        """Calculate chance of getting a drop by specific KC"""
        return 1 - (1 - item_rate) ** kc

# Add more Slayer masters
SlayerSystem.MASTERS.update({
    "Vannaka": {
        "level_required": 40,
        "tasks": {
            "Aberrant Spectres": {"weight": 7, "min": 60, "max": 120},
            "Ankou": {"weight": 7, "min": 50, "max": 90},
            "Bloodveld": {"weight": 8, "min": 60, "max": 120},
            "Brine Rats": {"weight": 7, "min": 50, "max": 100},
            "Cave Crawlers": {"weight": 8, "min": 60, "max": 120},
            "Cave Slimes": {"weight": 8, "min": 60, "max": 120},
            "Crawling Hands": {"weight": 8, "min": 60, "max": 120},
            "Dust Devils": {"weight": 7, "min": 60, "max": 120},
            "Earth Warriors": {"weight": 7, "min": 60, "max": 120},
            "Ghouls": {"weight": 7, "min": 60, "max": 120},
            "Green Dragons": {"weight": 7, "min": 30, "max": 70},
            "Jellies": {"weight": 7, "min": 60, "max": 120},
            "Lesser Demons": {"weight": 8, "min": 60, "max": 120},
            "Moss Giants": {"weight": 7, "min": 60, "max": 120},
            "Pyrefiends": {"weight": 8, "min": 60, "max": 120},
            "Wall Beasts": {"weight": 7, "min": 60, "max": 120}
        }
    },
    "Chaeldar": {
        "level_required": 70,
        "tasks": {
            "Aberrant Spectres": {"weight": 8, "min": 110, "max": 170},
            "Abyssal Demons": {"weight": 6, "min": 110, "max": 170},
            "Baby Blue Dragons": {"weight": 7, "min": 110, "max": 170},
            "Basilisks": {"weight": 7, "min": 110, "max": 170},
            "Black Demons": {"weight": 8, "min": 110, "max": 170},
            "Bloodveld": {"weight": 8, "min": 110, "max": 170},
            "Blue Dragons": {"weight": 7, "min": 110, "max": 170},
            "Bronze Dragons": {"weight": 7, "min": 30, "max": 50},
            "Cave Horrors": {"weight": 7, "min": 110, "max": 170},
            "Dust Devils": {"weight": 7, "min": 110, "max": 170},
            "Fire Giants": {"weight": 8, "min": 110, "max": 170},
            "Gargoyles": {"weight": 7, "min": 110, "max": 170},
            "Greater Demons": {"weight": 8, "min": 110, "max": 170},
            "Iron Dragons": {"weight": 5, "min": 30, "max": 50},
            "Jellies": {"weight": 7, "min": 110, "max": 170},
            "Kurask": {"weight": 7, "min": 110, "max": 170},
            "Nechryael": {"weight": 7, "min": 110, "max": 170},
            "Steel Dragons": {"weight": 5, "min": 30, "max": 50},
            "Turoth": {"weight": 7, "min": 110, "max": 170}
        }
    }
})

# Add more superior monsters
SuperiorSlayer.SUPERIOR_MONSTERS.update({
    "Nechryael": {
        "superior": "Nechryarch",
        "chance": 0.008,
        "combat_level": 200,
        "base_hp": 450,
        "max_hit": 30,
        "xp_multiplier": 3.5
    },
    "Gargoyle": {
        "superior": "Marble Gargoyle",
        "chance": 0.008,
        "combat_level": 180,
        "base_hp": 400,
        "max_hit": 28,
        "xp_multiplier": 3.5
    },
    "Kurask": {
        "superior": "King Kurask",
        "chance": 0.008,
        "combat_level": 170,
        "base_hp": 420,
        "max_hit": 24,
        "xp_multiplier": 3.5
    }
})

class Zulrah:
    """
    Real OSRS Zulrah mechanics and phases
    """
    PHASES = {
        "Green": {
            "combat_level": 725,
            "hitpoints": 500,
            "max_hit": 41,
            "attack_style": "ranged",
            "weakness": "none",
            "protection": None,
            "special": "Toxic clouds, Snakelings"
        },
        "Red": {
            "combat_level": 725,
            "hitpoints": 500,
            "max_hit": 46,
            "attack_style": "melee",
            "weakness": "none",
            "protection": "melee",
            "special": "Fire breath"
        },
        "Blue": {
            "combat_level": 725,
            "hitpoints": 500,
            "max_hit": 41,
            "attack_style": "magic",
            "weakness": "none",
            "protection": "magic",
            "special": "Toxic clouds"
        },
        "Jad": {
            "combat_level": 725,
            "hitpoints": 500,
            "max_hit": 46,
            "attack_styles": ["magic", "ranged"],
            "weakness": "none",
            "protection": None,
            "special": "Prayer switching required"
        }
    }

    UNIQUE_DROPS = {
        "Tanzanite fang": 1/512,
        "Magic fang": 1/512,
        "Serpentine visage": 1/512,
        "Uncut onyx": 1/512,
        "Pet snakeling": 1/4000
    }

    ROTATIONS = {
        "Rotation 1": [
            ("Green", "East", None),
            ("Blue", "South", "magic"),
            ("Red", "North", "melee"),
            ("Green", "West", None),
            ("Blue", "South", "magic"),
            ("Green", "East", None),
            ("Red", "North", "melee"),
            ("Jad", "West", None),
            ("Green", "East", None)
        ],
        # Add more rotations...
    }

    @staticmethod
    def calculate_kill_time(dps: float) -> float:
        """Calculate average kill time based on DPS"""
        total_hp = 500  # HP per phase
        phases = 9  # Average number of phases
        return (total_hp * phases) / dps

    @staticmethod
    def calculate_profit_per_hour(kill_time: float, include_uniques: bool = True) -> int:
        """Calculate average profit per hour"""
        kills_per_hour = 3600 / (kill_time + 20)  # 20 seconds banking/setup
        
        # Regular drops average (scales, herbs, etc.)
        regular_drop_value = 100_000  # Average regular drop
        
        # Unique drops
        unique_value = 0
        if include_uniques:
            unique_chances = {
                15_000_000: 1/512,  # Tanzanite fang
                3_000_000: 1/512,   # Magic fang
                3_000_000: 1/512,   # Serpentine visage
                2_000_000: 1/512    # Uncut onyx
            }
            for value, chance in unique_chances.items():
                unique_value += value * chance
                
        return math.floor((regular_drop_value + unique_value) * kills_per_hour)

class Vorkath:
    """
    Real OSRS Vorkath mechanics
    """
    STATS = {
        "combat_level": 732,
        "hitpoints": 750,
        "max_hit": 32,
        "base_attack_styles": ["magic", "ranged"],
        "weakness": ["ruby bolts (e)", "diamond bolts (e)"],
        "examine": "This is no ordinary dragon."
    }

    SPECIAL_ATTACKS = {
        "Acid Phase": {
            "damage": 10,  # Per tick standing on acid
            "duration": 30,  # In ticks
            "frequency": 7   # Attacks between specials
        },
        "Spawn Phase": {
            "spawn_hp": 38,
            "spawn_max_hit": 7,
            "duration": 25,
            "frequency": 7
        },
        "Fire Bomb": {
            "max_hit": 115,
            "frequency": 7
        },
        "Ice Phase": {
            "freeze_duration": 8,  # In ticks
            "frequency": "random"
        }
    }

    UNIQUE_DROPS = {
        "Draconic visage": 1/5000,
        "Skeletal visage": 1/5000,
        "Jar of decay": 1/3000,
        "Vorki": 1/3000,
        "Dragon bones": 1/1,      # Guaranteed 2
        "Blue dragonhide": 1/1,   # Guaranteed 2
        "Superior dragon bones": 1/1  # Guaranteed during DS2
    }

    @staticmethod
    def calculate_kill_time(dps: float, woox_walk: bool = False) -> float:
        """Calculate average kill time based on DPS"""
        total_hp = 750
        acid_phase_loss = 0 if woox_walk else 16  # Seconds lost during acid phase
        return (total_hp / dps) + acid_phase_loss + 6  # 6 seconds for spawn phase

    @staticmethod
    def calculate_profit_per_hour(kill_time: float, include_uniques: bool = True) -> int:
        """Calculate average profit per hour"""
        kills_per_hour = 3600 / (kill_time + 15)  # 15 seconds banking
        
        # Regular drops average
        regular_drop_value = 140_000  # Average regular drop
        
        # Unique drops
        unique_value = 0
        if include_uniques:
            unique_chances = {
                25_000_000: 1/5000,  # Draconic visage
                25_000_000: 1/5000,  # Skeletal visage
                1_000_000: 1/3000,   # Jar of decay
            }
            for value, chance in unique_chances.items():
                unique_value += value * chance
                
        return math.floor((regular_drop_value + unique_value) * kills_per_hour)

# Add more Slayer masters
SlayerSystem.MASTERS.update({
    "Duradel": {
        "level_required": 100,  # Combat level
        "slayer_required": 50,  # Slayer level
        "tasks": {
            "Abyssal Demons": {"weight": 12, "min": 130, "max": 200},
            "Dark Beasts": {"weight": 10, "min": 130, "max": 200},
            "Kalphites": {"weight": 9, "min": 130, "max": 200},
            "Greater Demons": {"weight": 9, "min": 130, "max": 200},
            "Black Dragons": {"weight": 9, "min": 130, "max": 200},
            "Bloodveld": {"weight": 9, "min": 130, "max": 200},
            "Fire Giants": {"weight": 9, "min": 130, "max": 200},
            "Gargoyles": {"weight": 8, "min": 130, "max": 200},
            "Nechryael": {"weight": 8, "min": 130, "max": 200},
            "Kraken": {"weight": 9, "min": 130, "max": 200},
            "Cave Kraken": {"weight": 8, "min": 130, "max": 200},
            "Black Demons": {"weight": 9, "min": 130, "max": 200},
            "Iron Dragons": {"weight": 5, "min": 40, "max": 60},
            "Steel Dragons": {"weight": 5, "min": 40, "max": 60},
            "Mithril Dragons": {"weight": 4, "min": 20, "max": 40},
            "Skeletal Wyverns": {"weight": 7, "min": 130, "max": 200}
        }
    },
    "Konar": {
        "level_required": 75,  # Combat level
        "slayer_required": 1,
        "tasks": {
            "Adamant Dragons": {"weight": 5, "min": 3, "max": 6},
            "Black Demons": {"weight": 9, "min": 130, "max": 200},
            "Black Dragons": {"weight": 6, "min": 10, "max": 20},
            "Bloodveld": {"weight": 9, "min": 130, "max": 200},
            "Blue Dragons": {"weight": 8, "min": 130, "max": 200},
            "Drake": {"weight": 8, "min": 75, "max": 150},
            "Fire Giants": {"weight": 9, "min": 130, "max": 200},
            "Gargoyles": {"weight": 8, "min": 130, "max": 200},
            "Hydras": {"weight": 10, "min": 125, "max": 190},
            "Kraken": {"weight": 6, "min": 80, "max": 150},
            "Rune Dragons": {"weight": 4, "min": 3, "max": 6},
            "Skeletal Wyverns": {"weight": 7, "min": 130, "max": 200},
            "Smoke Devils": {"weight": 7, "min": 130, "max": 200},
            "Wyrms": {"weight": 8, "min": 100, "max": 160}
        },
        "location_bonus": {
            "points": 1.2,  # 20% more points
            "key_chance": 1/100  # Brimstone key chance per kill
        }
    }
})

# Add more superior monsters
SuperiorSlayer.SUPERIOR_MONSTERS.update({
    "Smoke Devil": {
        "superior": "Nuclear Smoke Devil",
        "chance": 0.008,
        "combat_level": 280,
        "base_hp": 440,
        "max_hit": 24,
        "xp_multiplier": 3.5
    },
    "Dark Beast": {
        "superior": "Night Beast",
        "chance": 0.008,
        "combat_level": 182,
        "base_hp": 400,
        "max_hit": 27,
        "xp_multiplier": 3.5
    },
    "Abyssal Demon": {
        "superior": "Greater Abyssal Demon",
        "chance": 0.008,
        "combat_level": 342,
        "base_hp": 400,
        "max_hit": 27,
        "xp_multiplier": 3.5
    }
})

class ChambersOfXeric:
    """
    Real OSRS Chambers of Xeric (CoX) mechanics
    """
    BOSSES = {
        "Great Olm": {
            "combat_level": 862,
            "hitpoints": {
                "head": 600,
                "left_hand": 600,
                "right_hand": 600
            },
            "max_hit": {
                "auto": 26,
                "crystal": 43,
                "lightning": 35,
                "flame_wall": 25,
                "acid_spray": 20,
                "falling_crystal": 30
            },
            "phases": ["Running", "Crystal", "Flame", "Acid", "Head"],
            "special_attacks": {
                "Lightning": "Targets random player, spreads to nearby players",
                "Crystal Burst": "Falling crystals deal heavy damage",
                "Flame Wall": "Fire wall that must be avoided",
                "Acid Spray": "Pools of acid deal continuous damage",
                "Teleport Crystals": "Teleports players to crystals that must be destroyed"
            }
        },
        "Tekton": {
            "combat_level": 364,
            "hitpoints": 300,
            "max_hit": 35,
            "attack_style": "melee",
            "weakness": "crush",
            "special": "Anvil phase reduces damage taken"
        },
        "Vespula": {
            "combat_level": 526,
            "hitpoints": 200,
            "max_hit": 30,
            "attack_style": "magic",
            "weakness": "ranged",
            "special": "Portal must be destroyed"
        }
        # Add more CoX bosses...
    }

    UNIQUE_DROPS = {
        "Dexterous prayer scroll": 1/28,
        "Arcane prayer scroll": 1/28,
        "Twisted buckler": 1/28,
        "Dragon hunter crossbow": 1/28,
        "Dinh's bulwark": 1/28,
        "Ancestral hat": 1/35,
        "Ancestral robe top": 1/35,
        "Ancestral robe bottom": 1/35,
        "Dragon claws": 1/40,
        "Elder maul": 1/40,
        "Kodai insignia": 1/40,
        "Twisted bow": 1/40
    }

    POINTS_SYSTEM = {
        "Death reduction": 40,  # % points lost on death
        "Personal point cap": 131_071,
        "Team point cap": 570_000,
        "Point modifiers": {
            "Team size": {
                1: 0.0,      # Solo
                2: 0.4,      # Duo
                3: 0.8,      # Trio
                "max": 0.8   # Capped at trio scaling
            },
            "Challenge mode": 1.4  # 40% more points
        }
    }

    @staticmethod
    def calculate_drop_chance(total_points: int, personal_points: int, team_size: int) -> float:
        """Calculate unique drop chance based on points"""
        base_chance = min(total_points / 8675, 65) / 100  # Max 65% chance
        personal_chance = base_chance * (personal_points / total_points)
        return personal_chance

    @staticmethod
    def calculate_points(completion_time: int, deaths: int, team_size: int, 
                        challenge_mode: bool = False) -> int:
        """Calculate raid points"""
        base_points = 100_000  # Example base points
        time_modifier = max(0, 1 - (completion_time - 1800) / 3600)  # Optimal time ~30 mins
        death_penalty = 1 - (deaths * 0.4)  # 40% reduction per death
        team_modifier = ChambersOfXeric.POINTS_SYSTEM["Point modifiers"]["Team size"].get(
            min(team_size, 3), 
            ChambersOfXeric.POINTS_SYSTEM["Point modifiers"]["Team size"]["max"]
        )
        cm_modifier = ChambersOfXeric.POINTS_SYSTEM["Point modifiers"]["Challenge mode"] if challenge_mode else 1.0
        
        return min(
            int(base_points * time_modifier * death_penalty * team_modifier * cm_modifier),
            ChambersOfXeric.POINTS_SYSTEM["Personal point cap"]
        )

class TheatreOfBlood:
    """
    Real OSRS Theatre of Blood (ToB) mechanics
    """
    BOSSES = {
        "The Maiden of Sugadinti": {
            "combat_level": 940,
            "hitpoints": 3250,
            "max_hit": 35,
            "attack_styles": ["magic", "melee"],
            "phases": [70, 50, 30],  # HP % for phase changes
            "special_attacks": {
                "Blood Spawn": "Creates blood spawns that heal Maiden",
                "Blood Splash": "Blood attack that can bounce between players",
                "Blood Trail": "Creates damaging blood trails"
            }
        },
        "Pestilent Bloat": {
            "combat_level": 870,
            "hitpoints": 2000,
            "max_hit": 40,
            "mechanics": {
                "Walk duration": 32,  # ticks
                "Sleep duration": 18,  # ticks
                "Fly spawn rate": 10,  # ticks
                "Stomp damage": 35
            }
        },
        "Nylocas Vasilias": {
            "combat_level": 1040,
            "hitpoints": 2500,
            "max_hit": 30,
            "phases": {
                "Melee": {"color": "red", "weakness": "crush"},
                "Ranged": {"color": "green", "weakness": "slash"},
                "Magic": {"color": "blue", "weakness": "stab"}
            },
            "pillar_hp": 100
        },
        "Sotetseg": {
            "combat_level": 995,
            "hitpoints": 3000,
            "max_hit": 40,
            "special_attacks": {
                "Maze": "Team must navigate identical mazes",
                "Death Ball": "High damage projectile that must be avoided",
                "Line Attack": "Linear attack that must be dodged"
            }
        },
        "Xarpus": {
            "combat_level": 960,
            "hitpoints": 2000,
            "max_hit": 30,
            "phases": {
                1: "Healing from poison",
                2: "Ranged attacks",
                3: "Exhumed poison"
            }
        },
        "Verzik Vitur": {
            "combat_level": 1040,
            "phase_hp": {
                "P1": 1800,
                "P2": 3250,
                "P3": 2000
            },
            "max_hit": {
                "P1": 40,
                "P2": 35,
                "P3": 45
            },
            "special_attacks": {
                "Web": "Traps players in web that must be broken",
                "Nylocas": "Spawns nylocas that must be killed",
                "Purple Bounce": "Bouncing attack between players",
                "Yellow Bounce": "Must be caught by players",
                "Green Ball": "Healing orb that must be attacked"
            }
        }
    }

    UNIQUE_DROPS = {
        "Avernic defender hilt": 1/100,
        "Ghrazi rapier": 1/100,
        "Sanguinesti staff": 1/100,
        "Justiciar faceguard": 1/100,
        "Justiciar chestguard": 1/100,
        "Justiciar legguards": 1/100,
        "Scythe of vitur": 1/200
    }

    WIPE_MECHANICS = {
        "Death cap": 4,  # Maximum team deaths allowed
        "Death penalties": {
            1: 0.80,  # 20% point reduction
            2: 0.60,  # 40% point reduction
            3: 0.40,  # 60% point reduction
            4: 0.00   # Raid failed
        }
    }

    @staticmethod
    def calculate_drop_chance(team_size: int, deaths: int, completion_time: int) -> float:
        """Calculate unique drop chance"""
        base_chance = 1/9.1  # Base chance for unique
        death_modifier = TheatreOfBlood.WIPE_MECHANICS["Death penalties"].get(deaths, 0)
        time_modifier = max(0.5, 1 - (completion_time - 1800) / 3600)  # Optimal time 30 mins
        team_modifier = min(1, 3/team_size)  # Better chances in smaller teams
        
        return base_chance * death_modifier * time_modifier * team_modifier

    @staticmethod
    def calculate_mvp_chance(personal_damage: int, total_damage: int, deaths: int = 0) -> float:
        """Calculate chance of MVP for unique drop chance boost"""
        damage_ratio = personal_damage / total_damage
        death_penalty = max(0, 1 - (deaths * 0.25))  # 25% reduction per death
        return damage_ratio * death_penalty 

class WildernessSystem:
    """
    Real OSRS Wilderness mechanics and calculations
    """
    LEVEL_RANGES = {
        "edgeville": (1, 4),
        "chaos_altar": (11, 13),
        "wilderness_course": (50, 56),
        "mage_arena": (54, 56),
        "demonic_ruins": (45, 47),
        "lava_dragons": (37, 39),
        "revenant_caves": (17, 40),
        "deep_wilderness_dungeon": (43, 45)
    }

    COMBAT_LEVEL_RANGES = {
        1: (3, 3),    # Level 1 wild: combat ±3
        20: (4, 4),   # Level 1-20: combat ±4
        50: (6, 6),   # Level 21-50: combat ±6
        100: (8, 8)   # Level 51+: combat ±8
    }

    SKULL_MECHANICS = {
        "normal": {
            "duration": 1200,  # 20 minutes in ticks
            "items_kept": 3,
            "xp_bonus": 1.0
        },
        "abyss": {
            "duration": 1200,
            "items_kept": 3,
            "xp_bonus": 1.0
        },
        "smite": {
            "duration": 1200,
            "items_kept": 3,
            "prayer_drain": 0.25  # 1/4 of damage dealt
        }
    }

    PROTECTION_PRAYERS = {
        "protect_item": {
            "items_kept": 1,
            "prayer_cost": 0.2  # Points per tick
        }
    }

    @staticmethod
    def calculate_combat_range(combat_level: int, wilderness_level: int) -> Tuple[int, int]:
        """Calculate combat level range that can attack you."""
        for level, (lower, upper) in COMBAT_LEVEL_RANGES.items():
            if wilderness_level <= level:
                min_level = max(3, combat_level - lower - wilderness_level)
                max_level = min(126, combat_level + upper + wilderness_level)
                return (min_level, max_level)
        return (3, 126)  # Default range

    @staticmethod
    def calculate_skull_timer(skull_type: str, modifiers: Dict[str, float] = None) -> int:
        """Calculate skull duration in ticks."""
        if skull_type not in SKULL_MECHANICS:
            return 0
            
        base_duration = SKULL_MECHANICS[skull_type]["duration"]
        if not modifiers:
            return base_duration
            
        total_modifier = 1.0
        for modifier in modifiers.values():
            total_modifier *= modifier
            
        return math.floor(base_duration * total_modifier)

    @staticmethod
    def calculate_items_kept(skull_type: str, protect_item: bool = False) -> int:
        """Calculate number of items kept on death."""
        if skull_type not in SKULL_MECHANICS:
            return 3
            
        base_kept = SKULL_MECHANICS[skull_type]["items_kept"]
        if protect_item:
            base_kept += PROTECTION_PRAYERS["protect_item"]["items_kept"]
            
        return base_kept

class ConstructionSystem:
    """
    Real OSRS Construction mechanics and calculations
    """
    ROOM_TYPES = {
        "parlour": {
            "level": 1,
            "cost": 1000,
            "hotspots": ["chair", "rug", "bookcase", "fireplace"],
            "doors": 4
        },
        "garden": {
            "level": 1,
            "cost": 1000,
            "hotspots": ["tree", "big_tree", "small_plant", "big_plant", "fountain"],
            "doors": 4
        },
        "kitchen": {
            "level": 5,
            "cost": 5000,
            "hotspots": ["stove", "sink", "larder", "shelf"],
            "doors": 3
        },
        "dining_room": {
            "level": 10,
            "cost": 5000,
            "hotspots": ["table", "bench", "bell_pull"],
            "doors": 2
        },
        "workshop": {
            "level": 15,
            "cost": 10000,
            "hotspots": ["workbench", "repair_bench", "tool_store"],
            "doors": 3
        },
        "bedroom": {
            "level": 20,
            "cost": 10000,
            "hotspots": ["bed", "dresser", "wardrobe", "clock"],
            "doors": 3
        },
        "skill_hall": {
            "level": 25,
            "cost": 15000,
            "hotspots": ["trophy", "head_trophy", "armour", "cape_hanger"],
            "doors": 6
        },
        "games_room": {
            "level": 30,
            "cost": 25000,
            "hotspots": ["prize_chest", "elemental_balance", "treasure_hunt"],
            "doors": 4
        },
        "combat_room": {
            "level": 32,
            "cost": 25000,
            "hotspots": ["dummy", "rack", "decorative"],
            "doors": 4
        },
        "quest_hall": {
            "level": 35,
            "cost": 25000,
            "hotspots": ["quest_list", "guild_trophy", "mounted_cape"],
            "doors": 6
        },
        "study": {
            "level": 40,
            "cost": 50000,
            "hotspots": ["lectern", "globe", "crystal_ball", "telescope"],
            "doors": 3
        },
        "costume_room": {
            "level": 42,
            "cost": 50000,
            "hotspots": ["armour_case", "magic_wardrobe", "cape_rack", "toy_box"],
            "doors": 3
        },
        "chapel": {
            "level": 45,
            "cost": 50000,
            "hotspots": ["altar", "lamp", "icon", "musical"],
            "doors": 2
        },
        "portal_chamber": {
            "level": 50,
            "cost": 100000,
            "hotspots": ["portal_frame", "portal_focus", "scrying_pool"],
            "doors": 3
        },
        "formal_garden": {
            "level": 55,
            "cost": 75000,
            "hotspots": ["topiary", "pond", "fancy_fountain", "hedge"],
            "doors": 4
        },
        "throne_room": {
            "level": 60,
            "cost": 150000,
            "hotspots": ["throne", "lever", "trapdoor"],
            "doors": 2
        },
        "oubliette": {
            "level": 65,
            "cost": 150000,
            "hotspots": ["cage", "decoration", "ladder"],
            "doors": 2
        },
        "dungeon": {
            "level": 70,
            "cost": 200000,
            "hotspots": ["guard", "trap", "decoration"],
            "doors": 4
        },
        "achievement_gallery": {
            "level": 80,
            "cost": 200000,
            "hotspots": ["display", "boss_lair", "adventure_log"],
            "doors": 3
        }
    }

    PORTAL_DESTINATIONS = {
        "varrock": {"level": 51, "runes": {"law": 2, "fire": 1, "air": 3}},
        "lumbridge": {"level": 51, "runes": {"law": 1, "earth": 1, "air": 3}},
        "falador": {"level": 51, "runes": {"law": 1, "water": 1, "air": 3}},
        "camelot": {"level": 55, "runes": {"law": 1, "air": 5}},
        "ardougne": {"level": 61, "runes": {"law": 2, "water": 2}},
        "watchtower": {"level": 66, "runes": {"law": 2, "earth": 2}},
        "trollheim": {"level": 71, "runes": {"law": 2, "fire": 2}},
        "kourend": {"level": 69, "runes": {"law": 2, "soul": 2, "water": 4}},
        "lunar_isle": {"level": 69, "runes": {"law": 1, "astral": 1, "earth": 1}},
        "ancient_magicks": {"level": 75, "runes": {"law": 2, "soul": 1, "blood": 1}}
    }

    @staticmethod
    def calculate_build_cost(room_type: str, upgrades: List[str] = None) -> int:
        """Calculate total cost to build and furnish a room."""
        if room_type not in ROOM_TYPES:
            return 0
            
        total_cost = ROOM_TYPES[room_type]["cost"]
        if not upgrades:
            return total_cost
            
        # Add upgrade costs
        for upgrade in upgrades:
            if upgrade in HOTSPOT_COSTS:
                total_cost += HOTSPOT_COSTS[upgrade]
                
        return total_cost

    @staticmethod
    def calculate_portal_requirements(destination: str) -> Dict[str, int]:
        """Calculate rune requirements for portal."""
        if destination not in PORTAL_DESTINATIONS:
            return {}
            
        return PORTAL_DESTINATIONS[destination]["runes"]

    @staticmethod
    def calculate_servant_trip_time(servant_type: str, distance: int) -> int:
        """Calculate servant trip time in ticks."""
        base_times = {
            "rick": 20,
            "butler": 12,
            "demon_butler": 7
        }
        
        if servant_type not in base_times:
            return 0
            
        return base_times[servant_type] + math.ceil(distance * 1.5)

class FarmingSystem:
    """
    Real OSRS Farming mechanics and calculations
    """
    PATCH_TYPES = {
        "allotment": {
            "locations": ["catherby", "ardougne", "falador", "morytania"],
            "protection": "flower",
            "compost_effect": 0.1,  # 10% disease reduction
            "tools": ["spade", "rake", "seed_dibber"]
        },
        "herb": {
            "locations": ["catherby", "ardougne", "falador", "morytania"],
            "protection": None,
            "compost_effect": 0.15,
            "tools": ["spade", "rake", "seed_dibber"]
        },
        "flower": {
            "locations": ["catherby", "ardougne", "falador", "morytania"],
            "protection": None,
            "compost_effect": 0.12,
            "tools": ["spade", "rake", "seed_dibber"]
        },
        "tree": {
            "locations": ["varrock", "lumbridge", "falador", "taverly", "gnome_stronghold"],
            "protection": "gardener",
            "compost_effect": 0.08,
            "tools": ["spade", "rake", "tree_patch"]
        },
        "fruit_tree": {
            "locations": ["catherby", "gnome_stronghold", "gnome_maze", "brimhaven", "lletya"],
            "protection": "gardener",
            "compost_effect": 0.08,
            "tools": ["spade", "rake", "tree_patch"]
        },
        "bush": {
            "locations": ["ardougne", "rimmington", "etceteria"],
            "protection": None,
            "compost_effect": 0.12,
            "tools": ["spade", "rake", "seed_dibber"]
        },
        "hops": {
            "locations": ["lumbridge", "yanille", "entrana", "seers"],
            "protection": "scarecrow",
            "compost_effect": 0.12,
            "tools": ["spade", "rake", "seed_dibber"]
        },
        "spirit_tree": {
            "locations": ["etceteria", "port_sarim", "brimhaven", "hosidius"],
            "protection": None,
            "compost_effect": 0,
            "tools": ["spade", "rake", "crystal_saw"]
        },
        "seaweed": {
            "locations": ["fossil_island"],
            "protection": None,
            "compost_effect": 0.15,
            "tools": ["spade", "rake", "seed_dibber"]
        }
    }

    GROWTH_STAGES = {
        "herb": {
            "stage_count": 4,
            "minutes_per_stage": 20,
            "minimum_yield": 3,
            "maximum_yield": 18,
            "lives": 1
        },
        "allotment": {
            "stage_count": 5,
            "minutes_per_stage": 10,
            "minimum_yield": 3,
            "maximum_yield": 56,
            "lives": 3
        },
        "flower": {
            "stage_count": 4,
            "minutes_per_stage": 5,
            "minimum_yield": 1,
            "maximum_yield": 1,
            "lives": 1
        },
        "tree": {
            "stage_count": 6,
            "minutes_per_stage": 40,
            "check_health": True,
            "lives": 1
        },
        "fruit_tree": {
            "stage_count": 6,
            "minutes_per_stage": 160,
            "produce_count": 6,
            "regrowth_time": 960,  # 16 hours
            "lives": 1
        },
        "bush": {
            "stage_count": 5,
            "minutes_per_stage": 20,
            "produce_count": 4,
            "regrowth_time": 240,  # 4 hours
            "lives": 1
        },
        "hops": {
            "stage_count": 5,
            "minutes_per_stage": 10,
            "minimum_yield": 3,
            "maximum_yield": 46,
            "lives": 1
        }
    }

    DISEASE_CHANCES = {
        "none": 0.128,          # No compost
        "compost": 0.064,       # Regular compost
        "supercompost": 0.032,  # Supercompost
        "ultracompost": 0.016   # Ultracompost
    }

    @staticmethod
    def calculate_growth_time(crop_type: str, stages_complete: int = 0) -> int:
        """Calculate remaining growth time in minutes."""
        if crop_type not in GROWTH_STAGES:
            return 0
            
        growth_info = GROWTH_STAGES[crop_type]
        remaining_stages = growth_info["stage_count"] - stages_complete
        return remaining_stages * growth_info["minutes_per_stage"]

    @staticmethod
    def calculate_yield(crop_type: str, compost_type: str = None, 
                       magic_secateurs: bool = False) -> Tuple[int, int]:
        """Calculate minimum and maximum yield."""
        if crop_type not in GROWTH_STAGES:
            return (0, 0)
            
        growth_info = GROWTH_STAGES[crop_type]
        min_yield = growth_info.get("minimum_yield", 1)
        max_yield = growth_info.get("maximum_yield", 1)
        
        # Apply compost bonus
        if compost_type:
            compost_bonus = {
                "compost": 1.1,
                "supercompost": 1.2,
                "ultracompost": 1.3
            }.get(compost_type, 1.0)
            min_yield = math.floor(min_yield * compost_bonus)
            max_yield = math.floor(max_yield * compost_bonus)
        
        # Apply magic secateurs bonus
        if magic_secateurs:
            min_yield = math.floor(min_yield * 1.1)
            max_yield = math.floor(max_yield * 1.1)
            
        return (min_yield, max_yield)

    @staticmethod
    def calculate_disease_chance(crop_type: str, compost_type: str = None, 
                               protection: bool = False) -> float:
        """Calculate chance of disease."""
        if protection:
            return 0.0
            
        base_chance = FARMING_SYSTEM.DISEASE_CHANCES.get(compost_type, FARMING_SYSTEM.DISEASE_CHANCES["none"])
        patch_info = FARMING_SYSTEM.PATCH_TYPES.get(crop_type, {})
        compost_effect = patch_info.get("compost_effect", 0.1)
        
        return max(0, base_chance * (1 - compost_effect)) 

class InfernoSystem:
    """
    Real OSRS Inferno mechanics and wave information
    """
    WAVES = {
        1: ["Nibbler", "Bat", "Bat"],
        2: ["Nibbler", "Bat", "Bat", "Blob"],
        3: ["Nibbler", "Bat", "Blob", "Melee"],
        4: ["Nibbler", "Blob", "Melee", "Ranger"],
        5: ["Nibbler", "Melee", "Ranger", "Mager"],
        # ... more waves
        67: ["Nibbler", "Jad", "Jad", "Jad"],
        68: ["Zuk", "Shield", "Jad", "Healers", "Mager", "Ranger"]
    }

    MONSTERS = {
        "Nibbler": {
            "combat_level": 32,
            "hitpoints": 10,
            "max_hit": 1,
            "attack_style": None,  # Only damages pillars
            "weakness": "any"
        },
        "Bat": {
            "combat_level": 84,
            "hitpoints": 20,
            "max_hit": 4,
            "attack_style": "ranged",
            "weakness": "melee"
        },
        "Blob": {
            "combat_level": 160,
            "hitpoints": 40,
            "max_hit": 25,
            "attack_styles": ["melee", "ranged", "magic"],
            "weakness": "prayer_switching"
        },
        "Melee": {
            "combat_level": 240,
            "hitpoints": 50,
            "max_hit": 37,
            "attack_style": "melee",
            "weakness": "safespot"
        },
        "Ranger": {
            "combat_level": 240,
            "hitpoints": 50,
            "max_hit": 47,
            "attack_style": "ranged",
            "weakness": "prayer"
        },
        "Mager": {
            "combat_level": 240,
            "hitpoints": 50,
            "max_hit": 70,
            "attack_style": "magic",
            "weakness": "prayer"
        },
        "Jad": {
            "combat_level": 900,
            "hitpoints": 100,
            "max_hit": 98,
            "attack_styles": ["magic", "ranged"],
            "weakness": "prayer_switching",
            "healers": {
                "count": 4,
                "heal_amount": 13,
                "trigger_hp": 50  # % HP when healers spawn
            }
        },
        "Zuk": {
            "combat_level": 1400,
            "hitpoints": 1200,
            "max_hit": 251,
            "attack_style": "magic",
            "weakness": "shield",
            "shield": {
                "hitpoints": 600,
                "movement_delay": 8,  # ticks
                "safe_range": 2  # tiles
            },
            "healers": {
                "count": 4,
                "heal_amount": 25,
                "trigger_hp": 480  # Absolute HP when healers spawn
            },
            "sets": [
                {"hp": 600, "spawn": ["Ranger", "Mager"]},
                {"hp": 480, "spawn": ["Jad", "Healers"]},
                {"hp": 240, "spawn": ["Ranger", "Mager"]}
            ]
        }
    }

    @staticmethod
    def calculate_wave_difficulty(wave: int) -> float:
        """Calculate relative difficulty of a wave."""
        if wave not in WAVES:
            return 0.0
            
        difficulty = 0.0
        for monster in WAVES[wave]:
            monster_info = MONSTERS[monster]
            difficulty += (
                monster_info["hitpoints"] * 
                monster_info["max_hit"] / 100
            )
            
            # Add complexity modifiers
            if "attack_styles" in monster_info:
                difficulty *= 1.5  # Prayer switching required
            if monster == "Jad":
                difficulty *= 2.0  # High risk
            if monster == "Zuk":
                difficulty *= 3.0  # Extremely high risk
                
        return difficulty

    @staticmethod
    def calculate_supply_usage(wave: int) -> Dict[str, int]:
        """Calculate expected supply usage up to a wave."""
        if wave < 1 or wave > 68:
            return {}
            
        # Base supply calculations
        supplies = {
            "prayer_potion": 0,
            "saradomin_brew": 0,
            "super_restore": 0,
            "blood_runes": 0
        }
        
        # Calculate damage taken and prayer drain
        total_damage = 0
        prayer_drain = 0
        
        for w in range(1, wave + 1):
            wave_monsters = WAVES[w]
            for monster in wave_monsters:
                monster_info = MONSTERS[monster]
                
                # Estimate hits taken
                hits = monster_info["hitpoints"] / 20  # Average DPS
                damage_per_hit = monster_info["max_hit"] / 3  # Average damage
                total_damage += hits * damage_per_hit
                
                # Prayer drain
                if monster_info["attack_style"] in ["magic", "ranged"]:
                    prayer_drain += monster_info["hitpoints"] * 0.05
                
        # Convert damage to brew doses
        supplies["saradomin_brew"] = math.ceil(total_damage / 16)  # Each dose heals 16
        supplies["super_restore"] = math.ceil(supplies["saradomin_brew"] / 3)  # Restore stats
        
        # Convert prayer drain to prayer potions
        supplies["prayer_potion"] = math.ceil(prayer_drain / 7)  # Each dose restores 7 points
        
        # Blood runes for healing
        supplies["blood_runes"] = math.ceil(total_damage / 4)  # Each blood barrage heals 4
        
        return supplies

class AchievementDiarySystem:
    """
    Real OSRS Achievement Diary system
    """
    AREAS = {
        "Ardougne": {
            "easy": {
                "requirements": {
                    "thieving": 5,
                    "fishing": 15,
                    "agility": 10,
                    "crafting": 16
                },
                "tasks": [
                    "Steal from Ardougne market stall",
                    "Fish at Ardougne fishing spots",
                    "Cross the log balance",
                    "Make a leather glove"
                ],
                "rewards": {
                    "ardougne_cloak_1": {
                        "stats": {"prayer": 1},
                        "effects": ["Unlimited teleports to monastery"]
                    }
                }
            },
            "medium": {
                "requirements": {
                    "thieving": 38,
                    "agility": 39,
                    "magic": 51,
                    "farming": 31
                },
                "tasks": [
                    "Steal from gem stall",
                    "Complete Ardougne rooftop course",
                    "Teleport to Ardougne",
                    "Plant strawberries"
                ],
                "rewards": {
                    "ardougne_cloak_2": {
                        "stats": {"prayer": 2},
                        "effects": ["Better stealing chance", "Farm teleport"]
                    }
                }
            }
            # Add more difficulties...
        },
        "Falador": {
            "easy": {
                "requirements": {
                    "agility": 5,
                    "mining": 10,
                    "prayer": 10
                },
                "tasks": [
                    "Climb over crumbling wall",
                    "Mine iron in mining guild",
                    "Pray at altar"
                ],
                "rewards": {
                    "falador_shield_1": {
                        "stats": {"prayer": 1},
                        "effects": ["Prayer restore once daily"]
                    }
                }
            }
            # Add more difficulties...
        }
        # Add more areas...
    }

    @staticmethod
    def check_requirements(area: str, difficulty: str, 
                         player_stats: Dict[str, int]) -> Tuple[bool, List[str]]:
        """Check if player meets diary requirements."""
        if area not in AREAS or difficulty not in AREAS[area]:
            return False, ["Invalid area or difficulty"]
            
        diary = AREAS[area][difficulty]
        missing = []
        
        for skill, level in diary["requirements"].items():
            if player_stats.get(skill, 1) < level:
                missing.append(f"{skill.title()}: {level}")
                
        return len(missing) == 0, missing

    @staticmethod
    def get_rewards(area: str, difficulty: str) -> Dict[str, any]:
        """Get rewards for completing a diary."""
        if area not in AREAS or difficulty not in AREAS[area]:
            return {}
            
        return AREAS[area][difficulty]["rewards"]

class ClueScrollSystem:
    """
    Real OSRS Clue Scroll system
    """
    TYPES = {
        "beginner": {
            "steps": 3,
            "unique_drops": {
                "mole_slippers": 1/100,
                "frog_slippers": 1/100,
                "bear_feet": 1/100
            }
        },
        "easy": {
            "steps": 3,
            "unique_drops": {
                "team_cape": 1/16,
                "monks_robe": 1/16,
                "bob_shirt": 1/16
            }
        },
        "medium": {
            "steps": 4,
            "unique_drops": {
                "ranger_boots": 1/1133,
                "wizard_boots": 1/1133,
                "holy_sandals": 1/1133
            }
        },
        "hard": {
            "steps": 5,
            "unique_drops": {
                "robin_hood_hat": 1/1133,
                "gilded_armor": 1/1133,
                "3rd_age": 1/42120
            }
        },
        "elite": {
            "steps": 6,
            "unique_drops": {
                "3rd_age": 1/42120,
                "gilded_armor": 1/1133,
                "ranger_tunic": 1/1133
            }
        },
        "master": {
            "steps": 7,
            "unique_drops": {
                "3rd_age": 1/42120,
                "bloodhound_pet": 1/1000,
                "ornament_kits": 1/1133
            }
        }
    }

    STEP_TYPES = {
        "anagram": {
            "difficulty": 0.2,
            "requirements": None
        },
        "coordinate": {
            "difficulty": 0.4,
            "requirements": {
                "watch": True,
                "sextant": True,
                "chart": True
            }
        },
        "cryptic": {
            "difficulty": 0.3,
            "requirements": None
        },
        "emote": {
            "difficulty": 0.5,
            "requirements": {
                "items": True,
                "equipment": True
            }
        },
        "hot_cold": {
            "difficulty": 0.6,
            "requirements": {
                "strange_device": True
            }
        },
        "puzzle": {
            "difficulty": 0.8,
            "requirements": None
        }
    }

    @staticmethod
    def calculate_completion_chance(clue_type: str, 
                                 has_requirements: bool = True) -> float:
        """Calculate chance of completing a clue scroll."""
        if clue_type not in TYPES:
            return 0.0
            
        base_chance = 1.0
        steps = TYPES[clue_type]["steps"]
        
        # Each step has a chance to be completable
        step_chance = 0.9 if has_requirements else 0.6
        
        return base_chance * (step_chance ** steps)

    @staticmethod
    def calculate_average_reward(clue_type: str) -> int:
        """Calculate average reward value."""
        if clue_type not in TYPES:
            return 0
            
        # Base rewards
        base_values = {
            "beginner": 5_000,
            "easy": 10_000,
            "medium": 25_000,
            "hard": 100_000,
            "elite": 200_000,
            "master": 500_000
        }
        
        # Add unique drop values
        unique_value = 0
        for item, chance in TYPES[clue_type]["unique_drops"].items():
            # Estimated values
            if item == "3rd_age":
                value = 1_000_000_000  # Average 3rd age piece
            elif item == "ranger_boots":
                value = 40_000_000
            elif "gilded" in item:
                value = 1_000_000
            else:
                value = 100_000
                
            unique_value += value * chance
            
        return base_values[clue_type] + math.floor(unique_value)

    @staticmethod
    def get_step_requirements(step_type: str) -> Dict[str, any]:
        """Get requirements for a clue step type."""
        if step_type not in STEP_TYPES:
            return {}
            
        return STEP_TYPES[step_type]["requirements"] 

class WoodcuttingSystem:
    """
    Real OSRS Woodcutting mechanics and calculations
    """
    TREES = {
        "regular": {
            "level": 1,
            "xp": 25.0,
            "respawn_time": 4,  # seconds
            "log_value": 1,
            "success_rate": lambda level, axe_bonus: min(0.95, 0.15 + level * 0.01 + axe_bonus * 0.02)
        },
        "oak": {
            "level": 15,
            "xp": 37.5,
            "respawn_time": 4,
            "log_value": 20,
            "success_rate": lambda level, axe_bonus: min(0.90, 0.10 + (level-15) * 0.01 + axe_bonus * 0.02)
        },
        "willow": {
            "level": 30,
            "xp": 67.5,
            "respawn_time": 4,
            "log_value": 8,
            "success_rate": lambda level, axe_bonus: min(0.85, 0.08 + (level-30) * 0.01 + axe_bonus * 0.02)
        },
        "teak": {
            "level": 35,
            "xp": 85.0,
            "respawn_time": 4,
            "log_value": 85,
            "success_rate": lambda level, axe_bonus: min(0.80, 0.07 + (level-35) * 0.01 + axe_bonus * 0.02)
        },
        "maple": {
            "level": 45,
            "xp": 100.0,
            "respawn_time": 4,
            "log_value": 12,
            "success_rate": lambda level, axe_bonus: min(0.75, 0.06 + (level-45) * 0.01 + axe_bonus * 0.02)
        },
        "mahogany": {
            "level": 50,
            "xp": 125.0,
            "respawn_time": 4,
            "log_value": 420,
            "success_rate": lambda level, axe_bonus: min(0.70, 0.05 + (level-50) * 0.01 + axe_bonus * 0.02)
        },
        "yew": {
            "level": 60,
            "xp": 175.0,
            "respawn_time": 6,
            "log_value": 320,
            "success_rate": lambda level, axe_bonus: min(0.65, 0.04 + (level-60) * 0.01 + axe_bonus * 0.02)
        },
        "magic": {
            "level": 75,
            "xp": 250.0,
            "respawn_time": 8,
            "log_value": 1280,
            "success_rate": lambda level, axe_bonus: min(0.60, 0.03 + (level-75) * 0.01 + axe_bonus * 0.02)
        },
        "redwood": {
            "level": 90,
            "xp": 380.0,
            "respawn_time": 4,
            "log_value": 400,
            "success_rate": lambda level, axe_bonus: min(0.55, 0.02 + (level-90) * 0.01 + axe_bonus * 0.02)
        }
    }

    AXES = {
        "bronze": {"level": 1, "bonus": 0},
        "iron": {"level": 1, "bonus": 1},
        "steel": {"level": 6, "bonus": 2},
        "black": {"level": 11, "bonus": 3},
        "mithril": {"level": 21, "bonus": 4},
        "adamant": {"level": 31, "bonus": 5},
        "rune": {"level": 41, "bonus": 6},
        "dragon": {"level": 61, "bonus": 7},
        "crystal": {"level": 71, "bonus": 8},
        "infernal": {"level": 61, "bonus": 7}  # Same as dragon but burns logs
    }

    LOCATIONS = {
        "lumbridge": ["regular", "oak", "willow"],
        "draynor": ["willow", "oak"],
        "varrock": ["regular", "oak", "yew"],
        "edgeville": ["yew", "regular"],
        "seers": ["maple", "yew"],
        "woodcutting_guild": ["regular", "oak", "willow", "maple", "yew", "magic"],
        "fossil_island": ["teak", "mahogany"],
        "prif": ["teak", "mahogany", "magic"],
        "hosidius": ["redwood"]
    }

    NEST_CHANCE = {
        "regular": 0.001,
        "oak": 0.002,
        "willow": 0.003,
        "teak": 0.002,
        "maple": 0.004,
        "mahogany": 0.003,
        "yew": 0.005,
        "magic": 0.006,
        "redwood": 0.008
    }

    @staticmethod
    def calculate_xp_rate(tree_type: str, level: int, axe_type: str) -> float:
        """Calculate XP per hour for given tree and setup"""
        if tree_type not in WoodcuttingSystem.TREES or axe_type not in WoodcuttingSystem.AXES:
            return 0.0

        tree = WoodcuttingSystem.TREES[tree_type]
        axe = WoodcuttingSystem.AXES[axe_type]

        if level < tree["level"] or level < axe["level"]:
            return 0.0

        success_rate = tree["success_rate"](level, axe["bonus"])
        ticks_per_attempt = 4  # Standard 2.4s attempt rate
        attempts_per_hour = 3600 / (ticks_per_attempt * 0.6)  # 0.6s per tick
        successful_attempts = attempts_per_hour * success_rate

        return successful_attempts * tree["xp"]

    @staticmethod
    def calculate_profit_per_hour(tree_type: str, level: int, axe_type: str) -> int:
        """Calculate profit per hour including bird nests"""
        if tree_type not in WoodcuttingSystem.TREES or axe_type not in WoodcuttingSystem.AXES:
            return 0

        tree = WoodcuttingSystem.TREES[tree_type]
        axe = WoodcuttingSystem.AXES[axe_type]

        if level < tree["level"] or level < axe["level"]:
            return 0

        success_rate = tree["success_rate"](level, axe["bonus"])
        ticks_per_attempt = 4
        attempts_per_hour = 3600 / (ticks_per_attempt * 0.6)
        successful_attempts = attempts_per_hour * success_rate

        # Calculate log profit
        log_profit = successful_attempts * tree["log_value"]

        # Calculate nest profit
        nest_chance = WoodcuttingSystem.NEST_CHANCE[tree_type]
        nests_per_hour = successful_attempts * nest_chance
        nest_value = 5000  # Average nest value including seeds
        nest_profit = nests_per_hour * nest_value

        return math.floor(log_profit + nest_profit)

    @staticmethod
    def get_best_location(tree_type: str) -> List[str]:
        """Get best locations for specific tree type"""
        return [loc for loc, trees in WoodcuttingSystem.LOCATIONS.items() if tree_type in trees]

class MiningSystem:
    """
    Real OSRS Mining mechanics and calculations
    """
    ROCKS = {
        "copper": {
            "level": 1,
            "xp": 17.5,
            "respawn_time": 2,  # seconds
            "ore_value": 3,
            "success_rate": lambda level, pick_bonus: min(0.95, 0.15 + level * 0.01 + pick_bonus * 0.02)
        },
        "tin": {
            "level": 1,
            "xp": 17.5,
            "respawn_time": 2,
            "ore_value": 3,
            "success_rate": lambda level, pick_bonus: min(0.95, 0.15 + level * 0.01 + pick_bonus * 0.02)
        },
        "iron": {
            "level": 15,
            "xp": 35.0,
            "respawn_time": 3,
            "ore_value": 28,
            "success_rate": lambda level, pick_bonus: min(0.90, 0.10 + (level-15) * 0.01 + pick_bonus * 0.02)
        },
        "coal": {
            "level": 30,
            "xp": 50.0,
            "respawn_time": 10,
            "ore_value": 95,
            "success_rate": lambda level, pick_bonus: min(0.85, 0.08 + (level-30) * 0.01 + pick_bonus * 0.02)
        },
        "gold": {
            "level": 40,
            "xp": 65.0,
            "respawn_time": 10,
            "ore_value": 75,
            "success_rate": lambda level, pick_bonus: min(0.80, 0.07 + (level-40) * 0.01 + pick_bonus * 0.02)
        },
        "mithril": {
            "level": 55,
            "xp": 80.0,
            "respawn_time": 20,
            "ore_value": 115,
            "success_rate": lambda level, pick_bonus: min(0.75, 0.06 + (level-55) * 0.01 + pick_bonus * 0.02)
        },
        "adamantite": {
            "level": 70,
            "xp": 95.0,
            "respawn_time": 40,
            "ore_value": 280,
            "success_rate": lambda level, pick_bonus: min(0.70, 0.05 + (level-70) * 0.01 + pick_bonus * 0.02)
        },
        "runite": {
            "level": 85,
            "xp": 125.0,
            "respawn_time": 720,  # 12 minutes
            "ore_value": 11000,
            "success_rate": lambda level, pick_bonus: min(0.65, 0.04 + (level-85) * 0.01 + pick_bonus * 0.02)
        },
        "amethyst": {
            "level": 92,
            "xp": 240.0,
            "respawn_time": 120,
            "ore_value": 3000,
            "success_rate": lambda level, pick_bonus: min(0.60, 0.03 + (level-92) * 0.01 + pick_bonus * 0.02)
        }
    }

    PICKAXES = {
        "bronze": {"level": 1, "bonus": 0},
        "iron": {"level": 1, "bonus": 1},
        "steel": {"level": 6, "bonus": 2},
        "black": {"level": 11, "bonus": 3},
        "mithril": {"level": 21, "bonus": 4},
        "adamant": {"level": 31, "bonus": 5},
        "rune": {"level": 41, "bonus": 6},
        "dragon": {"level": 61, "bonus": 7},
        "crystal": {"level": 71, "bonus": 8},
        "infernal": {"level": 61, "bonus": 7}  # Same as dragon but chance to smelt
    }

    LOCATIONS = {
        "lumbridge_swamp": ["copper", "tin"],
        "varrock_west": ["clay", "tin", "iron"],
        "varrock_east": ["copper", "iron"],
        "al_kharid": ["copper", "tin", "iron", "coal", "mithril", "adamantite"],
        "mining_guild": ["coal", "mithril", "adamantite", "runite"],
        "wilderness_rune_rocks": ["runite"],
        "mining_guild_basement": ["amethyst"],
        "motherlode_mine": ["pay-dirt"]
    }

    GEM_CHANCES = {
        "uncut_sapphire": 0.002,
        "uncut_emerald": 0.0015,
        "uncut_ruby": 0.001,
        "uncut_diamond": 0.0005
    }

    @staticmethod
    def calculate_xp_rate(rock_type: str, level: int, pickaxe_type: str) -> float:
        """Calculate XP per hour for given rock and setup"""
        if rock_type not in MiningSystem.ROCKS or pickaxe_type not in MiningSystem.PICKAXES:
            return 0.0

        rock = MiningSystem.ROCKS[rock_type]
        pickaxe = MiningSystem.PICKAXES[pickaxe_type]

        if level < rock["level"] or level < pickaxe["level"]:
            return 0.0

        success_rate = rock["success_rate"](level, pickaxe["bonus"])
        ticks_per_attempt = 3  # Standard 1.8s attempt rate
        attempts_per_hour = 3600 / (ticks_per_attempt * 0.6)  # 0.6s per tick
        successful_attempts = attempts_per_hour * success_rate

        return successful_attempts * rock["xp"]

    @staticmethod
    def calculate_profit_per_hour(rock_type: str, level: int, pickaxe_type: str) -> int:
        """Calculate profit per hour including gems"""
        if rock_type not in MiningSystem.ROCKS or pickaxe_type not in MiningSystem.PICKAXES:
            return 0

        rock = MiningSystem.ROCKS[rock_type]
        pickaxe = MiningSystem.PICKAXES[pickaxe_type]

        if level < rock["level"] or level < pickaxe["level"]:
            return 0

        success_rate = rock["success_rate"](level, pickaxe["bonus"])
        ticks_per_attempt = 3
        attempts_per_hour = 3600 / (ticks_per_attempt * 0.6)
        successful_attempts = attempts_per_hour * success_rate

        # Calculate ore profit
        ore_profit = successful_attempts * rock["ore_value"]

        # Calculate gem profit
        gem_profit = 0
        gem_values = {
            "uncut_sapphire": 500,
            "uncut_emerald": 750,
            "uncut_ruby": 1000,
            "uncut_diamond": 2000
        }
        for gem, chance in MiningSystem.GEM_CHANCES.items():
            gems_per_hour = successful_attempts * chance
            gem_profit += gems_per_hour * gem_values[gem]

        return math.floor(ore_profit + gem_profit)

    @staticmethod
    def get_best_location(rock_type: str) -> List[str]:
        """Get best locations for specific rock type"""
        return [loc for loc, rocks in MiningSystem.LOCATIONS.items() if rock_type in rocks]

class FishingSystem:
    """
    Real OSRS Fishing mechanics and calculations
    """
    SPOTS = {
        "shrimp": {
            "level": 1,
            "xp": 10.0,
            "tool": "small_net",
            "bait": None,
            "fish_value": 5,
            "catch_time": 3,  # ticks
            "success_rate": lambda level: min(0.95, 0.15 + level * 0.01)
        },
        "sardine": {
            "level": 5,
            "xp": 20.0,
            "tool": "fishing_rod",
            "bait": "fishing_bait",
            "fish_value": 8,
            "catch_time": 3,
            "success_rate": lambda level: min(0.90, 0.12 + (level-5) * 0.01)
        },
        "herring": {
            "level": 10,
            "xp": 30.0,
            "tool": "fishing_rod",
            "bait": "fishing_bait",
            "fish_value": 12,
            "catch_time": 3,
            "success_rate": lambda level: min(0.85, 0.10 + (level-10) * 0.01)
        },
        "trout": {
            "level": 20,
            "xp": 50.0,
            "tool": "fly_fishing_rod",
            "bait": "feather",
            "fish_value": 20,
            "catch_time": 3,
            "success_rate": lambda level: min(0.80, 0.08 + (level-20) * 0.01)
        },
        "salmon": {
            "level": 30,
            "xp": 70.0,
            "tool": "fly_fishing_rod",
            "bait": "feather",
            "fish_value": 50,
            "catch_time": 3,
            "success_rate": lambda level: min(0.75, 0.07 + (level-30) * 0.01)
        },
        "tuna": {
            "level": 35,
            "xp": 80.0,
            "tool": "harpoon",
            "bait": None,
            "fish_value": 100,
            "catch_time": 4,
            "success_rate": lambda level: min(0.70, 0.06 + (level-35) * 0.01)
        },
        "lobster": {
            "level": 40,
            "xp": 90.0,
            "tool": "lobster_pot",
            "bait": None,
            "fish_value": 150,
            "catch_time": 4,
            "success_rate": lambda level: min(0.65, 0.05 + (level-40) * 0.01)
        },
        "swordfish": {
            "level": 50,
            "xp": 100.0,
            "tool": "harpoon",
            "bait": None,
            "fish_value": 400,
            "catch_time": 5,
            "success_rate": lambda level: min(0.60, 0.04 + (level-50) * 0.01)
        },
        "monkfish": {
            "level": 62,
            "xp": 120.0,
            "tool": "small_net",
            "bait": None,
            "fish_value": 500,
            "catch_time": 4,
            "success_rate": lambda level: min(0.55, 0.03 + (level-62) * 0.01)
        },
        "shark": {
            "level": 76,
            "xp": 110.0,
            "tool": "harpoon",
            "bait": None,
            "fish_value": 800,
            "catch_time": 5,
            "success_rate": lambda level: min(0.50, 0.02 + (level-76) * 0.01)
        },
        "anglerfish": {
            "level": 82,
            "xp": 120.0,
            "tool": "fishing_rod",
            "bait": "sandworm",
            "fish_value": 1200,
            "catch_time": 5,
            "success_rate": lambda level: min(0.45, 0.02 + (level-82) * 0.01)
        },
        "dark_crab": {
            "level": 85,
            "xp": 130.0,
            "tool": "dark_fishing_bait",
            "bait": "lobster_pot",
            "fish_value": 1600,
            "catch_time": 5,
            "success_rate": lambda level: min(0.40, 0.01 + (level-85) * 0.01)
        }
    }

    LOCATIONS = {