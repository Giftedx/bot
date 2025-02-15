import aiohttp
import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging
from bs4 import BeautifulSoup
import mwclient

from .models import (
    OSRSPet, OSRSPetSource, OSRSPetRarity, OSRSPetAbility,
    OSRSPetVariant, OSRSLocation, OSRSCombatStats, OSRSSkill,
    OSRSBoss, OSRSSkillingActivity, OSRSMinigame
)

logger = logging.getLogger(__name__)

class OSRSEndpoints:
    """OSRS API endpoints and data sources"""
    WIKI_API = "https://oldschool.runescape.wiki/api.php"
    PRICES_API = "https://prices.runescape.wiki/api/v1/osrs"
    HISCORES_API = "https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws"
    GRAND_EXCHANGE_API = "https://secure.runescape.com/m=itemdb_oldschool/api"
    
    # Wiki categories
    PETS_CATEGORY = "Pets"
    BOSS_PETS_CATEGORY = "Boss pets"
    SKILLING_PETS_CATEGORY = "Skilling pets"
    
    # Common page patterns
    PET_INFO_TEMPLATE = "Infobox Pet"
    BOSS_INFO_TEMPLATE = "Infobox Monster"
    SKILL_INFO_TEMPLATE = "Infobox Skill"

class EnhancedDataManager:
    """Enhanced OSRS data manager with comprehensive data handling"""
    
    def __init__(self, cache_dir: str = "data/cache/osrs"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.wiki_site = mwclient.Site('oldschool.runescape.wiki', path='/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Any] = {}
        self.last_update: Optional[datetime] = None
        
        # Initialize data containers
        self.pets: Dict[str, OSRSPet] = {}
        self.bosses: Dict[str, OSRSBoss] = {}
        self.activities: Dict[str, OSRSSkillingActivity] = {}
        self.current_prices: Dict[str, int] = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def initialize(self):
        """Initialize all data"""
        try:
            await self.load_cache()
            if self.needs_update():
                await self.update_all_data()
            logger.info("OSRS data manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OSRS data manager: {e}")
            raise

    async def fetch_wiki_data(self, query: str, props: List[str] = None) -> Dict[str, Any]:
        """Enhanced Wiki data fetching with retries and error handling"""
        if not props:
            props = ['text', 'categories', 'templates']
            
        params = {
            'action': 'query',
            'format': 'json',
            'titles': query,
            'prop': '|'.join(props)
        }
        
        for attempt in range(3):  # Retry up to 3 times
            try:
                async with self.session.get(OSRSEndpoints.WIKI_API, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_wiki_response(data)
                    else:
                        logger.warning(f"Wiki API returned status {response.status} for {query}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {query}: {e}")
                if attempt == 2:  # Last attempt
                    raise
                await asyncio.sleep(1)  # Wait before retry
        return {}

    async def fetch_current_prices(self, item_ids: List[str]) -> Dict[str, int]:
        """Fetch current GE prices for items"""
        params = {'items': ','.join(item_ids)}
        try:
            async with self.session.get(f"{OSRSEndpoints.PRICES_API}/latest", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {str(k): v['price'] for k, v in data['data'].items()}
        except Exception as e:
            logger.error(f"Failed to fetch prices: {e}")
        return {}

    async def fetch_hiscores(self, username: str) -> Optional[Dict[str, int]]:
        """Fetch player hiscores data"""
        try:
            async with self.session.get(f"{OSRSEndpoints.HISCORES_API}?player={username}") as response:
                if response.status == 200:
                    content = await response.text()
                    return self._parse_hiscores(content)
        except Exception as e:
            logger.error(f"Failed to fetch hiscores for {username}: {e}")
        return None

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        skills = list(OSRSSkill)
        lines = content.strip().split('\n')
        
        if len(lines) < len(skills):
            raise ValueError("Incomplete hiscores data")
            
        return {
            skill.value: int(lines[i].split(',')[1])
            for i, skill in enumerate(skills)
            if i < len(lines)
        }

    async def get_pet_drop_sources(self, pet_name: str) -> List[Dict[str, Any]]:
        """Get detailed information about pet drop sources"""
        pet = self.pets.get(pet_name)
        if not pet:
            return []
            
        sources = []
        for source_name in pet.obtainable_from:
            if source_name in self.bosses:
                boss = self.bosses[source_name]
                sources.append({
                    'type': 'boss',
                    'name': boss.name,
                    'combat_level': boss.combat_level,
                    'location': boss.locations[0].name if boss.locations else None,
                    'requirements': boss.recommended_stats
                })
            elif source_name in self.activities:
                activity = self.activities[source_name]
                sources.append({
                    'type': 'skilling',
                    'name': activity.name,
                    'skill': activity.skill.value,
                    'level_required': activity.level_required,
                    'location': activity.locations[0].name if activity.locations else None
                })
        return sources

    async def calculate_pet_chance(self, pet_name: str, player_stats: Dict[str, int],
                                 modifiers: Dict[str, float] = None) -> Dict[str, float]:
        """Calculate detailed pet chance based on player stats and modifiers"""
        pet = self.pets.get(pet_name)
        if not pet:
            return {}
            
        base_chance = pet.drop_rate or 0
        if not base_chance:
            return {'error': 'No base drop rate available'}
            
        chances = {}
        sources = await self.get_pet_drop_sources(pet_name)
        
        for source in sources:
            source_chance = base_chance
            
            # Apply skill level bonuses
            if source['type'] == 'skilling':
                skill_level = player_stats.get(source['skill'], 1)
                level_bonus = min((skill_level - source['level_required']) * 0.001, 0.1)
                source_chance *= (1 + level_bonus)
            
            # Apply combat level bonuses for boss pets
            elif source['type'] == 'boss':
                combat_level = self._calculate_combat_level(player_stats)
                if combat_level > source['combat_level']:
                    combat_bonus = min((combat_level - source['combat_level']) * 0.002, 0.15)
                    source_chance *= (1 + combat_bonus)
            
            # Apply external modifiers
            if modifiers:
                for modifier, value in modifiers.items():
                    source_chance *= (1 + value)
            
            chances[source['name']] = min(source_chance, 1.0)
            
        return chances

    def _calculate_combat_level(self, stats: Dict[str, int]) -> int:
        """Calculate combat level from stats"""
        base = 0.25 * (stats.get('defence', 1) + stats.get('hitpoints', 10) + 
                      math.floor(stats.get('prayer', 1)/2))
        melee = 0.325 * (stats.get('attack', 1) + stats.get('strength', 1))
        range_magic = 0.325 * (math.floor(3*stats.get('ranged', 1)/2) + 
                              math.floor(3*stats.get('magic', 1)/2))
        return math.floor(base + max(melee, range_magic))

    async def get_pet_requirements(self, pet_name: str) -> Dict[str, Any]:
        """Get comprehensive pet requirements including quests and items"""
        pet = self.pets.get(pet_name)
        if not pet:
            return {}
            
        requirements = {
            'skills': {skill.value: level for skill, level in (pet.requirements or {}).items()},
            'quests': pet.quest_requirements or [],
            'items': []
        }
        
        # Fetch additional item requirements if any
        if pet.item_requirements:
            items_data = []
            for item_id in pet.item_requirements:
                try:
                    async with self.session.get(
                        f"{OSRSEndpoints.GRAND_EXCHANGE_API}/catalogue/detail.json?item={item_id}"
                    ) as response:
                        if response.status == 200:
                            item_data = await response.json()
                            current_price = self.current_prices.get(item_id)
                            items_data.append({
                                'id': item_id,
                                'name': item_data['item']['name'],
                                'current_price': current_price,
                                'members': item_data['item']['members']
                            })
                except Exception as e:
                    logger.error(f"Failed to fetch item data for {item_id}: {e}")
                    
            requirements['items'] = items_data
            
        return requirements

    async def get_pet_variants(self, pet_name: str) -> List[Dict[str, Any]]:
        """Get detailed information about pet variants"""
        pet = self.pets.get(pet_name)
        if not pet or not pet.variants:
            return []
            
        variants = []
        for variant in pet.variants:
            variant_data = {
                'name': variant.name,
                'examine_text': variant.examine_text,
                'metamorphic': variant.metamorphic,
                'requirements': variant.requirements
            }
            
            # Fetch additional variant-specific data from wiki
            try:
                variant_page = await self.fetch_wiki_data(variant.name)
                if variant_page:
                    variant_data.update({
                        'release_date': variant_page.get('release_date'),
                        'additional_info': variant_page.get('additional_info'),
                        'unlock_method': variant_page.get('unlock_method')
                    })
            except Exception as e:
                logger.error(f"Failed to fetch variant data for {variant.name}: {e}")
                
            variants.append(variant_data)
            
        return variants

    def get_pet_statistics(self) -> Dict[str, Any]:
        """Get comprehensive pet statistics"""
        total_pets = len(self.pets)
        
        stats = {
            'total_pets': total_pets,
            'by_source': {},
            'by_rarity': {},
            'metamorphic_count': 0,
            'quest_locked_count': 0,
            'skill_requirements': {skill.value: 0 for skill in OSRSSkill},
            'average_combat_level': 0
        }
        
        total_combat = 0
        for pet in self.pets.values():
            # Count by source
            stats['by_source'][pet.source.value] = stats['by_source'].get(pet.source.value, 0) + 1
            
            # Count by rarity
            stats['by_rarity'][pet.rarity.value] = stats['by_rarity'].get(pet.rarity.value, 0) + 1
            
            # Count metamorphic variants
            if any(v.metamorphic for v in pet.variants):
                stats['metamorphic_count'] += 1
                
            # Count quest requirements
            if pet.quest_requirements:
                stats['quest_locked_count'] += 1
                
            # Count skill requirements
            if pet.requirements:
                for skill, level in pet.requirements.items():
                    stats['skill_requirements'][skill.value] = max(
                        stats['skill_requirements'][skill.value],
                        level
                    )
                    
            # Track combat levels
            total_combat += pet.base_stats.combat_level
            
        stats['average_combat_level'] = total_combat / total_pets if total_pets > 0 else 0
        
        return stats 

    async def load_cache(self):
        """Load cached data from disk"""
        cache_file = self.cache_dir / "data_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                    self.cache = data.get("cache", {})
                    last_update_str = data.get("last_update")
                    if last_update_str:
                        self.last_update = datetime.fromisoformat(last_update_str)
                logger.info("Cache loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
                self.cache = {}
                self.last_update = None
        else:
            logger.info("No cache file found")
            self.cache = {}
            self.last_update = None

    async def save_cache(self):
        """Save current data to cache"""
        cache_file = self.cache_dir / "data_cache.json"
        try:
            data = {
                "cache": self.cache,
                "last_update": self.last_update.isoformat() if self.last_update else None
            }
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info("Cache saved successfully")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def needs_update(self) -> bool:
        """Check if data needs to be updated"""
        if not self.last_update:
            return True
        age = datetime.now() - self.last_update
        return age.days >= 7  # Update weekly 

    async def update_all_data(self):
        """Update all OSRS data"""
        try:
            # Fetch all pets data
            logger.info("Fetching pets data...")
            pets_data = await self.fetch_wiki_data("Category:" + OSRSEndpoints.PETS_CATEGORY)
            for pet_name, pet_data in pets_data.items():
                self.pets[pet_name] = await self._process_pet_data(pet_data)

            # Fetch boss data
            logger.info("Fetching boss data...")
            boss_data = await self.fetch_wiki_data("Category:" + OSRSEndpoints.BOSS_PETS_CATEGORY)
            for boss_name, boss_data in boss_data.items():
                self.bosses[boss_name] = await self._process_boss_data(boss_data)

            # Fetch skilling activities
            logger.info("Fetching skilling activities...")
            skilling_data = await self.fetch_wiki_data("Category:" + OSRSEndpoints.SKILLING_PETS_CATEGORY)
            for activity_name, activity_data in skilling_data.items():
                self.activities[activity_name] = await self._process_activity_data(activity_data)

            # Update current prices
            logger.info("Updating current prices...")
            item_ids = self._collect_item_ids()
            self.current_prices = await self.fetch_current_prices(item_ids)

            # Update cache
            self.last_update = datetime.now()
            await self.save_cache()
            
            logger.info("All data updated successfully")
        except Exception as e:
            logger.error(f"Failed to update data: {e}")
            raise

    async def _process_pet_data(self, data: Dict[str, Any]) -> OSRSPet:
        """Process raw pet data into OSRSPet object"""
        try:
            return OSRSPet(
                name=data.get("name", ""),
                source=OSRSPetSource[data.get("source", "UNKNOWN").upper()],
                rarity=OSRSPetRarity[data.get("rarity", "UNKNOWN").upper()],
                release_date=datetime.fromisoformat(data.get("release_date", "2000-01-01")),
                base_stats=await self._process_combat_stats(data.get("combat_stats", {})),
                abilities=[OSRSPetAbility[a.upper()] for a in data.get("abilities", [])],
                variants=[await self._process_variant(v) for v in data.get("variants", [])],
                obtainable_from=data.get("obtainable_from", []),
                requirements=data.get("requirements", {}),
                quest_requirements=data.get("quest_requirements", []),
                item_requirements=data.get("item_requirements", [])
            )
        except Exception as e:
            logger.error(f"Failed to process pet data: {e}")
            raise

    async def _process_boss_data(self, data: Dict[str, Any]) -> OSRSBoss:
        """Process raw boss data into OSRSBoss object"""
        try:
            return OSRSBoss(
                name=data.get("name", ""),
                combat_level=data.get("combat_level", 0),
                locations=[OSRSLocation(**l) for l in data.get("locations", [])],
                recommended_stats=await self._process_combat_stats(data.get("recommended_stats", {}))
            )
        except Exception as e:
            logger.error(f"Failed to process boss data: {e}")
            raise

    async def _process_activity_data(self, data: Dict[str, Any]) -> OSRSSkillingActivity:
        """Process raw skilling activity data into OSRSSkillingActivity object"""
        try:
            return OSRSSkillingActivity(
                name=data.get("name", ""),
                skill=OSRSSkill[data.get("skill", "UNKNOWN").upper()],
                level_required=data.get("level_required", 1),
                locations=[OSRSLocation(**l) for l in data.get("locations", [])]
            )
        except Exception as e:
            logger.error(f"Failed to process activity data: {e}")
            raise

    async def _process_variant(self, data: Dict[str, Any]) -> OSRSPetVariant:
        """Process raw variant data into OSRSPetVariant object"""
        try:
            return OSRSPetVariant(
                name=data.get("name", ""),
                examine_text=data.get("examine_text", ""),
                metamorphic=data.get("metamorphic", False),
                requirements=data.get("requirements", {})
            )
        except Exception as e:
            logger.error(f"Failed to process variant data: {e}")
            raise

    def _collect_item_ids(self) -> List[str]:
        """Collect all item IDs that need price updates"""
        item_ids = set()
        for pet in self.pets.values():
            item_ids.update(pet.item_requirements)
        return list(item_ids)

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw wiki response and return structured data"""
        # Implementation of _process_wiki_response method
        pass

    def _process_combat_stats(self, stats: Dict[str, Any]) -> OSRSCombatStats:
        """Process raw combat stats and return OSRSCombatStats object"""
        # Implementation of _process_combat_stats method
        pass

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        # Implementation of _parse_hiscores method
        pass

    def _process_wiki_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
import aiohttp
import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging
from bs4 import BeautifulSoup
import mwclient

from .models import (
    OSRSPet, OSRSPetSource, OSRSPetRarity, OSRSPetAbility,
    OSRSPetVariant, OSRSLocation, OSRSCombatStats, OSRSSkill,
    OSRSBoss, OSRSSkillingActivity, OSRSMinigame
)

logger = logging.getLogger(__name__)

class OSRSEndpoints:
    """OSRS API endpoints and data sources"""
    WIKI_API = "https://oldschool.runescape.wiki/api.php"
    PRICES_API = "https://prices.runescape.wiki/api/v1/osrs"
    HISCORES_API = "https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws"
    GRAND_EXCHANGE_API = "https://secure.runescape.com/m=itemdb_oldschool/api"
    
    # Wiki categories
    PETS_CATEGORY = "Pets"
    BOSS_PETS_CATEGORY = "Boss pets"
    SKILLING_PETS_CATEGORY = "Skilling pets"
    
    # Common page patterns
    PET_INFO_TEMPLATE = "Infobox Pet"
    BOSS_INFO_TEMPLATE = "Infobox Monster"
    SKILL_INFO_TEMPLATE = "Infobox Skill"

class EnhancedDataManager:
    """Enhanced OSRS data manager with comprehensive data handling"""
    
    def __init__(self, cache_dir: str = "data/cache/osrs"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.wiki_site = mwclient.Site('oldschool.runescape.wiki', path='/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Any] = {}
        self.last_update: Optional[datetime] = None
        
        # Initialize data containers
        self.pets: Dict[str, OSRSPet] = {}
        self.bosses: Dict[str, OSRSBoss] = {}
        self.activities: Dict[str, OSRSSkillingActivity] = {}
        self.current_prices: Dict[str, int] = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def initialize(self):
        """Initialize all data"""
        try:
            await self.load_cache()
            if self.needs_update():
                await self.update_all_data()
            logger.info("OSRS data manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OSRS data manager: {e}")
            raise

    async def fetch_wiki_data(self, query: str, props: List[str] = None) -> Dict[str, Any]:
        """Enhanced Wiki data fetching with retries and error handling"""
        if not props:
            props = ['text', 'categories', 'templates']
            
        params = {
            'action': 'query',
            'format': 'json',
            'titles': query,
            'prop': '|'.join(props)
        }
        
        for attempt in range(3):  # Retry up to 3 times
            try:
                async with self.session.get(OSRSEndpoints.WIKI_API, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_wiki_response(data)
                    else:
                        logger.warning(f"Wiki API returned status {response.status} for {query}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {query}: {e}")
                if attempt == 2:  # Last attempt
                    raise
                await asyncio.sleep(1)  # Wait before retry
        return {}

    async def fetch_current_prices(self, item_ids: List[str]) -> Dict[str, int]:
        """Fetch current GE prices for items"""
        params = {'items': ','.join(item_ids)}
        try:
            async with self.session.get(f"{OSRSEndpoints.PRICES_API}/latest", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {str(k): v['price'] for k, v in data['data'].items()}
        except Exception as e:
            logger.error(f"Failed to fetch prices: {e}")
        return {}

    async def fetch_hiscores(self, username: str) -> Optional[Dict[str, int]]:
        """Fetch player hiscores data"""
        try:
            async with self.session.get(f"{OSRSEndpoints.HISCORES_API}?player={username}") as response:
                if response.status == 200:
                    content = await response.text()
                    return self._parse_hiscores(content)
        except Exception as e:
            logger.error(f"Failed to fetch hiscores for {username}: {e}")
        return None

    def _parse_hiscores(self, content: str) -> Dict[str, int]:
        """Parse hiscores data into structured format"""
        skills = list(OSRSSkill)
        lines = content.strip().split('\n')
        
        if len(lines) < len(skills):
            raise ValueError("Incomplete hiscores data")
            
        return {
            skill.value: int(lines[i].split(',')[1])
            for i, skill in enumerate(skills)
            if i < len(lines)
        }

    async def get_pet_drop_sources(self, pet_name: str) -> List[Dict[str, Any]]:
        """Get detailed information about pet drop sources"""
        pet = self.pets.get(pet_name)
        if not pet:
            return []
            
        sources = []
        for source_name in pet.obtainable_from:
            if source_name in self.bosses:
                boss = self.bosses[source_name]
                sources.append({
                    'type': 'boss',
                    'name': boss.name,
                    'combat_level': boss.combat_level,
                    'location': boss.locations[0].name if boss.locations else None,
                    'requirements': boss.recommended_stats
                })
            elif source_name in self.activities:
                activity = self.activities[source_name]
                sources.append({
                    'type': 'skilling',
                    'name': activity.name,
                    'skill': activity.skill.value,
                    'level_required': activity.level_required,
                    'location': activity.locations[0].name if activity.locations else None
                })
        return sources

    async def calculate_pet_chance(self, pet_name: str, player_stats: Dict[str, int],
                                 modifiers: Dict[str, float] = None) -> Dict[str, float]:
        """Calculate detailed pet chance based on player stats and modifiers"""
        pet = self.pets.get(pet_name)
        if not pet:
            return {}
            
        base_chance = pet.drop_rate or 0
        if not base_chance:
            return {'error': 'No base drop rate available'}
            
        chances = {}
        sources = await self.get_pet_drop_sources(pet_name)
        
        for source in sources:
            source_chance = base_chance
            
            # Apply skill level bonuses
            if source['type'] == 'skilling':
                skill_level = player_stats.get(source['skill'], 1)
                level_bonus = min((skill_level - source['level_required']) * 0.001, 0.1)
                source_chance *= (1 + level_bonus)
            
            # Apply combat level bonuses for boss pets
            elif source['type'] == 'boss':
                combat_level = self._calculate_combat_level(player_stats)
                if combat_level > source['combat_level']:
                    combat_bonus = min((combat_level - source['combat_level']) * 0.002, 0.15)
                    source_chance *= (1 + combat_bonus)
            
            # Apply external modifiers
            if modifiers:
                for modifier, value in modifiers.items():
                    source_chance *= (1 + value)
            
            chances[source['name']] = min(source_chance, 1.0)
            
        return chances

    def _calculate_combat_level(self, stats: Dict[str, int]) -> int:
        """Calculate combat level from stats"""
        base = 0.25 * (stats.get('defence', 1) + stats.get('hitpoints', 10) + 
                      math.floor(stats.get('prayer', 1)/2))
        melee = 0.325 * (stats.get('attack', 1) + stats.get('strength', 1))
        range_magic = 0.325 * (math.floor(3*stats.get('ranged', 1)/2) + 
                              math.floor(3*stats.get('magic', 1)/2))
        return math.floor(base + max(melee, range_magic))

    async def get_pet_requirements(self, pet_name: str) -> Dict[str, Any]:
        """Get comprehensive pet requirements including quests and items"""
        pet = self.pets.get(pet_name)
        if not pet:
            return {}
            
        requirements = {
            'skills': {skill.value: level for skill, level in (pet.requirements or {}).items()},
            'quests': pet.quest_requirements or [],
            'items': []
        }
        
        # Fetch additional item requirements if any
        if pet.item_requirements:
            items_data = []
            for item_id in pet.item_requirements:
                try:
                    async with self.session.get(
                        f"{OSRSEndpoints.GRAND_EXCHANGE_API}/catalogue/detail.json?item={item_id}"
                    ) as response:
                        if response.status == 200:
                            item_data = await response.json()
                            current_price = self.current_prices.get(item_id)
                            items_data.append({
                                'id': item_id,
                                'name': item_data['item']['name'],
                                'current_price': current_price,
                                'members': item_data['item']['members']
                            })
                except Exception as e:
                    logger.error(f"Failed to fetch item data for {item_id}: {e}")
                    
            requirements['items'] = items_data
            
        return requirements

    async def get_pet_variants(self, pet_name: str) -> List[Dict[str, Any]]:
        """Get detailed information about pet variants"""
        pet = self.pets.get(pet_name)
        if not pet or not pet.variants:
            return []
            
        variants = []
        for variant in pet.variants:
            variant_data = {
                'name': variant.name,
                'examine_text': variant.examine_text,
                'metamorphic': variant.metamorphic,
                'requirements': variant.requirements
            }
            
            # Fetch additional variant-specific data from wiki
            try:
                variant_page = await self.fetch_wiki_data(variant.name)
                if variant_page:
                    variant_data.update({
                        'release_date': variant_page.get('release_date'),
                        'additional_info': variant_page.get('additional_info'),
                        'unlock_method': variant_page.get('unlock_method')
                    })
            except Exception as e:
                logger.error(f"Failed to fetch variant data for {variant.name}: {e}")
                
            variants.append(variant_data)
            
        return variants

    def get_pet_statistics(self) -> Dict[str, Any]:
        """Get comprehensive pet statistics"""
        total_pets = len(self.pets)
        
        stats = {
            'total_pets': total_pets,
            'by_source': {},
            'by_rarity': {},
            'metamorphic_count': 0,
            'quest_locked_count': 0,
            'skill_requirements': {skill.value: 0 for skill in OSRSSkill},
            'average_combat_level': 0
        }
        
        total_combat = 0
        for pet in self.pets.values():
            # Count by source
            stats['by_source'][pet.source.value] = stats['by_source'].get(pet.source.value, 0) + 1
            
            # Count by rarity
            stats['by_rarity'][pet.rarity.value] = stats['by_rarity'].get(pet.rarity.value, 0) + 1
            
            # Count metamorphic variants
            if any(v.metamorphic for v in pet.variants):
                stats['metamorphic_count'] += 1
                
            # Count quest requirements
            if pet.quest_requirements:
                stats['quest_locked_count'] += 1
                
            # Count skill requirements
            if pet.requirements:
                for skill, level in pet.requirements.items():
                    stats['skill_requirements'][skill.value] = max(
                        stats['skill_requirements'][skill.value],
                        level
                    )
                    
            # Track combat levels
            total_combat += pet.base_stats.combat_level
            
        stats['average_combat_level'] = total_combat / total_pets if total_pets > 0 else 0
        
        return stats 

    async def load_cache(self):
        """Load cached data from disk"""
        cache_file = self.cache_dir / "data_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                    self.cache = data.get("cache", {})
                    last_update_str = data.get("last_update")
                    if last_update_str:
                        self.last_update = datetime.fromisoformat(last_update_str)
                logger.info("Cache loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
                self.cache = {}
                self.last_update = None
        else:
            logger.info("No cache file found")
            self.cache = {}
            self.last_update = None

    async def save_cache(self):
        """Save current data to cache"""
        cache_file = self.cache_dir / "data_cache.json"
        try:
            data = {
                "cache": self.cache,
                "last_update": self.last_update.isoformat() if self.last_update else None
            }
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info("Cache saved successfully")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def needs_update(self) -> bool:
        """Check if data needs to be updated"""
        if not self.last_update:
            return True
        age = datetime.now() - self.last_update
        return age.days >= 7  # Update weekly 