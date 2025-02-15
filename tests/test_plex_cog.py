import pytest
from unittest.mock import Mock, patch
from discord.ext import commands
from src.bot.discord.cogs.plex_cog import (
    PlexCog,
    PlexConnectionError,
    PlexAuthError,
)
from plexapi.server import PlexServer
from plexapi.exceptions import Unauthorized


@pytest.fixture
def mock_bot() -> commands.Bot:
    return Mock(spec=commands.Bot)


@pytest.fixture
def plex_cog(mock_bot: commands.Bot) -> PlexCog:
    return PlexCog(
        bot=mock_bot,
        plex_url="http://test.plex.tv:32400",
        plex_token="test_token",
    )


@pytest.mark.asyncio
async def test_init_plex_success(
    plex_cog: PlexCog, mock_bot: commands.Bot
) -> None:
    with patch("src.bot.discord.cogs.plex_cog.PlexServer") as MockPlexServer:
        mock_server = MockPlexServer.return_value
        mock_server.library = Mock()  # Simulate a successful connection

        await plex_cog._init_plex()
        assert plex_cog._server is mock_server
        assert plex_cog._retry_count == 0


@pytest.mark.asyncio
async def test_init_plex_auth_failure(
    plex_cog: PlexCog, mock_bot: commands.Bot
) -> None:
    with patch(
        "src.bot.discord.cogs.plex_cog.PlexServer", side_effect=Unauthorized
    ):
        with pytest.raises(PlexAuthError):
            await plex_cog._init_plex()
        assert plex_cog._retry_count == 0


@pytest.mark.asyncio
async def test_init_plex_connection_failure_retries(
    plex_cog: PlexCog, mock_bot: commands.Bot
) -> None:
    with patch(
        "src.bot.discord.cogs.plex_cog.PlexServer",
        side_effect=[ConnectionError, ConnectionError, PlexServer],
    ) as MockPlexServer:
        mock_server = MockPlexServer.return_value
        mock_server.library = Mock()

        await plex_cog._init_plex()
        assert plex_cog._server is mock_server
        assert plex_cog._retry_count == 0
        assert MockPlexServer.call_count == 3


@pytest.mark.asyncio
async def test_init_plex_connection_failure_max_retries(
    plex_cog: PlexCog, mock_bot: commands.Bot
) -> None:
    with patch(
        "src.bot.discord.cogs.plex_cog.PlexServer",
        side_effect=[ConnectionError, ConnectionError, ConnectionError],
    ):
        with pytest.raises(PlexConnectionError):
            await plex_cog._init_plex()
        assert plex_cog._retry_count == 0


@pytest.mark.asyncio
async def test_health_check_success(
    plex_cog: PlexCog, mock_bot: commands.Bot
) -> None:
    with patch("src.bot.discord.cogs.plex_cog.PlexServer") as MockPlexServer:
        mock_server = MockPlexServer.return_value
        mock_server.library = Mock()

        plex_cog._server = mock_server
        assert await plex_cog.health_check() is True


@pytest.mark.asyncio
async def test_health_check_failure(
    plex_cog: PlexCog, mock_bot: commands.Bot
) -> None:
    with patch("src.bot.discord.cogs.plex_cog.PlexServer") as MockPlexServer:
        mock_server = MockPlexServer.return_value
        mock_server.library.side_effect = Exception("Test Error")
        plex_cog._server = mock_server
        with pytest.raises(PlexConnectionError):
            await plex_cog.health_check()