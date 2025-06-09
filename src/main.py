"""Main entry point for the OSRS Discord Game."""
import asyncio
import logging
import sys
from pathlib import Path

# from src.core.config import Config # Removed Config import
from src.core.config import ConfigManager # Added ConfigManager import
from src.bot.osrs_bot import OSRSBot

def setup_logging() -> None:
    """Set up logging configuration."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                log_dir / "game.log",
                encoding='utf-8'
            )
        ]
    )

async def main() -> None:
    """Main entry point for the game."""
    try:
        # Set up logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting OSRS Discord Game...")
        
        # ConfigManager is now instantiated within OSRSBot directly
        # # Load config
        # config = Config() # Old config loading removed
        
        # Initialize bot
        bot = OSRSBot() # OSRSBot now instantiates its own ConfigManager
        
        # Start display update task
        asyncio.create_task(bot.start_display_updates())
        
        # Run the bot
        await bot.start() # OSRSBot's start method now fetches its own token
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())