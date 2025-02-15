from .models import (
    OSRSSkill, OSRSCombatStyle, OSRSPetSource, OSRSPetRarity,
    OSRSStats, OSRSCombatStats, OSRSMonster, OSRSLocation,
    OSRSPetAbility, OSRSPetVariant, OSRSPet, OSRSBoss,
    OSRSSkillingActivity, OSRSMinigame
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
    """Initialize OSRS data by fetching and populating the database"""
    try:
        populator = OSRSDataPopulator()
        await populator.populate_pets()
        logger.info("OSRS data initialization complete")
    except Exception as e:
        logger.error(f"Failed to initialize OSRS data: {e}")
        raise 