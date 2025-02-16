#!/usr/bin/env python3
"""
Script to fetch equipment data from the OSRS Wiki.
Fetches complete equipment information including stats, requirements, and bonuses.
"""
import asyncio
import logging
from pathlib import Path
import sys
from typing import Dict, Any, Optional, List, Tuple

import aiohttp
import mwparserfromhell
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fetch_equipment.log")
    ]
)
logger = logging.getLogger(__name__)

OSRS_WIKI_API_URL = "https://oldschool.runescape.wiki/api.php"
USER_AGENT = "OSRSBot EquipmentFetcher/1.0"

class WikiEquipmentFetcher:
    """Fetches equipment data from the OSRS Wiki."""
    
    def __init__(self):
        """Initialize equipment fetcher."""
        self.session: Optional[aiohttp.ClientSession] = None
        self.equipment: Dict[str, Any] = {}
        self.equipment_slots = [
            "weapon", "shield", "head", "cape", "neck", "ammunition",
            "body", "legs", "hands", "feet", "ring"
        ]
        
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
                async with self.session.get(url, params=params) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Retry {attempt + 1}/{max_retries} after error: {e}")
                await asyncio.sleep(1)
                
    async def fetch_equipment_list(self) -> List[Tuple[str, str]]:
        """Fetch list of all equipment from the wiki."""
        equipment = []
        
        for slot in self.equipment_slots:
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": f"Category:{slot.title()} slot items",
                "cmlimit": "500",
                "format": "json"
            }
            
            while True:
                data = await self.fetch_with_retry(OSRS_WIKI_API_URL, params)
                if "query" not in data:
                    break
                    
                for item in data["query"]["categorymembers"]:
                    if not item["title"].startswith(("File:", "Category:")):
                        equipment.append((item["title"], slot))
                        
                if "continue" not in data:
                    break
                params.update(data["continue"])
                
        logger.info(f"Found {len(equipment)} equipment items")
        return equipment
        
    async def fetch_equipment_data(self, equipment_name: str, slot: str) -> Optional[Dict[str, Any]]:
        """Fetch data for a specific equipment item."""
        params = {
            "action": "parse",
            "prop": "wikitext",
            "format": "json",
            "page": equipment_name
        }
        
        try:
            data = await self.fetch_with_retry(OSRS_WIKI_API_URL, params)
            wikitext = data["parse"]["wikitext"]["*"]
            return self.parse_equipment_wikitext(wikitext, equipment_name, slot)
        except Exception as e:
            logger.error(f"Error fetching {equipment_name}: {e}")
            return None
            
    def parse_equipment_wikitext(self, wikitext: str, equipment_name: str, slot: str) -> Dict[str, Any]:
        """Parse equipment data from wiki text."""
        parsed = mwparserfromhell.parse(wikitext)
        templates = parsed.filter_templates()
        
        equipment_data = {
            "name": equipment_name,
            "slot": slot,
            "members": False,
            "tradeable": True,
            "equipable": True,
            "stackable": False,
            "weight": 0.0,
            "release_date": None,
            "examine": None,
            "value": 0,
            "high_alch": 0,
            "low_alch": 0,
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
            "wiki_url": f"https://oldschool.runescape.wiki/w/{equipment_name.replace(' ', '_')}"
        }
        
        for template in templates:
            if template.name.strip().lower() == "infobox item":
                # Parse basic properties
                for param in template.params:
                    name = param.name.strip().lower()
                    value = param.value.strip()
                    
                    if name == "members":
                        equipment_data["members"] = value.lower() == "yes"
                    elif name == "tradeable":
                        equipment_data["tradeable"] = value.lower() == "yes"
                    elif name == "stackable":
                        equipment_data["stackable"] = value.lower() == "yes"
                    elif name == "weight":
                        try:
                            equipment_data["weight"] = float(value)
                        except ValueError:
                            pass
                    elif name == "release":
                        equipment_data["release_date"] = value
                    elif name == "examine":
                        equipment_data["examine"] = value
                    elif name == "value":
                        try:
                            equipment_data["value"] = int(value)
                        except ValueError:
                            pass
                    elif name == "high":
                        try:
                            equipment_data["high_alch"] = int(value)
                        except ValueError:
                            pass
                    elif name == "low":
                        try:
                            equipment_data["low_alch"] = int(value)
                        except ValueError:
                            pass
                            
            elif template.name.strip().lower() == "infobox bonuses":
                # Parse equipment stats
                for param in template.params:
                    name = param.name.strip().lower()
                    try:
                        value = int(param.value.strip())
                        if name == "astab":
                            equipment_data["stats"]["attack_stab"] = value
                        elif name == "aslash":
                            equipment_data["stats"]["attack_slash"] = value
                        elif name == "acrush":
                            equipment_data["stats"]["attack_crush"] = value
                        elif name == "amagic":
                            equipment_data["stats"]["attack_magic"] = value
                        elif name == "arange":
                            equipment_data["stats"]["attack_ranged"] = value
                        elif name == "dstab":
                            equipment_data["stats"]["defence_stab"] = value
                        elif name == "dslash":
                            equipment_data["stats"]["defence_slash"] = value
                        elif name == "dcrush":
                            equipment_data["stats"]["defence_crush"] = value
                        elif name == "dmagic":
                            equipment_data["stats"]["defence_magic"] = value
                        elif name == "drange":
                            equipment_data["stats"]["defence_ranged"] = value
                        elif name == "str":
                            equipment_data["stats"]["melee_strength"] = value
                        elif name == "rstr":
                            equipment_data["stats"]["ranged_strength"] = value
                        elif name == "mdmg":
                            equipment_data["stats"]["magic_damage"] = value
                        elif name == "prayer":
                            equipment_data["stats"]["prayer"] = value
                        elif name == "speed":
                            equipment_data["stats"]["speed"] = value
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
                            equipment_data["requirements"][name] = int(value)
                        except ValueError:
                            pass
                    elif name == "quests":
                        equipment_data["requirements"]["quests"] = [
                            q.strip() for q in value.split(",")
                        ]
                        
        return equipment_data
        
    async def fetch_all_equipment(self):
        """Fetch data for all equipment."""
        equipment_list = await self.fetch_equipment_list()
        
        for i, (equipment_name, slot) in enumerate(equipment_list, 1):
            logger.info(f"Processing {i}/{len(equipment_list)}: {equipment_name}")
            equipment_data = await self.fetch_equipment_data(equipment_name, slot)
            if equipment_data:
                self.equipment[equipment_name] = equipment_data
                
    def save_data(self):
        """Save fetched equipment data to JSON file."""
        output_file = Path(__file__).parent.parent.parent / "src" / "data" / "equipment.json"
        with open(output_file, "w") as f:
            json.dump(self.equipment, f, indent=2)
        logger.info(f"Saved {len(self.equipment)} equipment items to {output_file}")

async def main():
    """Main function to fetch and save equipment data."""
    try:
        logger.info("Starting equipment data fetch...")
        
        async with WikiEquipmentFetcher() as fetcher:
            await fetcher.fetch_all_equipment()
            fetcher.save_data()
            
        logger.info("Equipment data fetch completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in equipment fetch process: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nEquipment fetch cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1) 