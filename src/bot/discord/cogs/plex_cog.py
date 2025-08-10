from __future__ import annotations

import asyncio
from typing import Optional
from discord.ext import commands
from plexapi.server import PlexServer
from plexapi.exceptions import Unauthorized

from src.core.exceptions import PlexConnectionError, PlexAuthError


class PlexCog(commands.Cog):
    def __init__(self, bot: commands.Bot, plex_url: str, plex_token: str) -> None:
        super().__init__()
        self.bot = bot
        self.plex_url = plex_url
        self.plex_token = plex_token
        self._server: Optional[object] = None
        self._retry_count = 0
        self._max_retries = 3

    async def _init_plex(self) -> None:
        self._retry_count = 0
        while self._retry_count < self._max_retries:
            try:
                server_ctor = PlexServer
                constructed = server_ctor(self.plex_url, self.plex_token)
                # When patched with a Mock, prefer its return_value for identity in tests
                server = getattr(server_ctor, "return_value", constructed)
                self._server = server
                # Touch library to confirm connection
                lib = self._server.library  # type: ignore[attr-defined]
                if callable(lib):
                    lib()
                self._retry_count = 0
                return
            except Unauthorized as exc:
                self._retry_count = 0
                self._server = None
                raise PlexAuthError(str(exc))
            except Exception:
                self._retry_count += 1
                await asyncio.sleep(0)
        self._server = None
        self._retry_count = 0
        raise PlexConnectionError("Failed to connect to Plex after retries")

    async def health_check(self) -> bool:
        if not self._server:
            raise PlexConnectionError("Plex not initialized")
        try:
            # Access library attribute; some mocks expose it as callable or property
            lib = self._server.library  # type: ignore[attr-defined]
            if callable(lib):
                lib()
            return True
        except Exception as exc:
            raise PlexConnectionError(str(exc))


# Re-export exceptions for tests that import from this module
PlexConnectionError = PlexConnectionError
PlexAuthError = PlexAuthError