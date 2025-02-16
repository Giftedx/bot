"""Configuration settings for Plex and Discord integration."""

import os
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings."""
    
    # Plex settings
    PLEX_URL: str = os.getenv('PLEX_URL', '')
    PLEX_TOKEN: str = os.getenv('PLEX_TOKEN', '')
    
    # Discord settings
    DISCORD_TOKEN: str = os.getenv('DISCORD_TOKEN', '')
    DISCORD_CLIENT_ID: str = os.getenv('DISCORD_CLIENT_ID', '')
    DISCORD_CLIENT_SECRET: str = os.getenv('DISCORD_CLIENT_SECRET', '')
    
    # Media settings
    MAX_BITRATE: int = int(os.getenv('MAX_BITRATE', '2000'))  # kbps
    TRANSCODE_QUALITY: str = os.getenv('TRANSCODE_QUALITY', '1080p')
    BUFFER_SIZE: int = int(os.getenv('BUFFER_SIZE', '10'))  # seconds
    
    # Cache settings
    CACHE_DURATION: int = int(os.getenv('CACHE_DURATION', '3600'))  # seconds
    MAX_CACHE_SIZE: int = int(os.getenv('MAX_CACHE_SIZE', '100'))  # items
    
    @classmethod
    def validate(cls) -> Optional[str]:
        """Validate the configuration.
        
        Returns:
            Error message if validation fails, None otherwise.
        """
        if not cls.PLEX_URL:
            return "PLEX_URL is required"
            
        if not cls.PLEX_TOKEN:
            return "PLEX_TOKEN is required"
            
        if not cls.DISCORD_TOKEN:
            return "DISCORD_TOKEN is required"
            
        if not cls.DISCORD_CLIENT_ID:
            return "DISCORD_CLIENT_ID is required"
            
        if not cls.DISCORD_CLIENT_SECRET:
            return "DISCORD_CLIENT_SECRET is required"
            
        return None
        
    @classmethod
    def to_dict(cls) -> Dict:
        """Convert config to dictionary.
        
        Returns:
            Dict containing configuration values.
        """
        return {
            'plex': {
                'url': cls.PLEX_URL,
                'token': cls.PLEX_TOKEN
            },
            'discord': {
                'token': cls.DISCORD_TOKEN,
                'client_id': cls.DISCORD_CLIENT_ID,
                'client_secret': cls.DISCORD_CLIENT_SECRET
            },
            'media': {
                'max_bitrate': cls.MAX_BITRATE,
                'transcode_quality': cls.TRANSCODE_QUALITY,
                'buffer_size': cls.BUFFER_SIZE
            },
            'cache': {
                'duration': cls.CACHE_DURATION,
                'max_size': cls.MAX_CACHE_SIZE
            }
        } 