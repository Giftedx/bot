from typing import Dict, TypedDict
from enum import Enum

class QuestStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class QuestData(TypedDict):
    id: int
    name: str
    description: str
    difficulty: str
    quest_points: int
    requirements: Dict[str, int]  # skill_name -> level
    rewards: Dict[str, int]  # reward_type -> amount 