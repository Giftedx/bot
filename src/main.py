"""Main entry point for the OSRS Discord Game."""
import asyncio
import logging
import sys
from pathlib import Path

from src.core.config import ConfigManager
from src.bot.base_bot import BaseBot


def setup_logging() -> None:
    """Set up logging configuration."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "game.log", encoding="utf-8"),
        ],
    )


async def main() -> None:
    """Main entry point for the game."""
    try:
        # Set up logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting Discord Bot...")

        # Load config
        config_manager = ConfigManager()

        # Initialize bot
        bot = BaseBot(config_manager=config_manager)

        # Run the bot
        discord_token = config_manager.get_secret("discord.token")
        if not discord_token:
            logger.error(
                "Discord token not found. "
                "Please set DISCORD_TOKEN environment variable "
                "or add it to config/secrets.yaml"
            )
            sys.exit(1)

        await bot.start(discord_token)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
