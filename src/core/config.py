"""Configuration settings module."""
from typing import Any, List, Optional, Dict
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central configuration management for the application."""
    
    def __init__(self) -> None:
        """Initialize settings with environment variables."""
        self._config: Dict[str, Any] = {
            "BOT_TYPE": os.getenv("BOT_TYPE", "regular"),
            "DISCORD_TOKEN": os.getenv("DISCORD_TOKEN"),
            "PLEX_TOKEN": os.getenv("PLEX_TOKEN"),
            "PLEX_URL": os.getenv("PLEX_URL"),
            "COMMAND_PREFIX": os.getenv("COMMAND_PREFIX", "!"),
            "REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            "GRACEFUL_SHUTDOWN_TIMEOUT": float(
                os.getenv("GRACEFUL_SHUTDOWN_TIMEOUT", "30.0")
            ),
            "HEALTH_CHECK_INTERVAL": float(
                os.getenv("HEALTH_CHECK_INTERVAL", "60.0")
            ),
            "COMMAND_COOLDOWN": float(
                os.getenv("COMMAND_COOLDOWN", "3.0")
            ),
            "MAX_CONCURRENT_STREAMS": int(
                os.getenv("MAX_CONCURRENT_STREAMS", "5")
            ),
            "PLEX_MAX_RETRIES": int(
                os.getenv("PLEX_MAX_RETRIES", "3")
            ),
            "PLEX_RETRY_DELAY": float(
                os.getenv("PLEX_RETRY_DELAY", "1.0")
            )
        }

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Retrieve configuration value with optional default."""
        return self._config.get(key, default)

    def get_str(self, key: str, default: str = "") -> str:
        """
        Type-safe string retrieval.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            str: Configuration value
            
        Raises:
            ValueError: If value cannot be converted to string
        """
        value = self.get(key, default)
        if value is None:
            return default
        return str(value)

    def get_int(self, key: str, default: Optional[int] = None) -> int:
        """
        Type-safe integer retrieval.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            int: Configuration value
            
        Raises:
            ValueError: If value cannot be converted to integer
        """
        value = self.get(key, default)
        if value is None:
            raise ValueError(f"No value or default for {key}")
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(
                f"Value for {key} cannot be converted to integer: {value}"
            )

    def get_bool(self, key: str, default: Optional[bool] = None) -> bool:
        """
        Type-safe boolean retrieval.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            bool: Configuration value
            
        Raises:
            ValueError: If value cannot be converted to boolean
        """
        value = self.get(key, default)
        if value is None:
            raise ValueError(f"No value or default for {key}")
            
        if isinstance(value, bool):
            return value
            
        if isinstance(value, str):
            value = value.lower()
            if value in ('true', '1', 'yes', 'on'):
                return True
            if value in ('false', '0', 'no', 'off'):
                return False
                
        raise ValueError(
            f"Value for {key} cannot be converted to boolean: {value}"
        )

    def get_list(
        self,
        key: str,
        default: Optional[List[Any]] = None
    ) -> List[Any]:
        """
        Type-safe list retrieval.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            List[Any]: Configuration value
            
        Raises:
            ValueError: If value cannot be converted to list
        """
        value = self.get(key, default)
        if value is None:
            raise ValueError(f"No value or default for {key}")
            
        if isinstance(value, str):
            return [x.strip() for x in value.split(',') if x.strip()]
            
        if isinstance(value, list):
            return value
            
        raise ValueError(
            f"Value for {key} cannot be converted to list: {value}"
        )
    
    def __getattr__(self, name: str) -> Any:
        """Allow attribute-style access to config values."""
        if name in self._config:
            return self._config[name]
        raise AttributeError(f"'Settings' object has no attribute '{name}'")
