"""Main entry point for the Discord bot."""
import logging
import sys
from pathlib import Path

# from src.bot.core.bot import run_bot # Removed old import
from src.core.bot import PersonalBot  # Added PersonalBot import


def setup_logging() -> None:
    """Set up logging configuration."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "bot.log", encoding="utf-8"),
        ],
    )


def main() -> None:
    """Main entry point for the bot."""
    try:
        # Set up logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting bot...")

        # Run the bot
        # run_bot() # Old way to run bot
        bot = PersonalBot()
        bot.run()  # PersonalBot.run no longer takes a token argument
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
