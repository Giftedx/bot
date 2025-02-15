from dataclasses import dataclass
from typing import Dict, List, Any
from enum import Enum

class AchievementType(Enum):
    COLLECTION = "collection"
    TRAINING = "training"
    CROSS_SYSTEM = "cross_system"
    SPECIAL = "special"

@dataclass
class Achievement:
    id: str
    name: str
    description: str
    type: AchievementType
    requirements: Dict[str, Any]
    rewards: Dict[str, Any]
    icon: str  # Discord emoji or custom emoji ID

class AchievementConfig:
    def __init__(self):
        self.achievements = {
            # Collection Achievements
            "catch_all_starters": Achievement(
                id="catch_all_starters",
                name="Starter Collector",
                description="Obtain all starter Pokemon (Charmander, Bulbasaur, Pikachu)",
                type=AchievementType.COLLECTION,
                requirements={
                    "pokemon_species": ["Charmander", "Bulbasaur", "Pikachu"]
                },
                rewards={
                    "boost": {"type": "catch_rate", "value": 0.05, "duration_hours": 48},
                    "title": "Starter Master"
                },
                icon="🌟"
            ),
            "boss_pet_collector": Achievement(
                id="boss_pet_collector",
                name="Boss Pet Hunter",
                description="Obtain all OSRS boss pets",
                type=AchievementType.COLLECTION,
                requirements={
                    "osrs_pets": ["Baby Mole", "Prince Black Dragon", "Pet Chaos Elemental"]
                },
                rewards={
                    "boost": {"type": "combat_exp", "value": 0.1, "duration_hours": 72},
                    "title": "Boss Pet Master"
                },
                icon="👑"
            ),

            # Training Achievements
            "max_combat": Achievement(
                id="max_combat",
                name="Combat Master",
                description="Get an OSRS pet to level 99 combat",
                type=AchievementType.TRAINING,
                requirements={
                    "osrs_combat_level": 99
                },
                rewards={
                    "boost": {"type": "pokemon_exp", "value": 0.15, "permanent": True},
                    "title": "Combat Legend"
                },
                icon="⚔️"
            ),
            "evolution_master": Achievement(
                id="evolution_master",
                name="Evolution Master",
                description="Evolve 3 different Pokemon",
                type=AchievementType.TRAINING,
                requirements={
                    "pokemon_evolutions": 3
                },
                rewards={
                    "boost": {"type": "osrs_pet_chance", "value": 0.1, "duration_hours": 48},
                    "title": "Evolution Expert"
                },
                icon="🔄"
            ),

            # Cross-System Achievements
            "hybrid_trainer": Achievement(
                id="hybrid_trainer",
                name="Hybrid Pet Trainer",
                description="Get both an OSRS pet and a Pokemon to level 50",
                type=AchievementType.CROSS_SYSTEM,
                requirements={
                    "osrs_pet_level": 50,
                    "pokemon_level": 50
                },
                rewards={
                    "boost": {"type": "all_exp", "value": 0.1, "duration_hours": 72},
                    "title": "Hybrid Master"
                },
                icon="🎮"
            ),
            "rare_collector": Achievement(
                id="rare_collector",
                name="Rare Pet Collector",
                description="Obtain 3 rare or higher rarity pets of any type",
                type=AchievementType.CROSS_SYSTEM,
                requirements={
                    "rare_pets": 3,
                    "min_rarity": "rare"
                },
                rewards={
                    "boost": {"type": "rare_chance", "value": 0.15, "permanent": True},
                    "title": "Rare Hunter"
                },
                icon="💎"
            ),

            # Special Achievements
            "perfect_trainer": Achievement(
                id="perfect_trainer",
                name="Perfect Trainer",
                description="Get a perfect stat Pokemon and a level 99 OSRS pet",
                type=AchievementType.SPECIAL,
                requirements={
                    "max_stat_pokemon": True,
                    "max_level_osrs": True
                },
                rewards={
                    "boost": {"type": "all", "value": 0.2, "permanent": True},
                    "title": "Perfect Master",
                    "custom_effect": "rainbow_name"
                },
                icon="🌈"
            ),
            "milestone_master": Achievement(
                id="milestone_master",
                name="Milestone Master",
                description="Reach 1000 total boss kills and evolve 10 Pokemon",
                type=AchievementType.SPECIAL,
                requirements={
                    "total_boss_kills": 1000,
                    "total_evolutions": 10
                },
                rewards={
                    "boost": {"type": "all_chance", "value": 0.15, "permanent": True},
                    "title": "Grand Master",
                    "custom_effect": "sparkle_name"
                },
                icon="✨"
            )
        }

    def get_achievement(self, achievement_id: str) -> Achievement:
        """Get achievement by ID"""
        return self.achievements.get(achievement_id)

    def get_achievements_by_type(self, achievement_type: AchievementType) -> List[Achievement]:
        """Get all achievements of a specific type"""
        return [ach for ach in self.achievements.values() if ach.type == achievement_type]

    def get_cross_system_achievements(self) -> List[Achievement]:
        """Get all cross-system achievements"""
        return self.get_achievements_by_type(AchievementType.CROSS_SYSTEM)

    def check_achievement_completion(self, achievement: Achievement, user_data: Dict[str, Any]) -> bool:
        """Check if a user has completed an achievement"""
        for req_key, req_value in achievement.requirements.items():
            if req_key not in user_data or user_data[req_key] < req_value:
                return False
        return True

achievement_config = AchievementConfig() 