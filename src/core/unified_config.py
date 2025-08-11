"""Unified configuration management system for the Discord bot.

This module provides a comprehensive configuration management system that combines
environment variables, configuration files, secrets management, and feature flags
into a single, robust interface.
"""

import os
import logging
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, TypeVar, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
from contextlib import contextmanager

try:
    import hvac

    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False
    hvac = None

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ConfigFormat(Enum):
    """Supported configuration file formats."""

    JSON = "json"
    YAML = "yaml"
    YML = "yml"


class SecretProvider(Enum):
    """Supported secret providers."""

    ENVIRONMENT = "environment"
    FILE = "file"
    VAULT = "vault"


@dataclass
class ConfigSchema:
    """Schema definition for configuration validation."""

    required_fields: Set[str] = field(default_factory=set)
    optional_fields: Set[str] = field(default_factory=set)
    field_types: Dict[str, type] = field(default_factory=dict)
    validators: Dict[str, callable] = field(default_factory=dict)


@dataclass
class SecretConfig:
    """Configuration for secret management."""

    providers: List[SecretProvider] = field(
        default_factory=lambda: [
            SecretProvider.ENVIRONMENT,
            SecretProvider.FILE,
            SecretProvider.VAULT,
        ]
    )
    vault_url: Optional[str] = None
    vault_token: Optional[str] = None
    vault_path: str = "secret/discord-bot"
    secrets_file: Optional[Path] = None
    encryption_key: Optional[str] = None


@dataclass
class UnifiedConfigSettings:
    """Settings for the unified configuration system."""

    config_dir: Path = Path("config")
    config_file: str = "config"
    secrets_file: str = "secrets"
    format: ConfigFormat = ConfigFormat.YAML
    env_file: Optional[Path] = None
    auto_reload: bool = False
    reload_interval: int = 300  # seconds
    backup_configs: bool = True
    max_backups: int = 5
    validate_on_load: bool = True
    secret_config: SecretConfig = field(default_factory=SecretConfig)


class ConfigurationError(Exception):
    """Raised when configuration operations fail."""

    pass


class ValidationError(ConfigurationError):
    """Raised when configuration validation fails."""

    pass


class SecretManager:
    """Manages secrets from multiple providers."""

    def __init__(self, config: SecretConfig):
        self.config = config
        self._vault_client = None
        self._init_vault()

    def _init_vault(self) -> None:
        """Initialize Vault client if available and configured."""
        if not VAULT_AVAILABLE:
            logger.warning("Vault support not available (hvac not installed)")
            return

        vault_url = self.config.vault_url or os.getenv("VAULT_ADDR")
        vault_token = self.config.vault_token or os.getenv("VAULT_TOKEN")

        if vault_url and vault_token:
            try:
                self._vault_client = hvac.Client(url=vault_url, token=vault_token)
                if not self._vault_client.is_authenticated():
                    logger.warning("Vault authentication failed")
                    self._vault_client = None
                else:
                    logger.info("Vault client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Vault client: {e}")
                self._vault_client = None

    def get_secret(self, key: str, default: Any = None) -> Any:
        """Get a secret value from the configured providers."""
        for provider in self.config.providers:
            try:
                value = self._get_from_provider(provider, key)
                if value is not None:
                    return value
            except Exception as e:
                logger.debug(f"Failed to get secret '{key}' from {provider.value}: {e}")
                continue

        return default

    def _get_from_provider(self, provider: SecretProvider, key: str) -> Optional[Any]:
        """Get secret from a specific provider."""
        if provider == SecretProvider.ENVIRONMENT:
            return os.getenv(key)
        elif provider == SecretProvider.FILE:
            return self._get_from_file(key)
        elif provider == SecretProvider.VAULT:
            return self._get_from_vault(key)

        return None

    def _get_from_file(self, key: str) -> Optional[Any]:
        """Get secret from file."""
        if not self.config.secrets_file or not self.config.secrets_file.exists():
            return None

        try:
            with open(self.config.secrets_file, "r") as f:
                if self.config.secrets_file.suffix in [".yaml", ".yml"]:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)

            # Support nested keys like "discord.token"
            keys = key.split(".")
            current = data
            for k in keys:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    return None

            return current
        except Exception as e:
            logger.error(f"Error reading secrets from file: {e}")
            return None

    def _get_from_vault(self, key: str) -> Optional[Any]:
        """Get secret from Vault."""
        if not self._vault_client:
            return None

        try:
            # Convert key to Vault path and field
            if "." in key:
                parts = key.split(".")
                vault_path = f"{self.config.vault_path}/{parts[0]}"
                field_name = parts[1]
            else:
                vault_path = f"{self.config.vault_path}/app"
                field_name = key

            response = self._vault_client.secrets.kv.read_secret_version(
                path=vault_path.replace(f"{self.config.vault_path}/", "")
            )
            return response["data"]["data"].get(field_name)
        except Exception as e:
            logger.debug(f"Error reading secret from Vault: {e}")
            return None


class FeatureFlags:
    """Manages feature flags and toggles."""

    def __init__(self):
        self._flags: Dict[str, bool] = {}
        self._load_default_flags()

    def _load_default_flags(self) -> None:
        """Load default feature flags."""
        self._flags.update(
            {
                "enable_metrics": True,
                "enable_caching": True,
                "enable_debug_mode": False,
                "enable_auto_backup": True,
                "enable_error_reporting": True,
                "enable_performance_monitoring": True,
                "enable_experimental_features": False,
            }
        )

    def is_enabled(self, flag: str, default: bool = False) -> bool:
        """Check if a feature flag is enabled."""
        return self._flags.get(flag, default)

    def set_flag(self, flag: str, enabled: bool) -> None:
        """Set a feature flag."""
        self._flags[flag] = enabled
        logger.debug(f"Feature flag '{flag}' set to {enabled}")

    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags."""
        return self._flags.copy()

    def load_from_dict(self, flags: Dict[str, bool]) -> None:
        """Load feature flags from a dictionary."""
        self._flags.update(flags)


class UnifiedConfig:
    """Unified configuration management system."""

    def __init__(self, settings: Optional[UnifiedConfigSettings] = None):
        """Initialize the unified configuration system."""
        self.settings = settings or UnifiedConfigSettings()
        self._config: Dict[str, Any] = {}
        self._schema: Optional[ConfigSchema] = None
        self._last_loaded: Optional[datetime] = None
        self._file_hashes: Dict[str, str] = {}

        # Initialize subsystems
        self.secret_manager = SecretManager(self.settings.secret_config)
        self.feature_flags = FeatureFlags()

        # Ensure directories exist
        self.settings.config_dir.mkdir(parents=True, exist_ok=True)

        # Load configuration
        self._load_configuration()

        logger.info(f"UnifiedConfig initialized with config dir: {self.settings.config_dir}")

    def _load_configuration(self) -> None:
        """Load configuration from all sources."""
        try:
            # Load environment file if specified
            if self.settings.env_file and self.settings.env_file.exists():
                load_dotenv(self.settings.env_file)
                logger.debug(f"Loaded environment from {self.settings.env_file}")

            # Load base configuration
            config_data = self._load_config_files()

            # Override with environment variables
            env_overrides = self._load_environment_overrides()
            config_data = self._deep_merge(config_data, env_overrides)

            # Load feature flags
            if "feature_flags" in config_data:
                self.feature_flags.load_from_dict(config_data["feature_flags"])

            # Store configuration
            self._config = config_data
            self._last_loaded = datetime.now()

            # Validate if enabled
            if self.settings.validate_on_load and self._schema:
                self._validate_config()

            logger.info("Configuration loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Configuration loading failed: {e}")

    def _load_config_files(self) -> Dict[str, Any]:
        """Load configuration from files."""
        config_data = {}

        # Define possible config files
        config_files = [
            self.settings.config_dir / f"{self.settings.config_file}.{self.settings.format.value}",
            self.settings.config_dir / f"{self.settings.config_file}.json",
            self.settings.config_dir / f"{self.settings.config_file}.yaml",
            self.settings.config_dir / f"{self.settings.config_file}.yml",
        ]

        for config_file in config_files:
            if config_file.exists():
                file_data = self._load_file(config_file)
                if file_data:
                    config_data = self._deep_merge(config_data, file_data)
                    logger.debug(f"Loaded config from {config_file}")
                break

        return config_data

    def _load_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load data from a configuration file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Calculate file hash for change detection
            file_hash = hashlib.md5(content.encode()).hexdigest()
            self._file_hashes[str(file_path)] = file_hash

            # Parse based on file extension
            if file_path.suffix in [".yaml", ".yml"]:
                return yaml.safe_load(content)
            elif file_path.suffix == ".json":
                return json.loads(content)
            else:
                logger.warning(f"Unsupported config file format: {file_path}")
                return None

        except Exception as e:
            logger.error(f"Error loading config file {file_path}: {e}")
            return None

    def _load_environment_overrides(self) -> Dict[str, Any]:
        """Load configuration overrides from environment variables."""
        overrides = {}

        # Define environment variable mappings
        env_mappings = {
            "DISCORD_TOKEN": "discord.token",
            "DISCORD_CLIENT_ID": "discord.client_id",
            "DISCORD_CLIENT_SECRET": "discord.client_secret",
            "PLEX_URL": "plex.url",
            "PLEX_TOKEN": "plex.token",
            "REDIS_URL": "redis.url",
            "DATABASE_URL": "database.url",
            "LOG_LEVEL": "logging.level",
            "DEBUG": "debug",
            "ENVIRONMENT": "environment",
        }

        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_value(overrides, config_key.split("."), value)

        return overrides

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _set_nested_value(self, data: Dict[str, Any], keys: List[str], value: Any) -> None:
        """Set a nested value in a dictionary."""
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    def _get_nested_value(self, data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
        """Get a nested value from a dictionary."""
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        # Check secrets first for sensitive data
        secret_keys = {"token", "password", "secret", "key", "api_key"}
        if any(secret_word in key.lower() for secret_word in secret_keys):
            secret_value = self.secret_manager.get_secret(key)
            if secret_value is not None:
                return secret_value

        # Get from regular config
        keys = key.split(".")
        return self._get_nested_value(self._config, keys, default)

    def set(self, key: str, value: Any, persist: bool = False) -> None:
        """Set a configuration value."""
        keys = key.split(".")
        self._set_nested_value(self._config, keys, value)

        if persist:
            self._save_config()

    def has(self, key: str) -> bool:
        """Check if a configuration key exists."""
        return self.get(key) is not None

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire configuration section."""
        return self.get(section, {})

    def register_schema(self, schema: ConfigSchema) -> None:
        """Register a configuration schema for validation."""
        self._schema = schema
        if self.settings.validate_on_load:
            self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration against the registered schema."""
        if not self._schema:
            return

        errors = []

        # Check required fields
        for field in self._schema.required_fields:
            if not self.has(field):
                errors.append(f"Required field '{field}' is missing")

        # Check field types
        for field, expected_type in self._schema.field_types.items():
            value = self.get(field)
            if value is not None and not isinstance(value, expected_type):
                errors.append(
                    f"Field '{field}' has invalid type: expected {expected_type}, got {type(value)}"
                )

        # Run custom validators
        for field, validator in self._schema.validators.items():
            value = self.get(field)
            if value is not None:
                try:
                    if not validator(value):
                        errors.append(f"Field '{field}' failed validation")
                except Exception as e:
                    errors.append(f"Validator for field '{field}' raised exception: {e}")

        if errors:
            raise ValidationError(f"Configuration validation failed: {'; '.join(errors)}")

    def _save_config(self) -> None:
        """Save configuration to file."""
        config_file = (
            self.settings.config_dir / f"{self.settings.config_file}.{self.settings.format.value}"
        )

        try:
            # Create backup if enabled
            if self.settings.backup_configs and config_file.exists():
                self._create_backup(config_file)

            # Save configuration
            with open(config_file, "w", encoding="utf-8") as f:
                if self.settings.format in [ConfigFormat.YAML, ConfigFormat.YML]:
                    yaml.safe_dump(self._config, f, indent=2, default_flow_style=False)
                else:
                    json.dump(self._config, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuration saved to {config_file}")

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise ConfigurationError(f"Failed to save configuration: {e}")

    def _create_backup(self, config_file: Path) -> None:
        """Create a backup of the configuration file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = (
            config_file.parent / f"{config_file.stem}_backup_{timestamp}{config_file.suffix}"
        )

        try:
            backup_file.write_text(config_file.read_text())

            # Clean old backups
            backup_pattern = f"{config_file.stem}_backup_*{config_file.suffix}"
            backups = list(config_file.parent.glob(backup_pattern))
            backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            for old_backup in backups[self.settings.max_backups :]:
                old_backup.unlink()
                logger.debug(f"Removed old backup: {old_backup}")

        except Exception as e:
            logger.warning(f"Failed to create configuration backup: {e}")

    def reload(self, force: bool = False) -> bool:
        """Reload configuration from sources."""
        if not force and not self._should_reload():
            return False

        try:
            self._load_configuration()
            logger.info("Configuration reloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False

    def _should_reload(self) -> bool:
        """Check if configuration should be reloaded."""
        if not self.settings.auto_reload:
            return False

        if not self._last_loaded:
            return True

        # Check time interval
        elapsed = (datetime.now() - self._last_loaded).total_seconds()
        if elapsed < self.settings.reload_interval:
            return False

        # Check file changes
        for file_path, stored_hash in self._file_hashes.items():
            path = Path(file_path)
            if path.exists():
                current_hash = hashlib.md5(path.read_bytes()).hexdigest()
                if current_hash != stored_hash:
                    return True

        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get configuration system statistics."""
        return {
            "config_dir": str(self.settings.config_dir),
            "format": self.settings.format.value,
            "last_loaded": self._last_loaded.isoformat() if self._last_loaded else None,
            "auto_reload": self.settings.auto_reload,
            "validation_enabled": self.settings.validate_on_load,
            "has_schema": self._schema is not None,
            "vault_available": VAULT_AVAILABLE and self.secret_manager._vault_client is not None,
            "config_keys_count": len(self._flatten_dict(self._config)),
            "feature_flags_count": len(self.feature_flags.get_all_flags()),
        }

    def _flatten_dict(
        self, d: Dict[str, Any], parent_key: str = "", sep: str = "."
    ) -> Dict[str, Any]:
        """Flatten a nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    @contextmanager
    def temporary_config(self, overrides: Dict[str, Any]):
        """Context manager for temporary configuration overrides."""
        original_values = {}

        # Store original values
        for key in overrides:
            original_values[key] = self.get(key)

        # Apply overrides
        for key, value in overrides.items():
            self.set(key, value)

        try:
            yield self
        finally:
            # Restore original values
            for key, value in original_values.items():
                if value is not None:
                    self.set(key, value)
                else:
                    # Remove the key if it didn't exist originally
                    keys = key.split(".")
                    current = self._config
                    for k in keys[:-1]:
                        if k in current:
                            current = current[k]
                        else:
                            break
                    else:
                        current.pop(keys[-1], None)


# Global configuration instance
_global_config: Optional[UnifiedConfig] = None


def get_config() -> UnifiedConfig:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = UnifiedConfig()
    return _global_config


def init_config(settings: Optional[UnifiedConfigSettings] = None) -> UnifiedConfig:
    """Initialize the global configuration instance."""
    global _global_config
    _global_config = UnifiedConfig(settings)
    return _global_config
