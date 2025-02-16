"""Plex-specific bot implementation."""
import logging
from typing import Optional

from .base_bot import BaseBot
from ..core.config import Config
from ..services.plex.client import PlexClient
from ..services.plex.manager import PlexManager
from ..services.media.player import MediaPlayer

logger = logging.getLogger(__name__)

class PlexBot(BaseBot):
    """Discord bot with Plex integration."""
    
    def __init__(
        self,
        config: Config,
        plex_url: str,
        plex_token: str,
        **kwargs
    ) -> None:
        """Initialize PlexBot with Plex configuration."""
        super().__init__(
            config,
            command_prefix=config.COMMAND_PREFIX,
            description="Plex Media Bot",
            **kwargs
        )
        
        # Initialize Plex components
        self.plex_client = PlexClient(plex_url, plex_token)
        self.plex_manager = PlexManager(self.plex_client)
        self.media_player = MediaPlayer()
        
        # Add Plex-specific metrics
        self._metrics.update({
            "plex_streams": self._metrics_registry.gauge(
                "plex_active_streams",
                "Number of active Plex streams"
            ),
            "plex_errors": self._metrics_registry.counter(
                "plex_errors_total",
                "Total number of Plex-related errors"
            )
        })

    async def setup_hook(self) -> None:
        """Set up Plex-specific components."""
        await super().setup_hook()
        
        # Load Plex-specific cogs
        plex_extensions = [
            "media.plex",
            "media.streaming",
            "media.voice"
        ]
        
        for extension in plex_extensions:
            try:
                await self.load_extension(f"cogs.{extension}")
                logger.info(f"Loaded Plex extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load Plex extension {extension}: {e}")

    async def close(self) -> None:
        """Clean up Plex-specific resources."""
        try:
            # Stop all active streams
            await self.plex_manager.stop_all_streams()
            
            # Clean up media player
            self.media_player.cleanup()
            
            # Close Plex client
            await self.plex_client.close()
        except Exception as e:
            logger.error(f"Error during Plex cleanup: {e}")
        
        await super().close()

def create_plex_bot(
    config: Config,
    plex_url: Optional[str] = None,
    plex_token: Optional[str] = None
) -> PlexBot:
    """Create and configure a PlexBot instance."""
    if not plex_url:
        plex_url = config.PLEX_URL
    if not plex_token:
        plex_token = config.PLEX_TOKEN
        
    if not all([plex_url, plex_token]):
        raise ValueError("Plex URL and token are required")
        
    return PlexBot(
        config=config,
        plex_url=plex_url,
        plex_token=plex_token
    ) 