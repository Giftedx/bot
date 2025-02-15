"""Core Discord bot implementation."""
import logging
import sys
from datetime import datetime
from typing import Any, Dict, cast

import discord
from discord.ext import commands

from src.core.config import Settings
from src.core.exceptions import ApplicationError


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BotConfigError(ApplicationError):
    """Raised when there is a bot configuration error."""
    pass


class DiscordBot(commands.Bot):
    """Main Discord bot implementation with integrated configuration."""
    
    def __init__(self, settings: Settings) -> None:
        """Initialize bot with settings and required intents."""
        self.settings = settings
        
        # Configure intents
        intents: discord.Intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.voice_states = True
        intents.guilds = True
        intents.reactions = True
        
        # Initialize bot with settings
        super().__init__(
            command_prefix=settings.get_str("COMMAND_PREFIX", "!"),
            intents=intents,
            help_command=None,
            description="A Discord bot with media controls and games!"
        )

        # Command handling
        self._command_cooldowns: Dict[str, float] = {}
        self._command_counters: Dict[str, int] = {}
        self._last_command_time: Dict[int, float] = {}
        self.max_commands_per_minute = 30
        self.command_cooldown = 3.0

        # Set up error handler
        self.setup_error_handler()

    def setup_error_handler(self) -> None:
        """Set up the global error handler."""
        @self.event
        async def on_error(event_method: str, *args: Any) -> None:
            """Handle any errors that occur in the bot."""
            error = sys.exc_info()[1]
            if error is not None:
                logger.error(f"Error in {event_method}: {error}")

    async def setup_hook(self) -> None:
        """Load cogs and initialize services on startup."""
        # Core cogs (essential functionality)
        core_cogs = [
            'src.bot.cogs.error_handler',
            'src.bot.cogs.help_command',
        ]
        
        # Feature cogs (main bot features)
        feature_cogs = [
            'src.bot.cogs.media_commands',
            'src.bot.cogs.plex_commands',
            'src.bot.cogs.audio_commands',
            'src.bot.cogs.osrs_commands',  # Added OSRS commands
        ]
        
        # Utility cogs (additional functionality)
        utility_cogs = [
            'src.bot.cogs.moderation',
            'src.bot.cogs.user_utilities',
            'src.bot.cogs.utility_commands',
        ]
        
        # Optional cogs (fun/games)
        optional_cogs = [
            'src.bot.cogs.fun_commands',
            'src.bot.cogs.game_commands',
        ]
        
        # Load core cogs first - these are required
        for cog in core_cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded core cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load core cog {cog}: {e}")
                raise BotConfigError(
                    f"Critical cog loading failed: {cog}"
                ) from e
        
        # Load feature cogs - these provide main functionality
        for cog in feature_cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded feature cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load feature cog {cog}: {e}")
                # Don't raise for OSRS cog failure
                if 'osrs_commands' not in cog:
                    raise BotConfigError(
                        f"Feature cog loading failed: {cog}"
                    ) from e
                else:
                    logger.warning(
                        "OSRS commands not loaded - "
                        "continuing without game features"
                    )
        
        # Load utility cogs
        for cog in utility_cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded utility cog: {cog}")
            except Exception as e:
                logger.warning(f"Utility cog not loaded {cog}: {e}")
        
        # Load optional cogs
        for cog in optional_cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded optional cog: {cog}")
            except Exception as e:
                logger.warning(f"Optional cog not loaded {cog}: {e}")

    async def on_ready(self) -> None:
        """Handle bot ready event."""
        if self.user is not None:
            user = cast(discord.ClientUser, self.user)
            logger.info(
                f"Logged in as {user.name} ({user.id})"
            )
            logger.info(f"Connected to {len(self.guilds)} guilds")
            
            # Set bot status
            status = "Type !help for commands"
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.listening,
                    name=status
                )
            )
        else:
            logger.error("Bot user is None")

    async def process_commands(self, message: discord.Message) -> None:
        """Process commands with rate limiting and cooldowns."""
        if message.author.bot:
            return

        # Check rate limits
        now = datetime.now().timestamp()
        user_id = message.author.id
        
        # Clear old command times
        self._last_command_time = {
            uid: time for uid, time in self._last_command_time.items()
            if now - time < 60
        }
        
        # Check user rate limit
        if user_id in self._last_command_time:
            command_count = sum(
                1 for t in self._last_command_time.values()
                if now - t < 60
            )
            if command_count >= self.max_commands_per_minute:
                await message.channel.send(
                    "You're using commands too quickly! Please slow down."
                )
                return

        # Get command context
        ctx = await self.get_context(message)
        if ctx.command is None:
            return

        # Check command cooldown
        command_key = f"{ctx.command.name}:{user_id}"
        if command_key in self._command_cooldowns:
            cooldown_end = self._command_cooldowns[command_key]
            if now < cooldown_end:
                remaining = int(cooldown_end - now)
                await message.channel.send(
                    f"Command on cooldown. Try again in {remaining}s."
                )
                return

        # Update rate limit tracking
        self._last_command_time[user_id] = now
        self._command_cooldowns[command_key] = now + self.command_cooldown
        
        # Track command usage
        if ctx.command:
            self._command_counters[ctx.command.name] = \
                self._command_counters.get(ctx.command.name, 0) + 1

        # Process the command
        try:
            await self.invoke(ctx)
        except Exception as e:
            logger.error(
                f"Command error in {ctx.command}: {e}",
                exc_info=True
            )
            raise


def run_bot() -> None:
    """Initialize and run the Discord bot."""
    try:
        settings = Settings()
        bot = DiscordBot(settings)
        
        token = settings.get_str("DISCORD_TOKEN")
        if not token:
            raise BotConfigError(
                "Missing DISCORD_TOKEN in environment variables"
            )
            
        bot.run(token)
    except BotConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    finally:
        logger.info("Cleaning up resources")


if __name__ == "__main__":
    run_bot()
