import aiohttp
import asyncio
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from bs4 import BeautifulSoup
import mwclient  # For Wiki API
import aiofiles
import os

logger = logging.getLogger(__name__)


class OSRSDataManager:
    def __init__(self, cache_dir: str = "data/cache/osrs"):
        self.cache_dir = cache_dir
        self.api_base_url = "https://services.runescape.com/m=itemdb_oldschool/api"
        self.wiki_site = mwclient.Site("oldschool.runescape.wiki", path="/")
        self.cache: Dict[str, Any] = {}
        self.cache_duration = timedelta(hours=24)
        self.last_update: Dict[str, datetime] = {}

        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)

    async def initialize(self):
        """Initialize the data manager and load cached data"""
        await self.load_cache()
        if self.needs_update():
            await self.update_all_data()

    async def load_cache(self):
        """Load cached data from files"""
        try:
            async with aiofiles.open(f"{self.cache_dir}/items.json", "r") as f:
                self.cache["items"] = json.loads(await f.read())
            async with aiofiles.open(f"{self.cache_dir}/monsters.json", "r") as f:
                self.cache["monsters"] = json.loads(await f.read())
            async with aiofiles.open(f"{self.cache_dir}/pets.json", "r") as f:
                self.cache["pets"] = json.loads(await f.read())
            async with aiofiles.open(f"{self.cache_dir}/last_update.json", "r") as f:
                self.last_update = {
                    k: datetime.fromisoformat(v) for k, v in json.loads(await f.read()).items()
                }
        except FileNotFoundError:
            logger.info("No cache found, will create new cache")
            self.cache = {}
            self.last_update = {}

    async def save_cache(self):
        """Save current data to cache files"""
        async with aiofiles.open(f"{self.cache_dir}/items.json", "w") as f:
            await f.write(json.dumps(self.cache.get("items", {}), indent=2))
        async with aiofiles.open(f"{self.cache_dir}/monsters.json", "w") as f:
            await f.write(json.dumps(self.cache.get("monsters", {}), indent=2))
        async with aiofiles.open(f"{self.cache_dir}/pets.json", "w") as f:
            await f.write(json.dumps(self.cache.get("pets", {}), indent=2))
        async with aiofiles.open(f"{self.cache_dir}/last_update.json", "w") as f:
            await f.write(
                json.dumps({k: v.isoformat() for k, v in self.last_update.items()}, indent=2)
            )

    def needs_update(self) -> bool:
        """Check if data needs to be updated"""
        if not self.last_update:
            return True
        now = datetime.utcnow()
        return any(
            now - update_time > self.cache_duration for update_time in self.last_update.values()
        )

    async def update_all_data(self):
        """Update all OSRS data"""
        tasks = [self.update_items(), self.update_monsters(), self.update_pets()]
        await asyncio.gather(*tasks)
        await self.save_cache()

    async def fetch_api_data(self, endpoint: str) -> Dict[str, Any]:
        """Fetch data from OSRS API"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_base_url}/{endpoint}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API request failed: {response.status}")
                    return {}

    async def fetch_wiki_data(self, page_title: str) -> Dict[str, Any]:
        """Fetch data from OSRS Wiki"""
        try:
            page = self.wiki_site.pages[page_title]
            content = page.text()
            return self.parse_wiki_content(content)
        except Exception as e:
            logger.error(f"Wiki request failed: {e}")
            return {}

    def parse_wiki_content(self, content: str) -> Dict[str, Any]:
        """Parse Wiki page content into structured data"""
        data = {}

        # Extract infobox data
        infobox_match = re.search(r"\{\{Infobox(.+?)\}\}", content, re.DOTALL)
        if infobox_match:
            infobox = infobox_match.group(1)
            for line in infobox.split("\n"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    data[key.strip()] = value.strip()

        # Extract other relevant sections
        sections = re.split(r"==(.+?)==", content)
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                section_name = sections[i].strip()
                section_content = sections[i + 1].strip()
                data[section_name] = section_content

        return data

    async def update_items(self):
        """Update item database"""
        logger.info("Updating OSRS items...")
        items_data = await self.fetch_api_data("catalogue/items.json")

        # Enhance with Wiki data
        for item_id, item in items_data.items():
            wiki_data = await self.fetch_wiki_data(f"Item:{item['name']}")
            items_data[item_id].update(wiki_data)

        self.cache["items"] = items_data
        self.last_update["items"] = datetime.utcnow()

    async def update_monsters(self):
        """Update monster database"""
        logger.info("Updating OSRS monsters...")
        monsters_data = {}

        # Get list of monsters from Wiki
        category = self.wiki_site.categories["Monsters"]
        for page in category:
            monster_data = await self.fetch_wiki_data(page.name)
            if monster_data:
                monsters_data[page.name] = monster_data

        self.cache["monsters"] = monsters_data
        self.last_update["monsters"] = datetime.utcnow()

    async def update_pets(self):
        """Update pet database"""
        logger.info("Updating OSRS pets...")
        pets_data = {}

        # Get list of pets from Wiki
        category = self.wiki_site.categories["Pets"]
        for page in category:
            pet_data = await self.fetch_wiki_data(page.name)
            if pet_data:
                # Add additional pet-specific data
                pet_data.update(await self.get_pet_specific_data(page.name))
                pets_data[page.name] = pet_data

        self.cache["pets"] = pets_data
        self.last_update["pets"] = datetime.utcnow()

    async def get_pet_specific_data(self, pet_name: str) -> Dict[str, Any]:
        """Get additional pet-specific data"""
        pet_data = {
            "stats": {
                "combat": 0,
                "attack": 0,
                "defence": 0,
                "strength": 0,
                "hitpoints": 0,
                "ranged": 0,
                "magic": 0,
                "prayer": 0,
            },
            "abilities": [],
            "drop_rate": None,
            "requirements": {},
            "obtainable_from": [],
        }

        try:
            page = self.wiki_site.pages[pet_name]
            content = page.text()

            # Extract stats
            stats_match = re.search(r"\{\{Combat stats(.+?)\}\}", content, re.DOTALL)
            if stats_match:
                stats_text = stats_match.group(1)
                for stat in pet_data["stats"]:
                    stat_match = re.search(rf"\|{stat}\s*=\s*(\d+)", stats_text)
                    if stat_match:
                        pet_data["stats"][stat] = int(stat_match.group(1))

            # Extract drop rate
            drop_rate_match = re.search(r"drop rate.*?(\d+)/(\d+)", content, re.IGNORECASE)
            if drop_rate_match:
                numerator = int(drop_rate_match.group(1))
                denominator = int(drop_rate_match.group(2))
                pet_data["drop_rate"] = numerator / denominator

            # Extract requirements
            level_reqs = re.findall(r"(\d+) ([A-Za-z]+) required", content)
            for level, skill in level_reqs:
                pet_data["requirements"][skill.lower()] = int(level)

            # Extract sources
            sources_section = re.search(r"==\s*Sources\s*==(.+?)==", content, re.DOTALL)
            if sources_section:
                sources = re.findall(r"\*\s*(.+?)(?:\n|$)", sources_section.group(1))
                pet_data["obtainable_from"] = [source.strip() for source in sources]

            # Add special abilities
            abilities_section = re.search(r"==\s*Abilities\s*==(.+?)==", content, re.DOTALL)
            if abilities_section:
                abilities = re.findall(r"\*\s*(.+?)(?:\n|$)", abilities_section.group(1))
                pet_data["abilities"] = [ability.strip() for ability in abilities]

        except Exception as e:
            logger.error(f"Error getting pet-specific data for {pet_name}: {e}")

        return pet_data

    def get_pet_data(self, pet_name: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific pet"""
        return self.cache.get("pets", {}).get(pet_name)

    def get_monster_data(self, monster_name: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific monster"""
        return self.cache.get("monsters", {}).get(monster_name)

    def get_item_data(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific item"""
        return self.cache.get("items", {}).get(item_id)

    def search_pets(self, query: str) -> List[Dict[str, Any]]:
        """Search for pets matching the query"""
        query = query.lower()
        return [
            {"name": name, **data}
            for name, data in self.cache.get("pets", {}).items()
            if query in name.lower() or any(query in str(value).lower() for value in data.values())
        ]

    def get_boss_pets(self) -> List[Dict[str, Any]]:
        """Get all boss pets"""
        return [
            {"name": name, **data}
            for name, data in self.cache.get("pets", {}).items()
            if any("boss" in source.lower() for source in data.get("obtainable_from", []))
        ]

    def get_skilling_pets(self) -> List[Dict[str, Any]]:
        """Get all skilling pets"""
        return [
            {"name": name, **data}
            for name, data in self.cache.get("pets", {}).items()
            if any(
                skill in data.get("requirements", {})
                for skill in [
                    "woodcutting",
                    "fishing",
                    "mining",
                    "farming",
                    "agility",
                    "thieving",
                    "hunter",
                ]
            )
        ]

    async def get_current_prices(self, item_ids: List[str]) -> Dict[str, int]:
        """Get current GE prices for items"""
        prices = {}
        for item_id in item_ids:
            price_data = await self.fetch_api_data(f"catalogue/detail.json?item={item_id}")
            if price_data and "price" in price_data:
                prices[item_id] = price_data["price"]
        return prices

    async def get_pet_requirements(self, pet_name: str) -> Dict[str, Any]:
        """Get detailed requirements for obtaining a pet"""
        pet_data = self.get_pet_data(pet_name)
        if not pet_data:
            return {}

        requirements = {
            "skills": pet_data.get("requirements", {}),
            "items": [],
            "quests": [],
            "other": [],
        }

        # Get additional requirements from Wiki
        wiki_data = await self.fetch_wiki_data(f"Pet:{pet_name}")

        # Extract quest requirements
        quest_section = re.search(
            r"==\s*Quest requirements\s*==(.+?)==", wiki_data.get("content", ""), re.DOTALL
        )
        if quest_section:
            quests = re.findall(r"\*\s*(.+?)(?:\n|$)", quest_section.group(1))
            requirements["quests"] = [quest.strip() for quest in quests]

        # Extract item requirements
        item_section = re.search(
            r"==\s*Item requirements\s*==(.+?)==", wiki_data.get("content", ""), re.DOTALL
        )
        if item_section:
            items = re.findall(r"\*\s*(.+?)(?:\n|$)", item_section.group(1))
            requirements["items"] = [item.strip() for item in items]

        # Extract other requirements
        other_section = re.search(
            r"==\s*Other requirements\s*==(.+?)==", wiki_data.get("content", ""), re.DOTALL
        )
        if other_section:
            others = re.findall(r"\*\s*(.+?)(?:\n|$)", other_section.group(1))
            requirements["other"] = [other.strip() for other in others]

        return requirements
