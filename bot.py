import os
import discord
from discord.ext import commands
import asyncio
import logging
import os
import platform
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import uuid
import sys

import asyncpg
import discord
import yaml
from discord.ext import commands
from dotenv import load_dotenv

from cogs.database import osrs_db

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("discord.log")],
)
logger = logging.getLogger("DiscordBot")

# Load environment variables
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - [%(correlation_id)s] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)

# Add correlation ID filter
class CorrelationIDFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = 'NO_CORR_ID'
        return True

logger = logging.getLogger(__name__)
logger.addFilter(CorrelationIDFilter())

class CustomBot(commands.Bot):
    def __init__(self):
        # Load config
        try:
            with open('config.yaml', 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}", exc_info=True)
            raise

        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(
            command_prefix=self.config["discord"]["prefix"],
            intents=intents,
            case_insensitive=True,
        )

        # Initialize attributes
        self.db = osrs_db
        self.initial_extensions = [
            'cogs.admin',
            'cogs.games',
            'cogs.media',
            'cogs.plex',
            'cogs.fun',
            'cogs.osrs_commands',
            'cogs.battle_system',
            'cogs.game_commands',
            'cogs.fun_commands',
            'cogs.activities',
            'cogs.voice'
        ]

    async def setup_hook(self) -> None:
        """Setup hook that runs before the bot starts"""
        correlation_id = str(uuid.uuid4())
        logger.info("Starting bot setup", extra={'correlation_id': correlation_id})

        # Connect to database with retry logic
        retry_count = 0
        max_retries = self.config['database'].get('max_retries', 3)
        
        while retry_count < max_retries:
            try:
                self.db = await asyncpg.create_pool(
                    self.config['database']['url'],
                    min_size=5,
                    max_size=self.config['database'].get('pool_size', 20),
                    command_timeout=self.config['database'].get('command_timeout', 60),
                    max_inactive_connection_lifetime=self.config['database'].get('max_inactive_connection_lifetime', 300)
                )
                logger.info("Connected to database successfully", extra={'correlation_id': correlation_id})
                break
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    logger.error(f"Failed to connect to database after {max_retries} attempts: {e}", 
                               extra={'correlation_id': correlation_id}, exc_info=True)
                    raise
                logger.warning(f"Database connection attempt {retry_count} failed, retrying...", 
                             extra={'correlation_id': correlation_id})
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff

        # Load extensions
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}", extra={'correlation_id': correlation_id})
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}", 
                           extra={'correlation_id': correlation_id}, exc_info=True)

    async def on_ready(self) -> None:
        """Event that fires when the bot is ready"""
        correlation_id = str(uuid.uuid4())
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})", 
                   extra={'correlation_id': correlation_id})
        logger.info(f"Discord.py version: {discord.__version__}", 
                   extra={'correlation_id': correlation_id})
        logger.info(f"Python version: {platform.python_version()}", 
                   extra={'correlation_id': correlation_id})
        
        # Set activity
        activity = discord.Game(name=self.config['discord']['status'])
        await self.change_presence(activity=activity)

        # Log connected guilds
        guild_list = [f"- {guild.name} (id: {guild.id})" for guild in self.guilds]
        logger.info("Connected to the following guilds:\n%s", 
                   "\n".join(guild_list), extra={'correlation_id': correlation_id})

    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Global error handler with improved error handling and logging"""
        correlation_id = str(uuid.uuid4())
        
        if isinstance(error, commands.CommandNotFound):
            # Check for custom command
            command_name = ctx.message.content[len(self.command_prefix):].split()[0]
            try:
                custom_command = await self.db.fetchrow(
                    "SELECT response FROM custom_commands WHERE name = $1",
                    command_name.lower(),
                )
                if custom_command:
                    return await ctx.send(custom_command["response"])
            except Exception as e:
                logger.error(f"Error checking custom command: {e}", 
                           extra={'correlation_id': correlation_id}, exc_info=True)

        elif isinstance(error, commands.MissingPermissions):
            logger.warning(f"User {ctx.author} attempted to use command without permission: {ctx.command}", 
                         extra={'correlation_id': correlation_id})
            await ctx.send("You don't have permission to use this command!")

        elif isinstance(error, commands.CommandOnCooldown):
            logger.info(f"Command {ctx.command} on cooldown for user {ctx.author}", 
                       extra={'correlation_id': correlation_id})
            await ctx.send(
                f"This command is on cooldown. Try again in {error.retry_after:.2f}s"
            )

        elif isinstance(error, commands.MissingRequiredArgument):
            logger.info(f"Missing argument {error.param.name} for command {ctx.command}", 
                       extra={'correlation_id': correlation_id})
            await ctx.send(f"Missing required argument: {error.param.name}")

        else:
            # Log unexpected errors
            logger.error(f"Unexpected error in command {ctx.command}: {error}", 
                        extra={'correlation_id': correlation_id}, exc_info=True)
            await ctx.send(
                "An unexpected error occurred! The error has been logged."
            )

    async def on_message(self, message: discord.Message) -> None:
        """Event that fires when a message is received"""
        # Ignore messages from bots
        if message.author.bot:
            return

        # Process commands
        await self.process_commands(message)

    async def on_voice_state_update(self, member, before, after):
        """Handle voice state updates"""
        # If the bot is in a voice channel and alone, disconnect after timeout
        if member.id != self.user.id:  # Don't handle bot's own state changes
            return

        if before.channel and not after.channel:  # Bot disconnected
            return

        if after.channel:
            await asyncio.sleep(self.config['features']['voice']['timeout'])
            voice_client = discord.utils.get(self.voice_clients, guild=member.guild)
            if voice_client and len(voice_client.channel.members) == 1:
                await voice_client.disconnect()

    async def close(self) -> None:
        """Clean up when the bot is shutting down"""
        correlation_id = str(uuid.uuid4())
        
        # Close database connection
        if self.db:
            await self.db.close()
            logger.info("Closed database connection", extra={'correlation_id': correlation_id})

        # Close any voice clients
        for voice_client in self.voice_clients:
            try:
                await voice_client.disconnect()
            except:
                pass

        await super().close()
        logger.info("Bot shutdown complete", extra={'correlation_id': correlation_id})

@commands.command(name='join', help='Joins the user\'s voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You need to be in a voice channel first!")
        return
    
    channel = ctx.message.author.voice.channel
    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()
    
    await ctx.send(f'Joined {channel.name}!')

@commands.command(name='leave', help='Leaves the voice channel')
async def leave(ctx):
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()
        await ctx.send('Left the voice channel!')
    else:
        await ctx.send('I am not in a voice channel!')

async def main() -> None:
    """Main entry point for the bot"""
    correlation_id = str(uuid.uuid4())
    
    # Create bot instance
    bot = CustomBot()

    # Start the bot
    try:
        logger.info("Starting bot", extra={'correlation_id': correlation_id})
        await bot.start(TOKEN)
    except Exception as e:
        logger.error(f"Error starting bot: {e}", 
                    extra={'correlation_id': correlation_id}, exc_info=True)
        raise
    finally:
        await bot.close()

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
