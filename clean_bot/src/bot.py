"""Main Discord bot implementation."""
import asyncio
import logging
import signal
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator, Set, Dict, Any, List, Tuple, Optional

from discord.ext import commands

from src.core.di_container import Container

from prometheus_client import Counter, Histogram, Gauge

# from src.utils.error_handler import ErrorHandler
from src.utils.error_handler import ErrorHandler
# from src.core.config import Settings  # Removed Settings import
from src.core.config import ConfigManager  # Added ConfigManager import
from dependency_injector.wiring import inject, Provide
from src.utils.performance import measure_latency
import discord
import redis

# from core.config import load_config # Removed load_config import
from services.plex.client import PlexClient
from core.exceptions import PlexConnectionError, MediaNotFoundError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PlexBot(commands.Bot):
    """Discord bot for Plex integration."""
    
    def __init__(self):
        """Initialize the bot."""
        # config = load_config() # Old config loading removed
        self.config_manager = ConfigManager(config_dir="config") # Instantiated ConfigManager

        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        super().__init__(
            command_prefix=self.config_manager.get('bot.command_prefix', '!'), # Get command_prefix
            description=self.config_manager.get('bot.description', 'Discord Plex Player'), # Get description
            intents=intents
        )
        
        # Initialize components
        # self.config = config # Old config storage removed
        self.redis = redis.Redis(
            host=self.config_manager.get('redis.host', 'localhost'), # Get redis host
            port=self.config_manager.get('redis.port', 6379), # Get redis port
            db=self.config_manager.get('redis.db', 0), # Get redis db
            password=self.config_manager.get('redis.password') # Get redis password
        )
        
        try:
            self.plex = PlexClient(
                self.config_manager.get('plex.url'), # Get plex url
                self.config_manager.get('plex.token'), # Get plex token
                self.redis
            )
        except PlexConnectionError as e:
            logger.error(f"Failed to initialize Plex client: {e}")
            raise
            
        # Store voice clients
        self.voice_clients = {}
        
    async def setup_hook(self):
        """Set up the bot."""
        # Load cogs
        await self.load_extension('cogs.plex_commands')
        await self.load_extension('cogs.voice_handler')
        
    async def on_ready(self):
        """Handle bot ready event."""
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('------')
        
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            return
            
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
            return
            
        if isinstance(error, MediaNotFoundError):
            await ctx.send("No media found matching your search.")
            return
            
        logger.error(f'Error in command {ctx.command}: {error}')
        await ctx.send(f'An error occurred: {str(error)}')
        
    async def get_voice_client(self, channel: discord.VoiceChannel) -> Optional[discord.VoiceClient]:
        """Get or create voice client for channel."""
        if channel.id in self.voice_clients:
            return self.voice_clients[channel.id]
            
        try:
            voice_client = await channel.connect()
            self.voice_clients[channel.id] = voice_client
            return voice_client
        except Exception as e:
            logger.error(f"Error connecting to voice channel: {e}")
            return None
            
    def run(self):
        """Run the bot."""
        discord_token = self.config_manager.get('discord.token')
        if not discord_token:
            logger.error("Discord token not found in configuration. Bot cannot start.")
            return
        super().run(discord_token)

if __name__ == '__main__':
    bot = PlexBot()
    bot.run()
