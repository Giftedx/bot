"""Configuration management for the bot."""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class Config:
    """Bot configuration."""
    
    # Discord settings
    DISCORD_TOKEN: str
    COMMAND_PREFIX: str = "!"
    BOT_DESCRIPTION: str = "Discord Bot"
    
    # Plex settings
    PLEX_URL: str
    PLEX_TOKEN: str
    PLEX_LIBRARIES: List[str] = None
    
    # Media settings
    MAX_SEARCH_RESULTS: int = 10
    DEFAULT_VOLUME: int = 100
    STREAM_QUALITY: str = "Original"
    
    # Voice settings
    VOICE_TIMEOUT: int = 300  # 5 minutes
    AUTO_DISCONNECT: bool = True
    
    # Performance settings
    COMMAND_RATE_LIMIT: int = 5
    COMMAND_COOLDOWN: float = 3.0
    MAX_CONCURRENT_STREAMS: int = 3
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "bot.log"
    ENABLE_DEBUG: bool = False
    
    # Metrics settings
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Enabled extensions/cogs
    ENABLED_EXTENSIONS: List[str] = field(default_factory=lambda: [
        "base",
        "combat_commands",
        "economy_commands",
        "item_commands",
        "quest_commands",
        "skills_commands"
    ])self.config.ENABLED_EXTENSIONS
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        required = {
            "DISCORD_TOKEN": os.getenv("DISCORD_TOKEN"),
            "PLEX_URL": os.getenv("PLEX_URL"),
            "PLEX_TOKEN": os.getenv("PLEX_TOKEN")
        }
        
        # Check for missing required values
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
            
        # Create instance with required values
        config = cls(**required)
        
        # Update optional values from environment
        for field in cls.__dataclass_fields__:
            if field not in required and (value := os.getenv(field)):
                setattr(config, field, value)
                
        return config
    
    def validate(self) -> None:
        """Validate configuration values."""
        if not self.DISCORD_TOKEN:
            raise ValueError("Discord token is required")
            
        if not self.ENABLED_EXTENSIONS:
            raise ValueError("At least one extension must be enabled")
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
        }
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return getattr(self, key, default)
        
    def update(self, **kwargs: Any) -> None:
        """Update configuration values."""
        for key, value in kwargs.items():
            if key in self.__dataclass_fields__:
                setattr(self, key, value)
