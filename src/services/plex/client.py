"""Plex client service for interacting with Plex Media Server."""
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import redis
import json
from datetime import datetime, timedelta

from plexapi.server import PlexServer
from plexapi.video import Video
from plexapi.exceptions import NotFound

from .models import MediaInfo, StreamInfo

# from ...core.config import Config # Removed old Config import
from src.core.config import ConfigManager  # Added ConfigManager import
from ...core.exceptions import PlexConnectionError, MediaNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration settings."""

    LIBRARY_TTL: int = 300  # 5 minutes
    METADATA_TTL: int = 3600  # 1 hour
    STREAM_URL_TTL: int = 900  # 15 minutes
    SESSION_TTL: int = 86400  # 24 hours


class PlexCache:
    """Cache handler for Plex data."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.config = CacheConfig()

    def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        try:
            value = self.redis.get(f"plex:{key}")
            return json.loads(value) if value else None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        try:
            self.redis.setex(f"plex:{key}", ttl or self.config.METADATA_TTL, json.dumps(value))
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")


class PlexClient:
    """Client for interacting with Plex Media Server."""

    # def __init__(self, url: str, token: str, redis_client: redis.Redis): # Old __init__
    def __init__(self, config_manager: ConfigManager, redis_client: redis.Redis):  # New __init__
        """Initialize Plex client."""
        self.url = config_manager.get("plex.url")
        self.token = config_manager.get("plex.token")

        if not self.url or not self.token:
            logger.error(
                "Plex URL or Token not found in configuration. PlexClient cannot initialize."
            )
            raise PlexConnectionError("Plex URL and/or Token is not configured for PlexClient.")

        self.cache = PlexCache(redis_client)
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Plex server."""
        if not self.url or not self.token:  # Should be caught by __init__, but defensive check
            msg = "Plex URL or Token is not configured properly for connection."
            logger.error(msg)
            raise PlexConnectionError(msg)
        try:
            self.server = PlexServer(self.url, self.token)
            logger.info("Successfully connected to Plex server")
        except Exception as e:
            logger.error(f"Failed to connect to Plex server: {e}")
            raise PlexConnectionError(f"Could not connect to Plex server: {e}")

    async def get_libraries(self) -> List[Dict[str, Any]]:
        """Get all libraries from Plex server."""
        cache_key = "libraries"
        cached = self.cache.get(cache_key)

        if cached:
            return cached

        try:
            sections = self.server.library.sections()
            libraries = [
                {
                    "id": section.key,
                    "name": section.title,
                    "type": section.type,
                    "count": section.totalSize,
                }
                for section in sections
            ]

            self.cache.set(cache_key, libraries, self.cache.config.LIBRARY_TTL)
            return libraries
        except Exception as e:
            logger.error(f"Error fetching libraries: {e}")
            raise

    async def search_media(self, query: str, library_id: Optional[str] = None) -> List[MediaInfo]:
        """Search for media in Plex library."""
        cache_key = f"search:{library_id or 'all'}:{query}"
        cached = self.cache.get(cache_key)

        if cached:
            return [MediaInfo(**item) for item in cached]

        try:
            if library_id:
                section = self.server.library.sectionByID(library_id)
                results = section.search(query)
            else:
                results = self.server.library.search(query)

            media_items = [
                MediaInfo.from_plex(item) for item in results if isinstance(item, Video)
            ][
                :10
            ]  # Limit to 10 results

            self.cache.set(cache_key, [item.dict() for item in media_items])
            return media_items
        except NotFound:
            raise MediaNotFoundError(f"No media found for query: {query}")
        except Exception as e:
            logger.error(f"Error searching media: {e}")
            raise

    async def get_stream_url(self, media_id: str) -> StreamInfo:
        """Get streaming URL for media."""
        cache_key = f"stream:{media_id}"
        cached = self.cache.get(cache_key)

        if cached:
            return StreamInfo(**cached)

        try:
            media = self.server.fetchItem(int(media_id))
            stream_info = StreamInfo(
                url=media.getStreamURL(),
                quality="1080p",  # TODO: Make configurable
                direct_play=True,
                expires_at=datetime.now() + timedelta(minutes=15),
            )

            self.cache.set(cache_key, stream_info.dict(), self.cache.config.STREAM_URL_TTL)
            return stream_info
        except NotFound:
            raise MediaNotFoundError(f"Media not found: {media_id}")
        except Exception as e:
            logger.error(f"Error getting stream URL: {e}")
            raise

    async def get_metadata(self, media_id: str) -> Dict[str, Any]:
        """Get detailed metadata for media."""
        cache_key = f"metadata:{media_id}"
        cached = self.cache.get(cache_key)

        if cached:
            return cached

        try:
            media = self.server.fetchItem(int(media_id))
            metadata = {
                "title": media.title,
                "year": getattr(media, "year", None),
                "summary": media.summary,
                "duration": media.duration,
                "thumb": media.thumb,
                "art": media.art,
                "media_type": media.type,
                "rating": getattr(media, "rating", None),
                "content_rating": getattr(media, "contentRating", None),
                "studio": getattr(media, "studio", None),
                "genres": [genre.tag for genre in getattr(media, "genres", [])],
                "directors": [director.tag for director in getattr(media, "directors", [])],
                "actors": [actor.tag for actor in getattr(media, "roles", [])],
            }

            self.cache.set(cache_key, metadata, self.cache.config.METADATA_TTL)
            return metadata
        except NotFound:
            raise MediaNotFoundError(f"Media not found: {media_id}")
        except Exception as e:
            logger.error(f"Error fetching metadata: {e}")
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
                bitrate=media_streams.bitrate,
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

    async def update_progress(self, media_id: str, position: int, state: str = "playing") -> None:
        """Update media playback progress."""
        try:
            media = self.server.fetchItem(int(media_id))
            if isinstance(media, Video):
                if state == "playing":
                    media.updateTimeline(position, state="playing")
                elif state == "paused":
                    media.updateTimeline(position, state="paused")
                elif state == "stopped":
                    media.updateTimeline(position, state="stopped")
        except Exception as e:
            logger.error(f"Error updating progress for {media_id} to {position}: {e}")
            raise

    async def close(self) -> None:
        """Close the Plex client connection."""
        try:
            # Clean up any resources
            self.server = None
        except Exception as e:
            logger.error(f"Error closing Plex client: {e}")
            raise
