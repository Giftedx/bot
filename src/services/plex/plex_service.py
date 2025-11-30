"""Plex service implementation for managing media server interactions."""

import logging
from typing import Optional, List, Dict, Any, Union, cast
from plexapi.server import PlexServer
from plexapi.video import Video
from plexapi.audio import Track
from plexapi.photo import Photo
from plexapi.exceptions import Unauthorized

from src.core.exceptions import PlexConnectionError, PlexAuthError, MediaNotFoundError
from src.core.config import Settings

settings = Settings()

logger = logging.getLogger(__name__)


class PlaybackResult:
    """Result of a playback operation.

    Attributes:
        status (str): The status of the operation (e.g., 'success', 'error').
        media_id (str): The ID of the media item involved.
        title (Optional[str]): The title of the media, if available.
    """

    def __init__(self, status: str, media_id: str, title: Optional[str] = None) -> None:
        """Initialize the playback result.

        Args:
            status (str): The outcome status.
            media_id (str): The media identifier.
            title (Optional[str], optional): The media title. Defaults to None.
        """
        self.status = status
        self.media_id = media_id
        self.title = title


class PlexService:
    """Core service for Plex media server interactions.

    Handles connection initialization, health checks, media searching,
    playback requests, and session monitoring.
    """

    def __init__(self, base_url: str, token: str) -> None:
        """Initialize the Plex service.

        Args:
            base_url (str): Base URL of the Plex server.
            token (str): Authentication token for the Plex API.
        """
        self._base_url = base_url
        self._token = token
        self._server: Optional[PlexServer] = None
        self._retry_count = 0
        self._max_retries = settings.PLEX_MAX_RETRIES
        self._active_sessions: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize connection to the Plex server.

        Attempts to connect to the Plex server using the provided credentials.
        Retries up to `_max_retries` times on failure.

        Raises:
            PlexAuthError: If authentication fails (invalid token/credentials).
            PlexConnectionError: If the connection fails after max retries.
        """
        try:
            self._server = PlexServer(self._base_url, self._token)
            await self.health_check()
            self._retry_count = 0
        except Unauthorized as e:
            raise PlexAuthError(f"Invalid Plex credentials: {e}")
        except Exception as e:
            self._retry_count += 1
            if self._retry_count >= self._max_retries:
                self._retry_count = 0
                msg = f"Failed to connect after {self._max_retries} attempts"
                raise PlexConnectionError(f"{msg}: {e}")
            logger.warning(f"Connection attempt {self._retry_count} failed")
            await self.initialize()

    async def health_check(self) -> bool:
        """Check if the Plex server is responding.

        Ensures the `_server` object is initialized and performs a basic
        API call (`server.library`).

        Returns:
            bool: True if the server is reachable and healthy.

        Raises:
            PlexConnectionError: If the server is unreachable or throws an error.
        """
        try:
            if not self._server:
                await self.initialize()
            if self._server:  # mypy check
                # Simple API call to verify connection
                _ = self._server.library
            return True
        except Exception as e:
            raise PlexConnectionError(f"Health check failed: {e}")

    async def search_media(self, query: str) -> List[Union[Video, Track, Photo]]:
        """Search for media across all libraries.

        Args:
            query (str): The search term.

        Returns:
            List[Union[Video, Track, Photo]]: A list of matching media items.

        Raises:
            MediaNotFoundError: If no results are found.
            PlexConnectionError: If the search operation fails.
        """
        try:
            if not self._server:
                await self.initialize()
            if self._server:  # mypy check
                results = self._server.library.search(query)
                if not results:
                    raise MediaNotFoundError(f"No media found matching '{query}'")
                return cast(List[Union[Video, Track, Photo]], results)
            return []
        except (PlexConnectionError, MediaNotFoundError):
            raise
        except Exception as e:
            raise PlexConnectionError(f"Search failed: {e}")

    async def play_media(self, media_id: str, client_id: Optional[str] = None) -> PlaybackResult:
        """Start playback of specified media.

        Args:
            media_id (str): The unique ID of the media item.
            client_id (Optional[str], optional): The target client identifier. Defaults to None.

        Returns:
            PlaybackResult: An object containing the status and details of the operation.

        Raises:
            MediaNotFoundError: If the media ID does not exist.
            PlexConnectionError: If the playback request fails.
        """
        try:
            if not self._server:
                await self.initialize()
            if self._server:  # mypy check
                media = self._server.fetchItem(int(media_id))
                if not media:
                    raise MediaNotFoundError(f"Media ID {media_id} not found")

                # For now just return success - actual playback needs client setup
                return PlaybackResult(status="success", media_id=media_id, title=media.title)
            return PlaybackResult(status="error", media_id=media_id)
        except (PlexConnectionError, MediaNotFoundError):
            raise
        except Exception as e:
            raise PlexConnectionError(f"Playback failed: {e}")

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Retrieve information about currently playing media sessions.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing session details
            (username, title, type, device, state). Returns empty list on error.
        """
        try:
            if not self._server:
                await self.initialize()
            if not self._server:
                return []

            sessions = []
            for session in self._server.sessions():
                username = session.usernames[0] if session.usernames else "Unknown"
                sessions.append(
                    {
                        "username": username,
                        "title": session.title,
                        "type": session.type,
                        "device": session.player.title,
                        "state": session.player.state,
                    }
                )
            return sessions
        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")
            return []
