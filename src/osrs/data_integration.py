from typing import Dict, List, Optional, Union
import aiohttp
import json
from datetime import datetime
import asyncio
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class OSRSDataManager:
    def __init__(self):
        self.items_cache: Dict[int, Dict] = {}
        self.skills_cache: Dict[str, Dict] = {}
        self.quests_cache: Dict[str, Dict] = {}
        self.ge_cache: Dict[int, Dict] = {}
        self.cache_timestamp = None
        self.cache_duration = 3600  # 1 hour cache

    async def initialize(self):
        """Initialize the data manager and load initial cache"""
        await self.load_items()
        await self.load_skills()
        await self.load_quests()
        self.cache_timestamp = datetime.now()

    async def load_items(self):
        """Load OSRS items data"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://prices.runescape.wiki/api/v1/osrs/mapping") as resp:
                    if resp.status == 200:
                        items_data = await resp.json()
                        self.items_cache = {item["id"]: item for item in items_data}
                        logger.info(f"Loaded {len(self.items_cache)} items")
        except Exception as e:
            logger.error(f"Error loading items: {e}")

    async def load_skills(self):
        """Load OSRS skills data"""
        self.skills_cache = {
            "attack": {"max_level": 99, "combat": True},
            "strength": {"max_level": 99, "combat": True},
            "defence": {"max_level": 99, "combat": True},
            "ranged": {"max_level": 99, "combat": True},
            "prayer": {"max_level": 99, "combat": True},
            "magic": {"max_level": 99, "combat": True},
            "runecraft": {"max_level": 99, "combat": False},
            "construction": {"max_level": 99, "combat": False},
            "hitpoints": {"max_level": 99, "combat": True},
            "agility": {"max_level": 99, "combat": False},
            "herblore": {"max_level": 99, "combat": False},
            "thieving": {"max_level": 99, "combat": False},
            "crafting": {"max_level": 99, "combat": False},
            "fletching": {"max_level": 99, "combat": False},
            "slayer": {"max_level": 99, "combat": True},
            "hunter": {"max_level": 99, "combat": False},
            "mining": {"max_level": 99, "combat": False},
            "smithing": {"max_level": 99, "combat": False},
            "fishing": {"max_level": 99, "combat": False},
            "cooking": {"max_level": 99, "combat": False},
            "firemaking": {"max_level": 99, "combat": False},
            "woodcutting": {"max_level": 99, "combat": False},
            "farming": {"max_level": 99, "combat": False},
        }

    async def load_quests(self):
        """Load OSRS quest data"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://raw.githubusercontent.com/oldschoolgg/oldschooljs/master/src/data/quests.json"
                ) as resp:
                    if resp.status == 200:
                        self.quests_cache = await resp.json()
                        logger.info(f"Loaded {len(self.quests_cache)} quests")
        except Exception as e:
            logger.error(f"Error loading quests: {e}")

    async def get_item(self, item_id: int) -> Optional[Dict]:
        """Get item data by ID"""
        return self.items_cache.get(item_id)

    async def search_items(self, query: str) -> List[Dict]:
        """Search for items by name"""
        query = query.lower()
        return [item for item in self.items_cache.values() if query in item["name"].lower()]

    async def get_ge_price(self, item_id: int) -> Optional[Dict]:
        """Get current GE price for an item"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://prices.runescape.wiki/api/v1/osrs/latest?id={item_id}"
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["data"].get(str(item_id))
        except Exception as e:
            logger.error(f"Error fetching GE price: {e}")
        return None

    async def get_skill_info(self, skill: str) -> Optional[Dict]:
        """Get skill information"""
        return self.skills_cache.get(skill.lower())

    async def get_quest_info(self, quest_name: str) -> Optional[Dict]:
        """Get quest information"""
        quest_name = quest_name.lower()
        return next(
            (quest for quest in self.quests_cache if quest["name"].lower() == quest_name), None
        )

    async def calculate_combat_level(self, stats: Dict[str, int]) -> int:
        """Calculate combat level based on stats"""
        base = 0.25 * (
            stats.get("defence", 1) + stats.get("hitpoints", 10) + (stats.get("prayer", 1) // 2)
        )
        melee = 0.325 * (stats.get("attack", 1) + stats.get("strength", 1))
        ranged = 0.325 * (stats.get("ranged", 1) * 1.5)
        magic = 0.325 * (stats.get("magic", 1) * 1.5)

        return int(base + max(melee, ranged, magic))

    async def get_xp_for_level(self, level: int) -> int:
        """Get XP required for a specific level"""
        if level < 1 or level > 99:
            raise ValueError("Level must be between 1 and 99")

        xp = 0
        for i in range(1, level):
            xp += int(i + 300 * (2 ** (i / 7)))
        return int(xp / 4)

    async def get_level_for_xp(self, xp: int) -> int:
        """Get level for a specific amount of XP"""
        if xp < 0:
            raise ValueError("XP cannot be negative")

        level = 1
        while level < 99:
            next_level_xp = await self.get_xp_for_level(level + 1)
            if xp < next_level_xp:
                break
            level += 1
        return level
