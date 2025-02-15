"""Bot configuration settings."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Bot configuration settings"""
    # Discord settings
    DISCORD_TOKEN: str = os.getenv('DISCORD_TOKEN', '')
    DISCORD_TEXT_CHANNEL_ID: int = int(
        os.getenv('DISCORD_TEXT_CHANNEL_ID', '0')
    )
    
    # Plex settings
    PLEX_URL: Optional[str] = os.getenv('PLEX_URL')
    PLEX_TOKEN: Optional[str] = os.getenv('PLEX_TOKEN')
    PLEX_MOVIE_LIBRARY_NAME: Optional[str] = os.getenv(
        'PLEX_MOVIE_LIBRARY_NAME'
    )
    PLEX_TV_LIBRARY_NAME: Optional[str] = os.getenv('PLEX_TV_LIBRARY_NAME')
    PLEX_MAX_RETRIES: int = int(os.getenv('PLEX_MAX_RETRIES', '3'))
    PLEX_RETRY_DELAY: float = float(os.getenv('PLEX_RETRY_DELAY', '1.0'))
    
    # Third-party API settings
    GIPHY_API_KEY: Optional[str] = os.getenv('GIPHY_API_KEY')
    SPOTIFY_CLIENT_ID: Optional[str] = os.getenv('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET: Optional[str] = os.getenv('SPOTIFY_CLIENT_SECRET')


# Create singleton instance
settings = Settings()