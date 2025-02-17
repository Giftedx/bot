import asyncio
import logging
from dotenv import load_dotenv
import os

# Import all fetchers
from scripts.data.fetch_all import main as fetch_core_data
from scripts.data.fetch_pokemon_data import PokemonDataFetcher
from scripts.data.fetch_plex_data import PlexDataFetcher
from scripts.data.fetch_discord_data import DiscordDataFetcher
from scripts.data.fetch_wiki_equipment import WikiEquipmentFetcher
from scripts.data.fetch_wiki_items import WikiItemFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def fetch_everything():
    """Fetch all possible data from all sources"""
    try:
        # Load environment variables
        load_dotenv()
        
        # 1. Fetch core OSRS data
        logger.info("Fetching core OSRS data...")
        await fetch_core_data()
        
        # 2. Fetch Pokemon data
        logger.info("Fetching Pokemon data...")
        pokemon_fetcher = PokemonDataFetcher()
        await pokemon_fetcher.fetch_all_data()
        
        # 3. Fetch Plex data if token available
        plex_token = os.getenv('PLEX_TOKEN')
        if plex_token:
            logger.info("Fetching Plex data...")
            plex_fetcher = PlexDataFetcher(plex_token)
            await plex_fetcher.fetch_all_data()
        else:
            logger.warning("PLEX_TOKEN not found, skipping Plex data fetch")
        
        # 4. Fetch Discord data if token available
        discord_token = os.getenv('DISCORD_TOKEN')
        if discord_token:
            logger.info("Fetching Discord data...")
            discord_fetcher = DiscordDataFetcher(discord_token)
            await discord_fetcher.fetch_all_data()
        else:
            logger.warning("DISCORD_TOKEN not found, skipping Discord data fetch")
        
        # 5. Fetch Wiki equipment data
        logger.info("Fetching Wiki equipment data...")
        equipment_fetcher = WikiEquipmentFetcher()
        await equipment_fetcher.fetch_all_equipment()
        
        # 6. Fetch Wiki items data
        logger.info("Fetching Wiki items data...")
        item_fetcher = WikiItemFetcher()
        await item_fetcher.fetch_all_items()
        
        logger.info("All data fetching completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during data fetch: {str(e)}")
        raise

def main():
    """Main entry point"""
    try:
        asyncio.run(fetch_everything())
    except Exception as e:
        logger.error(f"Failed to fetch data: {str(e)}")
        raise

if __name__ == '__main__':
    main() 