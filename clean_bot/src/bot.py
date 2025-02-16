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
from src.core.config import Settings  # Import Settings
from dependency_injector.wiring import inject, Provide
from src.utils.performance import measure_latency
import discord
import redis

from core.config import load_config
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
        config = load_config()
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        super().__init__(
            command_prefix='!',
            description='Discord Plex Player',
            intents=intents
        )
        
        # Initialize components
        self.config = config
        self.redis = redis.Redis(
            host=config.redis.host,
            port=config.redis.port,
            db=config.redis.db,
            password=config.redis.password
        )
        
        try:
            self.plex = PlexClient(
                config.plex.url,
                config.plex.token,
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
        super().run(self.config.discord.token)

if __name__ == '__main__':
    bot = PlexBot()
    bot.run()
