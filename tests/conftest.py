"""Test configuration and fixtures."""

import asyncio
import os
import sys
from pathlib import Path
from typing import Generator, AsyncGenerator, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from discord import Embed
from discord.ext.commands import Bot, Context

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.battle_config import BattleSystemConfig
from src.core.models import BattleMove, BattleState, BattleType, StatusEffect
from src.utils.config import ConfigManager
from src.utils.metrics import MetricsManager
from src.utils.cache import Cache
from src.utils.tasks import TaskManager
from src.utils.health import HealthManager
from src.utils.container import Container

# Battle System Fixtures

@pytest.fixture
def battle_config() -> BattleSystemConfig:
    """Fixture for battle system configuration."""
    return BattleSystemConfig()


@pytest.fixture
def basic_move() -> BattleMove:
    """Fixture for basic battle move."""
    return BattleMove(
        name="Basic Attack", move_type="normal", base_power=50, accuracy=90
    )


@pytest.fixture
def perfect_move() -> BattleMove:
    """Fixture for move that always hits."""
    return BattleMove(
        name="Perfect Strike", move_type="normal", base_power=40, accuracy=None
    )


@pytest.fixture
def resource_move() -> BattleMove:
    """Fixture for move with resource cost."""
    return BattleMove(
        name="Energy Blast",
        move_type="special",
        base_power=80,
        accuracy=95,
        energy_cost=20,
    )


@pytest.fixture
def status_move() -> BattleMove:
    """Fixture for move with status effect."""
    effect = StatusEffect(
        name="Poison",
        duration=3,
        effect_type="dot",
        magnitude=5,
        description="Deals damage over time",
        dot_damage=5,
    )
    return BattleMove(
        name="Poison Strike",
        move_type="poison",
        base_power=30,
        accuracy=100,
        status_effects=[effect],
    )


@pytest.fixture
def battle_state() -> BattleState:
    """Fixture for battle state."""
    return BattleState(
        battle_id="test_battle_1",
        battle_type=BattleType.OSRS,
        challenger_id=1,
        opponent_id=2,
        current_turn=1,
        battle_data={
            "challenger_stats": {
                "hp": 100,
                "current_hp": 100,
                "attack": 50,
                "defense": 50,
                "accuracy_stage": 0,
                "current_energy": 100,
            },
            "opponent_stats": {
                "hp": 100,
                "current_hp": 100,
                "attack": 50,
                "defense": 50,
                "evasion_stage": 0,
                "current_energy": 100,
            },
        },
    )


@pytest.fixture
def mock_random() -> float:
    """Fixture for consistent random numbers in tests."""
    return 0.5


@pytest.fixture
def test_data_dir(tmp_path: Path) -> Path:
    """Fixture for test data directory."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def test_log_dir(tmp_path: Path) -> Path:
    """Fixture for test log directory."""
    log_dir = tmp_path / "test_logs"
    log_dir.mkdir()
    return log_dir


# Utility Functions

class EmbedField:
    """Helper class for testing Discord embed fields."""
    def __init__(self, name: str, value: str, inline: bool = False):
        self.name = name
        self.value = value
        self.inline = inline


def assert_embed_matches(
    embed: Embed,
    title: Optional[str] = None,
    description: Optional[str] = None,
    color: Optional[int] = None,
    fields: Optional[List[EmbedField]] = None
) -> None:
    """Assert that an embed matches the expected values."""
    if title is not None:
        assert embed.title == title, (
            f"Title mismatch. Expected '{title}', got '{embed.title}'"
        )
        
    if description is not None:
        assert embed.description == description, (
            f"Description mismatch. "
            f"Expected '{description}', got '{embed.description}'"
        )
        
    if color is not None:
        assert embed.color == color, (
            f"Color mismatch. Expected {color}, got {embed.color}"
        )
        
    if fields is not None:
        assert len(embed.fields) == len(fields), (
            f"Field count mismatch. "
            f"Expected {len(fields)}, got {len(embed.fields)}"
        )
        
        for expected, actual in zip(fields, embed.fields):
            assert actual.name == expected.name, (
                f"Field name mismatch. "
                f"Expected '{expected.name}', got '{actual.name}'"
            )
            assert actual.value == expected.value, (
                f"Field value mismatch for '{expected.name}'. "
                f"Expected '{expected.value}', got '{actual.value}'"
            )
            assert actual.inline == expected.inline, (
                f"Field inline mismatch for '{expected.name}'. "
                f"Expected {expected.inline}, got {actual.inline}"
            )


# Utility Fixtures

@pytest.fixture
def temp_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide a temporary directory for tests."""
    yield tmp_path


@pytest.fixture
def config(temp_dir: Path) -> Generator[ConfigManager, None, None]:
    """Provide a test configuration manager."""
    test_config = ConfigManager(
        config_file=temp_dir / "config.json",
        env_file=temp_dir / ".env"
    )
    # Override paths for testing
    test_config.set('REPO_DATA_DIR', temp_dir / "data")
    test_config.set('CACHE_DIR', temp_dir / "cache")
    test_config.set('LOG_FILE', temp_dir / "logs/test.log")
    yield test_config


@pytest.fixture
def metrics() -> Generator[MetricsManager, None, None]:
    """Provide a test metrics manager."""
    test_metrics = MetricsManager(port=0)  # Disable actual metrics server
    yield test_metrics


@pytest.fixture
def cache(temp_dir: Path) -> Generator[Cache, None, None]:
    """Provide a test cache instance."""
    test_cache = Cache(cache_dir=temp_dir / "cache")
    yield test_cache
    test_cache.clear()


@pytest.fixture
async def task_manager() -> AsyncGenerator[TaskManager, None]:
    """Provide a test task manager."""
    manager = TaskManager(max_concurrent=2, max_queue_size=10)
    await manager.start()
    yield manager
    await manager.stop()


@pytest.fixture
async def health_manager() -> AsyncGenerator[HealthManager, None]:
    """Provide a test health manager."""
    manager = HealthManager()
    await manager.start()
    yield manager
    await manager.stop()


@pytest.fixture
def container() -> Generator[Container, None, None]:
    """Provide a test dependency injection container."""
    test_container = Container()
    yield test_container


@pytest.fixture
def mock_github_api(monkeypatch):
    """Mock GitHub API responses."""
    class MockResponse:
        def __init__(self, data, status_code=200):
            self.data = data
            self.status_code = status_code

        async def json(self):
            return self.data

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    async def mock_get(*args, **kwargs):
        return MockResponse({"name": "test_repo", "stargazers_count": 100})

    monkeypatch.setattr("aiohttp.ClientSession.get", mock_get)
    return mock_get


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("TESTING", "1")
    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    monkeypatch.setenv("DISCORD_TOKEN", "test_token")


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def pytest_configure(config):
    """Configure test environment."""
    os.environ["TESTING"] = "1"

    # Create test directories if they don't exist
    Path("tests/data").mkdir(exist_ok=True)
    Path("tests/logs").mkdir(exist_ok=True)


def pytest_unconfigure(config):
    """Clean up test environment."""
    os.environ.pop("TESTING", None)
