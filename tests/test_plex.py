import pytest
from typing import Any, AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch
from plexapi.server import PlexServer
from plexapi.exceptions import NotFound, Unauthorized

from src.core.plex import PlexClient
from src.core.exceptions import PlexConnectionError, PlexAuthError, MediaNotFoundError

@pytest.fixture
def mock_plex_server() -> Mock:
    server = Mock(spec=PlexServer)
    server.library = Mock()
    server.sessions = Mock(return_value=[])
    return server

@pytest.fixture
async def plex_client(mock_plex_server: Mock) -> AsyncGenerator[PlexClient, None]:
    client = PlexClient(
        url="http://localhost:32400",
        token="test_token"
    )
    client._server = mock_plex_server
    yield client
    await client.close()

@pytest.mark.asyncio
async def test_plex_connection_success(mock_plex_server: Mock) -> None:
    """Test successful Plex server connection."""
    with patch('plexapi.server.PlexServer', return_value=mock_plex_server):
        client = PlexClient(
            url="http://localhost:32400",
            token="test_token"
        )
        await client.connect()
        assert client.is_connected()

@pytest.mark.asyncio
async def test_plex_connection_failure() -> None:
    """Test Plex server connection failure."""
    with patch('plexapi.server.PlexServer', side_effect=Unauthorized):
        client = PlexClient(
            url="http://localhost:32400",
            token="invalid_token"
        )
        with pytest.raises(PlexAuthError):
            await client.connect()

@pytest.mark.asyncio
async def test_plex_media_search(plex_client: PlexClient, mock_plex_server: Mock) -> None:
    """Test media search functionality."""
    mock_media = Mock()
    mock_media.title = "Test Movie"
    mock_media.type = "movie"
    
    mock_plex_server.library.search.return_value = [mock_media]
    
    results = await plex_client.search_media("Test Movie")
    assert len(results) == 1
    assert results[0].title == "Test Movie"
    mock_plex_server.library.search.assert_called_once_with("Test Movie")

@pytest.mark.asyncio
async def test_plex_media_not_found(plex_client: PlexClient, mock_plex_server: Mock) -> None:
    """Test media not found scenario."""
    mock_plex_server.library.search.return_value = []
    
    with pytest.raises(MediaNotFoundError):
        await plex_client.search_media("Nonexistent Media")

@pytest.mark.asyncio
async def test_plex_active_sessions(plex_client: PlexClient, mock_plex_server: Mock) -> None:
    """Test active sessions retrieval."""
    mock_session = Mock()
    mock_session.title = "Currently Playing"
    mock_session.usernames = ["test_user"]
    
    mock_plex_server.sessions.return_value = [mock_session]
    
    sessions = await plex_client.get_active_sessions()
    assert len(sessions) == 1
    assert sessions[0].title == "Currently Playing"
    assert "test_user" in sessions[0].usernames

@pytest.mark.asyncio
async def test_plex_library_sections(plex_client: PlexClient, mock_plex_server: Mock) -> None:
    """Test library sections retrieval."""
    mock_section = Mock()
    mock_section.title = "Movies"
    mock_section.type = "movie"
    
    mock_plex_server.library.sections.return_value = [mock_section]
    
    sections = await plex_client.get_library_sections()
    assert len(sections) == 1
    assert sections[0].title == "Movies"
    assert sections[0].type == "movie"

@pytest.mark.asyncio
async def test_plex_reconnection(plex_client: PlexClient, mock_plex_server: Mock) -> None:
    """Test automatic reconnection on connection loss."""
    # Simulate connection loss
    mock_plex_server.library.search.side_effect = [
        ConnectionError,  # First call fails
        [Mock(title="Test Movie")]  # Second call succeeds after reconnect
    ]
    
    results = await plex_client.search_media("Test Movie")
    assert len(results) == 1
    assert results[0].title == "Test Movie"
    assert mock_plex_server.library.search.call_count == 2