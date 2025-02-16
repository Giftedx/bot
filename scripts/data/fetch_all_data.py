#!/usr/bin/env python3
"""
Script to fetch and verify all OSRS data from the Wiki.
Coordinates fetching of items, monsters, NPCs, objects, locations, and game mechanics.
Implements rate limiting to avoid overloading the Wiki API.
"""
import asyncio
import aiohttp
import json
import logging
from pathlib import Path
import sys
import time
from typing import Dict, Any, List, Set
import re
import os
from datetime import datetime
import importlib

# Add parent directory to path for imports
script_dir = Path(__file__).parent.parent
sys.path.append(str(script_dir))

from data.fetch_wiki_items import WikiItemFetcher
from data.fetch_wiki_monsters import MonsterDataFetcher
from data.fetch_wiki_npcs import WikiNPCFetcher
from data.fetch_wiki_objects import WikiObjectFetcher
from data.fetch_wiki_locations import WikiLocationFetcher
from data.verify_data import DataVerifier

# Import all fetchers
from .fetch_wiki_items import fetch_wiki_items
from .fetch_wiki_equipment import fetch_wiki_equipment
from .fetch_wiki_monsters import fetch_wiki_monsters
from .fetch_wiki_npcs import fetch_wiki_npcs
from .fetch_wiki_locations import fetch_wiki_locations
from .fetch_wiki_objects import fetch_wiki_objects
from .fetch_wiki_quests import fetch_wiki_quests
from .fetch_wiki_skills import fetch_wiki_skills
from .fetch_wiki_minigames import fetch_minigames_data
from .fetch_wiki_clues import fetch_clue_data
from .fetch_wiki_diaries import fetch_achievement_diary_data
from .fetch_wiki_formulas import fetch_formula_data
from .fetch_wiki_item_stats import fetch_item_stats
from .fetch_osrs_ge_data import fetch_ge_data
from .fetch_osrs_worlds import fetch_world_data
from .fetch_external_services import fetch_external_services_data

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fetch_all_data.log")
    ]
)
logger = logging.getLogger(__name__)

OSRS_WIKI_API = "https://oldschool.runescape.wiki/api.php"
USER_AGENT = "OSRSBot Data Collection/1.0 (contact@osrsbot.com)"

class WikiRateLimiter:
    """Rate limiter for Wiki API requests."""
    
    def __init__(self, requests_per_minute: int = 30):
        """Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum number of requests allowed per minute
        """
        self.delay = 60.0 / requests_per_minute  # Time between requests in seconds
        self.last_request_time = 0.0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait until it's safe to make another request."""
        async with self._lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.delay:
                wait_time = self.delay - time_since_last
                await asyncio.sleep(wait_time)
            
            self.last_request_time = time.time()

class WikiDataFetcher:
    """Base class for fetching data from the OSRS Wiki."""
    
    def __init__(self):
        """Initialize the fetcher."""
        self.session: aiohttp.ClientSession = None
        self.rate_limiter: WikiRateLimiter = None
        
    async def __aenter__(self):
        """Set up async context."""
        self.session = aiohttp.ClientSession(headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.5"
        })
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up async context."""
        if self.session:
            await self.session.close()
            
    async def fetch_with_retry(self, params: Dict[str, str], max_retries: int = 3) -> Dict[str, Any]:
        """Fetch data with retry logic and rate limiting."""
        for attempt in range(max_retries):
            try:
                # Wait for rate limiter before making request
                if self.rate_limiter:
                    await self.rate_limiter.acquire()
                
                async with self.session.get(OSRS_WIKI_API, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Too Many Requests
                        wait_time = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"HTTP {response.status} for params {params}")
                        response.raise_for_status()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to fetch with params {params}: {e}")
                    raise
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Attempt {attempt + 1} failed. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        
        raise Exception(f"Failed to fetch after {max_retries} attempts")
        
    async def fetch_category_members(self, category: str) -> List[str]:
        """Fetch all pages in a category."""
        pages = []
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": "500",
            "format": "json"
        }
        
        while True:
            data = await self.fetch_with_retry(params)
            if "query" not in data:
                break
                
            for page in data["query"]["categorymembers"]:
                if not page["title"].startswith(("File:", "Category:", "Template:")):
                    pages.append(page["title"])
                    
            if "continue" not in data:
                break
            params.update(data["continue"])
            
        return pages
        
    async def fetch_page_wikitext(self, page_title: str) -> str:
        """Fetch wikitext for a specific page."""
        params = {
            "action": "parse",
            "page": page_title,
            "prop": "wikitext",
            "format": "json"
        }
        
        data = await self.fetch_with_retry(params)
        return data["parse"]["wikitext"]["*"]

class OsrsDataCollector:
    """Collects all OSRS data needed for the Discord bot."""
    
    def __init__(self, requests_per_minute: int = 30):
        """Initialize the collector."""
        self.rate_limiter = WikiRateLimiter(requests_per_minute)
        self.fetcher = WikiDataFetcher()
        self.fetcher.rate_limiter = self.rate_limiter
        self.data: Dict[str, Dict[str, Any]] = {}
        
        # Define all categories to fetch with their parsers
        self.categories = {
            "items": {
                "subcategories": [
                    "Items", "Equipment", "Weapons", "Armour", "Tools",
                    "Quest items", "Tradeable items", "Untradeable items"
                ],
                "parser": self.parse_item_data
            },
            "monsters": {
                "subcategories": [
                    "Monsters", "Slayer monsters", "Boss monsters",
                    "Aggressive monsters", "Wilderness monsters"
                ],
                "parser": self.parse_monster_data
            },
            "npcs": {
                "subcategories": [
                    "NPCs", "Quest NPCs", "Shop owners",
                    "Skill trainers", "Transportation NPCs"
                ],
                "parser": self.parse_npc_data
            },
            "locations": {
                "subcategories": [
                    "Locations", "Cities", "Dungeons", "Regions",
                    "Wilderness locations", "Islands", "Minigame locations"
                ],
                "parser": self.parse_location_data
            },
            "skills": {
                "subcategories": [
                    "Skills", "Training methods", "Experience", "Calculators"
                ],
                "parser": self.parse_skill_data
            },
            "quests": {
                "subcategories": [
                    "Quests", "Miniquests", "Quest series", "Quest requirements"
                ],
                "parser": self.parse_quest_data
            },
            "minigames": {
                "subcategories": [
                    "Minigames", "Minigame rewards", "Minigame items"
                ],
                "parser": self.parse_minigame_data
            },
            "activities": {
                "subcategories": [
                    "Activities", "Distractions and Diversions",
                    "Skilling activities", "Money making methods"
                ],
                "parser": self.parse_activity_data
            },
            "game_mechanics": {
                "subcategories": [
                    "Combat", "Prayer", "Magic", "Achievement Diaries",
                    "Collection log", "Bank", "Grand Exchange"
                ],
                "parser": self.parse_game_mechanics_data
            },
            "transportation": {
                "subcategories": [
                    "Transportation", "Teleportation", "Fairy rings",
                    "Spirit trees", "Gnome gliders"
                ],
                "parser": self.parse_transportation_data
            },
            "clue_scrolls": {
                "subcategories": [
                    "Clue scrolls", "Treasure Trails", "Clue scroll rewards"
                ],
                "parser": self.parse_clue_scroll_data
            }
        }

    def parse_item_data(self, wikitext: str, title: str) -> Dict[str, Any]:
        """Parse item data from wikitext."""
        data = {
            "name": title,
            "type": "ITEM",
            "members": False,
            "tradeable": True,
            "stackable": False,
            "equipable": False,
            "weight": 0.0,
            "examine": None,
            "value": 0,
            "high_alch": 0,
            "low_alch": 0,
            "stats": {},
            "requirements": {},
            "wiki_url": f"https://oldschool.runescape.wiki/w/{title.replace(' ', '_')}"
        }
        
        # Extract data from infobox
        if "{{Infobox Item" in wikitext:
            data["members"] = "members = yes" in wikitext.lower()
            data["tradeable"] = "tradeable = yes" in wikitext.lower()
            data["stackable"] = "stackable = yes" in wikitext.lower()
            data["equipable"] = "equipable = yes" in wikitext.lower()
            
            # Extract examine text
            examine_match = re.search(r"examine\s*=\s*(.+)", wikitext)
            if examine_match:
                data["examine"] = examine_match.group(1).strip()
                
            # Extract value
            value_match = re.search(r"value\s*=\s*(\d+)", wikitext)
            if value_match:
                data["value"] = int(value_match.group(1))
                
            # Extract alchemy values
            high_alch_match = re.search(r"high\s*=\s*(\d+)", wikitext)
            if high_alch_match:
                data["high_alch"] = int(high_alch_match.group(1))
                
            low_alch_match = re.search(r"low\s*=\s*(\d+)", wikitext)
            if low_alch_match:
                data["low_alch"] = int(low_alch_match.group(1))
                
        return data

    def parse_monster_data(self, wikitext: str, title: str) -> Dict[str, Any]:
        """Parse monster data from wikitext."""
        data = {
            "name": title,
            "type": "MONSTER",
            "combat_level": None,
            "hitpoints": None,
            "max_hit": None,
            "aggressive": False,
            "poisonous": False,
            "slayer_level": None,
            "slayer_xp": None,
            "combat_stats": {},
            "drops": [],
            "wiki_url": f"https://oldschool.runescape.wiki/w/{title.replace(' ', '_')}"
        }
        
        if "{{Infobox Monster" in wikitext:
            # Extract combat stats
            combat_match = re.search(r"combat\s*=\s*(\d+)", wikitext)
            if combat_match:
                data["combat_level"] = int(combat_match.group(1))
                
            hp_match = re.search(r"hitpoints\s*=\s*(\d+)", wikitext)
            if hp_match:
                data["hitpoints"] = int(hp_match.group(1))
                
            # Extract attributes
            data["aggressive"] = "aggressive = yes" in wikitext.lower()
            data["poisonous"] = "poisonous = yes" in wikitext.lower()
            
            # Extract slayer info
            slayer_match = re.search(r"slaylvl\s*=\s*(\d+)", wikitext)
            if slayer_match:
                data["slayer_level"] = int(slayer_match.group(1))
                
            slayer_xp_match = re.search(r"slayxp\s*=\s*(\d+)", wikitext)
            if slayer_xp_match:
                data["slayer_xp"] = int(slayer_xp_match.group(1))
                
        return data

    def parse_npc_data(self, wikitext: str, title: str) -> Dict[str, Any]:
        """Parse NPC data from wikitext."""
        data = {
            "name": title,
            "type": "NPC",
            "examine": None,
            "location": None,
            "shop": None,
            "quest": None,
            "options": [],
            "wiki_url": f"https://oldschool.runescape.wiki/w/{title.replace(' ', '_')}"
        }
        
        if "{{Infobox NPC" in wikitext:
            # Extract examine text
            examine_match = re.search(r"examine\s*=\s*(.+)", wikitext)
            if examine_match:
                data["examine"] = examine_match.group(1).strip()
                
            # Extract location
            location_match = re.search(r"location\s*=\s*(.+)", wikitext)
            if location_match:
                data["location"] = location_match.group(1).strip()
                
            # Extract quest involvement
            quest_match = re.search(r"quest\s*=\s*(.+)", wikitext)
            if quest_match:
                data["quest"] = quest_match.group(1).strip()
                
            # Extract options
            if "talk-to" in wikitext.lower():
                data["options"].append("Talk-to")
            if "trade" in wikitext.lower():
                data["options"].append("Trade")
                data["shop"] = True
                
        return data

    def parse_location_data(self, wikitext: str, title: str) -> Dict[str, Any]:
        """Parse location data from wikitext."""
        data = {
            "name": title,
            "type": "LOCATION",
            "location_type": None,
            "requirements": {},
            "features": [],
            "npcs": [],
            "monsters": [],
            "wiki_url": f"https://oldschool.runescape.wiki/w/{title.replace(' ', '_')}"
        }
        
        # Determine location type
        if "city" in wikitext.lower():
            data["location_type"] = "CITY"
        elif "dungeon" in wikitext.lower():
            data["location_type"] = "DUNGEON"
        elif "wilderness" in wikitext.lower():
            data["location_type"] = "WILDERNESS"
        
        # Extract features
        features_match = re.search(r"features\s*=\s*(.+)", wikitext)
        if features_match:
            data["features"] = [f.strip() for f in features_match.group(1).split(",")]
            
        # Extract NPCs
        npcs_match = re.search(r"npcs?\s*=\s*(.+)", wikitext)
        if npcs_match:
            data["npcs"] = [n.strip() for n in npcs_match.group(1).split(",")]
            
        # Extract monsters
        monsters_match = re.search(r"monsters?\s*=\s*(.+)", wikitext)
        if monsters_match:
            data["monsters"] = [m.strip() for m in monsters_match.group(1).split(",")]
            
        return data

    def parse_skill_data(self, wikitext: str, title: str) -> Dict[str, Any]:
        """Parse skill data from wikitext."""
        data = {
            "name": title,
            "type": "SKILL",
            "members": False,
            "max_level": 99,
            "experience_table": {},
            "training_methods": [],
            "wiki_url": f"https://oldschool.runescape.wiki/w/{title.replace(' ', '_')}"
        }
        
        if "{{Infobox Skill" in wikitext:
            data["members"] = "members = yes" in wikitext.lower()
            
            # Extract training methods
            methods_match = re.search(r"training\s*=\s*(.+)", wikitext)
            if methods_match:
                data["training_methods"] = [m.strip() for m in methods_match.group(1).split(",")]
                
        return data

    def parse_quest_data(self, wikitext: str, title: str) -> Dict[str, Any]:
        """Parse quest data from wikitext."""
        data = {
            "name": title,
            "type": "QUEST",
            "difficulty": None,
            "length": None,
            "requirements": {
                "skills": {},
                "quests": [],
                "items": []
            },
            "rewards": {
                "quest_points": 0,
                "experience": {},
                "items": []
            },
            "wiki_url": f"https://oldschool.runescape.wiki/w/{title.replace(' ', '_')}"
        }
        
        if "{{Infobox Quest" in wikitext:
            # Extract difficulty and length
            difficulty_match = re.search(r"difficulty\s*=\s*(.+)", wikitext)
            if difficulty_match:
                data["difficulty"] = difficulty_match.group(1).strip()
                
            length_match = re.search(r"length\s*=\s*(.+)", wikitext)
            if length_match:
                data["length"] = length_match.group(1).strip()
                
            # Extract quest points
            qp_match = re.search(r"qp\s*=\s*(\d+)", wikitext)
            if qp_match:
                data["rewards"]["quest_points"] = int(qp_match.group(1))
                
        return data

    def parse_minigame_data(self, wikitext: str, title: str) -> Dict[str, Any]:
        """Parse minigame data from wikitext."""
        data = {
            "name": title,
            "type": "MINIGAME",
            "location": None,
            "requirements": {},
            "rewards": [],
            "wiki_url": f"https://oldschool.runescape.wiki/w/{title.replace(' ', '_')}"
        }
        
        if "{{Infobox Minigame" in wikitext:
            # Extract location
            location_match = re.search(r"location\s*=\s*(.+)", wikitext)
            if location_match:
                data["location"] = location_match.group(1).strip()
                
            # Extract rewards
            rewards_match = re.search(r"rewards?\s*=\s*(.+)", wikitext)
            if rewards_match:
                data["rewards"] = [r.strip() for r in rewards_match.group(1).split(",")]
                
        return data

    def parse_activity_data(self, wikitext: str, title: str) -> Dict[str, Any]:
        """Parse activity data from wikitext."""
        data = {
            "name": title,
            "type": "ACTIVITY",
            "requirements": {},
            "rewards": [],
            "wiki_url": f"https://oldschool.runescape.wiki/w/{title.replace(' ', '_')}"
        }
        
        # Extract requirements and rewards from wikitext
        requirements_match = re.search(r"requirements?\s*=\s*(.+)", wikitext)
        if requirements_match:
            data["requirements"] = [r.strip() for r in requirements_match.group(1).split(",")]
            
        rewards_match = re.search(r"rewards?\s*=\s*(.+)", wikitext)
        if rewards_match:
            data["rewards"] = [r.strip() for r in rewards_match.group(1).split(",")]
            
        return data

    def parse_game_mechanics_data(self, wikitext: str, title: str) -> Dict[str, Any]:
        """Parse game mechanics data from wikitext."""
        data = {
            "name": title,
            "type": "GAME_MECHANIC",
            "description": None,
            "related_skills": [],
            "wiki_url": f"https://oldschool.runescape.wiki/w/{title.replace(' ', '_')}"
        }
        
        # Extract description (first paragraph)
        description_match = re.search(r"\n\n(.+?)\n\n", wikitext)
        if description_match:
            data["description"] = description_match.group(1).strip()
            
        # Extract related skills
        if "skills" in wikitext.lower():
            skills_match = re.search(r"skills?\s*=\s*(.+)", wikitext)
            if skills_match:
                data["related_skills"] = [s.strip() for s in skills_match.group(1).split(",")]
                
        return data

    def parse_transportation_data(self, wikitext: str, title: str) -> Dict[str, Any]:
        """Parse transportation data from wikitext."""
        data = {
            "name": title,
            "type": "TRANSPORTATION",
            "transport_type": None,
            "destinations": [],
            "requirements": {},
            "wiki_url": f"https://oldschool.runescape.wiki/w/{title.replace(' ', '_')}"
        }
        
        # Determine transport type
        if "fairy ring" in title.lower():
            data["transport_type"] = "FAIRY_RING"
        elif "spirit tree" in title.lower():
            data["transport_type"] = "SPIRIT_TREE"
        elif "teleport" in title.lower():
            data["transport_type"] = "TELEPORT"
            
        # Extract destinations
        destinations_match = re.search(r"destinations?\s*=\s*(.+)", wikitext)
        if destinations_match:
            data["destinations"] = [d.strip() for d in destinations_match.group(1).split(",")]
            
        return data

    def parse_clue_scroll_data(self, wikitext: str, title: str) -> Dict[str, Any]:
        """Parse clue scroll data from wikitext."""
        data = {
            "name": title,
            "type": "CLUE_SCROLL",
            "difficulty": None,
            "steps": [],
            "rewards": [],
            "wiki_url": f"https://oldschool.runescape.wiki/w/{title.replace(' ', '_')}"
        }
        
        # Determine difficulty
        if "easy" in title.lower():
            data["difficulty"] = "EASY"
        elif "medium" in title.lower():
            data["difficulty"] = "MEDIUM"
        elif "hard" in title.lower():
            data["difficulty"] = "HARD"
        elif "elite" in title.lower():
            data["difficulty"] = "ELITE"
        elif "master" in title.lower():
            data["difficulty"] = "MASTER"
            
        # Extract steps and rewards
        steps_match = re.search(r"steps?\s*=\s*(.+)", wikitext)
        if steps_match:
            data["steps"] = [s.strip() for s in steps_match.group(1).split(",")]
            
        rewards_match = re.search(r"rewards?\s*=\s*(.+)", wikitext)
        if rewards_match:
            data["rewards"] = [r.strip() for r in rewards_match.group(1).split(",")]
            
        return data
        
    async def fetch_category_data(self, category: str, config: Dict[str, Any]):
        """Fetch data for a category and its subcategories."""
        logger.info(f"\nFetching {category} data...")
        all_pages = set()
        
        async with self.fetcher as fetcher:
            for subcat in config["subcategories"]:
                try:
                    pages = await fetcher.fetch_category_members(subcat)
                    logger.info(f"Found {len(pages)} pages in {subcat}")
                    all_pages.update(pages)
                except Exception as e:
                    logger.error(f"Error fetching {subcat}: {e}")
                    continue
                    
            # Fetch and parse detailed data for each page
            category_data = {}
            for i, page in enumerate(all_pages, 1):
                try:
                    logger.info(f"Processing {i}/{len(all_pages)}: {page}")
                    wikitext = await fetcher.fetch_page_wikitext(page)
                    parsed_data = config["parser"](wikitext, page)
                    category_data[page] = parsed_data
                except Exception as e:
                    logger.error(f"Error processing {page}: {e}")
                    continue
                    
            self.data[category] = category_data
            
    def save_data(self):
        """Save all collected data to JSON files."""
        output_dir = Path("src/data")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for category, data in self.data.items():
            output_file = output_dir / f"{category}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(data)} {category} to {output_file}")
            
    async def fetch_all_data(self):
        """Fetch all OSRS data categories."""
        try:
            for category, config in self.categories.items():
                await self.fetch_category_data(category, config)
                
            self.save_data()
            logger.info("\nData collection completed!")
            
        except Exception as e:
            logger.error(f"Error during data collection: {e}", exc_info=True)
            raise

async def main():
    """Main function to fetch all OSRS data."""
    try:
        logger.info("Starting OSRS data collection...")
        
        collector = OsrsDataCollector(requests_per_minute=30)
        await collector.fetch_all_data()
        
        logger.info("\nData collection completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in data collection: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nData collection cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

def fetch_all_data():
    """
    Fetches all game data from various sources and saves it to appropriate directories.
    Includes:
    - Wiki data (items, monsters, NPCs, locations, etc.)
    - OSRS API data (GE prices, world status)
    - External services data (Twitch, YouTube, etc.)
    """
    start_time = time.time()
    
    # Create base data directory if it doesn't exist
    base_dir = Path("src/osrs/data")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Dictionary to store all fetched data
    all_data = {
        'timestamp': datetime.now().isoformat(),
        'sources': {}
    }
    
    # List of all fetcher functions and their categories
    fetchers = [
        # Wiki data fetchers
        ('wiki', 'items', fetch_wiki_items),
        ('wiki', 'equipment', fetch_wiki_equipment),
        ('wiki', 'monsters', fetch_wiki_monsters),
        ('wiki', 'npcs', fetch_wiki_npcs),
        ('wiki', 'locations', fetch_wiki_locations),
        ('wiki', 'objects', fetch_wiki_objects),
        ('wiki', 'quests', fetch_wiki_quests),
        ('wiki', 'skills', fetch_wiki_skills),
        ('wiki', 'minigames', fetch_minigames_data),
        ('wiki', 'clues', fetch_clue_data),
        ('wiki', 'diaries', fetch_achievement_diary_data),
        ('wiki', 'formulas', fetch_formula_data),
        ('wiki', 'item_stats', fetch_item_stats),
        
        # OSRS API data fetchers
        ('osrs', 'ge', fetch_ge_data),
        ('osrs', 'worlds', fetch_world_data),
        
        # External services fetcher
        ('external', 'services', fetch_external_services_data)
    ]
    
    # Fetch data from each source
    for source, category, fetcher in fetchers:
        try:
            print(f"Fetching {source} {category} data...")
            data = fetcher()
            
            # Create category in all_data if it doesn't exist
            if source not in all_data['sources']:
                all_data['sources'][source] = {}
            
            all_data['sources'][source][category] = {
                'timestamp': datetime.now().isoformat(),
                'status': 'success' if data else 'error',
                'data': data
            }
            
            # Save individual category data
            category_dir = base_dir / source / category
            category_dir.mkdir(parents=True, exist_ok=True)
            
            with open(category_dir / f"{category}_data.json", 'w') as f:
                json.dump(data, f, indent=4)
            
            print(f"Successfully fetched {source} {category} data")
        
        except Exception as e:
            print(f"Error fetching {source} {category} data: {str(e)}")
            all_data['sources'][source][category] = {
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }
    
    # Save complete data summary
    with open(base_dir / "all_data_summary.json", 'w') as f:
        # Remove actual data from summary to keep it small
        summary_data = {
            'timestamp': all_data['timestamp'],
            'sources': {
                source: {
                    category: {
                        k: v for k, v in info.items() if k != 'data'
                    }
                    for category, info in categories.items()
                }
                for source, categories in all_data['sources'].items()
            }
        }
        json.dump(summary_data, f, indent=4)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nData fetch completed in {duration:.2f} seconds")
    print(f"Data saved to {base_dir}")
    
    return all_data

if __name__ == "__main__":
    fetch_all_data() 