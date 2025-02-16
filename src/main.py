"""Main entry point for the Discord bot."""
import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from .bot.base_bot import BaseBot
from .core.config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log")
    ]
)
logger = logging.getLogger(__name__)

async def main() -> None:
    """Main entry point."""
    try:
        # Load environment variables
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)
        else:
            logger.warning(".env file not found, using environment variables")
            
        # Create configuration
        config = Config.from_env()
        
        # Create and run bot
        bot = BaseBot(config)
        
        # Start the bot
        logger.info("Starting bot...")
        await bot.start(config.DISCORD_TOKEN)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error("Unexpected error", exc_info=True)
        raise