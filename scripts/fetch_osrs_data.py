import asyncio
import logging
import sys
from pathlib import Path

# Add the parent directory to the Python path
root_path = str(Path(__file__).parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from src.data.osrs.fetcher import OSRSDataFetcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def fetch_data():
    """Fetch OSRS data using the data fetcher"""
    try:
        logger.info("Initializing OSRS data fetcher...")
        async with OSRSDataFetcher() as fetcher:
            # Fetch all pets
            logger.info("Fetching pet data...")
            pets = await fetcher.fetch_all_pets()
            logger.info(f"Fetched {len(pets)} pets")
            
            # Fetch boss data for each pet source
            logger.info("Fetching boss data...")
            bosses = []
            for pet in pets:
                if pet.source == 'BOSS':
                    for source in pet.obtainable_from:
                        boss = await fetcher.fetch_boss_data(source)
                        if boss:
                            bosses.append(boss)
            logger.info(f"Fetched {len(bosses)} bosses")
            
            # Fetch skilling activity data
            logger.info("Fetching skilling activity data...")
            activities = []
            for pet in pets:
                if pet.source == 'SKILLING':
                    for source in pet.obtainable_from:
                        activity = await fetcher.fetch_skilling_activity(source)
                        if activity:
                            activities.append(activity)
            logger.info(f"Fetched {len(activities)} skilling activities")
            
            # Print summary
            logger.info("\nData Collection Summary:")
            logger.info(f"Total Pets: {len(pets)}")
            logger.info(f"Total Bosses: {len(bosses)}")
            logger.info(f"Total Skilling Activities: {len(activities)}")
            
            # Print some example data
            if pets:
                example_pet = pets[0]
                logger.info(f"\nExample Pet Data:")
                logger.info(f"Name: {example_pet.name}")
                logger.info(f"Source: {example_pet.source}")
                logger.info(f"Rarity: {example_pet.rarity}")
                logger.info(f"Obtainable From: {', '.join(example_pet.obtainable_from)}")
            
            logger.info("\nOSRS data fetching completed successfully")
            
    except Exception as e:
        logger.error(f"Failed to fetch OSRS data: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(fetch_data()) 