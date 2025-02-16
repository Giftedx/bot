"""Configuration management for the bot."""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class PlexConfig:
    """Plex configuration settings."""
    url: str = os.getenv('PLEX_URL', '')
    token: str = os.getenv('PLEX_TOKEN', '')
    client_id: str = os.getenv('PLEX_CLIENT_ID', 'discord-plex-player')
    device_name: str = os.getenv('PLEX_DEVICE_NAME', 'Discord Player')
    
    def validate(self) -> None:
        """Validate Plex configuration."""
        if not self.url:
            raise ValueError("PLEX_URL is required")
        if not self.token:
            raise ValueError("PLEX_TOKEN is required")

@dataclass
class DiscordConfig:
    """Discord configuration settings."""
    token: str = os.getenv('DISCORD_TOKEN', '')
    client_id: str = os.getenv('DISCORD_CLIENT_ID', '')
    client_secret: str = os.getenv('DISCORD_CLIENT_SECRET', '')
    redirect_uri: str = os.getenv('DISCORD_REDIRECT_URI', 'http://localhost:5000/auth/callback')
    
    def validate(self) -> None:
        """Validate Discord configuration."""
        if not self.token:
            raise ValueError("DISCORD_TOKEN is required")
        if not self.client_id:
            raise ValueError("DISCORD_CLIENT_ID is required")
        if not self.client_secret:
            raise ValueError("DISCORD_CLIENT_SECRET is required")

@dataclass
class RedisConfig:
    """Redis configuration settings."""
    host: str = os.getenv('REDIS_HOST', 'localhost')
    port: int = int(os.getenv('REDIS_PORT', '6379'))
    db: int = int(os.getenv('REDIS_DB', '0'))
    password: Optional[str] = os.getenv('REDIS_PASSWORD')

@dataclass
class WebConfig:
    """Web server configuration settings."""
    host: str = os.getenv('WEB_HOST', 'localhost')
    port: int = int(os.getenv('WEB_PORT', '5000'))
    debug: bool = os.getenv('WEB_DEBUG', 'false').lower() == 'true'
    secret_key: str = os.getenv('WEB_SECRET_KEY', 'your-secret-key')
    cors_origins: list = os.getenv('CORS_ORIGINS', '*').split(',')

@dataclass
class Config:
    """Application configuration."""
    plex: PlexConfig = PlexConfig()
    discord: DiscordConfig = DiscordConfig()
    redis: RedisConfig = RedisConfig()
    web: WebConfig = WebConfig()
    
    def validate(self) -> None:
        """Validate all configuration settings."""
        self.plex.validate()
        self.discord.validate()

def load_config() -> Config:
    """Load and validate configuration."""
    config = Config()
    config.validate()
    return config

class ConfigManager:
    """Manages configuration settings and secrets"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_path = self.config_dir / "config.json"
        self.secrets_path = self.config_dir / "secrets.json"
        
        # Default configuration
        self.default_config = {
            'bot': {
                'command_prefix': '!',
                'description': 'Personal content and cross-game features bot',
                'status_message': 'Watching for roastable moments',
                'roast_cooldown_minutes': 5,
                'roast_min_score': 0.7,
                'roast_chance': 0.3
            },
            'channels': {
                'event_channel_id': None,
                'roast_channel_ids': [],
                'watch_party_channel_id': None,
                'pet_channel_id': None
            },
            'database': {
                'path': 'data/bot.db',
                'backup_interval_hours': 24,
                'max_backups': 7
            },
            'events': {
                'check_interval_minutes': 1,
                'cleanup_interval_minutes': 5,
                'roast_interval_minutes': 15
            },
            'pets': {
                'max_pets': 10,
                'interaction_cooldown_minutes': 30,
                'happiness_decay_rate': 0.1,
                'experience_multiplier': 1.0
            },
            'watch_parties': {
                'max_members': 10,
                'auto_end_minutes': 360,
                'min_duration_minutes': 15
            },
            'effects': {
                'max_active': 5,
                'stack_limit': 3,
                'default_duration_minutes': 60
            },
            'easter_eggs': {
                'trigger_chance': 0.1,
                'rare_event_chance': 0.01,
                'special_date_multiplier': 2.0
            }
        }
        
        # Default secrets structure (values should be loaded from environment or secrets file)
        self.default_secrets = {
            'discord': {
                'token': None,
                'client_id': None,
                'client_secret': None
            },
            'plex': {
                'server_url': None,
                'token': None
            },
            'api_keys': {
                'openai': None,
                'weather': None
            }
        }
        
        # Load configuration
        self.config = self.load_config()
        self.secrets = self.load_secrets()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    loaded_config = json.load(f)
                # Merge with defaults to ensure all keys exist
                return self.merge_configs(self.default_config, loaded_config)
            else:
                # Save and return defaults
                self.save_config(self.default_config)
                return self.default_config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self.default_config
    
    def load_secrets(self) -> Dict[str, Any]:
        """Load secrets from environment or file"""
        secrets = self.default_secrets.copy()
        
        # Try to load from environment first
        secrets['discord']['token'] = os.getenv('DISCORD_TOKEN')
        secrets['discord']['client_id'] = os.getenv('DISCORD_CLIENT_ID')
        secrets['discord']['client_secret'] = os.getenv('DISCORD_CLIENT_SECRET')
        secrets['plex']['server_url'] = os.getenv('PLEX_SERVER_URL')
        secrets['plex']['token'] = os.getenv('PLEX_TOKEN')
        secrets['api_keys']['openai'] = os.getenv('OPENAI_API_KEY')
        secrets['api_keys']['weather'] = os.getenv('WEATHER_API_KEY')
        
        # If any secrets are missing, try to load from file
        if any(v is None for v in self.flatten_dict(secrets).values()):
            try:
                if self.secrets_path.exists():
                    with open(self.secrets_path) as f:
                        file_secrets = json.load(f)
                    secrets = self.merge_configs(secrets, file_secrets)
            except Exception as e:
                logger.error(f"Error loading secrets: {e}")
        
        return secrets
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def save_secrets(self, secrets: Dict[str, Any]) -> None:
        """Save secrets to file"""
        try:
            with open(self.secrets_path, 'w') as f:
                json.dump(secrets, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving secrets: {e}")
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values"""
        self.config = self.merge_configs(self.config, updates)
        self.save_config(self.config)
    
    def update_secrets(self, updates: Dict[str, Any]) -> None:
        """Update secrets with new values"""
        self.secrets = self.merge_configs(self.secrets, updates)
        self.save_secrets(self.secrets)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key path"""
        return self.get_nested_value(self.config, key.split('.'), default)
    
    def get_secret(self, key: str, default: Any = None) -> Any:
        """Get secret value by key path"""
        return self.get_nested_value(self.secrets, key.split('.'), default)
    
    @staticmethod
    def merge_configs(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two configurations"""
        merged = base.copy()
        
        for key, value in update.items():
            if (
                key in merged and 
                isinstance(merged[key], dict) and 
                isinstance(value, dict)
            ):
                merged[key] = ConfigManager.merge_configs(merged[key], value)
            else:
                merged[key] = value
                
        return merged
    
    @staticmethod
    def get_nested_value(data: Dict[str, Any], key_path: list, default: Any = None) -> Any:
        """Get value from nested dictionary using key path"""
        current = data
        
        for key in key_path:
            if isinstance(current, dict):
                current = current.get(key)
                if current is None:
                    return default
            else:
                return default
                
        return current
    
    @staticmethod
    def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary"""
        items = []
        
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(
                    ConfigManager.flatten_dict(v, new_key, sep=sep).items()
                )
            else:
                items.append((new_key, v))
                
        return dict(items)
    
    def validate_config(self) -> bool:
        """Validate configuration values"""
        try:
            # Check required channels
            if not self.get_config('channels.event_channel_id'):
                logger.warning("Event channel ID not configured")
            
            if not self.get_config('channels.roast_channel_ids'):
                logger.warning("No roast channels configured")
            
            # Check database settings
            db_path = Path(self.get_config('database.path'))
            if not db_path.parent.exists():
                logger.warning(f"Database directory {db_path.parent} does not exist")
            
            # Check numeric ranges
            if not (0 < self.get_config('bot.roast_chance') <= 1):
                logger.error("Roast chance must be between 0 and 1")
                return False
            
            if self.get_config('pets.max_pets') < 1:
                logger.error("Max pets must be at least 1")
                return False
            
            if self.get_config('effects.max_active') < 1:
                logger.error("Max active effects must be at least 1")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Config validation error: {e}")
            return False
    
    def validate_secrets(self) -> bool:
        """Validate secret values"""
        try:
            # Check required secrets
            if not self.get_secret('discord.token'):
                logger.error("Discord token not configured")
                return False
            
            if not self.get_secret('discord.client_id'):
                logger.warning("Discord client ID not configured")
            
            if not self.get_secret('plex.server_url') or not self.get_secret('plex.token'):
                logger.warning("Plex integration not fully configured")
            
            if not self.get_secret('api_keys.openai'):
                logger.warning("OpenAI API key not configured")
            
            return True
        except Exception as e:
            logger.error(f"Secrets validation error: {e}")
            return False
    
    def backup_config(self) -> None:
        """Create backup of current configuration"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = self.config_dir / 'backups'
            backup_dir.mkdir(exist_ok=True)
            
            # Backup config
            if self.config_path.exists():
                backup_path = backup_dir / f"config_{timestamp}.json"
                with open(self.config_path) as f:
                    config_data = json.load(f)
                with open(backup_path, 'w') as f:
                    json.dump(config_data, f, indent=4)
            
            # Backup secrets
            if self.secrets_path.exists():
                backup_path = backup_dir / f"secrets_{timestamp}.json"
                with open(self.secrets_path) as f:
                    secrets_data = json.load(f)
                with open(backup_path, 'w') as f:
                    json.dump(secrets_data, f, indent=4)
            
            # Clean up old backups
            max_backups = self.get_config('database.max_backups', 7)
            config_backups = sorted(backup_dir.glob('config_*.json'))
            secrets_backups = sorted(backup_dir.glob('secrets_*.json'))
            
            while len(config_backups) > max_backups:
                config_backups[0].unlink()
                config_backups = config_backups[1:]
            
            while len(secrets_backups) > max_backups:
                secrets_backups[0].unlink()
                secrets_backups = secrets_backups[1:]
                
        except Exception as e:
            logger.error(f"Error backing up config: {e}")
    
    def get_backup_list(self) -> Dict[str, list]:
        """Get list of available backups"""
        try:
            backup_dir = self.config_dir / 'backups'
            if not backup_dir.exists():
                return {'config': [], 'secrets': []}
            
            return {
                'config': sorted(str(p) for p in backup_dir.glob('config_*.json')),
                'secrets': sorted(str(p) for p in backup_dir.glob('secrets_*.json'))
            }
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return {'config': [], 'secrets': []}
