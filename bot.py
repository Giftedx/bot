"""Main Discord bot implementation."""

import os
import discord
from discord.ext import commands
import logging
from typing import Dict, Optional

from src.osrs.models import Player
from src.osrs.core.world_manager import WorldManager
from src.osrs.core.item_database import ItemDatabase
from src.database.db_service import DatabaseService


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('OSRSBot')


class OSRSBot(commands.Bot):
    """Main bot class for OSRS Discord bot."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            description='Old School RuneScape Discord Bot'
        )
        
        # Initialize components
        self.db = DatabaseService(os.getenv('DATABASE_URL'))
        self.world_manager = WorldManager()
        self.item_db = ItemDatabase()
        
        # Cache for player data
        self.players: Dict[int, Player] = {}
        
        # Load cogs
        self.initial_extensions = [
            'cogs.osrs_commands',
            'cogs.combat_commands',
            'cogs.quest_commands',
            'cogs.trade_commands'
        ]
    
    async def setup_hook(self):
        """Set up the bot before it starts running."""
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f'Loaded extension: {extension}')
            except Exception as e:
                logger.error(f'Failed to load extension {extension}: {e}')
    
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f'Logged in as {self.user.name} ({self.user.id})')
        logger.info('------')
        
        # Initialize database tables if they don't exist
        await self.db.initialize_tables()
        
        # Load item database
        await self.item_db.load_items()
        
        # Set up activity
        activity = discord.Game(name="OSRS | !help")
        await self.change_presence(activity=activity)
    
    def get_player(self, user_id: int) -> Optional[Player]:
        """Get a player from cache or database."""
        # Check cache first
        if user_id in self.players:
            return self.players[user_id]
        
        # Load from database
        player_data = self.db.load_player(user_id)
        if player_data:
            player = Player(**player_data)
            self.players[user_id] = player
            return player
        
        return None
    
    async def save_player(self, player: Player) -> bool:
        """Save player data to database."""
        try:
            await self.db.save_player(player)
            return True
        except Exception as e:
            logger.error(f'Failed to save player {player.id}: {e}')
            return False


def main():
    """Main entry point for the bot."""
    # Load environment variables
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise ValueError('DISCORD_TOKEN environment variable not set')
    
    # Create and run bot
    bot = OSRSBot()
    bot.run(token)


if __name__ == '__main__':
    main()
