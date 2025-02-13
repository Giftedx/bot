import discord
from discord.ext import commands
import os
import logging
import asyncio
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Setup logging
logger = logging.getLogger('DiscordBot')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    'logs/discord_bot.log',
    maxBytes=5_000_000,
    backupCount=5,
    encoding='utf-8'
)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Load environment variables
BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

class CustomBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            description="A bot to play media from Plex in Discord voice channels."
        )
        
        self.start_time = datetime.now()
        self.command_usage = {}

    async def setup_hook(self):
        """Load extensions on bot startup"""
        logger.info("Loading extensions...")
        extensions = [
            'cogs.fun_commands',
            'cogs.plex_commands',
            'cogs.game_commands'
        ]
        
        for ext in extensions:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name} ({self.user.id})')
        await self.change_presence(activity=discord.Game(name="Plex with friends"))

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found! Use !help to see available commands.")
            return
        
        logger.error(f"Command error in {ctx.command}: {error}", exc_info=error)
        await ctx.send("An error occurred while processing your command.")

def create_bot() -> CustomBot:
    return CustomBot()

if __name__ == '__main__':
    if not BOT_TOKEN:
        logger.error("DISCORD_BOT_TOKEN environment variable not set.")
        exit(1)

    bot = create_bot()
    try:
        asyncio.run(bot.start(BOT_TOKEN))
    except KeyboardInterrupt:
        logger.info("Bot shutdown initiated by user.")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=e)
    finally:
        asyncio.run(bot.close())
