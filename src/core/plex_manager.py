"""Plex media server management module."""

import logging
from typing import List, Optional, Dict, Any, cast
from functools import lru_cache
from plexapi.server import PlexServer
from plexapi.video import Video
from plexapi.exceptions import Unauthorized

logger = logging.getLogger(__name__)


class StreamingError(Exception):
    """Base exception for streaming-related errors."""
    pass


class MediaNotFoundError(Exception):
    """Raised when requested media is not found."""
    pass


class PlexManager:
    """Manages Plex server connection and operations."""

    def __init__(self, url: str, token: str) -> None:
        """Initialize PlexManager.
        
        Args:
            url: Plex server URL
            token: Plex authentication token
            
        Raises:
            StreamingError: If initial connection fails
        """
        self._url = url
        self._token = token
        self._server: Optional[PlexServer] = None
        self._retry_delay = 1.0
        self._max_retry_delay = 30.0
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Plex server."""
        try:
            self._server = PlexServer(self._url, self._token)
        except Unauthorized:
            raise StreamingError("Invalid Plex credentials")
        except Exception as e:
            raise StreamingError(f"Failed to connect to Plex: {e}")

    @property
    def server(self) -> PlexServer:
        """Get Plex server instance, reconnecting if needed."""
        if self._server is None:
            self._connect()
        return cast(PlexServer, self._server)

    @lru_cache(maxsize=100)
    def search_media(self, query: str) -> List[Video]:
        """Search for media in Plex libraries.
        
        Args:
            query: Search term
            
        Returns:
            List of matching media items
            
        Raises:
            MediaNotFoundError: If no results found
            StreamingError: If search fails
        """
        try:
            results = self.server.library.search(query)
            if not results:
                raise MediaNotFoundError(f"No media found matching '{query}'")
            return cast(List[Video], results)
        except Exception as e:
            if isinstance(e, MediaNotFoundError):
                raise
            raise StreamingError(f"Media search failed: {e}")

    def get_stream_url(self, video: Video) -> str:
        """Get direct stream URL for video.
        
        Args:
            video: Video to get URL for
            
        Returns:
            Direct stream URL
            
        Raises:
            StreamingError: If URL generation fails
        """
        try:
            url = video.getStreamURL()
            return cast(str, url)
        except Exception as e:
            raise StreamingError(f"Failed to get stream URL: {e}")

    def get_video_info(self, video: Video) -> Dict[str, Any]:
        """Get detailed video information.
        
        Args:
            video: Video to get info for
            
        Returns:
            Dict containing video metadata
        """
        return {
            "title": video.title,
            "duration": video.duration,
            "bitrate": video.bitrate,
            "resolution": f"{video.width}x{video.height}",
            "codec": video.videoCodec,
            "container": video.container
        }

    def invalidate_cache(self) -> None:
        """Clear the search cache."""
        self.search_media.cache_clear()

    async def close(self) -> None:
        """Clean up resources."""
        self._server = None
        self.invalidate_cache()