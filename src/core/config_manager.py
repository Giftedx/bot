from typing import Any, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import os
import logging
import json
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

@dataclass
class BotConfig:
    """Bot configuration settings"""
    COMMAND_PREFIX: str = "!"
    MAX_CONCURRENT_COMMANDS: int = 10
    MAX_QUEUE_SIZE: int = 100
    HEALTH_CHECK_INTERVAL: float = 60.0
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: float = 60.0
    MAX_CONCURRENT_STREAMS: int = 5
    COMMAND_COOLDOWN: float = 3.0
    GRACEFUL_SHUTDOWN_TIMEOUT: float = 30.0
    BOT_TYPE: str = "regular"

class ConfigManager:
    """Manages bot configuration from multiple sources"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self._config = BotConfig()
        self._config_path = config_path or Path("config/bot_config.json")
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from environment and config file"""
        # Load environment variables
        load_dotenv()
        
        # Override from environment variables
        for field in BotConfig.__dataclass_fields__:
            env_value = os.getenv(field)
            if env_value is not None:
                # Convert to appropriate type
                field_type = type(getattr(self._config, field))
                try:
                    if field_type == bool:
                        value = env_value.lower() in ('true', '1', 'yes')
                    else:
                        value = field_type(env_value)
                    setattr(self._config, field, value)
                except ValueError as e:
                    logger.error(f"Failed to convert {field} value: {e}")

        # Load from config file if it exists
        if self._config_path.exists():
            try:
                with open(self._config_path) as f:
                    file_config = json.load(f)
                    for key, value in file_config.items():
                        if hasattr(self._config, key):
                            setattr(self._config, key, value)
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return getattr(self._config, key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        if hasattr(self._config, key):
            setattr(self._config, key, value)
        else:
            raise ValueError(f"Invalid configuration key: {key}")

    def save(self) -> None:
        """Save current configuration to file"""
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, 'w') as f:
                json.dump(self._config.__dict__, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return self._config.__dict__.copy()