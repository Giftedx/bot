"""OSRS Achievement System"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from enum import Enum
import asyncio
from datetime import datetime


class AchievementTier(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ELITE = "elite"


class AchievementCategory(Enum):
    COMBAT = "combat"
    SKILLS = "skills"
    QUESTS = "quests"
    MINIGAMES = "minigames"
    EXPLORATION = "exploration"
    COLLECTION = "collection"


@dataclass
class AchievementRequirement:
    """Requirements for an achievement"""

    skills: Dict[str, int] = None
    quests: List[str] = None
    items: Dict[str, int] = None  # item -> quantity
    monsters_killed: Dict[str, int] = None
    minigames_completed: Dict[str, int] = None
    locations_visited: Set[str] = None


@dataclass
class AchievementReward:
    """Rewards for completing an achievement"""

    experience: Dict[str, int] = None  # skill -> xp
    items: Dict[str, int] = None  # item -> quantity
    achievement_points: int = 0
    unlocks: Set[str] = None


class Achievement:
    """Represents an OSRS achievement"""

    def __init__(
        self,
        name: str,
        description: str,
        tier: AchievementTier,
        category: AchievementCategory,
        requirements: AchievementRequirement,
        rewards: AchievementReward,
    ):
        self.name = name
        self.description = description
        self.tier = tier
        self.category = category
        self.requirements = requirements
        self.rewards = rewards


@dataclass
class AchievementProgress:
    """Tracks progress towards an achievement"""

    achievement: Achievement
    completed: bool = False
    completion_date: Optional[datetime] = None
    progress: Dict[str, int] = None  # requirement -> current value


class AchievementManager:
    """Manages all achievements and player progress"""

    def __init__(self):
        self.achievements = self._load_achievements()
        self.player_progress: Dict[str, Dict[str, AchievementProgress]] = {}

    def _load_achievements(self) -> Dict[str, Achievement]:
        """Load all achievement definitions"""
        return {
            "Dragon Slayer": Achievement(
                name="Dragon Slayer",
                description="Complete the Dragon Slayer quest",
                tier=AchievementTier.MEDIUM,
                category=AchievementCategory.QUESTS,
                requirements=AchievementRequirement(quests=["Dragon Slayer"]),
                rewards=AchievementReward(achievement_points=10, items={"Dragon slayer trophy": 1}),
            ),
            "Combat Master": Achievement(
                name="Combat Master",
                description="Achieve level 99 in all combat skills",
                tier=AchievementTier.ELITE,
                category=AchievementCategory.COMBAT,
                requirements=AchievementRequirement(
                    skills={
                        "attack": 99,
                        "strength": 99,
                        "defence": 99,
                        "ranged": 99,
                        "magic": 99,
                        "prayer": 99,
                        "hitpoints": 99,
                    }
                ),
                rewards=AchievementReward(
                    achievement_points=50,
                    items={"Combat master cape": 1},
                    unlocks={"Combat master title"},
                ),
            ),
            "Pest Control Expert": Achievement(
                name="Pest Control Expert",
                description="Complete 500 games of Pest Control",
                tier=AchievementTier.HARD,
                category=AchievementCategory.MINIGAMES,
                requirements=AchievementRequirement(minigames_completed={"Pest Control": 500}),
                rewards=AchievementReward(achievement_points=25, items={"Void knight seal": 1}),
            ),
            # Add more achievements...
        }

    def get_player_achievements(self, player_id: str) -> Dict[str, AchievementProgress]:
        """Get all achievements and their progress for a player"""
        if player_id not in self.player_progress:
            self.player_progress[player_id] = {
                name: AchievementProgress(achievement=achievement)
                for name, achievement in self.achievements.items()
            }
        return self.player_progress[player_id]

    def update_achievement_progress(
        self,
        player_id: str,
        player_stats: Dict[str, int],
        completed_quests: Set[str],
        minigame_completions: Dict[str, int],
        monster_kills: Dict[str, int],
        visited_locations: Set[str],
    ) -> List[Achievement]:
        """Update achievement progress and return newly completed achievements"""
        completed = []
        player_achievements = self.get_player_achievements(player_id)

        for name, progress in player_achievements.items():
            if progress.completed:
                continue

            achievement = progress.achievement
            reqs = achievement.requirements

            # Update progress tracking
            if not progress.progress:
                progress.progress = {}

            # Check skills
            if reqs.skills:
                for skill, level in reqs.skills.items():
                    current = player_stats.get(skill, 0)
                    progress.progress[f"skill_{skill}"] = current
                    if current < level:
                        continue

            # Check quests
            if reqs.quests and not all(q in completed_quests for q in reqs.quests):
                continue

            # Check minigames
            if reqs.minigames_completed:
                completed_all = True
                for game, count in reqs.minigames_completed.items():
                    current = minigame_completions.get(game, 0)
                    progress.progress[f"minigame_{game}"] = current
                    if current < count:
                        completed_all = False
                if not completed_all:
                    continue

            # Check monster kills
            if reqs.monsters_killed:
                killed_all = True
                for monster, count in reqs.monsters_killed.items():
                    current = monster_kills.get(monster, 0)
                    progress.progress[f"kills_{monster}"] = current
                    if current < count:
                        killed_all = False
                if not killed_all:
                    continue

            # Check locations
            if reqs.locations_visited and not reqs.locations_visited.issubset(visited_locations):
                continue

            # All requirements met
            progress.completed = True
            progress.completion_date = datetime.now()
            completed.append(achievement)

        return completed

    def get_achievement_rewards(
        self, player_id: str, achievement_name: str
    ) -> Optional[AchievementReward]:
        """Get rewards for a completed achievement"""
        progress = self.get_player_achievements(player_id).get(achievement_name)
        if not progress or not progress.completed:
            return None
        return progress.achievement.rewards

    def get_total_achievement_points(self, player_id: str) -> int:
        """Get total achievement points for a player"""
        total = 0
        for progress in self.get_player_achievements(player_id).values():
            if progress.completed:
                total += progress.achievement.rewards.achievement_points
        return total
