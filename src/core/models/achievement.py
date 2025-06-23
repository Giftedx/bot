from typing import Dict, TypedDict

class Achievement(TypedDict):
    id: int
    name: str
    description: str
    category: str
    rewards: Dict[str, int] # e.g., {"xp": 100, "coins": 500} 