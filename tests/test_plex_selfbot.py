from unittest.mock import AsyncMock, Mock, patch

import discord
import pytest
from plexapi.server import PlexServer

from src.bot.media_player import MediaPlayer
from src.bot.plex_selfbot import PlexSelfBot


@pytest.fixture
def mock_plex():
    """Create a mock Plex server"""
    mock = Mock(spec=PlexServer)
    mock.library = Mock()
    mock.library.section = Mock(return_value=Mock())
    return mock


@pytest.fixture
def mock_media_player():
    """Create a mock media player"""
    return Mock(spec=MediaPlayer)


@pytest.fixture
async def bot(mock_plex, mock_media_player):
    """Create a test bot instance"""
    with patch("src.bot.plex_selfbot.PlexServer", return_value=mock_plex):
        with patch("src.bot.plex_selfbot.MediaPlayer", return_value=mock_media_player):
            bot = PlexSelfBot("http://fake-plex:32400", "fake-token")
            yield bot
            # Cleanup
            if hasattr(bot, "close"):
                await bot.close()


@pytest.mark.asyncio
async def test_search_command(bot, mock_plex):
    """Test the search command"""
    # Mock Plex search results
    mock_media = Mock()
    mock_media.title = "Test Movie"
    mock_media.duration = 5400000  # 90 minutes
    mock_media.year = 2023

    mock_section = mock_plex.library.section.return_value
    mock_section.search.return_value = [mock_media]

    # Mock context
    ctx = AsyncMock()
    ctx.send = AsyncMock()

    # Call search command
    search_cmd = None
    for command in bot.commands:
        if command.name == "search":
            search_cmd = command
            break

    assert search_cmd is not None
    await search_cmd(ctx, query="test movie")

    # Verify search was performed
    mock_section.search.assert_called_once_with("test movie")

    # Verify response was sent
    ctx.send.assert_called_once()
    call_args = ctx.send.call_args[0]
    assert isinstance(call_args[0], discord.Embed)
    assert "Test Movie" in call_args[0].fields[0].name


@pytest.mark.asyncio
async def test_stream_command_no_voice(bot):
    """Test stream command when user is not in voice channel"""
    # Mock context with author not in voice
    ctx = AsyncMock()
    ctx.author = Mock(spec=discord.Member)
    ctx.author.voice = None

    # Call stream command
    stream_cmd = None
    for command in bot.commands:
        if command.name == "stream":
            stream_cmd = command
            break

    assert stream_cmd is not None
    await stream_cmd(ctx, query="test movie")

    # Verify error message was sent
    ctx.send.assert_called_once_with("You need to be in a voice channel!")


@pytest.mark.asyncio
async def test_stop_command_no_stream(bot):
    """Test stop command when no stream is active"""
    # Mock context
    ctx = AsyncMock()

    # Call stop command
    stop_cmd = None
    for command in bot.commands:
        if command.name == "stop":
            stop_cmd = command
            break

    assert stop_cmd is not None
    await stop_cmd(ctx)

    # Verify error message was sent
    ctx.send.assert_called_once_with("No active stream!")


def test_bot_initialization():
    """Test bot initialization with invalid credentials"""
    with pytest.raises(Exception):
        PlexSelfBot("invalid-url", "invalid-token")
