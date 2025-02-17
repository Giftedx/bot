from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import math
import asyncio

from .movement import Tile, TileType, MovementSystem

class ObstacleType(Enum):
    BALANCE = "balance"
    CLIMB = "climb"
    CRAWL = "crawl"
    JUMP = "jump"
    SWING = "swing"
    CROSS = "cross"
    SQUEEZE = "squeeze"
    VAULT = "vault"

@dataclass
class AgilityObstacle:
    name: str
    type: ObstacleType
    level_required: int
    experience: float
    fail_rate: float  # Base fail rate at required level
    fail_damage: Tuple[int, int]  # (min_damage, max_damage)
    tile: Tile
    next_tile: Tile  # Where you end up after completing the obstacle
    animation_id: int
    completion_delay: float  # Time in seconds to complete
    fail_message: str
    success_message: str

@dataclass
class AgilityCourse:
    name: str
    location: str
    min_level: int
    obstacles: List[AgilityObstacle]
    total_experience: float
    completion_bonus: float
    mark_of_grace_chance: float
    lap_count: int = 0

class AgilitySystem:
    def __init__(self, movement_system: MovementSystem):
        self.movement = movement_system
        self.courses: Dict[str, AgilityCourse] = {}
        self.current_course: Optional[AgilityCourse] = None
        self.total_marks_of_grace: int = 0
        self.experience: float = 0
        self.level: int = 1
        self.current_obstacle: Optional[AgilityObstacle] = None

    def calculate_level(self) -> int:
        """Calculate agility level from experience."""
        # OSRS level calculation formula
        for level in range(1, 100):
            xp = sum(math.floor(level + 300 * (2 ** (level / 7.0))) for level in range(1, level))
            if xp > self.experience:
                return level - 1
        return 99

    def calculate_fail_rate(self, obstacle: AgilityObstacle) -> float:
        """Calculate actual fail rate based on player's level."""
        if self.level < obstacle.level_required:
            return 1.0  # 100% fail if under required level
        
        level_difference = self.level - obstacle.level_required
        reduction = min(0.9, level_difference * 0.05)  # Up to 90% reduction
        return max(0.01, obstacle.fail_rate * (1 - reduction))  # Minimum 1% fail rate

    def calculate_mark_of_grace_chance(self, course: AgilityCourse) -> float:
        """Calculate actual Mark of Grace chance based on level and lap count."""
        base_chance = course.mark_of_grace_chance
        level_bonus = max(0, (self.level - course.min_level) * 0.002)
        lap_bonus = min(0.1, course.lap_count * 0.001)  # Up to 10% bonus from laps
        return min(1.0, base_chance + level_bonus + lap_bonus)

    async def attempt_obstacle(self, obstacle: AgilityObstacle) -> Tuple[bool, str]:
        """Attempt to complete an agility obstacle."""
        if self.level < obstacle.level_required:
            return False, f"You need {obstacle.level_required} Agility to attempt this obstacle."

        self.current_obstacle = obstacle
        fail_rate = self.calculate_fail_rate(obstacle)

        # Simulate obstacle attempt
        await asyncio.sleep(0.5)  # Initial delay for starting animation

        if random.random() < fail_rate:
            # Failed attempt
            damage = random.randint(obstacle.fail_damage[0], obstacle.fail_damage[1])
            await asyncio.sleep(1.5)  # Delay for fail animation
            self.current_obstacle = None
            return False, f"{obstacle.fail_message} You take {damage} damage."

        # Successful attempt
        await asyncio.sleep(obstacle.completion_delay)
        self.experience += obstacle.experience
        self.level = self.calculate_level()
        self.movement.current_position = (obstacle.next_tile.x, obstacle.next_tile.y, obstacle.next_tile.z)
        self.current_obstacle = None
        
        return True, obstacle.success_message

    async def start_course(self, course_name: str) -> Tuple[bool, str]:
        """Start an agility course."""
        if course_name not in self.courses:
            return False, f"Course '{course_name}' not found."

        course = self.courses[course_name]
        if self.level < course.min_level:
            return False, f"You need {course.min_level} Agility to attempt this course."

        self.current_course = course
        return True, f"Starting {course.name} Agility Course."

    async def complete_lap(self) -> Tuple[bool, str, Dict[str, any]]:
        """Complete a lap of the current course."""
        if not self.current_course:
            return False, "You are not on an agility course.", {}

        # Award completion bonus
        self.experience += self.current_course.completion_bonus
        self.current_course.lap_count += 1
        
        # Check for Mark of Grace
        rewards = {"experience": self.current_course.completion_bonus}
        if random.random() < self.calculate_mark_of_grace_chance(self.current_course):
            self.total_marks_of_grace += 1
            rewards["marks_of_grace"] = 1

        return True, f"Lap completed! Total laps: {self.current_course.lap_count}", rewards

    def get_available_courses(self) -> List[Tuple[str, int, float]]:
        """Get list of available agility courses."""
        return [
            (name, course.min_level, course.total_experience)
            for name, course in self.courses.items()
            if self.level >= course.min_level
        ]

    def get_course_info(self, course_name: str) -> Optional[Dict[str, any]]:
        """Get detailed information about a course."""
        course = self.courses.get(course_name)
        if not course:
            return None

        return {
            "name": course.name,
            "location": course.location,
            "min_level": course.min_level,
            "obstacles": len(course.obstacles),
            "total_exp": course.total_experience,
            "completion_bonus": course.completion_bonus,
            "mark_chance": course.mark_of_grace_chance,
            "best_exp_rate": course.total_experience * (3600 / (len(course.obstacles) * 2.5))  # Estimated exp/hr
        }

    def get_progress_to_level(self) -> Tuple[int, float, float]:
        """Get progress to next level."""
        current_level = self.level
        current_xp = self.experience
        next_level_xp = sum(math.floor(current_level + 1 + 300 * (2 ** ((current_level + 1) / 7.0))) for level in range(1, current_level + 1))
        
        xp_needed = next_level_xp - current_xp
        progress = (current_xp / next_level_xp) * 100 if next_level_xp > 0 else 100

        return current_level, xp_needed, progress 