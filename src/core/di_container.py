from dependency_injector import containers, providers
from src.services.plex.plex_service import PlexService
from src.bot.discord.core.bot import Bot
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
    settings = providers.Configuration()
    redis_service = providers.Singleton(RedisService)
    discord_service = providers.Singleton(DiscordService)
    plex_service = providers.Singleton(
        PlexService,
        config=settings
    )
    bot = providers.Singleton(
Bot,
 
        Bot,
        config=settings
    )