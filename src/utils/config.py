"""Configuration management for the application."""
from typing import Any, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import os
import json
from dotenv import load_dotenv
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class AppConfig:
    """Application configuration settings."""

    # GitHub settings
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_API_URL: str = "https://api.github.com"
    GITHUB_RATE_LIMIT_PAUSE: float = 1.0

    # Repository settings
    REPO_DATA_DIR: Path = Path("src/data")
    REPO_FILE: str = "repositories.yaml"

    # Search settings
    DEFAULT_SEARCH_LIMIT: int = 100
    CACHE_EXPIRY: int = 3600

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[Path] = Path("logs/app.log")
    LOG_FORMAT: str = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    # Metrics settings
    METRICS_PORT: int = 8000
    ENABLE_METRICS: bool = True

    # Cache settings
    ENABLE_CACHE: bool = True
    CACHE_DIR: Path = Path("cache")
    MAX_CACHE_SIZE: int = 1000

    # Performance settings
    MAX_WORKERS: int = 4
    REQUEST_TIMEOUT: float = 30.0
    BATCH_SIZE: int = 50


class ConfigManager:
    """Manages application configuration from multiple sources."""

    def __init__(self, config_file: Optional[Path] = None, env_file: Optional[Path] = None):
        self._config = AppConfig()
        self._config_file = config_file or Path("config.json")

        # Load configuration in order of precedence
        self._load_defaults()
        if env_file:
            self._load_env_file(env_file)
        self._load_environment()
        if self._config_file.exists():
            self._load_config_file()

        # Ensure required directories exist
        self._create_directories()

    def _load_defaults(self) -> None:
        """Load default configuration values."""
        # Defaults are already set in AppConfig dataclass
        pass

    def _load_env_file(self, env_file: Path) -> None:
        """Load configuration from .env file."""
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"Loaded environment from {env_file}")

    def _load_environment(self) -> None:
        """Load configuration from environment variables."""
        for field in self._config.__dataclass_fields__:
            env_value = os.getenv(field)
            if env_value is not None:
                # Convert value to appropriate type
                field_type = type(getattr(self._config, field))
                if field_type == bool:
                    value = env_value.lower() in ("true", "1", "yes")
                elif field_type == int:
                    value = int(env_value)
                elif field_type == float:
                    value = float(env_value)
                elif field_type == Path:
                    value = Path(env_value)
                else:
                    value = env_value
                setattr(self._config, field, value)

    def _load_config_file(self) -> None:
        """Load configuration from JSON file."""
        try:
            with open(self._config_file) as f:
                config_data = json.load(f)

            for key, value in config_data.items():
                if hasattr(self._config, key):
                    if isinstance(value, dict) and key.endswith("_PATH"):
                        value = Path(value)
                    setattr(self._config, key, value)

            logger.info(f"Loaded configuration from {self._config_file}")
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")

    def _create_directories(self) -> None:
        """Create required directories."""
        directories = [
            self._config.REPO_DATA_DIR,
            self._config.CACHE_DIR,
            self._config.LOG_FILE.parent if self._config.LOG_FILE else None,
        ]

        for directory in directories:
            if directory:
                directory.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return getattr(self._config, key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        if hasattr(self._config, key):
            setattr(self._config, key, value)
        else:
            raise ValueError(f"Invalid configuration key: {key}")

    def save(self) -> None:
        """Save current configuration to file."""
        try:
            config_data = {
                field: (
                    str(getattr(self._config, field))
                    if isinstance(getattr(self._config, field), Path)
                    else getattr(self._config, field)
                )
                for field in self._config.__dataclass_fields__
                if getattr(self._config, field) is not None
            }

            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_file, "w") as f:
                json.dump(config_data, f, indent=2)

            logger.info(f"Saved configuration to {self._config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return {field: getattr(self._config, field) for field in self._config.__dataclass_fields__}


# Global configuration manager instance
config = ConfigManager()
