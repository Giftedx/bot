"""Configuration management for the Discord bot."""

import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the Discord bot."""
    
    # Discord Configuration
    DISCORD_TOKEN: str = os.getenv('DISCORD_TOKEN', '')
    COMMAND_PREFIX: str = os.getenv('COMMAND_PREFIX', '!')
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # API Keys
    WEATHER_API_KEY: Optional[str] = os.getenv('WEATHER_API_KEY')
    PLEX_TOKEN: Optional[str] = os.getenv('PLEX_TOKEN')
    
    # Plex Configuration
    PLEX_URL: str = os.getenv('PLEX_URL', 'http://localhost:32400')
    
    # Lavalink Configuration
    LAVALINK_HOST: str = os.getenv('LAVALINK_HOST', 'localhost')
    LAVALINK_PORT: int = int(os.getenv('LAVALINK_PORT', '2333'))
    LAVALINK_PASSWORD: str = os.getenv('LAVALINK_PASSWORD', 'youshallnotpass')
    
    # Database Configuration
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///bot.db')
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration values."""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN must be set in environment variables")
        return True 