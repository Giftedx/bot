import asyncio
import logging
from scripts.data.enhanced_fetcher import EnhancedFetcher
from scripts.data.additional_fetchers import AdditionalFetchers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def fetch_all_data():
    """Fetch all data using both fetchers"""
    try:
        # Fetch core data
        logger.info("Starting core data fetch...")
        async with EnhancedFetcher() as core_fetcher:
            core_results = await core_fetcher.fetch_all()
        logger.info("Core data fetch completed")

        # Fetch additional data
        logger.info("Starting additional data fetch...")
        async with AdditionalFetchers() as additional_fetcher:
            additional_results = await additional_fetcher.fetch_all_additional()
        logger.info("Additional data fetch completed")

        return {
            'core': core_results,
            'additional': additional_results
        }
    except Exception as e:
        logger.error(f"Error during data fetch: {str(e)}")
        raise

def main():
    """Main entry point"""
    try:
        asyncio.run(fetch_all_data())
        logger.info("All data fetching completed successfully")
    except Exception as e:
        logger.error(f"Failed to fetch data: {str(e)}")
        raise

if __name__ == '__main__':
    main() 