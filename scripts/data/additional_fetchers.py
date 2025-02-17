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

class AdditionalFetchers:
    """Additional data fetchers for OSRS data."""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_fetch: Dict[str, datetime] = {}
        self.rate_limits: Dict[str, float] = {
            'wiki': 1.0,
            'ge': 0.5,
            'hiscores': 1.0,
            'clan': 2.0,
            'minigame': 1.0
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_all_additional(self):
        """Fetch all additional data types"""
        try:
            tasks = [
                self.fetch_minigame_data(),
                self.fetch_clan_data(),
                self.fetch_skill_data(),
                self.fetch_equipment_data(),
                self.fetch_pet_data(),
                self.fetch_music_data(),
                self.fetch_diary_data()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error in task {tasks[i].__name__}: {str(result)}")
                else:
                    await self._cache_data(tasks[i].__name__.replace('fetch_', ''), result)
            
            logger.info("All additional data fetched and cached successfully")
            return results
        except Exception as e:
            logger.error(f"Error fetching additional data: {str(e)}")
            raise

    async def fetch_minigame_data(self) -> Dict[str, Any]:
        """Fetch data about OSRS minigames"""
        minigames = {}
        wiki_data = await self._get_cached_data('wiki')
        
        if not wiki_data or 'Minigames' not in wiki_data:
            return minigames
            
        for minigame in wiki_data['Minigames']:
            page_title = minigame.get('title')
            if not page_title:
                continue
                
            await self._respect_rate_limit('minigame')
            try:
                params = {
                    'action': 'parse',
                    'page': page_title,
                    'prop': 'text|templates',
                    'format': 'json'
                }
                
                async with self.session.get(
                    "https://oldschool.runescape.wiki/api.php",
                    params=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        page_data = result.get('parse', {})
                        
                        minigame_info = self._parse_minigame_data(page_data)
                        if minigame_info:
                            minigames[page_title] = minigame_info
                    else:
                        logger.warning(f"Wiki API returned status {response.status} for minigame {page_title}")
            except Exception as e:
                logger.error(f"Error fetching minigame data for {page_title}: {str(e)}")
                
        return minigames

    async def fetch_clan_data(self) -> Dict[str, Any]:
        """Fetch data about OSRS clans"""
        try:
            await self._respect_rate_limit('clan')
            async with self.session.get(
                "https://secure.runescape.com/m=clan-hiscores/oldschool/ranking.json?ranking=0"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Clan API returned status {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching clan data: {str(e)}")
            return {}

    async def fetch_skill_data(self) -> Dict[str, Any]:
        """Fetch detailed data about OSRS skills"""
        skills = {}
        wiki_data = await self._get_cached_data('wiki')
        
        if not wiki_data or 'Skills' not in wiki_data:
            return skills
            
        for skill in wiki_data['Skills']:
            page_title = skill.get('title')
            if not page_title:
                continue
                
            await self._respect_rate_limit('wiki')
            try:
                params = {
                    'action': 'parse',
                    'page': page_title,
                    'prop': 'text|templates',
                    'format': 'json'
                }
                
                async with self.session.get(
                    "https://oldschool.runescape.wiki/api.php",
                    params=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        page_data = result.get('parse', {})
                        
                        skill_info = self._parse_skill_data(page_data)
                        if skill_info:
                            skills[page_title] = skill_info
            except Exception as e:
                logger.error(f"Error fetching skill data for {page_title}: {str(e)}")
                
        return skills

    async def fetch_equipment_data(self) -> Dict[str, Any]:
        """Fetch data about OSRS equipment and gear"""
        equipment = {}
        wiki_data = await self._get_cached_data('wiki')
        
        if not wiki_data or 'Items' not in wiki_data:
            return equipment
            
        for item in wiki_data['Items']:
            page_title = item.get('title')
            if not page_title:
                continue
                
            await self._respect_rate_limit('wiki')
            try:
                params = {
                    'action': 'parse',
                    'page': page_title,
                    'prop': 'text|templates',
                    'format': 'json'
                }
                
                async with self.session.get(
                    "https://oldschool.runescape.wiki/api.php",
                    params=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        page_data = result.get('parse', {})
                        
                        if self._is_equipment(page_data):
                            equipment_info = self._parse_equipment_data(page_data)
                            if equipment_info:
                                equipment[page_title] = equipment_info
            except Exception as e:
                logger.error(f"Error fetching equipment data for {page_title}: {str(e)}")
                
        return equipment

    async def fetch_pet_data(self) -> Dict[str, Any]:
        """Fetch detailed data about OSRS pets"""
        pets = {}
        wiki_data = await self._get_cached_data('wiki')
        
        if not wiki_data or 'Pets' not in wiki_data:
            return pets
            
        for pet in wiki_data['Pets']:
            page_title = pet.get('title')
            if not page_title:
                continue
                
            await self._respect_rate_limit('wiki')
            try:
                params = {
                    'action': 'parse',
                    'page': page_title,
                    'prop': 'text|templates',
                    'format': 'json'
                }
                
                async with self.session.get(
                    "https://oldschool.runescape.wiki/api.php",
                    params=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        page_data = result.get('parse', {})
                        
                        pet_info = self._parse_pet_data(page_data)
                        if pet_info:
                            pets[page_title] = pet_info
            except Exception as e:
                logger.error(f"Error fetching pet data for {page_title}: {str(e)}")
                
        return pets

    async def fetch_music_data(self) -> Dict[str, Any]:
        """Fetch data about OSRS music tracks"""
        music = {}
        wiki_data = await self._get_cached_data('wiki')
        
        if not wiki_data or 'Music' not in wiki_data:
            return music
            
        for track in wiki_data['Music']:
            page_title = track.get('title')
            if not page_title:
                continue
                
            await self._respect_rate_limit('wiki')
            try:
                params = {
                    'action': 'parse',
                    'page': page_title,
                    'prop': 'text|templates',
                    'format': 'json'
                }
                
                async with self.session.get(
                    "https://oldschool.runescape.wiki/api.php",
                    params=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        page_data = result.get('parse', {})
                        
                        music_info = self._parse_music_data(page_data)
                        if music_info:
                            music[page_title] = music_info
            except Exception as e:
                logger.error(f"Error fetching music data for {page_title}: {str(e)}")
                
        return music

    async def fetch_diary_data(self) -> Dict[str, Any]:
        """Fetch data about OSRS achievement diaries"""
        diaries = {}
        wiki_data = await self._get_cached_data('wiki')
        
        if not wiki_data or 'Diaries' not in wiki_data:
            return diaries
            
        for diary in wiki_data['Diaries']:
            page_title = diary.get('title')
            if not page_title:
                continue
                
            await self._respect_rate_limit('wiki')
            try:
                params = {
                    'action': 'parse',
                    'page': page_title,
                    'prop': 'text|templates',
                    'format': 'json'
                }
                
                async with self.session.get(
                    "https://oldschool.runescape.wiki/api.php",
                    params=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        page_data = result.get('parse', {})
                        
                        diary_info = self._parse_diary_data(page_data)
                        if diary_info:
                            diaries[page_title] = diary_info
            except Exception as e:
                logger.error(f"Error fetching diary data for {page_title}: {str(e)}")
                
        return diaries

    def _parse_minigame_data(self, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse minigame data from wiki page"""
        try:
            templates = page_data.get('templates', [])
            text = page_data.get('text', {}).get('*', '')
            
            # Find minigame infobox
            infobox = None
            for template in templates:
                if template.get('*', '').startswith('Infobox Minigame'):
                    infobox = template
                    break
                    
            if not infobox:
                return None
                
            minigame_info = {
                'name': self._extract_template_param(infobox, 'name'),
                'release_date': self._extract_template_param(infobox, 'release'),
                'location': self._extract_template_param(infobox, 'location'),
                'members': self._extract_template_param(infobox, 'members') == 'Yes',
                'combat_level': self._extract_template_param(infobox, 'combat'),
                'skills': self._parse_skill_requirements(text),
                'rewards': self._parse_rewards(text)
            }
            
            return minigame_info
        except Exception as e:
            logger.error(f"Error parsing minigame data: {str(e)}")
            return None

    def _parse_skill_data(self, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse skill data from wiki page"""
        try:
            templates = page_data.get('templates', [])
            text = page_data.get('text', {}).get('*', '')
            
            # Find skill infobox
            infobox = None
            for template in templates:
                if template.get('*', '').startswith('Infobox Skill'):
                    infobox = template
                    break
                    
            if not infobox:
                return None
                
            skill_info = {
                'name': self._extract_template_param(infobox, 'name'),
                'members': self._extract_template_param(infobox, 'members') == 'Yes',
                'experience_multiplier': float(self._extract_template_param(infobox, 'xp_multiplier') or '1.0'),
                'tools': self._parse_tools(text),
                'training_methods': self._parse_training_methods(text)
            }
            
            return skill_info
        except Exception as e:
            logger.error(f"Error parsing skill data: {str(e)}")
            return None

    def _parse_equipment_data(self, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse equipment data from wiki page"""
        try:
            templates = page_data.get('templates', [])
            text = page_data.get('text', {}).get('*', '')
            
            # Find equipment infobox
            infobox = None
            for template in templates:
                if template.get('*', '').startswith('Infobox Equipment'):
                    infobox = template
                    break
                    
            if not infobox:
                return None
                
            equipment_info = {
                'name': self._extract_template_param(infobox, 'name'),
                'slot': self._extract_template_param(infobox, 'slot'),
                'requirements': self._parse_requirements(text),
                'bonuses': self._parse_equipment_bonuses(text),
                'special_attack': self._parse_special_attack(text)
            }
            
            return equipment_info
        except Exception as e:
            logger.error(f"Error parsing equipment data: {str(e)}")
            return None

    def _parse_pet_data(self, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse pet data from wiki page"""
        try:
            templates = page_data.get('templates', [])
            text = page_data.get('text', {}).get('*', '')
            
            # Find pet infobox
            infobox = None
            for template in templates:
                if template.get('*', '').startswith('Infobox Pet'):
                    infobox = template
                    break
                    
            if not infobox:
                return None
                
            pet_info = {
                'name': self._extract_template_param(infobox, 'name'),
                'release_date': self._extract_template_param(infobox, 'release'),
                'obtain_method': self._extract_template_param(infobox, 'obtain'),
                'requirements': self._parse_requirements(text),
                'examine': self._extract_template_param(infobox, 'examine'),
                'variants': self._parse_pet_variants(text)
            }
            
            return pet_info
        except Exception as e:
            logger.error(f"Error parsing pet data: {str(e)}")
            return None

    def _parse_music_data(self, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse music track data from wiki page"""
        try:
            templates = page_data.get('templates', [])
            text = page_data.get('text', {}).get('*', '')
            
            # Find music infobox
            infobox = None
            for template in templates:
                if template.get('*', '').startswith('Infobox Music'):
                    infobox = template
                    break
                    
            if not infobox:
                return None
                
            music_info = {
                'name': self._extract_template_param(infobox, 'name'),
                'release_date': self._extract_template_param(infobox, 'release'),
                'location': self._extract_template_param(infobox, 'location'),
                'requirements': self._parse_requirements(text),
                'quest': self._extract_template_param(infobox, 'quest')
            }
            
            return music_info
        except Exception as e:
            logger.error(f"Error parsing music data: {str(e)}")
            return None

    def _parse_diary_data(self, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse achievement diary data from wiki page"""
        try:
            templates = page_data.get('templates', [])
            text = page_data.get('text', {}).get('*', '')
            
            # Find diary infobox
            infobox = None
            for template in templates:
                if template.get('*', '').startswith('Infobox Achievement Diary'):
                    infobox = template
                    break
                    
            if not infobox:
                return None
                
            diary_info = {
                'name': self._extract_template_param(infobox, 'name'),
                'area': self._extract_template_param(infobox, 'area'),
                'difficulty': self._extract_template_param(infobox, 'difficulty'),
                'tasks': self._parse_tasks(text),
                'rewards': self._parse_rewards(text)
            }
            
            return diary_info
        except Exception as e:
            logger.error(f"Error parsing diary data: {str(e)}")
            return None

    def _is_equipment(self, page_data: Dict[str, Any]) -> bool:
        """Check if page is about equipment"""
        templates = page_data.get('templates', [])
        for template in templates:
            if template.get('*', '').startswith('Infobox Equipment'):
                return True
        return False

    async def _respect_rate_limit(self, api: str):
        """Ensure we respect rate limits for different APIs"""
        now = datetime.now()
        if api in self.last_fetch:
            time_since_last = (now - self.last_fetch[api]).total_seconds()
            if time_since_last < self.rate_limits[api]:
                await asyncio.sleep(self.rate_limits[api] - time_since_last)
        self.last_fetch[api] = now

    async def _cache_data(self, name: str, data: Any):
        """Cache fetched data with timestamp"""
        cache_file = self.cache_dir / f"{name}_data.json"
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=4)

    async def _get_cached_data(self, category: str, subcategory: str = None) -> Optional[Any]:
        """Retrieve cached data if available and not expired"""
        cache_file = self.cache_dir / f"{category}_data.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    
                # Check if cache is expired (24 hours)
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                if (datetime.now() - cache_time).total_seconds() < 86400:
                    data = cache_data['data']
                    return data.get(subcategory) if subcategory else data
            except Exception as e:
                logger.error(f"Error reading cache file {cache_file}: {str(e)}")
                
        return None

if __name__ == "__main__":
    async def main():
        async with AdditionalFetchers() as fetcher:
            await fetcher.fetch_all_additional()
    
    asyncio.run(main()) 