"""Plex client with async-friendly API used in tests."""
from __future__ import annotations
from typing import Any, List, Optional
from dataclasses import dataclass
from plexapi.server import PlexServer
from plexapi.exceptions import Unauthorized

from .exceptions import PlexConnectionError, PlexAuthError, MediaNotFoundError


@dataclass
class LibrarySection:
    title: str
    type: str


@dataclass
class SessionInfo:
    title: str
    usernames: list[str]


class PlexClient:
    def __init__(self, url: str, token: str) -> None:
        self._url = url
        self._token = token
        self._server: Optional[PlexServer] = None

    async def connect(self) -> None:
        try:
            self._server = PlexServer(self._url, self._token)
            # Touch library to validate connection
            _ = self._server.library
        except Unauthorized as e:
            raise PlexAuthError(str(e))
        except Exception as e:
            raise PlexConnectionError(str(e))

    def is_connected(self) -> bool:
        return self._server is not None

    async def close(self) -> None:
        # No persistent connection to close in plexapi
        self._server = None

    async def search_media(self, query: str) -> List[Any]:
        if not self._server:
            await self.connect()
        assert self._server is not None
        results = self._server.library.search(query)
        if not results:
            raise MediaNotFoundError(f"No media found matching '{query}'")
        return results

    async def get_active_sessions(self) -> List[SessionInfo]:
        if not self._server:
            await self.connect()
        assert self._server is not None
        sessions = []
        for s in self._server.sessions():
            sessions.append(SessionInfo(title=getattr(s, "title", ""), usernames=getattr(s, "usernames", []) or []))
        return sessions

    async def get_library_sections(self) -> List[LibrarySection]:
        if not self._server:
            await self.connect()
        assert self._server is not None
        sections = []
        for sec in self._server.library.sections():
            sections.append(LibrarySection(title=getattr(sec, "title", ""), type=getattr(sec, "type", "")))
        return sections