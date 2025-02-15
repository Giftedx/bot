import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

from src.core.di_container import Container
from src.bot.media_bot import MediaStreamingBot
from src.bot.selfbot import SelfBot

def setup_logging() -> None:
    """Configure logging with file rotation and console output"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_dir / "discord.log",
        maxBytes=5_000_000,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)

async def initialize_bot(container: Container) -> Optional[MediaStreamingBot | SelfBot]:
    """Initialize the appropriate bot type based on configuration"""
    settings = container.config()
    bot_type = settings.BOT_TYPE.lower()
    
    if bot_type == "regular":
        return MediaStreamingBot(container)
    elif bot_type == "selfbot":
        return SelfBot(container)
    else:
        logging.error(f"Invalid BOT_TYPE: {bot_type}")
        return None

async def shutdown(bot: MediaStreamingBot | SelfBot) -> None:
    """Handle graceful shutdown"""
    logging.info("Initiating graceful shutdown...")
    try:
        await bot.close()
    except Exception as e:
        logging.error(f"Error during shutdown: {e}", exc_info=True)

def handle_signals(bot: MediaStreamingBot | SelfBot, loop: asyncio.AbstractEventLoop) -> None:
    """Setup signal handlers for graceful shutdown"""
    if sys.platform == 'win32':
        # On Windows, use a different approach since signal handlers aren't fully supported
        async def watcher():
            while True:
                try:
                    await asyncio.sleep(1)
                except asyncio.CancelledError:
                    await shutdown(bot)
                    break
        loop.create_task(watcher())
    else:
        # On Unix systems, use signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(shutdown(bot))
            )

async def main() -> None:
    try:
        # Setup logging
        setup_logging()
        
        # Load environment variables
        load_dotenv()
        
        # Initialize container and wire dependencies
        container = Container()
        container.init_resources()
        container.wire(modules=[__name__])
        
        # Initialize bot
        bot = await initialize_bot(container)
        if not bot:
            sys.exit(1)
            
        # Setup signal handlers
        handle_signals(bot, asyncio.get_event_loop())
        
        # Start bot with graceful shutdown handling
        try:
            await bot.start(container.config().DISCORD_TOKEN)
        except KeyboardInterrupt:
            logging.info("Received keyboard interrupt")
            await shutdown(bot)
        except Exception as e:
            logging.error(f"Bot crashed: {e}", exc_info=True)
            await shutdown(bot)
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Failed to initialize: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())