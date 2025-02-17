from dataclasses import dataclass
from typing import Dict, Any, Optional
import os
import json
from pathlib import Path

@dataclass
class ServiceConfig:
    """Base configuration for all services"""
    service_name: str
    version: str
    environment: str
    debug: bool = False
    log_level: str = "INFO"
    
class ConfigService:
    """Central configuration management service"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.getenv("CONFIG_PATH", "config")
        self.env = os.getenv("ENVIRONMENT", "development")
        self._config_cache: Dict[str, Any] = {}
        self._feature_flags: Dict[str, bool] = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from files and environment"""
        # Load base config
        base_config = self._load_json_config("base")
        
        # Load environment specific config
        env_config = self._load_json_config(self.env)
        
        # Merge configs
        self._config_cache = {**base_config, **env_config}
        
        # Load feature flags
        self._feature_flags = self._load_json_config("feature_flags")
    
    def _load_json_config(self, name: str) -> Dict[str, Any]:
        """Load a JSON config file"""
        config_file = Path(self.config_path) / f"{name}.json"
        if not config_file.exists():
            return {}
            
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def get_service_config(self, service_name: str) -> ServiceConfig:
        """Get configuration for a specific service"""
        service_config = self._config_cache.get(service_name, {})
        return ServiceConfig(
            service_name=service_name,
            version=service_config.get("version", "0.1.0"),
            environment=self.env,
            debug=service_config.get("debug", False),
            log_level=service_config.get("log_level", "INFO")
        )
    
    def get_feature_flag(self, flag_name: str, default: bool = False) -> bool:
        """Check if a feature flag is enabled"""
        return self._feature_flags.get(flag_name, default)
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration"""
        return {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "database": os.getenv("DB_NAME", "osrs_game"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "")
        }
    
    def get_redis_config(self) -> Dict[str, str]:
        """Get Redis configuration"""
        return {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": os.getenv("REDIS_PORT", "6379"),
            "db": os.getenv("REDIS_DB", "0"),
            "password": os.getenv("REDIS_PASSWORD", "")
        }
    
    def get_discord_config(self) -> Dict[str, str]:
        """Get Discord configuration"""
        return {
            "token": os.getenv("DISCORD_TOKEN", ""),
            "client_id": os.getenv("DISCORD_CLIENT_ID", ""),
            "client_secret": os.getenv("DISCORD_CLIENT_SECRET", ""),
            "guild_id": os.getenv("DISCORD_GUILD_ID", "")
        } 