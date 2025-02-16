#!/usr/bin/env python3
"""
Script to populate OSRS game data from various sources.
This script fetches and combines data from:
- OSRS Wiki API
- OSRSBox API
- Local data files
"""
import asyncio
import logging
from pathlib import Path
import sys

# Add src directory to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.append(str(src_path))

from lib.data.osrs_data_loader import OSRSDataLoader

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("populate_data.log")
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to populate game data."""
    try:
        logger.info("Starting data population...")
        
        # Initialize data loader
        data_dir = src_path / "data"
        data_loader = OSRSDataLoader(data_dir)
        
        # Load all data
        logger.info("Loading data from all sources...")
        await data_loader.load_all_data()
        
        # Print summary
        logger.info("\nData Population Summary:")
        logger.info(f"Monsters: {len(data_loader.monsters)}")
        logger.info(f"NPCs: {len(data_loader.npcs)}")
        logger.info(f"Shops: {len(data_loader.shops)}")
        logger.info(f"Objects: {len(data_loader.objects)}")
        logger.info(f"Items: {len(data_loader.items)}")
        logger.info(f"Locations: {len(data_loader.locations)}")
        
        logger.info("\nData population completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during data population: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nData population cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1) 