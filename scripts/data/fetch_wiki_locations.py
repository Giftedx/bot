#!/usr/bin/env python3
"""
Script to fetch location data from the OSRS Wiki.
This script uses the OSRS Wiki API to get accurate location information.
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
        logging.FileHandler("fetch_wiki_locations.log")
    ]
)
logger = logging.getLogger(__name__)

class WikiLocationFetcher:
    """Fetches location data from the OSRS Wiki."""
    
    def __init__(self):
        """Initialize location fetcher."""
        self.session: Optional[aiohttp.ClientSession] = None
        self.locations: Dict[str, Any] = {}
        self.rate_limiter = None  # Will be injected by coordinator
        self.wiki_api_url = "https://oldschool.runescape.wiki/api.php"
        self.data_loader = OSRSDataLoader()
        self.location_categories = {
            "Cities",
            "Dungeons",
            "Islands",
            "Regions",
            "Kingdoms",
            "Guilds",
            "Minigames",
            "Wilderness locations",
            "Slayer areas",
            "Resource areas",
            "Mining sites",
            "Woodcutting sites",
            "Fishing spots",
            "Hunter areas",
            "Farming locations",
            "Quest locations",
            "Transportation locations",
            "Banks",
            "Shops",
            "Altars",
            "Agility courses"
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
        
    async def fetch_location_list(self) -> List[str]:
        """Fetch list of all locations from the Wiki."""
        locations = set()
        
        async with aiohttp.ClientSession() as session:
            for category in self.location_categories:
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
                            locations.update(
                                page["title"]
                                for page in data.get("query", {}).get("categorymembers", [])
                            )
                except Exception as e:
                    logger.error(f"Error fetching location list for {category}: {e}")
                    
        return list(locations)
                
    async def fetch_location_data(self, location_name: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed data for a specific location."""
        async with aiohttp.ClientSession() as session:
            params = {
                "action": "parse",
                "page": location_name,
                "prop": "wikitext",
                "format": "json"
            }
            
            try:
                async with session.get(self.wiki_api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
                        return self.parse_location_wikitext(wikitext, location_name)
                    return None
            except Exception as e:
                logger.error(f"Error fetching data for {location_name}: {e}")
                return None
                
    def parse_location_wikitext(self, wikitext: str, location_name: str) -> Dict[str, Any]:
        """Parse location data from Wiki markup."""
        location_data = {
            "id": self.data_loader.normalize_name(location_name),
            "name": location_name,
            "type": "LOCATION"
        }
        
        # Extract location type
        if "city" in wikitext.lower():
            location_data["location_type"] = "CITY"
        elif "dungeon" in wikitext.lower():
            location_data["location_type"] = "DUNGEON"
        elif "island" in wikitext.lower():
            location_data["location_type"] = "ISLAND"
        elif "region" in wikitext.lower():
            location_data["location_type"] = "REGION"
        elif "kingdom" in wikitext.lower():
            location_data["location_type"] = "KINGDOM"
        elif "guild" in wikitext.lower():
            location_data["location_type"] = "GUILD"
        elif "minigame" in wikitext.lower():
            location_data["location_type"] = "MINIGAME"
        elif "wilderness" in wikitext.lower():
            location_data["location_type"] = "WILDERNESS"
        elif "slayer" in wikitext.lower():
            location_data["location_type"] = "SLAYER_AREA"
        elif "resource" in wikitext.lower():
            location_data["location_type"] = "RESOURCE_AREA"
        elif "mining" in wikitext.lower():
            location_data["location_type"] = "MINING_SITE"
        elif "woodcutting" in wikitext.lower():
            location_data["location_type"] = "WOODCUTTING_SITE"
        elif "fishing" in wikitext.lower():
            location_data["location_type"] = "FISHING_SPOT"
        elif "hunter" in wikitext.lower():
            location_data["location_type"] = "HUNTER_AREA"
        elif "farming" in wikitext.lower():
            location_data["location_type"] = "FARMING_LOCATION"
        elif "quest" in wikitext.lower():
            location_data["location_type"] = "QUEST_LOCATION"
        elif "transport" in wikitext.lower():
            location_data["location_type"] = "TRANSPORTATION"
        elif "bank" in wikitext.lower():
            location_data["location_type"] = "BANK"
        elif "shop" in wikitext.lower():
            location_data["location_type"] = "SHOP"
        elif "altar" in wikitext.lower():
            location_data["location_type"] = "ALTAR"
        elif "agility" in wikitext.lower():
            location_data["location_type"] = "AGILITY_COURSE"
        else:
            location_data["location_type"] = "AREA"
            
        # Extract coordinates
        coordinates_match = re.search(r"coordinates\s*=\s*(\d+),\s*(\d+)", wikitext)
        if coordinates_match:
            location_data["coordinates"] = {
                "x": int(coordinates_match.group(1)),
                "y": int(coordinates_match.group(2))
            }
            
        # Extract level requirements
        requirements = {}
        
        if "agility" in wikitext.lower():
            agility_match = re.search(r"agility\s*=\s*(\d+)", wikitext)
            if agility_match:
                requirements["agility"] = int(agility_match.group(1))
                
        if "slayer" in wikitext.lower():
            slayer_match = re.search(r"slayer\s*=\s*(\d+)", wikitext)
            if slayer_match:
                requirements["slayer"] = int(slayer_match.group(1))
                
        if "combat" in wikitext.lower():
            combat_match = re.search(r"combat\s*=\s*(\d+)", wikitext)
            if combat_match:
                requirements["combat"] = int(combat_match.group(1))
                
        if "quest" in wikitext.lower():
            quest_match = re.search(r"quest\s*=\s*(.+)", wikitext)
            if quest_match:
                requirements["quests"] = [
                    q.strip()
                    for q in quest_match.group(1).split(",")
                ]
                
        if requirements:
            location_data["requirements"] = requirements
            
        # Extract monsters
        monsters_match = re.search(r"monsters?\s*=\s*(.+)", wikitext)
        if monsters_match:
            location_data["monsters"] = [
                m.strip()
                for m in monsters_match.group(1).split(",")
            ]
            
        # Extract NPCs
        npcs_match = re.search(r"npcs?\s*=\s*(.+)", wikitext)
        if npcs_match:
            location_data["npcs"] = [
                n.strip()
                for n in npcs_match.group(1).split(",")
            ]
            
        # Extract features
        features_match = re.search(r"features?\s*=\s*(.+)", wikitext)
        if features_match:
            location_data["features"] = [
                f.strip()
                for f in features_match.group(1).split(",")
            ]
            
        # Extract resources
        resources_match = re.search(r"resources?\s*=\s*(.+)", wikitext)
        if resources_match:
            location_data["resources"] = [
                r.strip()
                for r in resources_match.group(1).split(",")
            ]
            
        # Extract dangers
        dangers_match = re.search(r"dangers?\s*=\s*(.+)", wikitext)
        if dangers_match:
            location_data["dangers"] = [
                d.strip()
                for d in dangers_match.group(1).split(",")
            ]
            
        # Extract music tracks
        music_match = re.search(r"music\s*=\s*(.+)", wikitext)
        if music_match:
            location_data["music_tracks"] = [
                m.strip()
                for m in music_match.group(1).split(",")
            ]
            
        # Set wiki URL
        location_data["wiki_url"] = f"https://oldschool.runescape.wiki/w/{location_name.replace(' ', '_')}"
        
        return location_data
        
    async def fetch_all_locations(self):
        """Fetch data for all locations."""
        # Load existing data
        await self.data_loader.load_local_data()
        existing_locations = self.data_loader.locations
        
        # Fetch location list
        location_names = await self.fetch_location_list()
        logger.info(f"Found {len(location_names)} locations on Wiki")
        
        # Fetch location data
        new_locations = {}
        for name in location_names:
            location_id = self.data_loader.normalize_name(name)
            
            # Skip if we already have detailed data
            if location_id in existing_locations:
                continue
                
            logger.info(f"Fetching data for location {name}...")
            location_data = await self.fetch_location_data(name)
            
            if location_data:
                new_locations[location_id] = location_data
                
        # Merge with existing data
        all_locations = {**existing_locations, **new_locations}
        
        # Save updated data
        data_dir = src_path / "data"
        with open(data_dir / "locations.json", "w") as f:
            json.dump(all_locations, f, indent=4)
            
        logger.info(f"Added {len(new_locations)} new locations")
        logger.info(f"Total locations: {len(all_locations)}")

async def main():
    """Main function to fetch Wiki location data."""
    try:
        fetcher = WikiLocationFetcher()
        await fetcher.fetch_all_locations()
        
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