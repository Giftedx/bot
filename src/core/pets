from typing import Dict, List


class PetPersonality:
    """Pet personality traits that affect behavior and stats"""

    PERSONALITIES = {
        "brave": {
            "description": "Fearless in battle, higher attack but lower defense",
            "stat_mods": {"attack": 1.2, "defense": 0.8},
            "battle_style": "aggressive",
        },
        "cautious": {
            "description": "Careful and defensive, higher defense but lower attack speed",
            "stat_mods": {"defense": 1.2, "attack_speed": 0.8},
            "battle_style": "defensive",
        },
        "clever": {
            "description": "Smart and strategic, better at special moves",
            "stat_mods": {"special_attack": 1.2, "healing": 1.1},
            "battle_style": "tactical",
        },
        "energetic": {
            "description": "High energy and fast, better speed and agility",
            "stat_mods": {"speed": 1.2, "dodge": 1.1},
            "battle_style": "swift",
        },
        "gentle": {
            "description": "Kind and supportive, better at healing and buffs",
            "stat_mods": {"healing": 1.3, "attack": 0.9},
            "battle_style": "support",
        },
    }

    @staticmethod
    def get_random_personality() -> str:
        """Get a random personality type"""
        import random

        return random.choice(list(PetPersonality.PERSONALITIES.keys()))


class PetType:
    """Different types of pets with unique abilities"""

    TYPES = {
        "dog": {
            "emoji": "🐕",
            "base_stats": {"hp": 100, "attack": 15, "defense": 12},
            "abilities": ["loyal_guard", "fetch", "bark"],
            "evolution_line": ["puppy", "adult_dog", "alpha_dog"],
        },
        "cat": {
            "emoji": "🐱",
            "base_stats": {"hp": 85, "attack": 18, "defense": 10},
            "abilities": ["night_vision", "quick_paw", "pounce"],
            "evolution_line": ["kitten", "adult_cat", "elder_cat"],
        },
        "dragon": {
            "emoji": "🐲",
            "base_stats": {"hp": 120, "attack": 20, "defense": 15},
            "abilities": ["fire_breath", "wing_gust", "intimidate"],
            "evolution_line": ["wyrmling", "young_dragon", "elder_dragon"],
        },
        "unicorn": {
            "emoji": "🦄",
            "base_stats": {"hp": 95, "attack": 12, "defense": 14},
            "abilities": ["healing_horn", "rainbow_dash", "magical_shield"],
            "evolution_line": ["foal", "unicorn", "alicorn"],
        },
        "phoenix": {
            "emoji": "🦅",
            "base_stats": {"hp": 90, "attack": 16, "defense": 13},
            "abilities": ["rebirth", "flame_wing", "sun_beam"],
            "evolution_line": ["chick", "phoenix", "eternal_phoenix"],
        },
    }

    @staticmethod
    def get_abilities(pet_type: str, level: int) -> List[str]:
        """Get available abilities based on pet type and level"""
        if pet_type not in PetType.TYPES:
            return []

        abilities = PetType.TYPES[pet_type]["abilities"]
        # Unlock abilities based on level
        return abilities[: min(len(abilities), level // 5)]


class PetStats:
    """Pet statistics and leveling system"""

    @staticmethod
    def calculate_stats(
        base_stats: Dict[str, int], level: int, personality: str
    ) -> Dict[str, int]:
        """Calculate actual stats based on level and personality"""
        pers_mods = PetPersonality.PERSONALITIES[personality]["stat_mods"]

        stats = {}
        for stat, value in base_stats.items():
            # Level bonus
            level_bonus = value * (level - 1) * 0.1
            # Personality modifier
            pers_mod = pers_mods.get(stat, 1.0)
            # Final stat
            stats[stat] = int((value + level_bonus) * pers_mod)

        return stats

    @staticmethod
    def get_xp_for_level(level: int) -> int:
        """Get XP required for given level"""
        return int(100 * (level**1.5))

    @staticmethod
    def get_level_from_xp(xp: int) -> int:
        """Get level based on total XP"""
        import math

        return int(math.pow(xp / 100, 1 / 1.5))


class BattleMove:
    """Battle moves and abilities"""

    MOVES = {
        # Basic Moves (available to all pets)
        "tackle": {
            "power": 10,
            "accuracy": 0.95,
            "energy": 5,
            "description": "A basic attack",
        },
        "dodge": {
            "power": 0,
            "accuracy": 0.9,
            "energy": 3,
            "effect": "increase_evasion",
            "description": "Increases evasion for one turn",
        },
        "rest": {
            "power": 0,
            "accuracy": 1.0,
            "energy": -20,
            "heal": 15,
            "description": "Recover HP and energy",
        },
        # Type-Specific Moves
        "fire_breath": {
            "power": 25,
            "accuracy": 0.8,
            "energy": 15,
            "type": "dragon",
            "effect": "burn",
            "description": "Powerful fire attack that may burn",
        },
        "healing_horn": {
            "power": 0,
            "accuracy": 1.0,
            "energy": 10,
            "type": "unicorn",
            "heal": 25,
            "description": "Magical healing ability",
        },
        "quick_paw": {
            "power": 15,
            "accuracy": 0.9,
            "energy": 8,
            "type": "cat",
            "effect": "increase_speed",
            "description": "Swift attack that increases speed",
        },
        "loyal_guard": {
            "power": 0,
            "accuracy": 1.0,
            "energy": 12,
            "type": "dog",
            "effect": "increase_defense",
            "description": "Protective stance that boosts defense",
        },
        "rebirth": {
            "power": 0,
            "accuracy": 1.0,
            "energy": 50,
            "type": "phoenix",
            "heal": "full",
            "cooldown": 5,
            "description": "Once per battle resurrection",
        },
    }

    @staticmethod
    def get_available_moves(pet_type: str, level: int, personality: str) -> List[str]:
        """Get moves available to a pet based on type, level, and personality"""
        moves = ["tackle", "dodge", "rest"]  # Basic moves

        # Add type-specific moves based on level
        for move, data in BattleMove.MOVES.items():
            if data.get("type") == pet_type and level >= 5:
                moves.append(move)

        # Add personality-based moves
        battle_style = PetPersonality.PERSONALITIES[personality]["battle_style"]
        if battle_style == "aggressive" and level >= 10:
            moves.append("rage")
        elif battle_style == "defensive" and level >= 10:
            moves.append("shield")

        return moves


class Pet:
    """Main pet class combining all features"""

    def __init__(self, name: str, pet_type: str):
        self.name = name
        self.type = pet_type
        self.personality = PetPersonality.get_random_personality()
        self.level = 1
        self.xp = 0
        self.happiness = 100
        self.energy = 100
        self.base_stats = PetType.TYPES[pet_type]["base_stats"]
        self.abilities = []
        self.moves = []
        self.update_stats()

    def update_stats(self):
        """Update pet stats based on current level and personality"""
        self.stats = PetStats.calculate_stats(
            self.base_stats, self.level, self.personality
        )
        self.abilities = PetType.get_abilities(self.type, self.level)
        self.moves = BattleMove.get_available_moves(
            self.type, self.level, self.personality
        )

    def add_xp(self, amount: int) -> bool:
        """Add XP and return True if leveled up"""
        old_level = self.level
        self.xp += amount
        self.level = PetStats.get_level_from_xp(self.xp)

        if self.level > old_level:
            self.update_stats()
            return True
        return False

    def can_use_move(self, move: str) -> bool:
        """Check if pet can use a specific move"""
        return move in self.moves and self.energy >= BattleMove.MOVES[move]["energy"]

    def use_move(self, move: str) -> Dict:
        """Use a move and return the results"""
        if not self.can_use_move(move):
            return {"error": "Cannot use this move"}

        move_data = BattleMove.MOVES[move]
        self.energy -= move_data["energy"]

        return {
            "power": move_data.get("power", 0),
            "accuracy": move_data["accuracy"],
            "effects": move_data.get("effect", None),
            "heal": move_data.get("heal", 0),
        }
