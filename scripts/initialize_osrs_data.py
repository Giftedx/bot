import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from data.osrs import initialize_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Initialize OSRS data"""
    try:
        logger.info("Starting OSRS data initialization...")
        await initialize_data()
        logger.info("OSRS data initialization completed successfully")
    except Exception as e:
        logger.error(f"OSRS data initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 