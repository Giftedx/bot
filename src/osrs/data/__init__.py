"""OSRS data module for managing game data files."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Data file paths
DATA_DIR = Path(__file__).parent
ITEMS_FILE = DATA_DIR / "items.json"
QUESTS_FILE = DATA_DIR / "quests.json"
SKILLS_FILE = DATA_DIR / "skills.json"
EQUIPMENT_FILE = DATA_DIR / "equipment.json"
MONSTERS_FILE = DATA_DIR / "monsters.json"
ACHIEVEMENTS_FILE = DATA_DIR / "achievements.json"
PRICES_FILE = DATA_DIR / "api/prices_latest.json"

def load_json_data(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON data from file."""
    try:
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"Data file not found: {file_path}")
            return None
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None

# Initialize data containers
items_data = load_json_data(ITEMS_FILE)
quests_data = load_json_data(QUESTS_FILE)
skills_data = load_json_data(SKILLS_FILE)
equipment_data = load_json_data(EQUIPMENT_FILE)
monsters_data = load_json_data(MONSTERS_FILE)
achievements_data = load_json_data(ACHIEVEMENTS_FILE)
prices_data = load_json_data(PRICES_FILE)

def get_item_data(item_id: str) -> Optional[Dict[str, Any]]:
    """Get item data by ID."""
    return items_data.get(item_id) if items_data else None

def get_quest_data(quest_id: str) -> Optional[Dict[str, Any]]:
    """Get quest data by ID."""
    return quests_data.get(quest_id) if quests_data else None

def get_skill_data(skill_id: str) -> Optional[Dict[str, Any]]:
    """Get skill data by ID."""
    return skills_data.get(skill_id) if skills_data else None

def get_equipment_data(equip_id: str) -> Optional[Dict[str, Any]]:
    """Get equipment data by ID."""
    return equipment_data.get(equip_id) if equipment_data else None

def get_monster_data(monster_id: str) -> Optional[Dict[str, Any]]:
    """Get monster data by ID."""
    return monsters_data.get(monster_id) if monsters_data else None

def get_achievement_data(achievement_id: str) -> Optional[Dict[str, Any]]:
    """Get achievement data by ID."""
    return achievements_data.get(achievement_id) if achievements_data else None

def get_item_price(item_id: str) -> Optional[int]:
    """Get latest item price by ID."""
    return prices_data.get(item_id, {}).get('price') if prices_data else None
