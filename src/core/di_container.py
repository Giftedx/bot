from dependency_injector import containers, providers
from src.services.plex.plex_service import PlexService
from src.core.plex_manager import PlexManager
from src.core.config import Settings
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


class RedisService:
    """Placeholder for Redis Service"""
    pass


class DiscordService:
    """Placeholder for Discord Service"""
    pass


class Container(containers.DeclarativeContainer):
    """Dependency Injection Container"""
    
    config = providers.Singleton(Settings)
    
    redis_service = providers.Singleton(RedisService)
    discord_service = providers.Singleton(DiscordService)
    
    plex_manager = providers.Singleton(
        PlexManager,
        url=lambda: config().get("PLEX_URL"),
        token=lambda: config().get("PLEX_TOKEN")
    )
    
    plex_service = providers.Singleton(
        PlexService,
        base_url=lambda: config().get("PLEX_URL"),
        token=lambda: config().get("PLEX_TOKEN")
    )