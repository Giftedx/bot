"""Achievement manager for handling achievement tracking and rewards."""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from .game_tick import GameTick, TickPriority
from .skill_manager import SkillType

class AchievementDifficulty(Enum):
    """Achievement difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ELITE = "elite"
    MASTER = "master"

class AchievementCategory(Enum):
    """Achievement categories."""
    COMBAT = "combat"
    SKILLS = "skills"
    QUESTS = "quests"
    MINIGAMES = "minigames"
    EXPLORATION = "exploration"
    DIARIES = "diaries"
    MISC = "misc"

@dataclass
class AchievementRequirement:
    """Requirement for an achievement."""
    type: str  # skill, quest, item, etc.
    id: str  # skill name, quest id, item id, etc.
    value: int  # level required, quantity needed, etc.
    description: str

@dataclass
class AchievementReward:
    """Reward for completing an achievement."""
    type: str  # xp, item, unlock, etc.
    id: str  # skill name, item id, unlock id, etc.
    value: int  # xp amount, item quantity, etc.
    description: str

@dataclass
class Achievement:
    """Represents an achievement."""
    id: str
    name: str
    description: str
    category: AchievementCategory
    difficulty: AchievementDifficulty
    requirements: List[AchievementRequirement]
    rewards: List[AchievementReward]
    points: int
    is_hidden: bool = False
    series: Optional[str] = None  # Achievement diary/series name

class AchievementProgress:
    """Tracks progress for an achievement."""
    
    def __init__(self, achievement: Achievement):
        """Initialize achievement progress.
        
        Args:
            achievement: Achievement being tracked
        """
        self.achievement = achievement
        self.completed = False
        self.completed_at = None
        self.progress: Dict[str, int] = {}  # requirement_id: current_value
        
        # Initialize progress tracking
        for req in achievement.requirements:
            self.progress[req.id] = 0

class AchievementManager:
    """Manages achievement tracking and rewards."""
    
    def __init__(self, game_tick: GameTick):
        """Initialize achievement manager.
        
        Args:
            game_tick: GameTick system instance
        """
        self.game_tick = game_tick
        self.achievements: Dict[str, Achievement] = {}
        self.player_progress: Dict[int, Dict[str, AchievementProgress]] = {}  # player_id: {achievement_id: progress}
        
        # Register achievement tick task
        self.game_tick.register_task(
            "achievement_update",
            self._achievement_tick,
            TickPriority.WORLD
        )
        
    async def _achievement_tick(self):
        """Process achievement updates for current game tick."""
        # Process achievement-related events
        pass
        
    def add_achievement(self, achievement: Achievement):
        """Add an achievement to the manager.
        
        Args:
            achievement: Achievement to add
        """
        self.achievements[achievement.id] = achievement
        
    def get_achievement(self, achievement_id: str) -> Optional[Achievement]:
        """Get achievement by ID.
        
        Args:
            achievement_id: Achievement identifier
            
        Returns:
            Achievement if found, None otherwise
        """
        return self.achievements.get(achievement_id)
        
    def get_player_progress(self,
                          player_id: int,
                          achievement_id: str) -> Optional[AchievementProgress]:
        """Get player's progress for an achievement.
        
        Args:
            player_id: Player's ID
            achievement_id: Achievement identifier
            
        Returns:
            Achievement progress if found
        """
        return self.player_progress.get(player_id, {}).get(achievement_id)
        
    def initialize_player(self, player_id: int):
        """Initialize achievement tracking for a player.
        
        Args:
            player_id: Player's ID
        """
        if player_id not in self.player_progress:
            self.player_progress[player_id] = {}
            
        # Initialize progress for all achievements
        for achievement in self.achievements.values():
            if achievement.id not in self.player_progress[player_id]:
                self.player_progress[player_id][achievement.id] = AchievementProgress(achievement)
                
    def update_progress(self,
                       player_id: int,
                       requirement_type: str,
                       requirement_id: str,
                       value: int):
        """Update progress for achievements.
        
        Args:
            player_id: Player's ID
            requirement_type: Type of requirement being updated
            requirement_id: Identifier for requirement
            value: New value for requirement
        """
        if player_id not in self.player_progress:
            return
            
        # Update progress for all relevant achievements
        for achievement_id, progress in self.player_progress[player_id].items():
            if progress.completed:
                continue
                
            achievement = self.achievements[achievement_id]
            
            # Find matching requirements
            for req in achievement.requirements:
                if req.type == requirement_type and req.id == requirement_id:
                    progress.progress[req.id] = value
                    
                    # Check if achievement is completed
                    if self._check_completion(progress):
                        self._complete_achievement(player_id, achievement_id)
                        
    def _check_completion(self, progress: AchievementProgress) -> bool:
        """Check if all requirements are met.
        
        Args:
            progress: Achievement progress to check
            
        Returns:
            True if all requirements are met
        """
        for req in progress.achievement.requirements:
            if progress.progress.get(req.id, 0) < req.value:
                return False
        return True
        
    def _complete_achievement(self,
                            player_id: int,
                            achievement_id: str):
        """Mark achievement as completed and grant rewards.
        
        Args:
            player_id: Player's ID
            achievement_id: Achievement being completed
        """
        progress = self.player_progress[player_id][achievement_id]
        if progress.completed:
            return
            
        progress.completed = True
        progress.completed_at = self.game_tick.get_tick_count()
        
        # Grant rewards
        achievement = self.achievements[achievement_id]
        for reward in achievement.rewards:
            self._grant_reward(player_id, reward)
            
    def _grant_reward(self,
                     player_id: int,
                     reward: AchievementReward):
        """Grant a reward to a player.
        
        Args:
            player_id: Player's ID
            reward: Reward to grant
        """
        # This would integrate with other systems to grant rewards
        # For example:
        # if reward.type == "xp":
        #     skill_manager.add_experience(player_id, reward.id, reward.value)
        # elif reward.type == "item":
        #     inventory_manager.add_item(player_id, reward.id, reward.value)
        pass
        
    def get_completed_achievements(self,
                                 player_id: int,
                                 category: Optional[AchievementCategory] = None) -> List[Achievement]:
        """Get player's completed achievements.
        
        Args:
            player_id: Player's ID
            category: Optional category filter
            
        Returns:
            List of completed achievements
        """
        if player_id not in self.player_progress:
            return []
            
        completed = []
        for achievement_id, progress in self.player_progress[player_id].items():
            if progress.completed:
                achievement = self.achievements[achievement_id]
                if not category or achievement.category == category:
                    completed.append(achievement)
                    
        return completed
        
    def get_achievement_points(self, player_id: int) -> int:
        """Get player's total achievement points.
        
        Args:
            player_id: Player's ID
            
        Returns:
            Total achievement points
        """
        if player_id not in self.player_progress:
            return 0
            
        return sum(
            self.achievements[achievement_id].points
            for achievement_id, progress in self.player_progress[player_id].items()
            if progress.completed
        )
        
    def get_series_progress(self,
                          player_id: int,
                          series: str) -> Tuple[int, int]:
        """Get progress in an achievement series.
        
        Args:
            player_id: Player's ID
            series: Achievement series name
            
        Returns:
            Tuple of (completed count, total count)
        """
        series_achievements = [
            achievement for achievement in self.achievements.values()
            if achievement.series == series
        ]
        
        if not series_achievements:
            return (0, 0)
            
        completed = sum(
            1 for achievement in series_achievements
            if self.player_progress.get(player_id, {}).get(achievement.id, AchievementProgress(achievement)).completed
        )
        
        return (completed, len(series_achievements))
        
    def get_available_achievements(self,
                                 player_id: int,
                                 player_stats: Dict[SkillType, int],
                                 completed_quests: Set[str],
                                 inventory: Dict[str, int]) -> List[Achievement]:
        """Get achievements available to complete.
        
        Args:
            player_id: Player's ID
            player_stats: Player's skill levels
            completed_quests: Set of completed quest IDs
            inventory: Player's inventory
            
        Returns:
            List of available achievements
        """
        if player_id not in self.player_progress:
            return []
            
        available = []
        for achievement in self.achievements.values():
            # Skip if already completed
            progress = self.player_progress[player_id][achievement.id]
            if progress.completed:
                continue
                
            # Check if requirements can be met
            can_complete = True
            for req in achievement.requirements:
                if req.type == "skill" and player_stats.get(req.id, 1) < req.value:
                    can_complete = False
                    break
                elif req.type == "quest" and req.id not in completed_quests:
                    can_complete = False
                    break
                elif req.type == "item" and inventory.get(req.id, 0) < req.value:
                    can_complete = False
                    break
                    
            if can_complete:
                available.append(achievement)
                
        return available 