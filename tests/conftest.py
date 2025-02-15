"""Common test fixtures and utilities."""
from typing import (
    Any, AsyncGenerator, Generator, List, Optional, Type, TypeVar, cast
)
import pytest
from unittest.mock import AsyncMock, MagicMock
import asyncio
from discord import Embed
from discord.ext.commands import Bot, Context

from src.osrs.models import Player, SkillType
from src.osrs.core.world_manager import World


T = TypeVar('T')


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def bot() -> MagicMock:
    """Create a mock bot instance."""
    bot = MagicMock(spec=Bot)
    bot.add_cog = AsyncMock()
    return bot


@pytest.fixture
def ctx() -> MagicMock:
    """Create a mock context."""
    ctx = MagicMock(spec=Context)
    ctx.send = AsyncMock()
    ctx.author.id = 123456789
    return ctx


@pytest.fixture
def player() -> Player:
    """Create a test player."""
    return Player(
        id=123456789,
        name="TestPlayer"
    )


@pytest.fixture
def high_level_player() -> Player:
    """Create a high level test player."""
    player = Player(
        id=987654321,
        name="HighLevelPlayer"
    )
    
    # Set all skills to level 70
    for skill_type in SkillType:
        player.skills[skill_type].level = 70
        player.skills[skill_type].xp = player.xp_for_level(70)
        
    return player


@pytest.fixture
def test_world() -> World:
    """Create a test game world."""
    return World(
        id=301,
        name="Test World 301",
        type="normal",
        region="us"
    )


@pytest.fixture
async def mock_redis() -> AsyncGenerator[MagicMock, None]:
    """Create a mock Redis instance."""
    redis = MagicMock()
    redis.get = AsyncMock()
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.exists = AsyncMock()
    redis.close = AsyncMock()
    
    yield redis
    
    # Verify Redis was properly closed
    await redis.close()


class EmbedField:
    """Helper class for embed field assertions."""
    def __init__(self, name: str, value: str, inline: bool = True) -> None:
        self.name = name
        self.value = value
        self.inline = inline


def assert_embed_field(
    embed: Embed,
    name: str,
    value: str,
    inline: Optional[bool] = None
) -> None:
    """Assert that an embed has a field with the given name and value."""
    for field in embed.fields:
        if field.name == name and field.value == value:
            if inline is not None:
                assert field.inline == inline, (
                    f"Field '{name}' inline mismatch. "
                    f"Expected {inline}, got {field.inline}"
                )
            return
    pytest.fail(f"Embed field '{name}' with value '{value}' not found")


def assert_embed_color(embed: Embed, color: int) -> None:
    """Assert that an embed has the expected color."""
    assert embed.color == color, f"Expected color {color}, got {embed.color}"


def assert_command_registered(bot: MagicMock, command_name: str) -> None:
    """Assert that a command is registered with the bot."""
    commands = cast(List[Any], bot.add_command.call_args_list)
    for command in commands:
        if command.args[0].name == command_name:
            return
    pytest.fail(f"Command '{command_name}' not registered")


def assert_cog_loaded(bot: MagicMock, cog_type: Type[T]) -> None:
    """Assert that a cog of the given type was loaded."""
    cog_calls = cast(List[Any], bot.add_cog.call_args_list)
    for call in cog_calls:
        if isinstance(call.args[0], cog_type):
            return
    pytest.fail(f"Cog of type {cog_type.__name__} not loaded")


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
