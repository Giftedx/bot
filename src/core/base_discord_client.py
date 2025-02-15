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
    """Base Discord client with cog loading and core services."""

    def __init__(self, config: BotConfig):
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
        """Initialize bot services and load cogs"""
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
        """Clean shutdown of bot services"""
        try:
            await self._metrics.stop()
            await self._health_monitor.stop()
        finally:
            await super().close()

    async def process_commands(self, message: discord.Message) -> None:
        """Process commands through command processor"""
        await self.command_processor.process_message(message)
