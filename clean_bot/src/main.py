"""Main entry point for all bot implementations."""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Bot implementations
from src.plex.bot import PlexBot
from src.core.app.bot import OSRSBot
from src.bot.plex_selfbot import PlexSelfBot
from src.core.config import Settings

def setup_logging() -> None:
    """Set up logging configuration."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "bot.log", encoding='utf-8')
        ]
    )

def main() -> None:
    """Main entry point for running bots."""
    parser = argparse.ArgumentParser(description='Run Discord bot')
    parser.add_argument('--type', choices=['plex', 'osrs', 'plex-selfbot'], default='plex',
                       help='Type of bot to run (default: plex)')
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        if args.type == 'plex':
            # Standard Plex bot with basic media commands
            bot = PlexBot()
            logger.info("Starting Plex bot...")
            bot.run(Settings.DISCORD_TOKEN)
        elif args.type == 'plex-selfbot':
            # Advanced Plex bot with streaming capabilities
            bot = PlexSelfBot(Settings.PLEX_URL, Settings.PLEX_TOKEN)
            logger.info("Starting Plex selfbot...")
            bot.run(Settings.DISCORD_TOKEN)
        elif args.type == 'osrs':
            # OSRS game bot
            bot = OSRSBot()
            logger.info("Starting OSRS bot...")
            bot.run(Settings.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()