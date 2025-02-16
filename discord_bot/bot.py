"""Main bot module."""

import discord
from discord.ext import commands
import os
import logging
import asyncio
import aiohttp
from typing import Optional
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bot')

class Config:
    """Bot configuration."""
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')
    PLEX_URL = os.getenv('PLEX_URL')
    PLEX_TOKEN = os.getenv('PLEX_TOKEN')
    LAVALINK_HOST = os.getenv('LAVALINK_HOST', 'localhost')
    LAVALINK_PORT = int(os.getenv('LAVALINK_PORT', '2333'))
    LAVALINK_PASSWORD = os.getenv('LAVALINK_PASSWORD', 'youshallnotpass')

class Bot(commands.Bot):
    """Custom bot class with enhanced functionality."""
    
    def __init__(self):
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        # Initialize the bot
        super().__init__(
            command_prefix=Config.COMMAND_PREFIX,
            intents=intents,
            case_insensitive=True
        )
        
        # Store configuration
        self.config = Config
        self.start_time = None
        
        # Create aiohttp session
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def setup_hook(self):
        """Initialize bot and load extensions."""
        # Create aiohttp session
        self.session = aiohttp.ClientSession()
        
        # Load all cogs
        await self.load_cogs()
    
    async def load_cogs(self):
        """Load all cogs from the cogs directory."""
        cogs = [
            'discord_bot.cogs.general_commands',
            'discord_bot.cogs.admin_commands',
            'discord_bot.cogs.pokemon_commands',
            'discord_bot.cogs.game_commands',
            'discord_bot.cogs.music_commands',
            'discord_bot.cogs.moderation_commands',
            'discord_bot.cogs.custom_commands',
            'discord_bot.cogs.media_commands'
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f'Loaded extension: {cog}')
            except Exception as e:
                logger.error(f'Failed to load extension {cog}: {e}')
    
    async def on_ready(self):
        """Event triggered when the bot is ready."""
        self.start_time = datetime.datetime.utcnow()
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('------')
        
        # Set custom status
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{self.config.COMMAND_PREFIX}help"
        )
        await self.change_presence(activity=activity)
    
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Global error handler for command errors."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
            
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
            return
            
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send("This command cannot be used in private messages.")
            return
            
        if isinstance(error, commands.DisabledCommand):
            await ctx.send("This command is currently disabled.")
            return
            
        # Log the error
        logger.error(f'Error in command {ctx.command}: {error}', exc_info=error)
        
        # Send error message to user
        error_msg = f"An error occurred while processing the command:\n```{str(error)}```"
        if ctx.guild is None:  # In DMs, always show error
            await ctx.send(error_msg)
        elif ctx.author.guild_permissions.administrator:  # In guild, only show to admins
            await ctx.send(error_msg)
        else:
            await ctx.send("An error occurred while processing the command.")
    
    async def close(self):
        """Clean up resources when shutting down."""
        if self.session:
            await self.session.close()
        await super().close()

def main():
    """Main entry point for the bot."""
    # Create and run bot
    bot = Bot()
    
    try:
        bot.run(Config.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f'Error running bot: {e}')
        raise

if __name__ == '__main__':
    main() 