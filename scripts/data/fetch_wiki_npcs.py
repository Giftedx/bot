#!/usr/bin/env python3
"""
Script to fetch NPC and shop data from the OSRS Wiki.
This script uses the OSRS Wiki API to get accurate NPC information and shop inventories.
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
        logging.FileHandler("fetch_wiki_npcs.log")
    ]
)
logger = logging.getLogger(__name__)

class WikiNPCFetcher:
    """Fetches NPC data from the OSRS Wiki."""
    
    def __init__(self):
        """Initialize NPC fetcher."""
        self.session: Optional[aiohttp.ClientSession] = None
        self.npcs: Dict[str, Any] = {}
        self.shops: Dict[str, Any] = {}
        self.rate_limiter = None  # Will be injected by coordinator
        self.wiki_api_url = "https://oldschool.runescape.wiki/api.php"
        self.data_loader = OSRSDataLoader()
        self.shop_categories = {
            "General stores",
            "Equipment shops",
            "Weapon shops",
            "Rune shops",
            "Food shops",
            "Crafting shops",
            "Fishing shops",
            "Magic shops",
            "Tool shops"
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
        
    async def fetch_npc_list(self) -> List[str]:
        """Fetch list of all NPCs from the Wiki."""
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": "Category:NPCs",
            "cmlimit": 500,
            "format": "json"
        }
        
        try:
            data = await self.fetch_with_retry(self.wiki_api_url, params)
            return [
                page["title"]
                for page in data.get("query", {}).get("categorymembers", [])
            ]
        except Exception as e:
            logger.error(f"Error fetching NPC list: {e}")
            return []
                
    async def fetch_shop_list(self) -> List[str]:
        """Fetch list of all shops from the Wiki."""
        shops = set()
        
        for category in self.shop_categories:
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": f"Category:{category}",
                "cmlimit": 500,
                "format": "json"
            }
            
            try:
                data = await self.fetch_with_retry(self.wiki_api_url, params)
                shops.update(
                    page["title"]
                    for page in data.get("query", {}).get("categorymembers", [])
                )
            except Exception as e:
                logger.error(f"Error fetching shop list for {category}: {e}")
                    
        return list(shops)
                
    async def fetch_npc_data(self, npc_name: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed data for a specific NPC."""
        params = {
            "action": "parse",
            "page": npc_name,
            "prop": "wikitext",
            "format": "json"
        }
        
        try:
            data = await self.fetch_with_retry(self.wiki_api_url, params)
            wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
            return self.parse_npc_wikitext(wikitext, npc_name)
        except Exception as e:
            logger.error(f"Error fetching data for {npc_name}: {e}")
            return None
                
    async def fetch_shop_data(self, shop_name: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed data for a specific shop."""
        params = {
            "action": "parse",
            "page": shop_name,
            "prop": "wikitext",
            "format": "json"
        }
        
        try:
            data = await self.fetch_with_retry(self.wiki_api_url, params)
            wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
            return self.parse_shop_wikitext(wikitext, shop_name)
        except Exception as e:
            logger.error(f"Error fetching data for {shop_name}: {e}")
            return None
                
    def parse_npc_wikitext(self, wikitext: str, npc_name: str) -> Dict[str, Any]:
        """Parse NPC data from Wiki markup."""
        npc_data = {
            "id": self.data_loader.normalize_name(npc_name),
            "name": npc_name,
            "type": "NPC"
        }
        
        # Extract examine text
        examine_match = re.search(r"examine\s*=\s*(.+)", wikitext)
        if examine_match:
            npc_data["examine"] = examine_match.group(1).strip()
            
        # Extract quest involvement
        quest_match = re.search(r"quest\s*=\s*(.+)", wikitext)
        if quest_match:
            npc_data["quests"] = [
                q.strip()
                for q in quest_match.group(1).split(",")
            ]
            
        # Extract options
        options = []
        if "talk-to" in wikitext.lower():
            options.append("Talk-to")
        if "trade" in wikitext.lower():
            options.append("Trade")
            npc_data["has_shop"] = True
            
        if options:
            npc_data["options"] = options
            
        # Extract location
        location_match = re.search(r"location\s*=\s*(.+)", wikitext)
        if location_match:
            npc_data["location"] = location_match.group(1).strip()
            
        # Set wiki URL
        npc_data["wiki_url"] = f"https://oldschool.runescape.wiki/w/{npc_name.replace(' ', '_')}"
        
        return npc_data
        
    def parse_shop_wikitext(self, wikitext: str, shop_name: str) -> Dict[str, Any]:
        """Parse shop data from Wiki markup."""
        shop_data = {
            "id": self.data_loader.normalize_name(shop_name),
            "name": shop_name,
            "type": "SHOP"
        }
        
        # Extract shop type
        if "general store" in wikitext.lower():
            shop_data["shop_type"] = "GENERAL"
        elif "equipment" in wikitext.lower():
            shop_data["shop_type"] = "EQUIPMENT"
        elif "weapon" in wikitext.lower():
            shop_data["shop_type"] = "WEAPON"
        elif "rune" in wikitext.lower():
            shop_data["shop_type"] = "RUNE"
        elif "food" in wikitext.lower():
            shop_data["shop_type"] = "FOOD"
        else:
            shop_data["shop_type"] = "SPECIALTY"
            
        # Extract items
        items = []
        item_pattern = r"\|\s*([^|]+?)\s*=\s*(\d+)"
        for match in re.finditer(item_pattern, wikitext):
            item_name = match.group(1).strip()
            price = int(match.group(2))
            items.append({
                "id": self.data_loader.normalize_name(item_name),
                "name": item_name,
                "price": price
            })
            
        if items:
            shop_data["stock"] = items
            
        # Extract location
        location_match = re.search(r"location\s*=\s*(.+)", wikitext)
        if location_match:
            shop_data["location"] = location_match.group(1).strip()
            
        # Set wiki URL
        shop_data["wiki_url"] = f"https://oldschool.runescape.wiki/w/{shop_name.replace(' ', '_')}"
        
        return shop_data
        
    async def fetch_all_data(self):
        """Fetch data for all NPCs and shops."""
        # Load existing data
        await self.data_loader.load_local_data()
        existing_npcs = self.data_loader.npcs
        existing_shops = self.data_loader.shops
        
        # Fetch NPC list
        npc_names = await self.fetch_npc_list()
        logger.info(f"Found {len(npc_names)} NPCs on Wiki")
        
        # Fetch shop list
        shop_names = await self.fetch_shop_list()
        logger.info(f"Found {len(shop_names)} shops on Wiki")
        
        # Fetch NPC data
        new_npcs = {}
        for name in npc_names:
            npc_id = self.data_loader.normalize_name(name)
            
            # Skip if we already have detailed data
            if npc_id in existing_npcs:
                continue
                
            logger.info(f"Fetching data for NPC {name}...")
            npc_data = await self.fetch_npc_data(name)
            
            if npc_data:
                new_npcs[npc_id] = npc_data
                
        # Fetch shop data
        new_shops = {}
        for name in shop_names:
            shop_id = self.data_loader.normalize_name(name)
            
            # Skip if we already have detailed data
            if shop_id in existing_shops:
                continue
                
            logger.info(f"Fetching data for shop {name}...")
            shop_data = await self.fetch_shop_data(name)
            
            if shop_data:
                new_shops[shop_id] = shop_data
                
        # Merge with existing data
        all_npcs = {**existing_npcs, **new_npcs}
        all_shops = {**existing_shops, **new_shops}
        
        # Save updated data
        data_dir = src_path / "data"
        
        with open(data_dir / "npcs.json", "w") as f:
            json.dump(all_npcs, f, indent=4)
            
        with open(data_dir / "shops.json", "w") as f:
            json.dump(all_shops, f, indent=4)
            
        logger.info(f"Added {len(new_npcs)} new NPCs")
        logger.info(f"Added {len(new_shops)} new shops")
        logger.info(f"Total NPCs: {len(all_npcs)}")
        logger.info(f"Total shops: {len(all_shops)}")

async def main():
    """Main function to fetch Wiki NPC and shop data."""
    try:
        fetcher = WikiNPCFetcher()
        await fetcher.fetch_all_data()
        
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