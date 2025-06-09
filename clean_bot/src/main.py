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
# from src.core.config import Settings # Removed Settings import
from src.core.config import ConfigManager # Added ConfigManager import

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
            bot = PlexBot() # PlexBot now handles its own config
            logger.info("Starting Plex bot...")
            bot.run() # PlexBot's run method no longer takes a token
        elif args.type == 'plex-selfbot':
            # Advanced Plex bot with streaming capabilities
            # Assuming PlexSelfBot will be refactored similarly to PlexBot
            # to use ConfigManager internally.
            bot = PlexSelfBot() # PlexSelfBot would init its own ConfigManager
            logger.info("Starting Plex selfbot...")
            bot.run() # PlexSelfBot's run would also fetch its own token
        elif args.type == 'osrs':
            # OSRS game bot
            # This part will likely break as Settings is removed and OSRSBot is not updated in this subtask.
            # For now, we'll fetch the token directly for it, though OSRSBot itself would need refactoring.
            config_manager = ConfigManager(config_dir="config")
            osrs_token = config_manager.get('discord.token')
            if not osrs_token:
                logger.error("Discord token for OSRSBot not found in configuration.")
                sys.exit(1)
            bot = OSRSBot()
            logger.info("Starting OSRS bot...")
            bot.run(osrs_token) # Still passing token until OSRSBot is refactored
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()