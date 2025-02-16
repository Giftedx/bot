#!/usr/bin/env python3
"""
Script to fetch skill data from the OSRS Wiki.
Fetches complete skill information including experience tables, unlocks, and training methods.
"""
import asyncio
import logging
from pathlib import Path
import sys
from typing import Dict, Any, Optional

import aiohttp
import mwparserfromhell

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fetch_skills.log")
    ]
)
logger = logging.getLogger(__name__)

OSRS_WIKI_API_URL = "https://oldschool.runescape.wiki/api.php"
USER_AGENT = "OSRSBot SkillFetcher/1.0"

class WikiSkillFetcher:
    """Fetches skill data from the OSRS Wiki."""
    
    def __init__(self):
        """Initialize skill fetcher."""
        self.session: Optional[aiohttp.ClientSession] = None
        self.skills: Dict[str, Any] = {}
        self.skill_names = [
            "Attack", "Strength", "Defence", "Ranged", "Prayer", "Magic",
            "Runecraft", "Hitpoints", "Crafting", "Mining", "Smithing",
            "Fishing", "Cooking", "Firemaking", "Woodcutting", "Agility",
            "Herblore", "Thieving", "Fletching", "Slayer", "Farming",
            "Construction", "Hunter"
        ]
        
    async def __aenter__(self):
        """Set up async context."""
        self.session = aiohttp.ClientSession(headers={"User-Agent": USER_AGENT})
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up async context."""
        if self.session:
            await self.session.close()
            
    async def fetch_with_retry(self, url: str, params: Dict[str, str], max_retries: int = 3) -> Dict:
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
                
    async def fetch_skill_data(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Fetch data for a specific skill."""
        params = {
            "action": "parse",
            "prop": "wikitext",
            "format": "json",
            "page": skill_name
        }
        
        try:
            data = await self.fetch_with_retry(OSRS_WIKI_API_URL, params)
            wikitext = data["parse"]["wikitext"]["*"]
            return self.parse_skill_wikitext(wikitext, skill_name)
        except Exception as e:
            logger.error(f"Error fetching {skill_name}: {e}")
            return None
            
    def parse_skill_wikitext(self, wikitext: str, skill_name: str) -> Dict[str, Any]:
        """Parse skill data from wiki text."""
        parsed = mwparserfromhell.parse(wikitext)
        templates = parsed.filter_templates()
        
        skill_data = {
            "name": skill_name,
            "members": False,
            "max_level": 99,
            "elite_level": 120,
            "xp_table": self.generate_xp_table(),
            "unlocks": [],
            "training_methods": [],
            "quests": [],
            "achievements": [],
            "wiki_url": f"https://oldschool.runescape.wiki/w/{skill_name}"
        }
        
        for template in templates:
            if template.name.strip().lower() == "skill info":
                # Parse basic properties
                for param in template.params:
                    name = param.name.strip().lower()
                    value = param.value.strip()
                    
                    if name == "members":
                        skill_data["members"] = value.lower() == "yes"
                    elif name == "max":
                        try:
                            skill_data["max_level"] = int(value)
                        except ValueError:
                            pass
                    elif name == "elite":
                        try:
                            skill_data["elite_level"] = int(value)
                        except ValueError:
                            pass
                            
            elif template.name.strip().lower() == "skill unlocks":
                # Parse skill unlocks
                unlocks = []
                for param in template.params:
                    level = param.name.strip()
                    try:
                        level = int(level)
                        unlocks.append({
                            "level": level,
                            "description": param.value.strip()
                        })
                    except ValueError:
                        continue
                skill_data["unlocks"] = sorted(unlocks, key=lambda x: x["level"])
                
            elif template.name.strip().lower() == "training methods":
                # Parse training methods
                methods = []
                for param in template.params:
                    name = param.name.strip()
                    if name.lower() not in ("name", "level", "xp"):
                        continue
                    try:
                        method = {
                            "name": param.value.strip(),
                            "level": int(param.value.strip()),
                            "xp_per_hour": float(param.value.strip().replace(",", ""))
                        }
                        methods.append(method)
                    except ValueError:
                        continue
                skill_data["training_methods"] = sorted(methods, key=lambda x: x["level"])
                
        return skill_data
        
    def generate_xp_table(self) -> Dict[int, int]:
        """Generate XP table for levels 1-99."""
        xp_table = {}
        for level in range(1, 100):
            if level == 1:
                xp_table[level] = 0
            else:
                points = 0
                for lvl in range(1, level):
                    points += int(lvl + 300 * pow(2, lvl / 7.0))
                xp_table[level] = int(points / 4)
        return xp_table
        
    async def fetch_all_skills(self):
        """Fetch data for all skills."""
        for skill_name in self.skill_names:
            logger.info(f"Processing skill: {skill_name}")
            if skill_data := await self.fetch_skill_data(skill_name):
                self.skills[skill_name.lower()] = skill_data
                
    def save_data(self):
        """Save fetched skill data to JSON file."""
        output_file = Path(__file__).parent.parent.parent / "src" / "data" / "skills.json"
        with open(output_file, "w") as f:
            json.dump(self.skills, f, indent=2)
        logger.info(f"Saved {len(self.skills)} skills to {output_file}")

async def main():
    """Main function to fetch and save skill data."""
    try:
        logger.info("Starting skill data fetch...")
        
        async with WikiSkillFetcher() as fetcher:
            await fetcher.fetch_all_skills()
            fetcher.save_data()
            
        logger.info("Skill data fetch completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in skill fetch process: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nSkill fetch cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1) 