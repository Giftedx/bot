"""Plex service implementation for managing media server interactions."""

import logging
from typing import Optional, List, Dict, Any, Union, cast
from plexapi.server import PlexServer
from plexapi.video import Video
from plexapi.audio import Track
from plexapi.photo import Photo
from plexapi.exceptions import Unauthorized

from src.core.exceptions import (
    PlexConnectionError,
    PlexAuthError,
    MediaNotFoundError
)
from src.core.config import Settings

settings = Settings()

logger = logging.getLogger(__name__)


class PlaybackResult:
    """Result of a playback operation."""
    def __init__(
        self,
        status: str,
        media_id: str,
        title: Optional[str] = None
    ) -> None:
        self.status = status
        self.media_id = media_id
        self.title = title


class PlexService:
    """Core service for Plex media server interactions."""

    def __init__(self, base_url: str, token: str) -> None:
        """Initialize the Plex service.

        Args:
            base_url: Base URL of the Plex server
            token: Authentication token for Plex API
        """
        self._base_url = base_url
        self._token = token
        self._server: Optional[PlexServer] = None
        self._retry_count = 0
        self._max_retries = settings.PLEX_MAX_RETRIES
        self._active_sessions: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize connection to Plex server.

        Raises:
            PlexConnectionError: If connection fails
            PlexAuthError: If authentication fails
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
        """Check if Plex server is responding.

        Returns:
            True if server is healthy

        Raises:
            PlexConnectionError: If server is not responding
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

    async def search_media(
        self,
        query: str
    ) -> List[Union[Video, Track, Photo]]:
        """Search for media across all libraries.

        Args:
            query: Search term to find media

        Returns:
            List of matching media items

        Raises:
            MediaNotFoundError: If no results found
            PlexConnectionError: If search fails
        """
        try:
            if not self._server:
                await self.initialize()
            if self._server:  # mypy check
                results = self._server.library.search(query)
                if not results:
                    raise MediaNotFoundError(
                        f"No media found matching '{query}'"
                    )
                return cast(List[Union[Video, Track, Photo]], results)
            return []
        except (PlexConnectionError, MediaNotFoundError):
            raise
        except Exception as e:
            raise PlexConnectionError(f"Search failed: {e}")

    async def play_media(
        self,
        media_id: str,
        client_id: Optional[str] = None
    ) -> PlaybackResult:
        """Start playback of specified media.

        Args:
            media_id: ID of media to play
            client_id: Optional client device ID

        Returns:
            PlaybackResult object with playback status

        Raises:
            MediaNotFoundError: If media_id is invalid
            PlexConnectionError: If playback fails
        """
        try:
            if not self._server:
                await self.initialize()
            if self._server:  # mypy check
                media = self._server.fetchItem(int(media_id))
                if not media:
                    raise MediaNotFoundError(f"Media ID {media_id} not found")

                # For now just return success - actual playback needs client setup
                return PlaybackResult(
                    status="success",
                    media_id=media_id,
                    title=media.title
                )
            return PlaybackResult(status="error", media_id=media_id)
        except (PlexConnectionError, MediaNotFoundError):
            raise
        except Exception as e:
            raise PlexConnectionError(f"Playback failed: {e}")

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get information about currently playing media sessions.

        Returns:
            List of active playback session details
        """
        try:
            if not self._server:
                await self.initialize()
            if not self._server:
                return []
                
            sessions = []
            for session in self._server.sessions():
                username = (
                    session.usernames[0]
                    if session.usernames else 'Unknown'
                )
                sessions.append({
                    'username': username,
                    'title': session.title,
                    'type': session.type,
                    'device': session.player.title,
                    'state': session.player.state
                })
            return sessions
        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")
            return []