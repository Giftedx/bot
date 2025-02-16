#!/usr/bin/env python3
"""
Script to fetch monster data from the OSRS Wiki.
Uses a similar approach to osrsbox-db but with improvements.
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

import aiohttp
import mwparserfromhell

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fetch_monsters.log")
    ]
)
logger = logging.getLogger(__name__)

OSRS_WIKI_API = "https://oldschool.runescape.wiki/api.php"
HEADERS = {
    "User-Agent": "OSRSBot Data Collection/1.0 (contact@osrsbot.com)",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

class MonsterDataFetcher:
    """Fetches and processes monster data from the OSRS Wiki."""
    
    def __init__(self):
        """Initialize the monster data fetcher."""
        self.session: Optional[aiohttp.ClientSession] = None
        self.monsters: Dict[str, Any] = {}
        self.drop_tables: Dict[str, List[Dict]] = {}
        self.rate_limiter = None  # Will be injected by coordinator
        
    async def __aenter__(self):
        """Create aiohttp session."""
        self.session = aiohttp.ClientSession(headers=HEADERS)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            
    async def fetch_with_retry(self, url: str, params: Dict[str, str], max_retries: int = 3) -> Dict:
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
            
    async def fetch_monster_list(self) -> List[str]:
        """Fetch list of all monsters from the Wiki."""
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": "Category:Monsters",
            "cmlimit": 500,
            "format": "json"
        }
        
        monster_pages = []
        while True:
            data = await self.fetch_with_retry(OSRS_WIKI_API, params)
            
            if "query" not in data:
                break
                
            for page in data["query"]["categorymembers"]:
                if not page["title"].startswith(("File:", "Category:")):
                    monster_pages.append(page["title"])
                    
            if "continue" not in data:
                break
            params.update(data["continue"])
            
        return monster_pages
        
    async def fetch_page_wikitext(self, page_title: str) -> Optional[str]:
        """Fetch wikitext for a specific page."""
        params = {
            "action": "parse",
            "page": page_title,
            "prop": "wikitext",
            "format": "json"
        }
        
        try:
            data = await self.fetch_with_retry(OSRS_WIKI_API, params)
            return data["parse"]["wikitext"]["*"]
        except (KeyError, Exception) as e:
            logger.warning(f"Failed to fetch wikitext for {page_title}: {e}")
            return None
            
    def parse_monster_infobox(self, wikitext: str) -> Dict[str, Any]:
        """Parse monster data from infobox template."""
        monster_data = {
            "combat_level": None,
            "hitpoints": None,
            "max_hit": None,
            "attack_type": [],
            "attack_speed": None,
            "aggressive": False,
            "poisonous": False,
            "immune": [],
            "weakness": [],
            "slayer_level": None,
            "slayer_xp": None,
            "combat_stats": {
                "attack": None,
                "strength": None,
                "defence": None,
                "magic": None,
                "ranged": None
            },
            "aggressive_stats": {
                "attack_bonus": None,
                "strength_bonus": None,
                "magic_bonus": None,
                "magic_damage": None,
                "ranged_bonus": None
            },
            "defensive_stats": {
                "stab_def": None,
                "slash_def": None,
                "crush_def": None,
                "magic_def": None,
                "ranged_def": None
            },
            "attributes": set(),
            "examine": None,
            "wiki_url": None
        }
        
        try:
            parsed = mwparserfromhell.parse(wikitext)
            templates = parsed.filter_templates()
            
            for template in templates:
                if template.name.strip().lower() == "infobox monster":
                    for param in template.params:
                        name = param.name.strip().lower()
                        value = param.value.strip()
                        
                        # Extract basic info
                        if name == "combat":
                            monster_data["combat_level"] = self._try_int(value)
                        elif name == "hitpoints":
                            monster_data["hitpoints"] = self._try_int(value)
                        elif name == "max hit":
                            monster_data["max_hit"] = self._try_int(value)
                        elif name == "attack speed":
                            monster_data["attack_speed"] = self._try_int(value)
                        elif name == "aggressive":
                            monster_data["aggressive"] = value.lower() == "yes"
                        elif name == "poisonous":
                            monster_data["poisonous"] = value.lower() == "yes"
                        
                        # Extract combat stats
                        elif name == "att":
                            monster_data["combat_stats"]["attack"] = self._try_int(value)
                        elif name == "str":
                            monster_data["combat_stats"]["strength"] = self._try_int(value)
                        elif name == "def":
                            monster_data["combat_stats"]["defence"] = self._try_int(value)
                        elif name == "mage":
                            monster_data["combat_stats"]["magic"] = self._try_int(value)
                        elif name == "range":
                            monster_data["combat_stats"]["ranged"] = self._try_int(value)
                            
                        # Extract attack types
                        elif name == "attack style":
                            styles = [s.strip().lower() for s in value.split(",")]
                            monster_data["attack_type"].extend(styles)
                            
                        # Extract weaknesses and immunities
                        elif name == "weakness":
                            weaknesses = [w.strip().lower() for w in value.split(",")]
                            monster_data["weakness"].extend(weaknesses)
                        elif name == "immune":
                            immunities = [i.strip().lower() for i in value.split(",")]
                            monster_data["immune"].extend(immunities)
                            
                        # Extract slayer info
                        elif name == "slaylvl":
                            monster_data["slayer_level"] = self._try_int(value)
                        elif name == "slayxp":
                            monster_data["slayer_xp"] = self._try_int(value)
                            
                        # Extract examine text
                        elif name == "examine":
                            monster_data["examine"] = value
                            
        except Exception as e:
            logger.warning(f"Error parsing monster infobox: {e}")
            
        return monster_data
        
    def parse_monster_drops(self, wikitext: str) -> List[Dict]:
        """Parse drop table from wikitext."""
        drops = []
        
        try:
            parsed = mwparserfromhell.parse(wikitext)
            templates = parsed.filter_templates()
            
            for template in templates:
                template_name = template.name.strip().lower()
                if "drop table" not in template_name:
                    continue
                    
                for param in template.params:
                    try:
                        name = param.name.strip()
                        value = param.value.strip()
                        
                        # Skip non-drop parameters
                        if not name.isdigit() or not value:
                            continue
                            
                        # Parse drop entry
                        parts = value.split(";")
                        if len(parts) < 2:
                            continue
                            
                        item_name = parts[0].strip()
                        quantity = "1"
                        rarity = "1/128"
                        
                        # Extract quantity if specified
                        if len(parts) > 1:
                            quantity = parts[1].strip()
                            
                        # Extract rarity if specified
                        if len(parts) > 2:
                            rarity = parts[2].strip()
                            
                        # Clean up the data
                        quantity = self._clean_quantity(quantity)
                        rarity = self._clean_rarity(rarity)
                        
                        drops.append({
                            "item": item_name,
                            "quantity": quantity,
                            "rarity": rarity,
                            "rolls": 1  # Default to 1 roll
                        })
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing drop entry: {e}")
                        continue
                        
        except Exception as e:
            logger.warning(f"Error parsing drop table: {e}")
            
        return drops
        
    def _clean_quantity(self, quantity: str) -> str:
        """Clean up drop quantity text."""
        if not quantity or quantity.lower() == "unknown":
            return "1"
            
        quantity = quantity.replace(" ", "")
        quantity = quantity.replace(u"\u2013", "-")
        quantity = re.sub(r" *\(noted\) *", "", quantity)
        quantity = re.sub(r"[; ]", ",", quantity)
        
        return quantity
        
    def _clean_rarity(self, rarity: str) -> str:
        """Clean up drop rarity text."""
        if rarity.lower() == "always":
            return "1/1"
        elif rarity.lower() == "common":
            return "1/8"
        elif rarity.lower() == "uncommon":
            return "1/32"
        elif rarity.lower() == "rare":
            return "1/128"
        elif rarity.lower() == "very rare":
            return "1/512"
        return rarity
        
    def _try_int(self, value: str) -> Optional[int]:
        """Try to convert a string to integer."""
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
            
    async def fetch_all_monsters(self):
        """Fetch data for all monsters."""
        # Get list of all monster pages
        monster_pages = await self.fetch_monster_list()
        logger.info(f"Found {len(monster_pages)} monster pages")
        
        # Process each monster
        for i, page_title in enumerate(monster_pages, 1):
            logger.info(f"Processing {i}/{len(monster_pages)}: {page_title}")
            
            try:
                # Get page wikitext
                wikitext = await self.fetch_page_wikitext(page_title)
                if not wikitext:
                    continue
                    
                # Parse monster data
                monster_data = self.parse_monster_infobox(wikitext)
                if not monster_data:
                    continue
                    
                # Parse drop table
                drops = self.parse_monster_drops(wikitext)
                monster_data["drops"] = drops
                
                # Add wiki URL
                monster_data["wiki_url"] = f"https://oldschool.runescape.wiki/w/{page_title.replace(' ', '_')}"
                
                # Store monster data
                self.monsters[page_title] = monster_data
                
                # Add small delay between requests
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing {page_title}: {e}")
                continue
                
        # Save to file
        self.save_data()
        
    def save_data(self):
        """Save monster data to JSON file."""
        output_dir = Path("src/data")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "monsters.json", "w") as f:
            json.dump(self.monsters, f, indent=4, default=list)
            
        logger.info(f"Saved {len(self.monsters)} monsters to monsters.json")

async def main():
    """Main function to fetch monster data."""
    try:
        async with MonsterDataFetcher() as fetcher:
            await fetcher.fetch_all_monsters()
    except Exception as e:
        logger.error(f"Error fetching monster data: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main()) 