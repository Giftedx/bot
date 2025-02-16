#!/usr/bin/env python3
"""
Script to fetch item data from the OSRS Wiki.
Fetches complete item information including properties, bonuses, and requirements.
"""
import asyncio
import json
import logging
from pathlib import Path
import sys
from typing import Dict, Any, Optional, List

import aiohttp
import mwparserfromhell

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fetch_items.log")
    ]
)
logger = logging.getLogger(__name__)

OSRS_WIKI_API_URL = "https://oldschool.runescape.wiki/api.php"
USER_AGENT = "OSRSBot ItemFetcher/1.0"

class WikiItemFetcher:
    """Fetches item data from the OSRS Wiki."""
    
    def __init__(self):
        """Initialize item fetcher."""
        self.session: Optional[aiohttp.ClientSession] = None
        self.items: Dict[str, Any] = {}
        self.rate_limiter = None  # Will be injected by coordinator
        
    async def __aenter__(self):
        """Set up async context."""
        self.session = aiohttp.ClientSession(headers={"User-Agent": USER_AGENT})
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up async context."""
        if self.session:
            await self.session.close()
            
    async def fetch_with_retry(self, url: str, params: Dict[str, str], max_retries: int = 3) -> Dict[str, Any]:
        """Fetch data with retry logic."""
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
                
    async def fetch_item_list(self) -> List[str]:
        """Fetch list of all items from the wiki."""
        items = []
        
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": "Category:Items",
            "cmlimit": "500",
            "format": "json"
        }
        
        while True:
            data = await self.fetch_with_retry(OSRS_WIKI_API_URL, params)
            if "query" not in data:
                break
                
            for item in data["query"]["categorymembers"]:
                if not item["title"].startswith(("File:", "Category:")):
                    items.append(item["title"])
                    
            if "continue" not in data:
                break
            params.update(data["continue"])
            
        logger.info(f"Found {len(items)} items")
        return items
        
    async def fetch_item_data(self, item_name: str) -> Optional[Dict[str, Any]]:
        """Fetch data for a specific item."""
        params = {
            "action": "parse",
            "prop": "wikitext",
            "format": "json",
            "page": item_name
        }
        
        try:
            data = await self.fetch_with_retry(OSRS_WIKI_API_URL, params)
            wikitext = data["parse"]["wikitext"]["*"]
            return self.parse_item_wikitext(wikitext, item_name)
        except Exception as e:
            logger.error(f"Error fetching {item_name}: {e}")
            return None
            
    def parse_item_wikitext(self, wikitext: str, item_name: str) -> Dict[str, Any]:
        """Parse item data from wiki text."""
        parsed = mwparserfromhell.parse(wikitext)
        templates = parsed.filter_templates()
        
        item_data = {
            "name": item_name,
            "members": False,
            "tradeable": True,
            "stackable": False,
            "noted": False,
            "noteable": True,
            "equipable": False,
            "weight": 0.0,
            "release_date": None,
            "examine": None,
            "value": 0,
            "high_alch": 0,
            "low_alch": 0,
            "buy_limit": None,
            "quest_item": False,
            "stats": {
                "attack_stab": 0,
                "attack_slash": 0,
                "attack_crush": 0,
                "attack_magic": 0,
                "attack_ranged": 0,
                "defence_stab": 0,
                "defence_slash": 0,
                "defence_crush": 0,
                "defence_magic": 0,
                "defence_ranged": 0,
                "melee_strength": 0,
                "ranged_strength": 0,
                "magic_damage": 0,
                "prayer": 0,
                "speed": 4
            },
            "requirements": {
                "attack": 1,
                "strength": 1,
                "defence": 1,
                "ranged": 1,
                "prayer": 1,
                "magic": 1,
                "slayer": 1,
                "quests": []
            },
            "wiki_url": f"https://oldschool.runescape.wiki/w/{item_name.replace(' ', '_')}"
        }
        
        for template in templates:
            if template.name.strip().lower() == "infobox item":
                # Parse basic properties
                for param in template.params:
                    name = param.name.strip().lower()
                    value = param.value.strip()
                    
                    if name == "members":
                        item_data["members"] = value.lower() == "yes"
                    elif name == "tradeable":
                        item_data["tradeable"] = value.lower() == "yes"
                    elif name == "stackable":
                        item_data["stackable"] = value.lower() == "yes"
                    elif name == "noted":
                        item_data["noted"] = value.lower() == "yes"
                    elif name == "noteable":
                        item_data["noteable"] = value.lower() == "yes"
                    elif name == "equipable":
                        item_data["equipable"] = value.lower() == "yes"
                    elif name == "weight":
                        try:
                            item_data["weight"] = float(value)
                        except ValueError:
                            pass
                    elif name == "release":
                        item_data["release_date"] = value
                    elif name == "examine":
                        item_data["examine"] = value
                    elif name == "value":
                        try:
                            item_data["value"] = int(value)
                        except ValueError:
                            pass
                    elif name == "high":
                        try:
                            item_data["high_alch"] = int(value)
                        except ValueError:
                            pass
                    elif name == "low":
                        try:
                            item_data["low_alch"] = int(value)
                        except ValueError:
                            pass
                    elif name == "limit":
                        try:
                            item_data["buy_limit"] = int(value)
                        except ValueError:
                            pass
                    elif name == "quest":
                        item_data["quest_item"] = value.lower() == "yes"
                            
            elif template.name.strip().lower() == "infobox bonuses":
                # Parse equipment stats
                for param in template.params:
                    name = param.name.strip().lower()
                    try:
                        value = int(param.value.strip())
                        if name == "astab":
                            item_data["stats"]["attack_stab"] = value
                        elif name == "aslash":
                            item_data["stats"]["attack_slash"] = value
                        elif name == "acrush":
                            item_data["stats"]["attack_crush"] = value
                        elif name == "amagic":
                            item_data["stats"]["attack_magic"] = value
                        elif name == "arange":
                            item_data["stats"]["attack_ranged"] = value
                        elif name == "dstab":
                            item_data["stats"]["defence_stab"] = value
                        elif name == "dslash":
                            item_data["stats"]["defence_slash"] = value
                        elif name == "dcrush":
                            item_data["stats"]["defence_crush"] = value
                        elif name == "dmagic":
                            item_data["stats"]["defence_magic"] = value
                        elif name == "drange":
                            item_data["stats"]["defence_ranged"] = value
                        elif name == "str":
                            item_data["stats"]["melee_strength"] = value
                        elif name == "rstr":
                            item_data["stats"]["ranged_strength"] = value
                        elif name == "mdmg":
                            item_data["stats"]["magic_damage"] = value
                        elif name == "prayer":
                            item_data["stats"]["prayer"] = value
                        elif name == "speed":
                            item_data["stats"]["speed"] = value
                    except ValueError:
                        pass
                        
            elif template.name.strip().lower() == "infobox requirements":
                # Parse requirements
                for param in template.params:
                    name = param.name.strip().lower()
                    value = param.value.strip()
                    
                    if name in ("attack", "strength", "defence", "ranged",
                              "prayer", "magic", "slayer"):
                        try:
                            item_data["requirements"][name] = int(value)
                        except ValueError:
                            pass
                    elif name == "quests":
                        item_data["requirements"]["quests"] = [
                            q.strip() for q in value.split(",")
                        ]
                        
        return item_data
        
    async def fetch_all_items(self):
        """Fetch data for all items."""
        item_list = await self.fetch_item_list()
        
        for i, item_name in enumerate(item_list, 1):
            logger.info(f"Processing {i}/{len(item_list)}: {item_name}")
            item_data = await self.fetch_item_data(item_name)
            if item_data:
                self.items[item_name] = item_data
                
    def save_data(self):
        """Save fetched item data to JSON file."""
        output_file = Path(__file__).parent.parent.parent / "src" / "data" / "items.json"
        with open(output_file, "w") as f:
            json.dump(self.items, f, indent=2)
        logger.info(f"Saved {len(self.items)} items to {output_file}")

async def main():
    """Main function to fetch and save item data."""
    try:
        logger.info("Starting item data fetch...")
        
        async with WikiItemFetcher() as fetcher:
            await fetcher.fetch_all_items()
            fetcher.save_data()
            
        logger.info("Item data fetch completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in item fetch process: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nItem fetch cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1) 