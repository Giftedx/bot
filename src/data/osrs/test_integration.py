import asyncio
import logging

from .fetcher import OSRSDataFetcher
from .loader import OSRSDataLoader
from .models import OSRSPetSource, OSRSPetRarity, OSRSSkill

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_data_fetching():
    """Test fetching data from OSRS Wiki"""
    logger.info("Testing data fetching...")
    async with OSRSDataFetcher() as fetcher:
        # Test fetching a specific pet
        pet = await fetcher.fetch_pet_data("Baby mole")
        if pet:
            logger.info("Successfully fetched Baby mole pet data:")
            logger.info(f"  Name: {pet.name}")
            logger.info(f"  Source: {pet.source}")
            logger.info(f"  Rarity: {pet.rarity}")
            logger.info(f"  Drop rate: {pet.drop_rate}")
        else:
            logger.error("Failed to fetch Baby mole pet data")

        # Test fetching all pets
        pets = await fetcher.fetch_all_pets()
        if pets:
            logger.info(f"Successfully fetched {len(pets)} pets")
            # Print some statistics
            source_counts = {}
            rarity_counts = {}
            for pet in pets:
                source_counts[pet.source] = source_counts.get(pet.source, 0) + 1
                rarity_counts[pet.rarity] = rarity_counts.get(pet.rarity, 0) + 1

            logger.info("\nPet sources distribution:")
            for source, count in source_counts.items():
                logger.info(f"  {source.value}: {count} pets")

            logger.info("\nPet rarity distribution:")
            for rarity, count in rarity_counts.items():
                logger.info(f"  {rarity.value}: {count} pets")
        else:
            logger.error("Failed to fetch all pets")


def test_data_loading():
    """Test loading data from JSON files"""
    logger.info("\nTesting data loading...")
    loader = OSRSDataLoader()

    # Test loading all pets
    pets = loader.load_pets(force_reload=True)
    if pets:
        logger.info(f"Successfully loaded {len(pets)} pets from JSON")

        # Test getting pet by name
        baby_mole = loader.get_pet_by_name("Baby mole")
        if baby_mole:
            logger.info("\nFound Baby mole:")
            logger.info(f"  Release date: {baby_mole.release_date}")
            logger.info(f"  Drop rate: {baby_mole.drop_rate}")
            logger.info(f"  Combat level: {baby_mole.base_stats.combat_level}")

        # Test getting pets by source
        boss_pets = loader.get_pets_by_source(OSRSPetSource.BOSS)
        logger.info(f"\nFound {len(boss_pets)} boss pets")

        # Test getting pets by rarity
        rare_pets = loader.get_pets_by_rarity(OSRSPetRarity.RARE)
        logger.info(f"Found {len(rare_pets)} rare pets")

        # Test getting pets by skill requirement
        slayer_pets = loader.get_pets_by_skill_requirement(OSRSSkill.SLAYER, 50)
        logger.info(f"Found {len(slayer_pets)} pets requiring 50+ Slayer")

        # Test getting metamorphic pets
        metamorphic_pets = loader.get_metamorphic_pets()
        logger.info(f"Found {len(metamorphic_pets)} pets with metamorphic variants")

        # Print some example pet details
        if pets:
            example_pet = pets[0]
            logger.info("\nExample pet details:")
            logger.info(f"  Name: {example_pet.name}")
            logger.info(f"  Source: {example_pet.source.value}")
            logger.info(f"  Rarity: {example_pet.rarity.value}")
            logger.info("  Combat stats:")
            logger.info(f"    Attack: {example_pet.base_stats.attack_level}")
            logger.info(f"    Strength: {example_pet.base_stats.strength_level}")
            logger.info(f"    Defence: {example_pet.base_stats.defence_level}")
            if example_pet.variants:
                logger.info("  Variants:")
                for variant in example_pet.variants:
                    logger.info(f"    - {variant.name}")
            if example_pet.requirements:
                logger.info("  Skill requirements:")
                for skill, level in example_pet.requirements.items():
                    logger.info(f"    {skill.value}: {level}")
    else:
        logger.error("Failed to load pets from JSON")


async def main():
    """Run all tests"""
    logger.info("Starting OSRS data integration tests...")

    # Test data fetching
    await test_data_fetching()

    # Test data loading
    test_data_loading()

    logger.info("Completed OSRS data integration tests")


if __name__ == "__main__":
    asyncio.run(main())
