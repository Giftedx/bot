import asyncio
import os
from dotenv import load_dotenv
import uvicorn
import logging

from infrastructure.database.database_service import DatabaseService
from infrastructure.cache.cache_service import CacheService
from shared.config.config_service import ConfigService
from shared.logging.logging_service import LoggingService
from services.game.src.service import GameService
from services.identity.src.service import IdentityService

from .service import DiscordService
from .api import init_api, app

# Load environment variables
load_dotenv()

async def init_services():
    """Initialize all required services"""
    # Initialize config service
    config_service = ConfigService()
    
    # Initialize logging
    logging_service = LoggingService("discord", config_service.get_service_config("discord").log_level)
    logger = logging_service.logger
    
    try:
        # Initialize database service
        database_service = DatabaseService(
            db_config=config_service.get_database_config()
        )
        await database_service.initialize()
        await database_service.start()
        
        # Initialize cache service
        cache_service = CacheService(
            redis_config=config_service.get_redis_config()
        )
        await cache_service.initialize()
        await cache_service.start()
        
        # Initialize game service
        game_service = GameService(
            database_service=database_service,
            cache_service=cache_service
        )
        await game_service.initialize()
        await game_service.start()
        
        # Initialize identity service
        identity_service = IdentityService(
            database_service=database_service,
            cache_service=cache_service
        )
        await identity_service.initialize()
        await identity_service.start()
        
        # Get Discord configuration
        discord_config = config_service.get_service_config("discord")
        
        # Initialize Discord service
        discord_service = DiscordService(
            database_service=database_service,
            cache_service=cache_service,
            game_service=game_service,
            identity_service=identity_service,
            token=discord_config.bot_token,
            guild_ids=discord_config.guild_ids
        )
        await discord_service.initialize()
        await discord_service.start()
        
        # Initialize API
        init_api(discord_service, discord_config.public_key)
        
        logger.info("All services initialized successfully")
        return (
            discord_service,
            game_service,
            identity_service,
            database_service,
            cache_service
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

async def cleanup_services(services):
    """Cleanup all services"""
    (
        discord_service,
        game_service,
        identity_service,
        database_service,
        cache_service
    ) = services
    
    try:
        await discord_service.cleanup()
        await game_service.cleanup()
        await identity_service.cleanup()
        await database_service.cleanup()
        await cache_service.cleanup()
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")

def main():
    """Main application entry point"""
    # Initialize logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize services
        services = asyncio.run(init_services())
        
        # Start FastAPI application
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8002"))  # Different port from other services
        
        logger.info(f"Starting Discord service on {host}:{port}")
        
        # Add cleanup handler
        async def cleanup():
            await cleanup_services(services)
            
        app.on_event("shutdown")(cleanup)
        
        # Run the application
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"Application failed: {e}")
        raise

if __name__ == "__main__":
    main() 