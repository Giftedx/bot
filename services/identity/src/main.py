import asyncio
import os
from dotenv import load_dotenv
import uvicorn
import logging

from shared.security.security_service import SecurityService
from infrastructure.database.database_service import DatabaseService
from infrastructure.cache.cache_service import CacheService
from shared.config.config_service import ConfigService
from shared.logging.logging_service import LoggingService

from .service import IdentityService
from .api import init_api, app

# Load environment variables
load_dotenv()

async def init_services():
    """Initialize all required services"""
    # Initialize config service
    config_service = ConfigService()
    
    # Initialize logging
    logging_service = LoggingService("identity", config_service.get_service_config("identity").log_level)
    logger = logging_service.logger
    
    try:
        # Initialize security service
        security_service = SecurityService(
            secret_key=os.getenv("JWT_SECRET_KEY"),
            token_expiry=None  # Use defaults
        )
        
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
        
        # Initialize identity service
        identity_service = IdentityService(
            security_service=security_service,
            database_service=database_service,
            cache_service=cache_service
        )
        await identity_service.initialize()
        await identity_service.start()
        
        # Initialize API
        init_api(identity_service)
        
        logger.info("All services initialized successfully")
        return identity_service, database_service, cache_service
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

async def cleanup_services(services):
    """Cleanup all services"""
    identity_service, database_service, cache_service = services
    
    try:
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
        port = int(os.getenv("PORT", "8000"))
        
        logger.info(f"Starting identity service on {host}:{port}")
        
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