import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from data.osrs.enhanced_data_manager import EnhancedDataManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def update_data():
    """Update OSRS data using the enhanced data manager"""
    try:
        logger.info("Initializing enhanced OSRS data manager...")
        async with EnhancedDataManager() as manager:
            await manager.initialize()
            
            # Fetch and display pet statistics
            stats = manager.get_pet_statistics()
            logger.info("\nPet Statistics:")
            logger.info(f"Total Pets: {stats['total_pets']}")
            logger.info("\nBy Source:")
            for source, count in stats['by_source'].items():
                logger.info(f"  {source}: {count}")
            logger.info("\nBy Rarity:")
            for rarity, count in stats['by_rarity'].items():
                logger.info(f"  {rarity}: {count}")
            logger.info(f"\nMetamorphic Pets: {stats['metamorphic_count']}")
            logger.info(f"Quest-Locked Pets: {stats['quest_locked_count']}")
            logger.info(f"Average Combat Level: {stats['average_combat_level']:.1f}")
            
            # Example: Calculate pet chances for a high-level player
            example_stats = {
                'attack': 99,
                'strength': 99,
                'defence': 99,
                'hitpoints': 99,
                'ranged': 99,
                'magic': 99,
                'prayer': 99
            }
            
            # Get chances for Baby Mole pet
            chances = await manager.calculate_pet_chance("Baby mole", example_stats)
            if chances:
                logger.info("\nBaby Mole Pet Chances (Max Combat):")
                for source, chance in chances.items():
                    logger.info(f"  From {source}: 1/{int(1/chance)}")
            
            # Get detailed requirements for a pet
            requirements = await manager.get_pet_requirements("Baby mole")
            if requirements:
                logger.info("\nBaby Mole Requirements:")
                if requirements.get('skills'):
                    logger.info("  Skills Required:")
                    for skill, level in requirements['skills'].items():
                        logger.info(f"    {skill}: {level}")
                if requirements.get('quests'):
                    logger.info("  Quests Required:")
                    for quest in requirements['quests']:
                        logger.info(f"    - {quest}")
                if requirements.get('items'):
                    logger.info("  Items Required:")
                    for item in requirements['items']:
                        price_str = f" (Current Price: {item['current_price']:,} gp)" if item.get('current_price') else ""
                        logger.info(f"    - {item['name']}{price_str}")
            
            logger.info("\nOSRS data update completed successfully")
            
    except Exception as e:
        logger.error(f"Failed to update OSRS data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(update_data()) 