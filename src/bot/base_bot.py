"""Base bot implementation with shared functionality."""
import asyncio
import logging
from typing import Optional, Dict, Any, Set
from pathlib import Path
import os

import discord
from discord.ext import commands

from ..core.config import ConfigManager
from ..core.database import DatabaseManager
from ..core.metrics import MetricsRegistry, setup_metrics
from ..core.battle_system import BattleManager as BattleManager
from ..utils.formatting import format_error

logger = logging.getLogger(__name__)


class BaseBot(commands.Bot):
    """Base bot class with shared functionality."""

    def __init__(
        self,
        config_manager: ConfigManager,
        command_prefix: str = "!",
        description: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize bot with configuration."""
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.voice_states = True

        super().__init__(
            command_prefix=command_prefix,
            description=description or "Discord Bot",
            intents=intents,
            **kwargs,
        )

        self.config_manager = config_manager
        self.db_manager = DatabaseManager(db_path=self.config_manager.get_config("database.path"))
        self.battle_manager = BattleManager()
        self.metrics = setup_metrics(port=8000)
        self._ready = asyncio.Event()
        self._cleanup_tasks: Set[asyncio.Task] = set()
        self.extensions_path = Path("src/bot/cogs")

    async def setup_hook(self) -> None:
        """Set up the bot before it starts running."""
        try:
            # Load extensions
            await self.load_extensions()

            # Set up metrics
            self._setup_metrics_tasks()

            logger.info("Bot setup complete")
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}", exc_info=True)
            raise

    async def load_extensions(self) -> None:
        """Load all extensions from the cogs and commands directories."""
        cogs_dir = self.extensions_path
        commands_dir = Path("src/app/commands")

        # Load cogs
        logger.info("Loading cogs...")
        for f in cogs_dir.iterdir():
            if f.is_file() and f.suffix == ".py" and f.name != "__init__.py":
                try:
                    await self.load_extension(f"src.bot.cogs.{f.stem}")
                    logger.info(f"Loaded cog: {f.stem}")
                except Exception as e:
                    logger.error(f"Failed to load cog {f.stem}: {e}", exc_info=True)

        # Load app commands
        logger.info("Loading app commands...")
        for f in commands_dir.iterdir():
            if f.is_file() and f.suffix == ".py" and f.name != "__init__.py":
                try:
                    await self.load_extension(f"src.app.commands.{f.stem}")
                    logger.info(f"Loaded app command: {f.stem}")
                except Exception as e:
                    logger.error(f"Failed to load app command {f.stem}: {e}", exc_info=True)

    def _setup_metrics_tasks(self) -> None:
        """Set up background tasks for metrics collection."""

        async def collect_metrics():
            while True:
                try:
                    self.metrics.gauge("bot_latency_seconds").set(self.latency)
                    self.metrics.gauge("bot_guilds").set(len(self.guilds))
                    self.metrics.gauge("bot_users").set(len(self.users))
                except Exception as e:
                    logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(60)

        task = asyncio.create_task(collect_metrics())
        self._cleanup_tasks.add(task)
        task.add_done_callback(self._cleanup_tasks.discard)

    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        logger.info(f"Logged in as {self.user}")
        self._ready.set()

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Handle command errors."""
        error_type = type(error).__name__
        self.metrics.counter("bot_errors_total").labels(type=error_type).inc()

        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        error_message = format_error(error)
        await ctx.send(error_message)

        if not isinstance(
            error, (commands.CommandNotFound, commands.MissingPermissions, commands.CheckFailure)
        ):
            logger.error(f"Command error: {error}", exc_info=True)

    async def on_app_command_error(
        self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError
    ) -> None:
        """Handle application command errors."""
        error_type = type(error).__name__
        self.metrics.counter("bot_errors_total").labels(type=error_type).inc()

        if isinstance(error, discord.app_commands.CommandInvokeError):
            error = error.original

        error_message = format_error(error)

        # Ensure we can still respond to the interaction
        if not interaction.response.is_done():
            await interaction.response.send_message(error_message, ephemeral=True)
        else:
            await interaction.followup.send(error_message, ephemeral=True)

        if not isinstance(error, discord.app_commands.CheckFailure):
            logger.error(f"Application command error: {error}", exc_info=True)

    async def close(self) -> None:
        """Clean up and close the bot."""
        logger.info("Shutting down bot...")

        # Cancel cleanup tasks
        for task in self._cleanup_tasks:
            task.cancel()

        if self._cleanup_tasks:
            await asyncio.gather(*self._cleanup_tasks, return_exceptions=True)

        await super().close()

    def add_cleanup_task(self, task: asyncio.Task) -> None:
        """Add a task to be cleaned up on shutdown."""
        self._cleanup_tasks.add(task)
        task.add_done_callback(self._cleanup_tasks.discard)

    async def wait_until_ready(self) -> None:
        """Wait until the bot is ready."""
        await self._ready.wait()
