"""Enhanced data fetcher for OSRS data."""

import aiohttp
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class EnhancedFetcher:
    """
    Enhanced data fetcher that combines multiple OSRS data sources
    and adds additional features like caching and rate limiting
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_fetch: Dict[str, datetime] = {}
        self.rate_limits: Dict[str, float] = {
            'wiki': 1.0,  # 1 request per second
            'ge': 0.5,    # 2 requests per second
            'hiscores': 1.0
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _respect_rate_limit(self, api: str):
        """Respect rate limits for different APIs"""
        if api in self.last_fetch:
            elapsed = datetime.now() - self.last_fetch[api]
            if elapsed.total_seconds() < self.rate_limits[api]:
                await asyncio.sleep(self.rate_limits[api] - elapsed.total_seconds())
        self.last_fetch[api] = datetime.now()

    async def _cache_data(self, name: str, data: Any):
        """Cache fetched data to file"""
        cache_file = self.cache_dir / f"{name}_data.json"
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            async with aiohttp.ClientSession() as session:
                async with session.get("https://oldschool.runescape.wiki/api.php") as response:
                    if response.status == 200:
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            json.dump(cache_data, f, indent=4)
        except Exception as e:
            logger.error(f"Error caching {name} data: {str(e)}")

    async def _get_cached_data(self, name: str, subkey: str = None) -> Optional[Any]:
        """Get data from cache if available"""
        cache_file = self.cache_dir / f"{name}_data.json"
        try:
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if subkey:
                        return data.get('data', {}).get(subkey)
                    return data.get('data')
        except Exception as e:
            logger.error(f"Error reading cache for {name}: {str(e)}")
        return None

    async def fetch_all(self):
        """Fetch all available data and cache it"""
        try:
            tasks = [
                self.fetch_ge_data(),
                self.fetch_wiki_data(),
                self.fetch_item_data(),
                self.fetch_monster_data(),
                self.fetch_quest_data(),
                self.fetch_achievement_data()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle any errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error in task {tasks[i].__name__}: {str(result)}")
                else:
                    await self._cache_data(tasks[i].__name__.replace('fetch_', ''), result)
            
            logger.info("All data fetched and cached successfully")
            return results
        except Exception as e:
            logger.error(f"Error fetching all data: {str(e)}")
            raise

    async def fetch_ge_data(self) -> Dict[str, Any]:
        """Fetch Grand Exchange data"""
        endpoints = {
            'latest': '/latest',
            'mapping': '/mapping',
            '5m': '/5m',
            '1h': '/1h',
            'timeseries': '/timeseries'
        }
        
        data = {}
        base_url = "https://prices.runescape.wiki/api/v1/osrs"
        
        for endpoint_name, endpoint in endpoints.items():
            await self._respect_rate_limit('ge')
            try:
                async with self.session.get(f"{base_url}{endpoint}") as response:
                    if response.status == 200:
                        data[endpoint_name] = await response.json()
                    else:
                        logger.warning(f"GE API returned status {response.status} for {endpoint}")
            except Exception as e:
                logger.error(f"Error fetching GE {endpoint_name} data: {str(e)}")
                data[endpoint_name] = None
                
        return data

    async def fetch_wiki_data(self) -> Dict[str, Any]:
        """Fetch comprehensive wiki data"""
        categories = [
            'Items', 'Monsters', 'Quests', 'Minigames',
            'Pets', 'Achievements', 'Skills', 'Equipment',
            'Weapons', 'Armour', 'Tools', 'Resources',
            'Locations', 'NPCs', 'Shops'
        ]
        
        data = {}
        for category in categories:
            await self._respect_rate_limit('wiki')
            try:
                params = {
                    'action': 'query',
                    'list': 'categorymembers',
                    'cmtitle': f'Category:{category}',
                    'cmlimit': 5000,  # Get more items
                    'format': 'json'
                }
                
                async with self.session.get(
                    "https://oldschool.runescape.wiki/api.php",
                    params=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        data[category] = result.get('query', {}).get('categorymembers', [])
                    else:
                        logger.warning(f"Wiki API returned status {response.status} for {category}")
            except Exception as e:
                logger.error(f"Error fetching wiki data for {category}: {str(e)}")
                data[category] = []
                
        return data

    async def fetch_item_data(self) -> Dict[str, Any]:
        """Fetch detailed item data"""
        items = {}
        mapping_data = await self._get_cached_data('ge', 'mapping')
        
        if not mapping_data:
            return items
            
        for item in mapping_data:  # Get all items
            item_id = str(item.get('id'))
            await self._respect_rate_limit('ge')
            try:
                async with self.session.get(
                    f"https://secure.runescape.com/m=itemdb_oldschool/api/catalogue/detail.json?item={item_id}"
                ) as response:
                    if response.status == 200:
                        items[item_id] = await response.json()
            except Exception as e:
                logger.error(f"Error fetching item data for {item_id}: {str(e)}")
                
        return items

    async def fetch_monster_data(self) -> Dict[str, Any]:
        """Fetch detailed monster data"""
        monsters = {}
        wiki_data = await self._get_cached_data('wiki')
        
        if not wiki_data or 'Monsters' not in wiki_data:
            return monsters
            
        for monster in wiki_data['Monsters']:  # Get all monsters
            page_title = monster.get('title')
            if not page_title:
                continue
                
            await self._respect_rate_limit('wiki')
            try:
                params = {
                    'action': 'parse',
                    'page': page_title,
                    'prop': 'text|templates|categories|links',
                    'format': 'json'
                }
                
                async with self.session.get(
                    "https://oldschool.runescape.wiki/api.php",
                    params=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        monsters[page_title] = result.get('parse', {})
            except Exception as e:
                logger.error(f"Error fetching monster data for {page_title}: {str(e)}")
                
        return monsters

    async def fetch_quest_data(self) -> Dict[str, Any]:
        """Fetch quest data"""
        quests = {}
        wiki_data = await self._get_cached_data('wiki')
        
        if not wiki_data or 'Quests' not in wiki_data:
            return quests
            
        for quest in wiki_data['Quests']:  # Get all quests
            page_title = quest.get('title')
            if not page_title:
                continue
                
            await self._respect_rate_limit('wiki')
            try:
                params = {
                    'action': 'parse',
                    'page': page_title,
                    'prop': 'text|templates|categories|links',
                    'format': 'json'
                }
                
                async with self.session.get(
                    "https://oldschool.runescape.wiki/api.php",
                    params=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        quests[page_title] = result.get('parse', {})
            except Exception as e:
                logger.error(f"Error fetching quest data for {page_title}: {str(e)}")
                
        return quests

    async def fetch_achievement_data(self) -> Dict[str, Any]:
        """Fetch achievement diary data"""
        achievements = {}
        wiki_data = await self._get_cached_data('wiki')
        
        if not wiki_data or 'Achievements' not in wiki_data:
            return achievements
            
        for achievement in wiki_data['Achievements']:  # Get all achievements
            page_title = achievement.get('title')
            if not page_title:
                continue
                
            await self._respect_rate_limit('wiki')
            try:
                params = {
                    'action': 'parse',
                    'page': page_title,
                    'prop': 'text|templates|categories|links',
                    'format': 'json'
                }
                
                async with self.session.get(
                    "https://oldschool.runescape.wiki/api.php",
                    params=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        achievements[page_title] = result.get('parse', {})
            except Exception as e:
                logger.error(f"Error fetching achievement data for {page_title}: {str(e)}")
                
        return achievements

if __name__ == "__main__":
    async def main():
        async with EnhancedFetcher() as fetcher:
            await fetcher.fetch_all()
    
    asyncio.run(main()) 