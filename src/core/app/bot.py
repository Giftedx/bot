"""Main Discord bot implementation."""

import os
import discord
from discord.ext import commands
import logging
import asyncio
from typing import Dict, Optional

from src.osrs.core.combat.combat_manager import CombatManager
from src.osrs.core.combat.monster_manager import MonsterManager
from src.osrs.core.player_stats import PlayerStats, PlayerStatsManager
from src.osrs.database.database_manager import DatabaseManager

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
        
        # Initialize managers
        self.db = DatabaseManager()
        self.combat_manager = CombatManager()
        self.monster_manager = MonsterManager()
        self.stats_manager = PlayerStatsManager()
        
        # Cache for player data
        self.players: Dict[int, PlayerStats] = {}
        
        # Load cogs
        self.initial_extensions = [
            'src.cogs.combat_commands',
            'src.cogs.stats_commands',
            'src.cogs.help_commands'
        ]
    
    async def setup_hook(self):
        """Set up the bot before it starts running."""
        # Load monster data
        await self.monster_manager.load_monsters()
        logger.info('Monster data loaded successfully')
        
        # Load extensions
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
        
        # Set up activity
        activity = discord.Game(name="OSRS | !help")
        await self.change_presence(activity=activity)
    
    async def on_message(self, message: discord.Message):
        """Handle incoming messages."""
        # Ignore messages from bots
        if message.author.bot:
            return
            
        # Create player record if it doesn't exist
        if not message.author.bot:
            self.db.create_player(
                message.author.id,
                message.author.display_name
            )
            
        await self.process_commands(message)
    
    def get_player_stats(self, user_id: int) -> Optional[PlayerStats]:
        """Get player stats from cache or database."""
        # Check cache first
        if user_id in self.players:
            return self.players[user_id]
        
        # Load from database
        stats = self.db.get_player_stats(user_id)
        if stats:
            self.players[user_id] = stats
            return stats
        
        return None
    
    async def update_player_stats(self, user_id: int, stats: PlayerStats):
        """Update player stats in cache and database."""
        self.players[user_id] = stats
        self.db.update_player_stats(user_id, stats)

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
