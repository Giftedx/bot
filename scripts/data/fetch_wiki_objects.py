#!/usr/bin/env python3
"""
Script to fetch object data from the OSRS Wiki.
This script uses the OSRS Wiki API to get accurate object information.
"""
import asyncio
import aiohttp
import json
import logging
from pathlib import Path
import sys
import re
from typing import Dict, Any, List, Optional, Set

# Add src directory to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.append(str(src_path))

from lib.data.osrs_data_loader import OSRSDataLoader

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fetch_wiki_objects.log")
    ]
)
logger = logging.getLogger(__name__)

class WikiObjectFetcher:
    """Fetches object data from the OSRS Wiki."""
    
    def __init__(self):
        """Initialize object fetcher."""
        self.session: Optional[aiohttp.ClientSession] = None
        self.objects: Dict[str, Any] = {}
        self.rate_limiter = None  # Will be injected by coordinator
        self.wiki_api_url = "https://oldschool.runescape.wiki/api.php"
        self.data_loader = OSRSDataLoader()
        self.object_categories = {
            "Agility obstacles",
            "Altars",
            "Banks",
            "Farming patches",
            "Fishing spots",
            "Mining rocks",
            "Shortcuts",
            "Thieving targets",
            "Trees",
            "Furnaces",
            "Anvils",
            "Fountains",
            "Ranges",
            "Crafting stations",
            "Spinning wheels",
            "Looms",
            "Pottery wheels",
            "Obelisks",
            "Fairy rings",
            "Spirit trees",
            "Ladders",
            "Staircases",
            "Doors",
            "Gates",
            "Chests",
            "Crates",
            "Barrels"
        }
        
    async def __aenter__(self):
        """Set up async context."""
        self.session = aiohttp.ClientSession(headers={"User-Agent": USER_AGENT})
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up async context."""
        if self.session:
            await self.session.close()
            
    async def fetch_with_retry(self, url: str, params: Dict[str, str], max_retries: int = 3) -> Dict[str, Any]:
        """Fetch data with retry logic and rate limiting."""
        for attempt in range(max_retries):
            try:
                # Wait for rate limiter before making request
                if self.rate_limiter:
                    await self.rate_limiter.acquire()
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Too Many Requests
                        wait_time = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"HTTP {response.status} for {url} with params {params}")
                        response.raise_for_status()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to fetch {url} with params {params}: {e}")
                    raise
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Attempt {attempt + 1} failed. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        
        raise Exception(f"Failed to fetch {url} after {max_retries} attempts")
                
    async def fetch_object_list(self) -> List[str]:
        """Fetch list of all objects from the Wiki."""
        objects = set()
        
        async with aiohttp.ClientSession() as session:
            for category in self.object_categories:
                params = {
                    "action": "query",
                    "list": "categorymembers",
                    "cmtitle": f"Category:{category}",
                    "cmlimit": 500,
                    "format": "json"
                }
                
                try:
                    async with session.get(self.wiki_api_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            objects.update(
                                page["title"]
                                for page in data.get("query", {}).get("categorymembers", [])
                            )
                except Exception as e:
                    logger.error(f"Error fetching object list for {category}: {e}")
                    
        return list(objects)
                
    async def fetch_object_data(self, object_name: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed data for a specific object."""
        async with aiohttp.ClientSession() as session:
            params = {
                "action": "parse",
                "page": object_name,
                "prop": "wikitext",
                "format": "json"
            }
            
            try:
                async with session.get(self.wiki_api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
                        return self.parse_object_wikitext(wikitext, object_name)
                    return None
            except Exception as e:
                logger.error(f"Error fetching data for {object_name}: {e}")
                return None
                
    def parse_object_wikitext(self, wikitext: str, object_name: str) -> Dict[str, Any]:
        """Parse object data from Wiki markup."""
        object_data = {
            "id": self.data_loader.normalize_name(object_name),
            "name": object_name,
            "type": "OBJECT"
        }
        
        # Extract examine text
        examine_match = re.search(r"examine\s*=\s*(.+)", wikitext)
        if examine_match:
            object_data["examine"] = examine_match.group(1).strip()
            
        # Extract object type
        if "agility" in wikitext.lower():
            object_data["object_type"] = "AGILITY_OBSTACLE"
        elif "altar" in wikitext.lower():
            object_data["object_type"] = "ALTAR"
        elif "bank" in wikitext.lower():
            object_data["object_type"] = "BANK"
        elif "farming" in wikitext.lower():
            object_data["object_type"] = "FARMING_PATCH"
        elif "fishing" in wikitext.lower():
            object_data["object_type"] = "FISHING_SPOT"
        elif "mining" in wikitext.lower():
            object_data["object_type"] = "MINING_ROCK"
        elif "shortcut" in wikitext.lower():
            object_data["object_type"] = "SHORTCUT"
        elif "thieving" in wikitext.lower():
            object_data["object_type"] = "THIEVING_TARGET"
        elif "tree" in wikitext.lower():
            object_data["object_type"] = "TREE"
        elif "furnace" in wikitext.lower():
            object_data["object_type"] = "FURNACE"
        elif "anvil" in wikitext.lower():
            object_data["object_type"] = "ANVIL"
        elif "fountain" in wikitext.lower():
            object_data["object_type"] = "FOUNTAIN"
        elif "range" in wikitext.lower():
            object_data["object_type"] = "RANGE"
        elif "crafting" in wikitext.lower():
            object_data["object_type"] = "CRAFTING_STATION"
        elif "spinning" in wikitext.lower():
            object_data["object_type"] = "SPINNING_WHEEL"
        elif "loom" in wikitext.lower():
            object_data["object_type"] = "LOOM"
        elif "pottery" in wikitext.lower():
            object_data["object_type"] = "POTTERY_WHEEL"
        elif "obelisk" in wikitext.lower():
            object_data["object_type"] = "OBELISK"
        elif "fairy ring" in wikitext.lower():
            object_data["object_type"] = "FAIRY_RING"
        elif "spirit tree" in wikitext.lower():
            object_data["object_type"] = "SPIRIT_TREE"
        elif "ladder" in wikitext.lower():
            object_data["object_type"] = "LADDER"
        elif "staircase" in wikitext.lower():
            object_data["object_type"] = "STAIRCASE"
        elif "door" in wikitext.lower():
            object_data["object_type"] = "DOOR"
        elif "gate" in wikitext.lower():
            object_data["object_type"] = "GATE"
        elif "chest" in wikitext.lower():
            object_data["object_type"] = "CHEST"
        elif "crate" in wikitext.lower():
            object_data["object_type"] = "CRATE"
        elif "barrel" in wikitext.lower():
            object_data["object_type"] = "BARREL"
        else:
            object_data["object_type"] = "SCENERY"
            
        # Extract level requirements
        requirements = {}
        
        level_match = re.search(r"level\s*=\s*(\d+)", wikitext)
        if level_match:
            requirements["level"] = int(level_match.group(1))
            
        if "agility" in wikitext.lower():
            agility_match = re.search(r"agility\s*=\s*(\d+)", wikitext)
            if agility_match:
                requirements["agility"] = int(agility_match.group(1))
                
        if "thieving" in wikitext.lower():
            thieving_match = re.search(r"thieving\s*=\s*(\d+)", wikitext)
            if thieving_match:
                requirements["thieving"] = int(thieving_match.group(1))
                
        if "mining" in wikitext.lower():
            mining_match = re.search(r"mining\s*=\s*(\d+)", wikitext)
            if mining_match:
                requirements["mining"] = int(mining_match.group(1))
                
        if "woodcutting" in wikitext.lower():
            woodcutting_match = re.search(r"woodcutting\s*=\s*(\d+)", wikitext)
            if woodcutting_match:
                requirements["woodcutting"] = int(woodcutting_match.group(1))
                
        if "farming" in wikitext.lower():
            farming_match = re.search(r"farming\s*=\s*(\d+)", wikitext)
            if farming_match:
                requirements["farming"] = int(farming_match.group(1))
                
        if requirements:
            object_data["requirements"] = requirements
            
        # Extract quest requirements
        quest_match = re.search(r"quest\s*=\s*(.+)", wikitext)
        if quest_match:
            object_data["quest_requirements"] = [
                q.strip()
                for q in quest_match.group(1).split(",")
            ]
            
        # Extract location
        location_match = re.search(r"location\s*=\s*(.+)", wikitext)
        if location_match:
            object_data["location"] = location_match.group(1).strip()
            
        # Extract actions
        actions = []
        if "actions" in wikitext.lower():
            actions_match = re.search(r"actions?\s*=\s*(.+)", wikitext)
            if actions_match:
                actions = [
                    action.strip()
                    for action in actions_match.group(1).split(",")
                ]
        else:
            # Try to infer actions from common patterns
            if "mine" in wikitext.lower():
                actions.append("mine")
            if "chop" in wikitext.lower():
                actions.append("chop down")
            if "pick" in wikitext.lower():
                actions.append("pick")
            if "search" in wikitext.lower():
                actions.append("search")
            if "open" in wikitext.lower():
                actions.append("open")
            if "close" in wikitext.lower():
                actions.append("close")
            if "climb" in wikitext.lower():
                actions.append("climb")
            if "enter" in wikitext.lower():
                actions.append("enter")
            if "pray" in wikitext.lower():
                actions.append("pray-at")
            if "use" in wikitext.lower():
                actions.append("use")
                
        if actions:
            object_data["actions"] = actions
            
        # Set wiki URL
        object_data["wiki_url"] = f"https://oldschool.runescape.wiki/w/{object_name.replace(' ', '_')}"
        
        return object_data
        
    async def fetch_all_objects(self):
        """Fetch data for all objects."""
        # Load existing data
        await self.data_loader.load_local_data()
        existing_objects = self.data_loader.objects
        
        # Fetch object list
        object_names = await self.fetch_object_list()
        logger.info(f"Found {len(object_names)} objects on Wiki")
        
        # Fetch object data
        new_objects = {}
        for name in object_names:
            object_id = self.data_loader.normalize_name(name)
            
            # Skip if we already have detailed data
            if object_id in existing_objects:
                continue
                
            logger.info(f"Fetching data for object {name}...")
            object_data = await self.fetch_object_data(name)
            
            if object_data:
                new_objects[object_id] = object_data
                
        # Merge with existing data
        all_objects = {**existing_objects, **new_objects}
        
        # Save updated data
        data_dir = src_path / "data"
        with open(data_dir / "objects.json", "w") as f:
            json.dump(all_objects, f, indent=4)
            
        logger.info(f"Added {len(new_objects)} new objects")
        logger.info(f"Total objects: {len(all_objects)}")

async def main():
    """Main function to fetch Wiki object data."""
    try:
        fetcher = WikiObjectFetcher()
        await fetcher.fetch_all_objects()
        
    except Exception as e:
        logger.error(f"Error fetching Wiki data: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nFetch cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1) 