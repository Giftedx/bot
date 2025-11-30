"""Main entry point for the OSRS Discord Game application."""
import asyncio
import logging
import sys
from pathlib import Path
from typing import NoReturn

from src.core.config import ConfigManager
from src.bot.base_bot import BaseBot

# Health server
from aiohttp import web


def setup_logging() -> None:
    """Initialize logging configuration for the application.

    Sets up both stream (console) and file handlers. Logs are written to
    the 'logs/game.log' file.
    """
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


async def _health_handler(_: web.Request) -> web.Response:
    """Handle health check requests.

    Args:
        _: The incoming web request (unused).

    Returns:
        web.Response: A JSON response indicating the status is "ok".
    """
    return web.json_response({"status": "ok"})


async def start_health_server(port: int = 8000) -> web.AppRunner:
    """Start the lightweight health check HTTP server.

    Args:
        port (int, optional): The port to listen on. Defaults to 8000.

    Returns:
        web.AppRunner: The running application runner instance.
    """
    app = web.Application()
    app.router.add_get("/health", _health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    return runner


async def main() -> None:
    """Execute the main application loop.

    This function:
    1. Sets up logging.
    2. Starts the health check server.
    3. Loads configuration.
    4. Initializes and runs the Discord bot.

    Raises:
        SystemExit: If the Discord token is missing or a fatal error occurs.
    """
    health_runner = None
    try:
        # Set up logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting Discord Bot...")

        # Start health server
        health_runner = await start_health_server()
        logger.info("Health endpoint available at /health on port 8000")

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
    finally:
        # Cleanup health server if it was started
        try:
            if health_runner is not None:
                await health_runner.cleanup()
        except Exception as e:
            # We can't log here easily if logging is broken, but we try
            print(f"Error during health server cleanup: {e}")


if __name__ == "__main__":
    asyncio.run(main())
