from __future__ import annotations

import asyncio
from typing import List, Optional
from dataclasses import dataclass

from plexapi.server import PlexServer
from plexapi.video import Video
from plexapi.exceptions import NotFound, Unauthorized

from .exceptions import PlexConnectionError, PlexAuthError, MediaNotFoundError


@dataclass
class PlexSessionInfo:
    title: str
    usernames: List[str]


class PlexClient:
    def __init__(self, url: str, token: str):
        self._url = url
        self._token = token
        self._server: Optional[PlexServer] = None

    async def connect(self) -> None:
        try:
            # run sync connect in thread to avoid blocking if needed
            def _connect_sync():
                self._server = PlexServer(self._url, self._token)
            await asyncio.to_thread(_connect_sync)
        except Unauthorized as e:
            raise PlexAuthError("Invalid Plex credentials") from e
        except Exception as e:
            raise PlexConnectionError(str(e)) from e

    def is_connected(self) -> bool:
        return self._server is not None

    async def search_media(self, query: str) -> List[Video]:
        if not self._server:
            await self.connect()
        assert self._server is not None
        try:
            return await asyncio.to_thread(self._server.library.search, query)
        except NotFound as e:
            raise MediaNotFoundError(f"No media found for '{query}'") from e

    async def get_active_sessions(self) -> List[PlexSessionInfo]:
        if not self._server:
            await self.connect()
        assert self._server is not None
        sessions = await asyncio.to_thread(self._server.sessions)
        result: List[PlexSessionInfo] = []
        for s in sessions:
            title = getattr(s, "title", "")
            usernames = list(getattr(s, "usernames", []) or [])
            result.append(PlexSessionInfo(title=title, usernames=usernames))
        return result

    async def get_library_sections(self):
        if not self._server:
            await self.connect()
        assert self._server is not None
        return await asyncio.to_thread(self._server.library.sections)

    async def close(self) -> None:
        # nothing persistent to close; clear server handle
        self._server = None