"""Base bot implementation with shared functionality."""
import asyncio
import logging
from typing import Optional, Dict, Any, Set
from pathlib import Path

import discord
from discord.ext import commands

from ..core.config import Config
from ..core.metrics import MetricsRegistry
from ..utils.formatting import format_error

logger = logging.getLogger(__name__)

class BaseBot(commands.Bot):
    """Base bot class with shared functionality."""
    
    def __init__(
        self,
        config: Config,
        command_prefix: str = "!",
        description: Optional[str] = None,
        **kwargs: Any
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
            **kwargs
        )

        self.config = config
        self.metrics = MetricsRegistry()
        self._ready = asyncio.Event()
        self._cleanup_tasks: Set[asyncio.Task] = set()

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
        """Load all extensions from the cogs directory."""
        cogs_dir = Path(__file__).parent.parent / "cogs"
        
        for extension in self.config.ENABLED_EXTENSIONS:
            try:
                await self.load_extension(f"cogs.{extension}")
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")

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

    async def on_command_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError
    ) -> None:
        """Handle command errors."""
        error_type = type(error).__name__
        self.metrics.counter("bot_errors_total").labels(type=error_type).inc()

        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        error_message = format_error(error)
        await ctx.send(error_message)

        if not isinstance(error, (
            commands.CommandNotFound,
            commands.MissingPermissions,
            commands.CheckFailure
        )):
            logger.error(f"Command error: {error}", exc_info=True)

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