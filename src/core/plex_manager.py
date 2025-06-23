"""Plex media server management module."""

import logging
from typing import List, Optional, Dict, Any, cast
from functools import lru_cache
from plexapi.server import PlexServer
from plexapi.video import Video
from plexapi.exceptions import Unauthorized, NotFound, BadRequest, PlexApiException
from requests.exceptions import (
    ConnectionError as RequestsConnectionError,
    Timeout as RequestsTimeout,
    RequestException,
)

from src.core.config import ConfigManager

logger = logging.getLogger(__name__)

# Exceptions are now imported from .exceptions
from .exceptions import StreamingError, MediaNotFoundError, PlexConnectionError, PlexAPIError


class PlexManager:
    """Manages Plex server connection and operations."""

    # def __init__(self, url: str, token: str) -> None: # Old __init__
    def __init__(self) -> None:  # New __init__
        """Initialize PlexManager.

        Raises:
            StreamingError: If initial connection fails or config is missing
        """
        config_manager = ConfigManager(config_dir="config")  # Instantiated ConfigManager
        self._url = config_manager.get("plex.url")
        self._token = config_manager.get("plex.token")

        if not self._url or not self._token:
            logger.error(
                "Plex URL or Token not found in configuration. PlexManager cannot operate."
            )
            raise StreamingError(
                "Plex URL and/or Token is not configured. PlexManager cannot operate."
            )

        self._server: Optional[PlexServer] = None
        self._retry_delay = 1.0
        self._max_retry_delay = 30.0
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Plex server."""
        try:
            self._server = PlexServer(self._url, self._token, timeout=10)  # Added timeout
        except Unauthorized:
            logger.error("Plex authentication failed: Invalid token or credentials.")
            raise PlexConnectionError("Invalid Plex credentials provided.")
        except RequestsConnectionError as e:
            logger.error(
                f"Plex connection failed: Could not connect to server at {self._url}. Error: {e}"
            )
            raise PlexConnectionError(f"Could not connect to Plex server at {self._url}.")
        except RequestsTimeout as e:
            logger.error(f"Plex connection timed out while trying to reach {self._url}. Error: {e}")
            raise PlexConnectionError(f"Connection to Plex server timed out.")
        except PlexApiException as e:  # Catch other plexapi specific errors
            logger.error(f"Plex API error during connection: {e}")
            raise PlexAPIError(f"Plex API error during connection: {e}")
        except RequestException as e:  # Catch other requests errors
            logger.error(f"Network error during Plex connection: {e}")
            raise PlexConnectionError(f"Network error connecting to Plex: {e}")
        except Exception as e:  # Catch-all for unexpected errors
            logger.error(f"Unexpected error connecting to Plex: {e}", exc_info=True)
            raise StreamingError(f"An unexpected error occurred while connecting to Plex: {e}")

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
        except NotFound:  # More specific Plex exception for "not found"
            raise MediaNotFoundError(f"No media found matching '{query}' (Plex NotFound).")
        except Unauthorized:
            logger.error("Plex authentication error during media search.")
            raise PlexConnectionError("Invalid Plex credentials for search.")
        except BadRequest as e:  # Specific Plex API error for bad requests
            logger.error(f"Plex API bad request during search for '{query}': {e}")
            raise PlexAPIError(f"Plex API bad request during search for '{query}': {e}")
        except PlexApiException as e:
            logger.error(f"Plex API error during search for '{query}': {e}")
            raise PlexAPIError(f"Plex API error during search for '{query}': {e}")
        except RequestsConnectionError as e:
            logger.error(f"Network connection error during Plex search: {e}")
            raise PlexConnectionError(f"Network error during Plex search: {e}")
        except RequestsTimeout as e:
            logger.error(f"Network timeout during Plex search: {e}")
            raise PlexConnectionError(f"Network timeout during Plex search: {e}")
        except RequestException as e:
            logger.error(f"Network error during Plex search: {e}")
            raise PlexConnectionError(f"General network error during Plex search: {e}")
        except Exception as e:
            if isinstance(e, MediaNotFoundError):  # Already handled or re-raised
                raise
            logger.error(f"Unexpected error during media search for '{query}': {e}", exc_info=True)
            raise StreamingError(f"Unexpected error during media search: {e}")

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
            if not url:  # getStreamURL might return None in some cases
                logger.error(f"Plex returned no stream URL for video: {video.title}")
                raise PlexAPIError(f"Plex returned no stream URL for video: {video.title}")
            return cast(str, url)
        except NotFound as e:
            logger.error(
                f"Media not found when trying to get stream URL for video: {video.title}. Error: {e}"
            )
            raise MediaNotFoundError(
                f"Media not found when trying to get stream URL for: {video.title}"
            )
        except Unauthorized:
            logger.error("Plex authentication error when getting stream URL.")
            raise PlexConnectionError("Invalid Plex credentials for getting stream URL.")
        except PlexApiException as e:
            logger.error(f"Plex API error getting stream URL for '{video.title}': {e}")
            raise PlexAPIError(f"Plex API error getting stream URL for '{video.title}': {e}")
        except RequestsConnectionError as e:
            logger.error(f"Network connection error getting stream URL for '{video.title}': {e}")
            raise PlexConnectionError(f"Network error getting stream URL: {e}")
        except RequestsTimeout as e:
            logger.error(f"Network timeout getting stream URL for '{video.title}': {e}")
            raise PlexConnectionError(f"Network timeout getting stream URL: {e}")
        except RequestException as e:
            logger.error(f"Network error getting stream URL for '{video.title}': {e}")
            raise PlexConnectionError(f"General network error getting stream URL: {e}")
        except Exception as e:
            logger.error(
                f"Unexpected error getting stream URL for '{video.title}': {e}", exc_info=True
            )
            raise StreamingError(f"Unexpected error getting stream URL: {e}")

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
            "container": video.container,
        }

    def invalidate_cache(self) -> None:
        """Clear the search cache."""
        self.search_media.cache_clear()

    async def close(self) -> None:
        """Clean up resources."""
        self._server = None
        self.invalidate_cache()
