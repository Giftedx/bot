import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import os
import json

from .enhanced_data_manager import EnhancedDataManager
from scripts.data.enhanced_fetcher import EnhancedFetcher
from scripts.data.additional_fetchers import AdditionalFetchers

logger = logging.getLogger(__name__)

class OSRSDataManager:
    """
    Unified data manager that combines all OSRS data fetchers.
    Provides a single interface for accessing all OSRS data.
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize all fetchers
        self.enhanced_fetcher = EnhancedFetcher(cache_dir)
        self.additional_fetchers = AdditionalFetchers(cache_dir)
        self.enhanced_manager = EnhancedDataManager(cache_dir)
        
        # Data containers
        self.data: Dict[str, Any] = {}
        self.last_update: Optional[datetime] = None
        
        # Load data from files
        self.load_data()
        
    def load_data(self):
        """Load data from files"""
        try:
            with open(os.path.join(self.cache_dir, 'quests.json'), 'r') as f:
                self.data['quests'] = json.load(f)
        except FileNotFoundError:
            self.data['quests'] = {}
            logger.warning("quests.json not found.")

        try:
            with open(os.path.join(self.cache_dir, 'achievements.json'), 'r') as f:
                self.data['achievements'] = json.load(f)
        except FileNotFoundError:
            self.data['achievements'] = []
            logger.warning("achievements.json not found.")
        
    async def initialize(self):
        """Initialize the data manager and fetch all data"""
        try:
            logger.info("Initializing OSRS data manager...")
            
            # Initialize enhanced data manager
            await self.enhanced_manager.initialize()
            
            # Fetch all data
            await self.fetch_all_data()
            
            logger.info("OSRS data manager initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing OSRS data manager: {e}")
            raise
            
    async def fetch_all_data(self):
        """Fetch all data from all sources"""
        try:
            # Fetch data from each source
            async with self.enhanced_fetcher as fetcher:
                enhanced_data = await fetcher.fetch_all()
                
            async with self.additional_fetchers as fetcher:
                additional_data = await fetcher.fetch_all_additional()
                
            # Combine all data
            self.data = {
                'ge': enhanced_data[0],  # GE data
                'wiki': enhanced_data[1],  # Wiki data
                'items': enhanced_data[2],  # Item data
                'monsters': enhanced_data[3],  # Monster data
                'quests': enhanced_data[4],  # Quest data
                'achievements': enhanced_data[5],  # Achievement data
                'minigames': additional_data[0],  # Minigame data
                'clans': additional_data[1],  # Clan data
                'skills': additional_data[2],  # Skill data
                'equipment': additional_data[3],  # Equipment data
                'pets': additional_data[4],  # Pet data
                'music': additional_data[5],  # Music data
                'diaries': additional_data[6]  # Achievement diary data
            }
            
            self.last_update = datetime.utcnow()
            logger.info("All OSRS data fetched successfully")
        except Exception as e:
            logger.error(f"Error fetching OSRS data: {e}")
            raise
            
    async def update_data(self, category: str = None):
        """Update specific data category or all data if none specified"""
        try:
            if category:
                logger.info(f"Updating {category} data...")
                if category in ['ge', 'wiki', 'items', 'monsters', 'quests', 'achievements']:
                    async with self.enhanced_fetcher as fetcher:
                        if hasattr(fetcher, f'fetch_{category}_data'):
                            self.data[category] = await getattr(fetcher, f'fetch_{category}_data')()
                elif category in ['minigames', 'clans', 'skills', 'equipment', 'pets', 'music', 'diaries']:
                    async with self.additional_fetchers as fetcher:
                        if hasattr(fetcher, f'fetch_{category}_data'):
                            self.data[category] = await getattr(fetcher, f'fetch_{category}_data')()
            else:
                await self.fetch_all_data()
                
            self.last_update = datetime.utcnow()
            logger.info(f"{'All' if not category else category} data updated successfully")
        except Exception as e:
            logger.error(f"Error updating {'all' if not category else category} data: {e}")
            raise
            
    def get_data(self, category: str, subcategory: str = None) -> Optional[Any]:
        """Get data from a specific category and optional subcategory"""
        if category not in self.data:
            return None
            
        if subcategory:
            return self.data[category].get(subcategory)
        return self.data[category]
        
    def search_data(self, query: str, categories: List[str] = None) -> Dict[str, Any]:
        """Search for data across all or specified categories"""
        results = {}
        search_categories = categories or self.data.keys()
        
        for category in search_categories:
            if category not in self.data:
                continue
                
            category_data = self.data[category]
            if isinstance(category_data, dict):
                # Search through dictionary data
                matches = {
                    k: v for k, v in category_data.items()
                    if query.lower() in str(k).lower() or query.lower() in str(v).lower()
                }
                if matches:
                    results[category] = matches
            elif isinstance(category_data, list):
                # Search through list data
                matches = [
                    item for item in category_data
                    if query.lower() in str(item).lower()
                ]
                if matches:
                    results[category] = matches
                    
        return results
        
    def get_item_info(self, item_id: str = None, item_name: str = None) -> Optional[Dict[str, Any]]:
        """Get detailed information about an item"""
        if not item_id and not item_name:
            return None
            
        items = self.data.get('items', {})
        
        if item_id:
            return items.get(item_id)
            
        # Search by name
        for item_data in items.values():
            if item_data.get('name', '').lower() == item_name.lower():
                return item_data
                
        return None
        
    def get_monster_info(self, monster_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a monster"""
        monsters = self.data.get('monsters', {})
        return next(
            (m for m in monsters.values() if m.get('name', '').lower() == monster_name.lower()),
            None
        )
        
    def get_all_quests(self) -> Dict[str, Any]:
        """Get all quests."""
        return self.data.get('quests', {})

    def get_quest_info(self, quest_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a quest"""
        quests = self.data.get('quests', {})
        return next(
            (q for q in quests.values() if q.get('name', '').lower() == quest_name.lower()),
            None
        )
        
    def get_skill_info(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a skill"""
        skills = self.data.get('skills', {})
        return next(
            (s for s in skills.values() if s.get('name', '').lower() == skill_name.lower()),
            None
        )
        
    def get_pet_info(self, pet_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a pet"""
        pets = self.data.get('pets', {})
        return next(
            (p for p in pets.values() if p.get('name', '').lower() == pet_name.lower()),
            None
        )
        
    def get_minigame_info(self, minigame_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a minigame"""
        minigames = self.data.get('minigames', {})
        return next(
            (m for m in minigames.values() if m.get('name', '').lower() == minigame_name.lower()),
            None
        )
        
    def get_diary_info(self, diary_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an achievement diary"""
        diaries = self.data.get('diaries', {})
        return next(
            (d for d in diaries.values() if d.get('name', '').lower() == diary_name.lower()),
            None
        )
        
    def get_equipment_info(self, equipment_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about equipment"""
        equipment = self.data.get('equipment', {})
        return next(
            (e for e in equipment.values() if e.get('name', '').lower() == equipment_name.lower()),
            None
        )
        
    def get_music_info(self, track_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a music track"""
        music = self.data.get('music', {})
        return next(
            (m for m in music.values() if m.get('name', '').lower() == track_name.lower()),
            None
        )
        
    def get_clan_info(self, clan_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a clan"""
        clans = self.data.get('clans', {})
        return next(
            (c for c in clans if c.get('name', '').lower() == clan_name.lower()),
            None
        )
        
    def get_ge_price(self, item_id: str) -> Optional[int]:
        """Get current Grand Exchange price for an item"""
        ge_data = self.data.get('ge', {})
        latest_prices = ge_data.get('latest', {})
        if latest_prices and item_id in latest_prices:
            return latest_prices[item_id].get('price')
        return None
        
    def get_ge_history(self, item_id: str, timeframe: str = '1h') -> Optional[Dict[str, Any]]:
        """Get Grand Exchange price history for an item"""
        ge_data = self.data.get('ge', {})
        if timeframe not in ['5m', '1h']:
            return None
            
        history = ge_data.get(timeframe, {})
        return history.get(item_id)
        
    def get_requirements(self, content_type: str, name: str) -> Optional[Dict[str, Any]]:
        """Get requirements for any content type (quest, diary, minigame, etc.)"""
        content_map = {
            'quest': self.get_quest_info,
            'diary': self.get_diary_info,
            'minigame': self.get_minigame_info,
            'pet': self.get_pet_info,
            'equipment': self.get_equipment_info
        }
        
        if content_type not in content_map:
            return None
            
        content_info = content_map[content_type](name)
        if content_info:
            return content_info.get('requirements')
        return None
        
    def get_rewards(self, content_type: str, name: str) -> Optional[Dict[str, Any]]:
        """Get rewards for any content type (quest, diary, minigame, etc.)"""
        content_map = {
            'quest': self.get_quest_info,
            'diary': self.get_diary_info,
            'minigame': self.get_minigame_info
        }
        
        if content_type not in content_map:
            return None
            
        content_info = content_map[content_type](name)
        if content_info:
            return content_info.get('rewards')
        return None
        
    def get_drop_table(self, monster_name: str) -> Optional[List[Dict[str, Any]]]:
        """Get drop table for a monster"""
        monster_info = self.get_monster_info(monster_name)
        if monster_info:
            return monster_info.get('drops')
        return None
        
    def get_pet_source(self, pet_name: str) -> Optional[Dict[str, Any]]:
        """Get source information for a pet"""
        pet_info = self.get_pet_info(pet_name)
        if pet_info:
            return {
                'method': pet_info.get('obtain_method'),
                'requirements': pet_info.get('requirements'),
                'variants': pet_info.get('variants')
            }
        return None
        
    def get_training_methods(self, skill_name: str) -> Optional[List[Dict[str, Any]]]:
        """Get training methods for a skill"""
        skill_info = self.get_skill_info(skill_name)
        if skill_info:
            return skill_info.get('training_methods')
        return None

    def get_all_achievements(self) -> List[Dict[str, Any]]:
        """Get all achievements."""
        return self.data.get('achievements', [])

    def get_achievement(self, achievement_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific achievement by its ID."""
        achievements = self.get_all_achievements()
        return next(
            (ach for ach in achievements if ach.get('id') == achievement_id),
            None
        )

if __name__ == "__main__":
    async def main():
        manager = OSRSDataManager()
        await manager.initialize()
        
    asyncio.run(main()) 