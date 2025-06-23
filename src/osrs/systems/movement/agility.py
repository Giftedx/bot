"""OSRS Agility System"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import random
import asyncio
from datetime import datetime


class ObstacleType(Enum):
    CLIMB = "climb"
    JUMP = "jump"
    BALANCE = "balance"
    CRAWL = "crawl"
    SWING = "swing"
    CROSS = "cross"
    SQUEEZE = "squeeze"


@dataclass
class ObstacleRequirements:
    """Requirements to attempt an obstacle"""

    agility_level: int
    quest_requirements: List[str] = None
    item_requirements: List[str] = None


@dataclass
class ObstacleReward:
    """Reward for completing an obstacle"""

    experience: float
    marks_of_grace: float = 0.0  # Chance to spawn mark of grace


class Obstacle:
    """Represents an agility obstacle"""

    def __init__(
        self,
        name: str,
        type: ObstacleType,
        requirements: ObstacleRequirements,
        reward: ObstacleReward,
        fail_damage: Tuple[int, int],  # (min, max) damage on fail
        fail_chance: float,  # Base chance of failing
        ticks_to_complete: int,
    ):
        self.name = name
        self.type = type
        self.requirements = requirements
        self.reward = reward
        self.fail_damage = fail_damage
        self.fail_chance = fail_chance
        self.ticks_to_complete = ticks_to_complete


@dataclass
class CourseRequirements:
    """Requirements to attempt an agility course"""

    agility_level: int
    quest_requirements: List[str] = None
    item_requirements: List[str] = None


@dataclass
class CourseReward:
    """Reward for completing a course"""

    experience: float
    marks_of_grace: float  # Chance to spawn mark of grace
    completion_bonus: float = 0.0  # Bonus XP for completing full course


class AgilityCourse:
    """Represents an agility training course"""

    def __init__(
        self,
        name: str,
        location: str,
        requirements: CourseRequirements,
        reward: CourseReward,
        obstacles: List[Obstacle],
        lap_record: float = float("inf"),  # Best possible lap time in seconds
    ):
        self.name = name
        self.location = location
        self.requirements = requirements
        self.reward = reward
        self.obstacles = obstacles
        self.lap_record = lap_record


class AgilityShortcut:
    """Represents an agility shortcut"""

    def __init__(
        self,
        name: str,
        start_location: str,
        end_location: str,
        obstacle: Obstacle,
        bidirectional: bool = True,
    ):
        self.name = name
        self.start_location = start_location
        self.end_location = end_location
        self.obstacle = obstacle
        self.bidirectional = bidirectional


class AgilityManager:
    """Manages agility courses and shortcuts"""

    def __init__(self):
        self.courses = self._load_courses()
        self.shortcuts = self._load_shortcuts()
        self.active_laps: Dict[
            str, Tuple[str, datetime, int]
        ] = {}  # player_id -> (course, start_time, obstacle_index)

    def _load_courses(self) -> Dict[str, AgilityCourse]:
        """Load all agility course definitions"""
        return {
            "Gnome Stronghold": AgilityCourse(
                name="Gnome Stronghold",
                location="Tree Gnome Stronghold",
                requirements=CourseRequirements(agility_level=1),
                reward=CourseReward(experience=86.5, marks_of_grace=0.0, completion_bonus=39.5),
                obstacles=[
                    Obstacle(
                        name="Log balance",
                        type=ObstacleType.BALANCE,
                        requirements=ObstacleRequirements(agility_level=1),
                        reward=ObstacleReward(experience=7.5),
                        fail_damage=(1, 3),
                        fail_chance=0.2,
                        ticks_to_complete=4,
                    ),
                    Obstacle(
                        name="Obstacle net",
                        type=ObstacleType.CLIMB,
                        requirements=ObstacleRequirements(agility_level=1),
                        reward=ObstacleReward(experience=7.5),
                        fail_damage=(0, 0),
                        fail_chance=0.0,
                        ticks_to_complete=3,
                    ),
                    Obstacle(
                        name="Tree branch",
                        type=ObstacleType.BALANCE,
                        requirements=ObstacleRequirements(agility_level=1),
                        reward=ObstacleReward(experience=5.0),
                        fail_damage=(1, 3),
                        fail_chance=0.15,
                        ticks_to_complete=3,
                    ),
                    # Add more obstacles...
                ],
                lap_record=27.0,
            ),
            "Draynor Village": AgilityCourse(
                name="Draynor Village",
                location="Draynor Village",
                requirements=CourseRequirements(agility_level=10),
                reward=CourseReward(experience=120.0, marks_of_grace=0.8, completion_bonus=79.0),
                obstacles=[
                    Obstacle(
                        name="Rough wall",
                        type=ObstacleType.CLIMB,
                        requirements=ObstacleRequirements(agility_level=10),
                        reward=ObstacleReward(experience=8.0),
                        fail_damage=(1, 3),
                        fail_chance=0.1,
                        ticks_to_complete=3,
                    ),
                    Obstacle(
                        name="Tightrope",
                        type=ObstacleType.BALANCE,
                        requirements=ObstacleRequirements(agility_level=10),
                        reward=ObstacleReward(experience=8.0),
                        fail_damage=(2, 6),
                        fail_chance=0.2,
                        ticks_to_complete=5,
                    ),
                    # Add more obstacles...
                ],
                lap_record=43.2,
            ),
        }

    def _load_shortcuts(self) -> Dict[str, AgilityShortcut]:
        """Load all agility shortcut definitions"""
        return {
            "Grand Exchange wall": AgilityShortcut(
                name="Grand Exchange wall",
                start_location="Grand Exchange",
                end_location="Edgeville",
                obstacle=Obstacle(
                    name="Wall",
                    type=ObstacleType.CLIMB,
                    requirements=ObstacleRequirements(agility_level=21),
                    reward=ObstacleReward(experience=5.0),
                    fail_damage=(1, 3),
                    fail_chance=0.1,
                    ticks_to_complete=2,
                ),
            ),
            "Al Kharid pit": AgilityShortcut(
                name="Al Kharid pit",
                start_location="Al Kharid",
                end_location="Lumbridge Swamp",
                obstacle=Obstacle(
                    name="Pit shortcut",
                    type=ObstacleType.SQUEEZE,
                    requirements=ObstacleRequirements(agility_level=38),
                    reward=ObstacleReward(experience=0.0),
                    fail_damage=(0, 0),
                    fail_chance=0.0,
                    ticks_to_complete=3,
                ),
            ),
        }

    async def start_course(
        self,
        player_id: str,
        course_name: str,
        player_agility: int,
        player_quests: Set[str],
        player_items: Set[str],
    ) -> Optional[str]:
        """Start an agility course"""
        if player_id in self.active_laps:
            return "You are already on a course!"

        course = self.courses.get(course_name)
        if not course:
            return f"Could not find course: {course_name}"

        # Check requirements
        reqs = course.requirements
        if player_agility < reqs.agility_level:
            return f"You need level {reqs.agility_level} Agility to attempt this course!"

        if reqs.quest_requirements and not all(q in player_quests for q in reqs.quest_requirements):
            return "You do not meet the quest requirements for this course!"

        if reqs.item_requirements and not all(i in player_items for i in reqs.item_requirements):
            return "You do not have the required items for this course!"

        # Start lap
        self.active_laps[player_id] = (course_name, datetime.now(), 0)
        return f"You start the {course_name} Agility Course"

    async def attempt_obstacle(
        self, player_id: str, player_hitpoints: int
    ) -> Tuple[Optional[int], Optional[float], Optional[str]]:
        """
        Attempt current obstacle in course
        Returns (damage_taken, xp_gained, message)
        """
        if player_id not in self.active_laps:
            return None, None, "You are not on an agility course!"

        course_name, start_time, obstacle_index = self.active_laps[player_id]
        course = self.courses[course_name]

        if obstacle_index >= len(course.obstacles):
            # Lap complete
            del self.active_laps[player_id]
            return (
                None,
                course.reward.completion_bonus,
                f"You complete the {course_name} Agility Course!",
            )

        # Attempt obstacle
        obstacle = course.obstacles[obstacle_index]

        # Check for fail
        fail_roll = random.random()
        if fail_roll < obstacle.fail_chance:
            # Failed obstacle
            damage = random.randint(*obstacle.fail_damage)
            if damage >= player_hitpoints:
                damage = player_hitpoints - 1  # Never kill player

            self.active_laps[player_id] = (course_name, start_time, obstacle_index)
            return damage, 0, f"You fail the {obstacle.name} and take {damage} damage!"

        # Success
        await asyncio.sleep(obstacle.ticks_to_complete * 0.6)  # 0.6s per tick

        # Check for mark of grace
        mark_chance = course.reward.marks_of_grace
        if random.random() < mark_chance:
            message = f"You find a Mark of grace!"
        else:
            message = f"You successfully pass the {obstacle.name}"

        # Move to next obstacle
        self.active_laps[player_id] = (course_name, start_time, obstacle_index + 1)

        return None, obstacle.reward.experience, message

    async def use_shortcut(
        self,
        player_id: str,
        shortcut_name: str,
        player_agility: int,
        player_quests: Set[str],
        player_items: Set[str],
        player_hitpoints: int,
        from_location: str,
    ) -> Tuple[Optional[str], Optional[int], Optional[float], Optional[str]]:
        """
        Attempt to use an agility shortcut
        Returns (new_location, damage_taken, xp_gained, message)
        """
        shortcut = self.shortcuts.get(shortcut_name)
        if not shortcut:
            return None, None, None, f"Could not find shortcut: {shortcut_name}"

        # Check location
        if from_location != shortcut.start_location:
            if shortcut.bidirectional and from_location == shortcut.end_location:
                # Swap start/end for bidirectional shortcuts
                shortcut.start_location, shortcut.end_location = (
                    shortcut.end_location,
                    shortcut.start_location,
                )
            else:
                return None, None, None, "You cannot use that shortcut from here!"

        # Check requirements
        obstacle = shortcut.obstacle
        reqs = obstacle.requirements

        if player_agility < reqs.agility_level:
            return (
                None,
                None,
                None,
                f"You need level {reqs.agility_level} Agility to use this shortcut!",
            )

        if reqs.quest_requirements and not all(q in player_quests for q in reqs.quest_requirements):
            return None, None, None, "You do not meet the quest requirements for this shortcut!"

        if reqs.item_requirements and not all(i in player_items for i in reqs.item_requirements):
            return None, None, None, "You do not have the required items for this shortcut!"

        # Attempt shortcut
        fail_roll = random.random()
        if fail_roll < obstacle.fail_chance:
            # Failed obstacle
            damage = random.randint(*obstacle.fail_damage)
            if damage >= player_hitpoints:
                damage = player_hitpoints - 1  # Never kill player
            return None, damage, 0, f"You fail the {shortcut_name} and take {damage} damage!"

        # Success
        await asyncio.sleep(obstacle.ticks_to_complete * 0.6)
        return (
            shortcut.end_location,
            None,
            obstacle.reward.experience,
            f"You successfully use the {shortcut_name}",
        )

    def get_available_shortcuts(self, location: str, player_agility: int) -> List[str]:
        """Get list of shortcuts available from current location"""
        available = []

        for name, shortcut in self.shortcuts.items():
            if shortcut.start_location == location or (
                shortcut.bidirectional and shortcut.end_location == location
            ):
                if player_agility >= shortcut.obstacle.requirements.agility_level:
                    available.append(name)

        return available

    def get_lap_time(self, player_id: str) -> Optional[float]:
        """Get current lap time in seconds"""
        if player_id not in self.active_laps:
            return None

        course_name, start_time, _ = self.active_laps[player_id]
        return (datetime.now() - start_time).total_seconds()
