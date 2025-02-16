"""
Discord application main entry point.
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from .client import DiscordAppClient
from .commands.plex import PlexCommands

logger = logging.getLogger(__name__)

class DiscordApp:
    """Main Discord application class."""
    
    def __init__(self):
        load_dotenv()
        
        # Required Discord application credentials
        self.app_id = os.getenv("DISCORD_APP_ID")
        self.public_key = os.getenv("DISCORD_PUBLIC_KEY")
        self.token = os.getenv("DISCORD_TOKEN")
        
        if not all([self.app_id, self.public_key, self.token]):
            raise ValueError("Missing required Discord application credentials")
            
        # Initialize client
        self.client = DiscordAppClient(self.app_id, self.public_key)
        
        # Store command handlers
        self.commands: Dict[str, Any] = {}
        
    async def initialize(self):
        """Initialize the Discord application and all commands."""
        # Initialize Plex commands if configured
        plex_url = os.getenv("PLEX_URL")
        plex_token = os.getenv("PLEX_TOKEN")
        
        if all([plex_url, plex_token]):
            plex_commands = PlexCommands(self.client.tree, plex_url, plex_token)
            await plex_commands.initialize()
            self.commands["plex"] = plex_commands
            logger.info("Initialized Plex commands")
        else:
            logger.warning("Plex configuration missing. Plex commands will not be available.")
            
        # Initialize other command modules here as needed
        
    async def cleanup(self):
        """Cleanup resources when shutting down."""
        for command_handler in self.commands.values():
            if hasattr(command_handler, "cleanup"):
                await command_handler.cleanup()
                
        await self.client.close()
        
    async def start(self):
        """Start the Discord application."""
        try:
            await self.initialize()
            await self.client.start(self.token)
        except Exception as e:
            logger.error(f"Error starting Discord application: {e}")
            await self.cleanup()
            raise
            
def run_app():
    """Run the Discord application."""
    app = DiscordApp()
    
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        logger.info("Shutting down Discord application...")
        asyncio.run(app.cleanup())
    except Exception as e:
        logger.error(f"Fatal error in Discord application: {e}")
        asyncio.run(app.cleanup())
        raise 