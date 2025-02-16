"""
OSRS data management package.
"""

from .models import (
    OSRSSkill, OSRSCombatStyle, OSRSPetSource, OSRSPetRarity,
    OSRSStats, OSRSCombatStats, OSRSMonster, OSRSLocation,
    OSRSPetAbility, OSRSPetVariant, OSRSPet, OSRSBoss,
    OSRSSkillingActivity, OSRSMinigame
)
from .enhanced_data_manager import (
    OSRSEndpoints,
    EnhancedDataManager,
)
from .fetcher import OSRSDataFetcher
from .loader import OSRSDataLoader
from .populate_db import OSRSDataPopulator

__all__ = [
    'OSRSSkill',
    'OSRSCombatStyle',
    'OSRSPetSource',
    'OSRSPetRarity',
    'OSRSStats',
    'OSRSCombatStats',
    'OSRSMonster',
    'OSRSLocation',
    'OSRSPetAbility',
    'OSRSPetVariant',
    'OSRSPet',
    'OSRSBoss',
    'OSRSSkillingActivity',
    'OSRSMinigame',
    'OSRSEndpoints',
    'EnhancedDataManager',
    'OSRSDataFetcher',
    'OSRSDataLoader',
    'OSRSDataPopulator'
]

# Initialize logging
import logging
logger = logging.getLogger(__name__)

# Create a singleton instance of the data loader
_loader = None

def get_loader() -> OSRSDataLoader:
    """Get the singleton instance of OSRSDataLoader"""
    global _loader
    if _loader is None:
        _loader = OSRSDataLoader()
    return _loader

async def initialize_data():
    """Initialize OSRS data by fetching from various sources."""
    data = {
        'items': [],
        'monsters': [],
        'quests': [],
        'ge_prices': []
    }
    
    async with aiohttp.ClientSession() as session:
        # Fetch items
        async with session.get(f"{OSRS_API_BASE}/items") as resp:
            if resp.status == 200:
                items = await resp.json()
                data['items'] = items.get('_items', [])
                logger.info(f"Fetched {len(data['items'])} items")
        
        # Fetch monsters
        async with session.get(f"{OSRS_API_BASE}/monsters") as resp:
            if resp.status == 200:
                monsters = await resp.json()
                data['monsters'] = monsters.get('_items', [])
                logger.info(f"Fetched {len(data['monsters'])} monsters")
        
        # Fetch quests
        async with session.get(f"{OSRS_API_BASE}/quests") as resp:
            if resp.status == 200:
                quests = await resp.json()
                data['quests'] = quests.get('_items', [])
                logger.info(f"Fetched {len(data['quests'])} quests")
        
        # Fetch GE prices for top items
        async with session.get(f"{GE_API_BASE}/catalogue/category.json?category=1") as resp:
            if resp.status == 200:
                ge_data = await resp.json()
                data['ge_prices'] = ge_data.get('items', [])
                logger.info(f"Fetched {len(data['ge_prices'])} GE prices")
    
    # Save data to files
    data_dir = os.path.join('data', 'osrs')
    os.makedirs(data_dir, exist_ok=True)
    
    for key, items in data.items():
        file_path = os.path.join(data_dir, f"{key}.json")
        with open(file_path, 'w') as f:
            json.dump(items, f, indent=2)
            logger.info(f"Saved {len(items)} {key} to {file_path}")
    
    return data 