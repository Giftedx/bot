import discord
from discord.ext import commands
import os
import sys
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from plexapi.server import PlexServer

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Set up logging
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(filename='discord.log', maxBytes=5*1024*1024, backupCount=2)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        intents.members = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.plex = None
        self.setup_complete = False

    async def setup_hook(self):
        """Async setup method that runs before the bot starts"""
        try:
            # Load cogs
            for ext in ['fun_commands', 'plex_commands']:
                try:
                    await self.load_extension(f'cogs.{ext}')
                    logger.info(f"Loaded {ext}")
                except Exception as e:
                    logger.error(f"Failed to load {ext}: {e}")
            
            # Initialize Plex
            try:
                self.plex = PlexServer(os.getenv('PLEX_URL'), os.getenv('PLEX_TOKEN'))
                logger.info("Connected to Plex")
            except Exception as e:
                logger.error(f"Plex connection failed: {e}")
            
            self.setup_complete = True
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            self.setup_complete = False

    async def on_ready(self):
        """Event handler that runs when the bot is ready"""
        await self.change_presence(activity=discord.Game(name="Plex with friends"))
        logger.info(f'{self.user} has connected to Discord!')

    def run(self, *args, **kwargs):
        """Override run to start the bot"""
        super().run(*args, **kwargs)

def main():
    try:
        bot = DiscordBot()
        bot.run(TOKEN)
    except Exception as e:
        logger.error(f"Bot failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()