"""Plex client service for interacting with Plex Media Server."""
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from plexapi.server import PlexServer
from plexapi.video import Video
from plexapi.media import Media
from plexapi.exceptions import NotFound, Unauthorized

from .models import MediaInfo, StreamInfo
from ...core.config import Config

logger = logging.getLogger(__name__)

class PlexClient:
    """Client for interacting with Plex Media Server."""
    
    def __init__(self, url: str, token: str):
        """Initialize Plex client."""
        self.url = url
        self.token = token
        self.server = PlexServer(url, token)
        self._validate_connection()
        
    def _validate_connection(self) -> None:
        """Validate connection to Plex server."""
        try:
            self.server.library
            logger.info("Successfully connected to Plex server")
        except Exception as e:
            logger.error(f"Failed to connect to Plex server: {e}")
            raise
            
    async def search(self, query: str) -> List[MediaInfo]:
        """Search for media on Plex server."""
        try:
            results = self.server.library.search(query)
            return [
                MediaInfo.from_plex(item)
                for item in results
                if isinstance(item, Video)
            ][:10]  # Limit to 10 results
        except Exception as e:
            logger.error(f"Error searching Plex: {e}")
            raise
            
    async def get_media(self, media_id: str) -> Optional[MediaInfo]:
        """Get media by ID."""
        try:
            media = self.server.fetchItem(int(media_id))
            if isinstance(media, Video):
                return MediaInfo.from_plex(media)
            return None
        except NotFound:
            logger.warning(f"Media not found: {media_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting media {media_id}: {e}")
            raise
            
    async def get_stream_url(self, media_id: str) -> Optional[str]:
        """Get streaming URL for media."""
        try:
            media = await self.get_media(media_id)
            if not media:
                return None
                
            plex_media = self.server.fetchItem(int(media_id))
            return plex_media.getStreamURL()
        except Exception as e:
            logger.error(f"Error getting stream URL for {media_id}: {e}")
            raise
            
    async def get_stream_info(self, media_id: str) -> Optional[StreamInfo]:
        """Get streaming information for media."""
        try:
            media = self.server.fetchItem(int(media_id))
            if not isinstance(media, Video):
                return None
                
            media_streams = media.media[0] if media.media else None
            if not media_streams:
                logger.warning(f"No media streams for {media_id}")
                return None
                
            return StreamInfo(
                stream_url=media.getStreamURL(),
                duration=media.duration,
                media_type=media.type,
                video_codec=media_streams.videoCodec,
                audio_codec=media_streams.audioCodec,
                resolution=media_streams.videoResolution,
                bitrate=media_streams.bitrate
            )
        except Exception as e:
            logger.error(f"Error getting stream info for {media_id}: {e}")
            raise
            
    async def mark_watched(self, media_id: str) -> None:
        """Mark media as watched."""
        try:
            media = self.server.fetchItem(int(media_id))
            if isinstance(media, Video):
                media.markWatched()
        except Exception as e:
            logger.error(f"Error marking media {media_id} as watched: {e}")
            raise
            
    async def update_progress(
        self,
        media_id: str,
        position: int,
        state: str = "playing"
    ) -> None:
        """Update media playback progress."""
        try:
            media = self.server.fetchItem(int(media_id))
            if isinstance(media, Video):
                if state == "playing":
                    media.updateTimeline(
                        position,
                        state="playing"
                    )
                elif state == "paused":
                    media.updateTimeline(
                        position,
                        state="paused"
                    )
                elif state == "stopped":
                    media.updateTimeline(
                        position,
                        state="stopped"
                    )
        except Exception as e:
            logger.error(
                f"Error updating progress for {media_id} to {position}: {e}"
            )
            raise
            
    async def close(self) -> None:
        """Close the Plex client connection."""
        try:
            # Clean up any resources
            self.server = None
        except Exception as e:
            logger.error(f"Error closing Plex client: {e}")
            raise 