"""Configuration for integration tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator, Generator
import asyncio
from discord.ext.commands import Bot

from src.core.config import ConfigManager


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def bot() -> AsyncGenerator[MagicMock, None]:
    """Create a mock bot instance."""
    bot = MagicMock(spec=Bot)
    bot.add_cog = AsyncMock()
    bot.remove_cog = AsyncMock()

    # Mock config manager
    config_manager = MagicMock(spec=ConfigManager)
    config_manager.get_config.return_value = "!"  # Default prefix
    config_manager.get_secret.return_value = "fake_token"
    bot.config_manager = config_manager

    yield bot

    # Clean up
    for cog_name in bot.cogs.copy():
        await bot.remove_cog(cog_name)


@pytest.fixture(autouse=True)
async def setup_teardown() -> AsyncGenerator[None, None]:
    """Set up and tear down test environment."""
    # Setup
    asyncio.get_event_loop().set_debug(True)

    yield

    # Teardown
    await asyncio.sleep(0)  # Let any pending tasks complete


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest for integration tests."""
    # Register markers
    config.addinivalue_line("markers", "integration: mark test as an integration test")


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Modify test collection."""
    # Add integration marker to all tests in this directory
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.asyncio)


@pytest.fixture(autouse=True)
def mock_discord_api() -> Generator[None, None, None]:
    """Mock Discord API calls."""
    # This would be where we'd mock any direct Discord API calls
    # that our tests might trigger
    yield


@pytest.fixture(autouse=True)
def mock_redis() -> Generator[None, None, None]:
    """Mock Redis connections."""
    # Mock any Redis operations that might be triggered
    # during integration tests
    yield


@pytest.fixture(autouse=True)
def mock_database() -> Generator[None, None, None]:
    """Mock database connections."""
    # Mock any database operations that might be triggered
    # during integration tests
    yield


@pytest.fixture(autouse=True)
def mock_external_apis() -> Generator[None, None, None]:
    """Mock external API calls."""
    # Mock any external API calls that might be triggered
    # during integration tests (e.g., OSRS Wiki API)
    yield


@pytest.fixture(autouse=True)
def integration_timeout() -> Generator[None, None, None]:
    """Set timeout for integration tests."""
    # This helps catch any hanging async operations
    pytest.timeout.set_timeout(5)
    yield
    pytest.timeout.set_timeout(0)


def pytest_assertrepr_compare(op: str, left: object, right: object) -> list[str] | None:
    """Provide custom assertion messages for integration tests."""
    if op == "in" and hasattr(left, "content") and isinstance(right, str):
        return [
            "Message content comparison failed:",
            f"Expected to find: {right}",
            f"In message content: {getattr(left, 'content', 'No content')}",
        ]
    return None
