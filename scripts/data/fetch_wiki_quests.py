#!/usr/bin/env python3
"""
Script to fetch quest data from the OSRS Wiki.
Fetches complete quest information including requirements, rewards, and steps.
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
        logging.FileHandler("fetch_quests.log")
    ]
)
logger = logging.getLogger(__name__)

OSRS_WIKI_API_URL = "https://oldschool.runescape.wiki/api.php"
USER_AGENT = "OSRSBot QuestFetcher/1.0"

class WikiQuestFetcher:
    """Fetches quest data from the OSRS Wiki."""
    
    def __init__(self):
        """Initialize quest fetcher."""
        self.session: Optional[aiohttp.ClientSession] = None
        self.quests: Dict[str, Any] = {}
        
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
                
    async def fetch_quest_list(self) -> list[str]:
        """Fetch list of all quests from the wiki."""
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": "Category:Quests",
            "cmlimit": "500",
            "format": "json"
        }
        
        quests = []
        while True:
            data = await self.fetch_with_retry(OSRS_WIKI_API_URL, params)
            if "query" not in data:
                break
                
            for quest in data["query"]["categorymembers"]:
                if not quest["title"].startswith(("File:", "Category:")):
                    quests.append(quest["title"])
                    
            if "continue" not in data:
                break
            params.update(data["continue"])
            
        logger.info(f"Found {len(quests)} quests")
        return quests
        
    async def fetch_quest_data(self, quest_name: str) -> Optional[Dict[str, Any]]:
        """Fetch data for a specific quest."""
        params = {
            "action": "parse",
            "prop": "wikitext",
            "format": "json",
            "page": quest_name
        }
        
        try:
            data = await self.fetch_with_retry(OSRS_WIKI_API_URL, params)
            wikitext = data["parse"]["wikitext"]["*"]
            return self.parse_quest_wikitext(wikitext, quest_name)
        except Exception as e:
            logger.error(f"Error fetching {quest_name}: {e}")
            return None
            
    def parse_quest_wikitext(self, wikitext: str, quest_name: str) -> Dict[str, Any]:
        """Parse quest data from wiki text."""
        parsed = mwparserfromhell.parse(wikitext)
        templates = parsed.filter_templates()
        
        quest_data = {
            "name": quest_name,
            "difficulty": "Novice",
            "length": "Short",
            "members": False,
            "description": "",
            "requirements": {
                "skills": {},
                "quests": [],
                "items": [],
                "combat": None,
                "quest_points": 0
            },
            "rewards": {
                "quest_points": 1,
                "xp": {},
                "items": [],
                "access": [],
                "other": []
            },
            "steps": [],
            "wiki_url": f"https://oldschool.runescape.wiki/w/{quest_name.replace(' ', '_')}"
        }
        
        for template in templates:
            if template.name.strip().lower() == "quest":
                # Parse basic properties
                for param in template.params:
                    name = param.name.strip().lower()
                    value = param.value.strip()
                    
                    if name == "name":
                        quest_data["name"] = value
                    elif name == "difficulty":
                        quest_data["difficulty"] = value
                    elif name == "length":
                        quest_data["length"] = value
                    elif name == "members":
                        quest_data["members"] = value.lower() == "yes"
                    elif name == "description":
                        quest_data["description"] = value
                        
            elif template.name.strip().lower() == "quest requirements":
                # Parse requirements
                for param in template.params:
                    name = param.name.strip().lower()
                    value = param.value.strip()
                    
                    if name in ("attack", "strength", "defence", "ranged", "prayer",
                              "magic", "runecraft", "hitpoints", "crafting", "mining",
                              "smithing", "fishing", "cooking", "firemaking", "woodcutting",
                              "agility", "herblore", "thieving", "fletching", "slayer",
                              "farming", "construction", "hunter"):
                        try:
                            quest_data["requirements"]["skills"][name] = int(value)
                        except ValueError:
                            pass
                    elif name == "quests":
                        quest_data["requirements"]["quests"] = [
                            q.strip() for q in value.split(",")
                        ]
                    elif name == "items":
                        quest_data["requirements"]["items"] = [
                            i.strip() for i in value.split(",")
                        ]
                    elif name == "combat":
                        try:
                            quest_data["requirements"]["combat"] = int(value)
                        except ValueError:
                            pass
                    elif name == "quest points":
                        try:
                            quest_data["requirements"]["quest_points"] = int(value)
                        except ValueError:
                            pass
                            
            elif template.name.strip().lower() == "quest rewards":
                # Parse rewards
                for param in template.params:
                    name = param.name.strip().lower()
                    value = param.value.strip()
                    
                    if name == "quest points":
                        try:
                            quest_data["rewards"]["quest_points"] = int(value)
                        except ValueError:
                            pass
                    elif name.endswith(" xp"):
                        skill = name[:-3]
                        try:
                            quest_data["rewards"]["xp"][skill] = int(value.replace(",", ""))
                        except ValueError:
                            pass
                    elif name == "items":
                        quest_data["rewards"]["items"] = [
                            i.strip() for i in value.split(",")
                        ]
                    elif name == "access":
                        quest_data["rewards"]["access"] = [
                            a.strip() for a in value.split(",")
                        ]
                    elif name == "other":
                        quest_data["rewards"]["other"] = [
                            o.strip() for o in value.split(",")
                        ]
                            
            elif template.name.strip().lower() == "quest steps":
                # Parse quest steps
                steps = []
                for param in template.params:
                    if param.name.strip().isdigit():
                        steps.append(param.value.strip())
                quest_data["steps"] = steps
                
        return quest_data
        
    async def fetch_all_quests(self):
        """Fetch data for all quests."""
        quests = await self.fetch_quest_list()
        
        for i, quest_name in enumerate(quests, 1):
            logger.info(f"Processing {i}/{len(quests)}: {quest_name}")
            if quest_data := await self.fetch_quest_data(quest_name):
                self.quests[quest_name] = quest_data
                
    def save_data(self):
        """Save fetched quest data to JSON file."""
        output_file = Path(__file__).parent.parent.parent / "src" / "data" / "quests.json"
        with open(output_file, "w") as f:
            json.dump(self.quests, f, indent=2)
        logger.info(f"Saved {len(self.quests)} quests to {output_file}")

async def main():
    """Main function to fetch and save quest data."""
    try:
        logger.info("Starting quest data fetch...")
        
        async with WikiQuestFetcher() as fetcher:
            await fetcher.fetch_all_quests()
            fetcher.save_data()
            
        logger.info("Quest data fetch completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in quest fetch process: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nQuest fetch cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1) 