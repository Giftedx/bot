import asyncio
import logging
import signal
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator, Set, Dict, Any, List, Tuple

from discord.ext import commands

from src.core.di_container import Container


from prometheus_client import Counter, Histogram, Gauge

# from src.utils.error_handler import ErrorHandler
from src.utils.error_handler import ErrorHandler
from src.core.config import Settings  # Import Settings
from dependency_injector.wiring import inject, Provide
from src.utils.performance import measure_latency
import discord


logger = logging.getLogger(__name__)


class MediaStreamingBot(commands.Bot):
    """
    Custom Discord bot for media streaming.
    """
    @inject
    def __init__(
        self,
        *args,
        settings: Settings = Provide[Container.settings],
        **kwargs
,
    ) -> None:
        intents = discord.Intents.all()
        intents.message_content = True
        super().__init__(
            command_prefix=settings.COMMAND_PREFIX,
            intents=intents,
            heartbeat_timeout=60.0,
            activity=discord.Activity(type=discord.ActivityType.watching, name="media streams")
        )
        self.settings = settings
        self._shutdown_event = asyncio.Event()
        
        
        self._command_latency = Histogram(
            'command_latency_seconds',
            'Command execution latency',
            ['command']
        )
        self._errors = Counter(
            'bot_errors_total',
            'Number of bot errors',
            ['type']
        )
        self._metrics = {
            'command_errors': Counter('bot_command_errors_total', 
                                    'Command error count', ['command']),
            'command_latency': Histogram('bot_command_latency_seconds',
                                       'Command execution time', ['command']),
            'active_commands': Gauge('bot_active_commands',
                                   'Number of active commands')
        }
        self._command_contexts: Dict[str, Any] = {}
        self._command_limiter = AsyncRateLimiter(
            rate=100,
            period=60.0,
            burst_size=20
        )
#         self._error_handler = ErrorHandler(
#             max_retries=3,
#             backoff_factor=1.5
#         )
        self._error_handler = ErrorHandler(
            max_retries=3,
            backoff_factor=1.5
        )
        self._command_queue: asyncio.Queue[Tuple[str, commands.Context]] = asyncio.Queue()
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
            cleanup_timeout = self.settings.GRACEFUL_SHUTDOWN_TIMEOUT  # Access via settings
            try:
                await asyncio.wait_for(self._cleanup(), timeout=cleanup_timeout)
            except asyncio.TimeoutError:
                logger.error(f"Cleanup timed out after {cleanup_timeout}s")

    async def _cleanup(self) -> None:
        tasks = [
            self.service_manager.cleanup(),
            self.heartbeat.shutdown(),
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
            await asyncio.gather(*self._cleanup_tasks, return_exceptions=True)

    async def setup_hook(self) -> None:
        try:
            # Start command workers
            for _ in range(self._max_concurrent_commands):
                worker = asyncio.create_task(self._command_worker())
                self._command_workers.append(worker)
            
            # Initialize dependency container and services
            container = Container()
            container.config.from_pydantic(self.settings)  # Use Pydantic settings
            container.wire(modules=[__name__, "src.cogs.media_commands"])

            # Register services with proper dependencies
            
            
            
            

            # Register heartbeats and health checks
            
            
            

            
            

            await self.add_cog(container.media_commands())
            logger.info("Bot setup complete.")

            # Register signal handlers
            for sig in (signal.SIGTERM, signal.SIGINT):
                self.loop.add_signal_handler(sig, self._handle_signal)

            # Register health checks
            self.health_check.register("redis", self._check_redis_health)
            self.health_check.register("ffmpeg", self._check_ffmpeg_health)
            self.health_check.register("plex", self._check_plex_health)
            
            # Start health monitoring
            health_task = asyncio.create_task(self._health_monitor())
            self._register_cleanup_task(health_task)
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}", exc_info=True)
            raise

    async def _command_worker(self):
        while True:
            cmd, ctx = await self._command_queue.get()
            try:
#             async with self._error_handler.handle_errors():
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
            await asyncio.sleep(self.settings.HEALTH_CHECK_INTERVAL)

    @measure_latency("health_check")
    async def _check_health(self) -> None:
        await self.health_check.run_checks()

    async def _check_redis_health(self) -> bool:
        try:
            await self.container.redis_manager().redis.ping()
            return True
        except Exception:
            return False

    async def _check_ffmpeg_health(self) -> bool:
        return len(self.container.ffmpeg_manager().active_processes) < self.settings.MAX_CONCURRENT_STREAMS  # Use settings

    async def _check_plex_health(self) -> bool:
        try:
            await self.container.plex_manager().server.ping()
            return True
        except Exception:
            return False

    async def _health_monitor(self) -> None:
        while not self._shutdown_event.is_set():
            try:
                await self._check_health()
            except Exception as e:
                logger.error(f"Health check failed: {e}")
            await asyncio.sleep(self.settings.HEALTH_CHECK_INTERVAL)  # Use settings

    async def close(self) -> None:
        if self.container and self.container.redis_manager():
            await self.container.redis_manager().close()
        if self.container and self.container.active_streams():
            self.container.active_streams().decrement()
        await super().close()
        logger.info("Bot shutdown complete.")

    async def on_ready(self) -> None:
        logger.info(f"Logged in as {self.user}")

    async def on_message(self, message: discord.Message) -> None:
        if await self.rate_limiter.is_rate_limited(str(message.author.id)):
            await message.channel.send("You are being rate limited. Please try again later.")
            return
        await self.process_commands(message)

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        logger.error(f"Error in {event_method}", exc_info=True)

    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        error_type = type(error).__name__
        self._errors.labels(type=error_type).inc()
        logger.error(f"Command error: {error}", exc_info=True)
        await super().on_command_error(ctx, error)

    async def on_command(self, ctx: commands.Context) -> None:
        start_time = time.monotonic()
        try:
            await super().on_command(ctx)
        finally:
            duration = time.monotonic() - start_time
            self._command_latency.labels(ctx.command.name).observe(duration)

    async def process_commands(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        async with self._command_semaphore:
            cmd_key = f"{message.author.id}:{message.content}"
            
            # Check command cooldown
            if self._command_timeouts.get(cmd_key, 0) > time.time():
                await message.channel.send("Please wait before using this command again.")
                return
                
            try:
                self._command_timeouts[cmd_key] = time.time() + self.settings.COMMAND_COOLDOWN
                await super().process_commands(message)
            except Exception as e:
                logger.error(f"Command processing error: {e}", exc_info=True)
                self._errors.labels(type=type(e).__name__).inc()
                await message.channel.send("An error occurred processing your command.")

    async def _execute_command(self, cmd: str, ctx: commands.Context):
        """Executes a command, handling rate limits and command-specific logic."""
        try:
            # Apply global rate limit
            
                # Execute the command
                await ctx.invoke(cmd)
        except commands.CommandNotFound:
            await ctx.send("Command not found.")
        except commands.MissingRequiredArgument:
            await ctx.send("Missing required arguments.")
        except commands.BadArgument:
            await ctx.send("Invalid arguments provided.")
        except commands.CommandOnCooldown as e:
            await ctx.send(f"Command is on cooldown, try again in {e.retry_after:.2f} seconds.")
        except Exception as e:
            logger.error(f"Command execution failed: {e}", exc_info=True)
            await ctx.send("An error occurred while executing the command.")
