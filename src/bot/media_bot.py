"""MediaStreamingBot implementation."""
import asyncio
import logging
import signal
import sys
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator, Set, Dict, Any, List, Tuple

from discord.ext import commands
from src.core.di_container import Container
from src.utils.error_handler import ErrorHandler
from src.core.config import Settings
from dependency_injector.wiring import inject, Provide
from src.utils.performance import measure_latency, METRICS
import discord

logger = logging.getLogger(__name__)

class MediaStreamingBot(commands.Bot):
    """Custom Discord bot for media streaming."""
    @inject
    def __init__(
        self,
        *args: Any,
        settings: Settings = Provide[Container.config],
        **kwargs: Any
    ) -> None:
        intents = discord.Intents.all()
        intents.message_content = True
        super().__init__(
            command_prefix=settings.get("COMMAND_PREFIX", "!"),
            intents=intents,
            heartbeat_timeout=60.0,
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="media streams"
            )
        )
        self.settings = settings
        self._shutdown_event = asyncio.Event()

        self._command_contexts: Dict[str, Any] = {}
        self._error_handler = ErrorHandler(
            max_retries=3,
            backoff_factor=1.5
        )
        self._command_queue: asyncio.Queue[
            Tuple[str, commands.Context]
        ] = asyncio.Queue()
        self._command_workers: List[asyncio.Task] = []
        self._max_concurrent_commands = 5
        self._command_semaphore = asyncio.Semaphore(10)
        self._cleanup_tasks: Set[asyncio.Task[Any]] = set()
        self._command_timeouts: Dict[str, float] = {}

    @asynccontextmanager
    async def graceful_shutdown(self) -> AsyncIterator[None]:
        try:
            yield
        finally:
            self._shutdown_event.set()
            cleanup_timeout = float(self.settings.get("GRACEFUL_SHUTDOWN_TIMEOUT", 30.0))
            try:
                await asyncio.wait_for(
                    self._cleanup(), timeout=cleanup_timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Cleanup timed out after {cleanup_timeout}s")

    async def _cleanup(self) -> None:
        tasks = [
            self._cancel_cleanup_tasks(),
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    def _register_cleanup_task(self, task: asyncio.Task) -> None:
        self._cleanup_tasks.add(task)
        task.add_done_callback(self._cleanup_tasks.discard)

    async def _cancel_cleanup_tasks(self) -> None:
        for task in self._cleanup_tasks:
            task.cancel()
        if self._cleanup_tasks:
            await asyncio.gather(
                *self._cleanup_tasks, return_exceptions=True
            )

    async def setup_hook(self) -> None:
        """Set up the bot."""
        try:
            # Start command workers
            for _ in range(self._max_concurrent_commands):
                worker = asyncio.create_task(self._command_worker())
                self._command_workers.append(worker)

            logger.info("Bot setup complete.")

            # Handle signals differently on Windows vs Unix
            if sys.platform != 'win32':
                # Register signal handlers only on Unix systems
                for sig in (signal.SIGTERM, signal.SIGINT):
                    self.loop.add_signal_handler(sig, self._handle_signal)
            else:
                # On Windows, use a background task to check for shutdown
                self._shutdown_check_task = self.loop.create_task(self._check_shutdown())

        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}", exc_info=True)
            raise

    async def _check_shutdown(self) -> None:
        """Background task to check for shutdown on Windows."""
        while True:
            try:
                await asyncio.sleep(1)
                if self._shutdown_event.is_set():
                    await self.close()
                    break
            except asyncio.CancelledError:
                break

    async def _command_worker(self) -> None:
        while True:
            cmd, ctx = await self._command_queue.get()
            try:
                async with self._error_handler.handle_errors():
                    await self._execute_command(cmd, ctx)
            except Exception as e:
                logger.error(f"Command execution error: {e}", exc_info=True)
            finally:
                self._command_queue.task_done()

    def _handle_signal(self) -> None:
        self._shutdown_event.set()
        logger.info("Shutdown signal received")

    async def _monitor(self) -> None:
        while not self._shutdown_event.is_set():
            try:
                await self._check_health()
            except Exception as e:
                logger.error(f"Health check failed: {e}")
            await asyncio.sleep(float(self.settings.get("HEALTH_CHECK_INTERVAL", 60.0)))

    @measure_latency("health_check")
    async def _check_health(self) -> None:
        pass

    async def _check_redis_health(self) -> bool:
        return True

    async def _check_ffmpeg_health(self) -> bool:
        return True

    async def _check_plex_health(self) -> bool:
        return True

    async def _health_monitor(self) -> None:
        while not self._shutdown_event.is_set():
            try:
                await self._check_health()
            except Exception as e:
                logger.error(f"Health check failed: {e}")
            await asyncio.sleep(float(self.settings.get("HEALTH_CHECK_INTERVAL", 60.0)))

    async def close(self) -> None:
        await super().close()
        logger.info("Bot shutdown complete.")

    async def on_ready(self) -> None:
        logger.info(f"Logged in as {self.user}")

    async def on_message(self, message: discord.Message) -> None:
        await self.process_commands(message)

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        error_type = type(error).__name__
        METRICS['command_errors'].labels(command=ctx.command.name if ctx.command else 'unknown').inc()
        logger.error(f"Command error: {error}", exc_info=True)
        if isinstance(error, commands.CommandInvokeError):
            await super().on_command_error(ctx, error.original)
        else:
            await super().on_command_error(ctx, error)

    async def on_command(self, ctx: commands.Context) -> None:
        if ctx.command is not None:
            logger.info(f"Command invoked: {ctx.command.name}")
            METRICS['command_latency'].labels(command_name=ctx.command.name).observe(
                (time.monotonic() - ctx.message.created_at.timestamp())
            )

    async def process_commands(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        async with self._command_semaphore:
            cmd_key = f"{message.author.id}:{message.content}"

            if self._command_timeouts.get(cmd_key, 0) > time.time():
                await message.channel.send(
                    "Please wait before using this command again."
                )
                return

            try:
                self._command_timeouts[cmd_key] = (
                    time.time() + float(self.settings.get("COMMAND_COOLDOWN", 3.0))
                )
                ctx = await self.get_context(message)
                if ctx.command is not None:
                    await self.invoke(ctx)
            except Exception as e:
                logger.error(f"Command processing error: {e}", exc_info=True)
                self._errors.labels(type=type(e).__name__).inc()
                await message.channel.send(
                    "An error occurred processing your command."
                )

    async def _execute_command(self, cmd: str, ctx: commands.Context) -> None:
        """Executes a command, handling rate limits/command-specific logic."""
        try:
            if ctx.command is not None:
                await ctx.invoke(ctx.command)
        except commands.CommandNotFound:
            await ctx.send("Command not found.")
        except commands.MissingRequiredArgument:
            await ctx.send("Missing required arguments.")
        except commands.BadArgument:
            await ctx.send("Invalid arguments provided.")
        except commands.CommandOnCooldown as e:
            await ctx.send(
                f"Command on cooldown, try again in {e.retry_after:.2f}."
            )
        except Exception as e:
            logger.error(f"Command execution failed: {e}", exc_info=True)
            await ctx.send("Error occurred while executing the command.")

# Initialize dependency container and wire it
container = Container()
container.init_resources()
container.wire(modules=[__name__, "src.bot.cogs.media_commands"])