"""Integration tests for bot commands and features."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Generator, List, Any, Optional, Union, cast
from discord import VoiceChannel, VoiceClient, Member, Guild, VoiceState, Message

from src.bot.cogs.media_commands import MediaCommands
from src.bot.cogs.osrs_commands import OSRSCommands


@pytest.fixture
def voice_channel() -> MagicMock:
    """Create a mock voice channel."""
    channel = MagicMock(spec=VoiceChannel)
    channel.name = "Test Channel"
    channel.connect = AsyncMock()
    return channel


@pytest.fixture
def voice_client() -> MagicMock:
    """Create a mock voice client."""
    client = MagicMock(spec=VoiceClient)
    client.disconnect = AsyncMock()
    client.stop = MagicMock()
    return client


@pytest.fixture
def voice_state(voice_channel: MagicMock) -> MagicMock:
    """Create a mock voice state."""
    state = MagicMock(spec=VoiceState)
    state.channel = voice_channel
    return state


@pytest.fixture
def member(voice_state: MagicMock) -> MagicMock:
    """Create a mock member."""
    member = MagicMock(spec=Member)
    member.id = 123456789
    member.voice = voice_state
    member.display_name = "Test User"
    return member


@pytest.fixture
def guild(member: MagicMock) -> MagicMock:
    """Create a mock guild."""
    guild = MagicMock(spec=Guild)
    guild.id = 987654321
    guild.get_member.return_value = member
    return guild


@pytest.fixture
def messages() -> List[Message]:
    """Store sent messages for verification."""
    return []


@pytest.fixture
def ctx(guild: MagicMock, member: MagicMock, messages: List[Message]) -> MagicMock:
    """Create a mock context."""
    ctx = MagicMock()
    ctx.guild = guild
    ctx.author = member

    async def send(content: Optional[Union[str, Any]] = None, **kwargs: Any) -> None:
        message = MagicMock(spec=Message)
        message.content = str(content) if content is not None else None
        message.embeds = [kwargs["embed"]] if "embed" in kwargs else []
        messages.append(message)

    ctx.send = AsyncMock(side_effect=send)
    return ctx


@pytest.fixture
def media_cog(bot: MagicMock) -> MediaCommands:
    """Create a media commands cog instance."""
    return MediaCommands(bot)


@pytest.fixture
def osrs_cog(bot: MagicMock) -> OSRSCommands:
    """Create an OSRS commands cog instance."""
    return OSRSCommands(bot)


@pytest.fixture(autouse=True)
def cleanup() -> Generator[None, None, None]:
    """Clean up after each test."""
    yield
    # Any cleanup code would go here


def assert_message_contains(message: Message, text: str) -> None:
    """Assert that a message contains specific text."""
    content = cast(Optional[str], getattr(message, "content", None))
    if content is not None and text in content:
        return

    embeds = getattr(message, "embeds", [])
    for embed in embeds:
        title = cast(str, getattr(embed, "title", ""))
        description = cast(str, getattr(embed, "description", ""))

        if text in title or text in description:
            return

        for field in getattr(embed, "fields", []):
            name = cast(str, getattr(field, "name", ""))
            value = cast(str, getattr(field, "value", ""))

            if text in name or text in value:
                return

    pytest.fail(f"Message does not contain '{text}'")


@pytest.mark.asyncio
async def test_music_during_combat(
    media_cog: MediaCommands,
    osrs_cog: OSRSCommands,
    ctx: MagicMock,
    voice_client: MagicMock,
    messages: List[Message],
) -> None:
    """Test playing music while in OSRS combat."""
    # Create OSRS character
    await osrs_cog.create_character(ctx, "TestPlayer")
    assert len(messages) > 0
    assert_message_contains(messages[0], "Character Created!")
    messages.clear()

    # Join voice channel
    voice_channel = ctx.author.voice.channel
    voice_channel.connect.return_value = voice_client
    await media_cog.join_voice(ctx)
    assert_message_contains(messages[0], f"Joined {voice_channel.name}")
    messages.clear()

    # Queue some music
    await media_cog.play_media(ctx, query="boss fight music")
    assert_message_contains(messages[0], "Added to queue")
    messages.clear()

    # Verify both systems working together
    assert ctx.guild.id in media_cog.voice_clients
    assert ctx.author.id in osrs_cog.players


@pytest.mark.asyncio
async def test_world_hop_voice_persistence(
    media_cog: MediaCommands,
    osrs_cog: OSRSCommands,
    ctx: MagicMock,
    voice_client: MagicMock,
    messages: List[Message],
) -> None:
    """Test voice connection persists through world hopping."""
    # Set up initial state
    await osrs_cog.create_character(ctx, "TestPlayer")
    messages.clear()

    voice_channel = ctx.author.voice.channel
    voice_channel.connect.return_value = voice_client
    await media_cog.join_voice(ctx)
    messages.clear()

    # Change worlds
    await osrs_cog.join_world(ctx, 302)
    assert_message_contains(messages[0], "World Change Successful!")
    messages.clear()

    # Verify voice connection maintained
    assert ctx.guild.id in media_cog.voice_clients
    assert not voice_client.disconnect.called


@pytest.mark.asyncio
async def test_concurrent_commands(
    media_cog: MediaCommands,
    osrs_cog: OSRSCommands,
    ctx: MagicMock,
    voice_client: MagicMock,
    messages: List[Message],
) -> None:
    """Test running media and OSRS commands concurrently."""
    # Set up character and voice
    await osrs_cog.create_character(ctx, "TestPlayer")
    messages.clear()

    voice_channel = ctx.author.voice.channel
    voice_channel.connect.return_value = voice_client
    await media_cog.join_voice(ctx)
    messages.clear()

    # Queue multiple songs
    for i in range(3):
        await media_cog.play_media(ctx, query=f"song {i+1}")

    # Check stats between songs
    await osrs_cog.show_stats(ctx)
    assert len(messages) == 4  # 3 queue messages + stats embed

    # Verify queue state
    await media_cog.show_queue(ctx)
    queue_embed = messages[-1].embeds[0]
    assert len(queue_embed.fields) == 3


@pytest.mark.asyncio
async def test_error_handling_interaction(
    media_cog: MediaCommands, osrs_cog: OSRSCommands, ctx: MagicMock, messages: List[Message]
) -> None:
    """Test error handling between cogs."""
    # Try media commands without character
    await media_cog.join_voice(ctx)
    assert len(messages) > 0
    messages.clear()

    # Create character but try invalid world
    await osrs_cog.create_character(ctx, "TestPlayer")
    messages.clear()

    await osrs_cog.join_world(ctx, 999)
    assert_message_contains(messages[0], "Could not join that world!")
    messages.clear()

    # Verify media commands still work
    voice_channel = ctx.author.voice.channel
    voice_client = MagicMock(spec=VoiceClient)
    voice_channel.connect.return_value = voice_client

    await media_cog.join_voice(ctx)
    assert_message_contains(messages[0], f"Joined {voice_channel.name}")


@pytest.mark.asyncio
async def test_cog_initialization(bot: MagicMock, messages: List[Message]) -> None:
    """Test cogs initialize properly together."""
    # Initialize cogs
    media_cog = MediaCommands(bot)
    osrs_cog = OSRSCommands(bot)

    await media_cog.cog_load()
    await osrs_cog.cog_load()

    # Verify both cogs loaded
    assert isinstance(media_cog, MediaCommands)
    assert isinstance(osrs_cog, OSRSCommands)
    assert media_cog.bot == bot
    assert osrs_cog.bot == bot
