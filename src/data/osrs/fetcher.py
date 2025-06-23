import aiohttp
import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
import mwclient
from bs4 import BeautifulSoup

from .models import (
    OSRSPet,
    OSRSPetSource,
    OSRSPetRarity,
    OSRSPetAbility,
    OSRSPetVariant,
    OSRSLocation,
    OSRSCombatStats,
    OSRSSkill,
    OSRSBoss,
    OSRSSkillingActivity,
    OSRSMinigame,
)

logger = logging.getLogger(__name__)


class OSRSDataFetcher:
    WIKI_API_URL = "https://oldschool.runescape.wiki/api.php"
    OSRS_API_URL = "https://secure.runescape.com/m=itemdb_oldschool/api"
    CACHE_DIR = Path("data/cache/osrs")
    CACHE_DURATION_DAYS = 7

    def __init__(self):
        self.wiki_site = mwclient.Site("oldschool.runescape.wiki", path="/")
        self.session = None
        self.cache = {}
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _get_cache_path(self, key: str) -> Path:
        return self.CACHE_DIR / f"{key}.json"

    def _load_cache(self, key: str) -> Optional[Dict]:
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                data = json.loads(cache_path.read_text())
                cache_date = datetime.fromisoformat(data["cached_at"])
                if (datetime.now() - cache_date).days < self.CACHE_DURATION_DAYS:
                    return data["content"]
            except Exception as e:
                logger.warning(f"Failed to load cache for {key}: {e}")
        return None

    def _save_cache(self, key: str, content: Any):
        cache_path = self._get_cache_path(key)
        try:
            cache_data = {"cached_at": datetime.now().isoformat(), "content": content}
            cache_path.write_text(json.dumps(cache_data, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save cache for {key}: {e}")

    async def fetch_wiki_page(self, title: str) -> Optional[Dict]:
        """Fetch a page from the OSRS Wiki"""
        cache_key = f"wiki_page_{title}"
        cached = self._load_cache(cache_key)
        if cached:
            return cached

        try:
            page = self.wiki_site.pages[title]
            if not page.exists:
                return None

            content = page.text()
            html = page.html

            data = {
                "title": title,
                "content": content,
                "html": html,
                "categories": [cat.name for cat in page.categories()],
                "links": [link.name for link in page.links()],
            }

            self._save_cache(cache_key, data)
            return data
        except Exception as e:
            logger.error(f"Failed to fetch wiki page {title}: {e}")
            return None

    async def fetch_osrs_api(self, endpoint: str) -> Optional[Dict]:
        """Fetch data from the OSRS API"""
        cache_key = f"osrs_api_{endpoint}"
        cached = self._load_cache(cache_key)
        if cached:
            return cached

        url = f"{self.OSRS_API_URL}/{endpoint}"
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    self._save_cache(cache_key, data)
                    return data
                else:
                    logger.warning(f"OSRS API returned status {response.status} for {endpoint}")
                    return None
        except Exception as e:
            logger.error(f"Failed to fetch OSRS API {endpoint}: {e}")
            return None

    def _parse_infobox(self, content: str) -> Dict[str, Any]:
        """Parse an OSRS Wiki infobox template"""
        infobox = {}
        current_key = None
        current_value = []

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith("|"):
                if current_key and current_value:
                    infobox[current_key] = "\n".join(current_value).strip()
                    current_value = []

                parts = line[1:].split("=", 1)
                if len(parts) == 2:
                    current_key = parts[0].strip()
                    current_value = [parts[1].strip()]
                else:
                    current_key = None
            elif current_key:
                current_value.append(line)

        if current_key and current_value:
            infobox[current_key] = "\n".join(current_value).strip()

        return infobox

    def _parse_combat_stats(self, infobox: Dict[str, Any]) -> OSRSCombatStats:
        """Parse combat stats from an infobox"""

        def parse_int(value: str, default: int = 1) -> int:
            try:
                return int(re.sub(r"[^\d]", "", value))
            except (ValueError, TypeError):
                return default

        return OSRSCombatStats(
            attack_level=parse_int(infobox.get("attack", "1")),
            strength_level=parse_int(infobox.get("strength", "1")),
            defence_level=parse_int(infobox.get("defence", "1")),
            hitpoints_level=parse_int(infobox.get("hitpoints", "1")),
            ranged_level=parse_int(infobox.get("ranged", "1")),
            magic_level=parse_int(infobox.get("magic", "1")),
            prayer_level=parse_int(infobox.get("prayer", "1")),
            combat_level=parse_int(infobox.get("combat", "1")),
            attack_bonus={
                "stab": parse_int(infobox.get("astab", "0")),
                "slash": parse_int(infobox.get("aslash", "0")),
                "crush": parse_int(infobox.get("acrush", "0")),
                "magic": parse_int(infobox.get("amagic", "0")),
                "ranged": parse_int(infobox.get("arange", "0")),
            },
            defence_bonus={
                "stab": parse_int(infobox.get("dstab", "0")),
                "slash": parse_int(infobox.get("dslash", "0")),
                "crush": parse_int(infobox.get("dcrush", "0")),
                "magic": parse_int(infobox.get("dmagic", "0")),
                "ranged": parse_int(infobox.get("drange", "0")),
            },
            other_bonuses={
                "strength": parse_int(infobox.get("str", "0")),
                "ranged_strength": parse_int(infobox.get("rstr", "0")),
                "magic_damage": parse_int(infobox.get("mdmg", "0")),
                "prayer": parse_int(infobox.get("prayer", "0")),
            },
        )

    async def fetch_pet_data(self, pet_name: str) -> Optional[OSRSPet]:
        """Fetch and parse pet data from the OSRS Wiki"""
        page_data = await self.fetch_wiki_page(pet_name)
        if not page_data:
            return None

        content = page_data["content"]
        infobox = self._parse_infobox(content)

        # Parse release date
        release_date = None
        if "release" in infobox:
            try:
                release_date = datetime.strptime(infobox["release"], "%d %B %Y")
            except ValueError:
                logger.warning(f"Could not parse release date for {pet_name}")

        # Determine pet source and rarity
        source = OSRSPetSource.OTHER
        rarity = OSRSPetRarity.RARE
        if "boss" in page_data["categories"]:
            source = OSRSPetSource.BOSS
        elif "skilling" in page_data["categories"]:
            source = OSRSPetSource.SKILLING
        elif "minigame" in page_data["categories"]:
            source = OSRSPetSource.MINIGAME
        elif "quest" in page_data["categories"]:
            source = OSRSPetSource.QUEST
            rarity = OSRSPetRarity.GUARANTEED

        # Parse drop rate
        drop_rate = None
        if "droprate" in infobox:
            rate_str = infobox["droprate"]
            if "/" in rate_str:
                try:
                    num, den = map(int, rate_str.split("/"))
                    drop_rate = num / den
                except ValueError:
                    logger.warning(f"Could not parse drop rate for {pet_name}")

        # Determine rarity based on drop rate if available
        if drop_rate:
            if drop_rate >= 1 / 1000:
                rarity = OSRSPetRarity.COMMON
            elif drop_rate >= 1 / 5000:
                rarity = OSRSPetRarity.UNCOMMON
            elif drop_rate >= 1 / 10000:
                rarity = OSRSPetRarity.RARE
            else:
                rarity = OSRSPetRarity.VERY_RARE

        # Parse requirements
        requirements = {}
        for skill in OSRSSkill:
            if f"{skill.value} level" in infobox:
                try:
                    level = int(infobox[f"{skill.value} level"])
                    requirements[skill] = level
                except ValueError:
                    continue

        # Parse variants
        variants = []
        if "versions" in infobox:
            for version in infobox["versions"].split(","):
                version = version.strip()
                variants.append(
                    OSRSPetVariant(
                        name=version, examine_text=f"A variant of {pet_name}", metamorphic=True
                    )
                )

        return OSRSPet(
            id=infobox.get("id", ""),
            name=pet_name,
            release_date=release_date or datetime.now(),
            source=source,
            rarity=rarity,
            base_stats=self._parse_combat_stats(infobox),
            abilities=[],  # Would need additional parsing for abilities
            variants=variants,
            obtainable_from=infobox.get("obtain", "").split(","),
            drop_rate=drop_rate,
            requirements=requirements,
            quest_requirements=[],  # Would need additional parsing
            item_requirements=[],  # Would need additional parsing
            locations=[],  # Would need additional parsing
            examine_text=infobox.get("examine", ""),
            trivia=[],  # Would need additional parsing
            wiki_url=f"https://oldschool.runescape.wiki/w/{pet_name.replace(' ', '_')}",
        )

    async def fetch_all_pets(self) -> List[OSRSPet]:
        """Fetch data for all OSRS pets"""
        # First, get the category members for pets
        pets_category = self.wiki_site.categories["Pets"]
        pet_pages = list(pets_category.members())

        pets = []
        for page in pet_pages:
            pet_data = await self.fetch_pet_data(page.name)
            if pet_data:
                pets.append(pet_data)

        return pets

    async def fetch_boss_data(self, boss_name: str) -> Optional[OSRSBoss]:
        """Fetch and parse boss data from the OSRS Wiki"""
        # Implementation similar to fetch_pet_data but for bosses
        pass

    async def fetch_skilling_activity(self, activity_name: str) -> Optional[OSRSSkillingActivity]:
        """Fetch and parse skilling activity data from the OSRS Wiki"""
        # Implementation for fetching skilling activity data
        pass

    async def fetch_minigame_data(self, minigame_name: str) -> Optional[OSRSMinigame]:
        """Fetch and parse minigame data from the OSRS Wiki"""
        # Implementation for fetching minigame data
        pass
