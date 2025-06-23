"""Base Discord client implementation for unified bot architecture.

This module defines the BaseDiscordClient, which provides:
- Unified cog loading
- Integration with core services (command processor, health monitor, metrics)
- Standardized bot initialization and shutdown

Typical usage example:
    from src.core.base_discord_client import BaseDiscordClient
    bot = BaseDiscordClient(config)
    bot.run()
"""

import logging

import discord
from discord.ext import commands

from src.core.command_processor import CommandProcessor
from src.core.config_manager import BotConfig
from src.core.health_monitor import HealthMonitor
from src.core.metrics_manager import MetricsManager

logger = logging.getLogger(__name__)

COGS = [
    "cogs.error_handler",
    "cogs.help_command",
    "cogs.fun_commands",
    "cogs.fun_extras",
    "cogs.game_commands",
    "cogs.audio_commands",
    "cogs.utility_commands",
]


class BaseDiscordClient(commands.Bot):
    """Base Discord client with cog loading and core services.
    
    Extends commands.Bot to provide:
    - Automated cog loading
    - Integration with command processor, health monitor, and metrics
    - Standardized setup and shutdown procedures
    """

    def __init__(self, config: BotConfig):
        """Initialize the Discord client and core services.
        
        Args:
            config: BotConfig instance with bot configuration
        """
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.reactions = True
        intents.members = True

        super().__init__(
            command_prefix=config.COMMAND_PREFIX,
            intents=intents,
            description="Discord bot for media management.",
        )

        self.config = config
        self.command_processor = CommandProcessor(self)
        self._health_monitor = HealthMonitor()
        self._metrics = MetricsManager()

    async def setup_hook(self) -> None:
        """Initialize bot services and load cogs.
        
        Loads all cogs listed in COGS and starts core services.
        
        Raises:
            Exception: If initialization fails
        """
        try:
            # Load all cogs
            for cog in COGS:
                try:
                    await self.load_extension(cog)
                    logger.info(f"Loaded cog: {cog}")
                except Exception as e:
                    logger.error(f"Failed to load cog {cog}: {e}")

            # Initialize services
            await self._metrics.start()
            await self._health_monitor.start()

        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        """Clean shutdown of bot services.
        
        Stops metrics and health monitor services before closing the bot.
        """
        try:
            await self._metrics.stop()
            await self._health_monitor.stop()
        finally:
            await super().close()

    async def process_commands(self, message: discord.Message) -> None:
        """Process commands through command processor.
        
        Args:
            message: Discord message to process
        """
        await self.command_processor.process_message(message)
