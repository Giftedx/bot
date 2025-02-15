"""Test media playback commands."""
from typing import Generator
import pytest
from unittest.mock import AsyncMock, MagicMock
from discord import (
    VoiceChannel, VoiceClient, Member,
    Guild, VoiceState, Embed,
    ClientException
)

from src.bot.cogs.media_commands import MediaCommands


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
def ctx(guild: MagicMock, member: MagicMock) -> MagicMock:
    """Create a mock context."""
    ctx = MagicMock()
    ctx.guild = guild
    ctx.author = member
    ctx.send = AsyncMock()
    return ctx


@pytest.fixture
def cog(bot: MagicMock) -> MediaCommands:
    """Create a media commands cog instance."""
    return MediaCommands(bot)


@pytest.fixture(autouse=True)
def cleanup() -> Generator[None, None, None]:
    """Clean up after each test."""
    yield
    # Any cleanup code would go here


@pytest.mark.asyncio
async def test_join_voice(
    cog: MediaCommands,
    ctx: MagicMock,
    voice_channel: MagicMock,
    voice_client: MagicMock
) -> None:
    """Test joining a voice channel."""
    voice_channel.connect.return_value = voice_client
    
    # Test joining specific channel
    await cog.join_voice(ctx, voice_channel)
    voice_channel.connect.assert_called_once()
    assert ctx.guild.id in cog.voice_clients
    ctx.send.assert_called_with(f"Joined {voice_channel.name}!")
    
    # Reset mocks
    ctx.send.reset_mock()
    voice_channel.connect.reset_mock()
    cog.voice_clients.clear()
    
    # Test joining author's channel
    await cog.join_voice(ctx)
    voice_channel.connect.assert_called_once()
    assert ctx.guild.id in cog.voice_clients
    ctx.send.assert_called_with(f"Joined {voice_channel.name}!")


@pytest.mark.asyncio
async def test_join_voice_errors(
    cog: MediaCommands,
    ctx: MagicMock,
    voice_channel: MagicMock
) -> None:
    """Test error cases when joining voice."""
    # Test when user not in voice
    ctx.author.voice = None
    await cog.join_voice(ctx)
    ctx.send.assert_called_with("You need to be in a voice channel!")
    
    # Test connection failure
    ctx.author.voice = voice_channel
    voice_channel.connect.side_effect = ClientException("Connection failed")
    await cog.join_voice(ctx)
    ctx.send.assert_called_with("Failed to join voice channel!")


@pytest.mark.asyncio
async def test_leave_voice(
    cog: MediaCommands,
    ctx: MagicMock,
    voice_client: MagicMock
) -> None:
    """Test leaving a voice channel."""
    # Test leaving when not in a channel
    await cog.leave_voice(ctx)
    ctx.send.assert_called_with("Not in a voice channel!")
    voice_client.disconnect.assert_not_called()
    
    # Test leaving when in a channel
    cog.voice_clients[ctx.guild.id] = voice_client
    await cog.leave_voice(ctx)
    voice_client.disconnect.assert_called_once()
    assert ctx.guild.id not in cog.voice_clients
    ctx.send.assert_called_with("Left voice channel!")


@pytest.mark.asyncio
async def test_leave_voice_errors(
    cog: MediaCommands,
    ctx: MagicMock,
    voice_client: MagicMock
) -> None:
    """Test error cases when leaving voice."""
    # Test disconnect failure
    cog.voice_clients[ctx.guild.id] = voice_client
    voice_client.disconnect.side_effect = ClientException("Disconnect failed")
    await cog.leave_voice(ctx)
    ctx.send.assert_called_with("Failed to leave voice channel!")


@pytest.mark.asyncio
async def test_play_media(
    cog: MediaCommands,
    ctx: MagicMock,
    voice_client: MagicMock
) -> None:
    """Test playing media."""
    # Test playing when not in a channel
    await cog.play_media(ctx, query="test song")
    ctx.send.assert_called_with("Not in a voice channel!")
    
    # Test playing when in a channel
    cog.voice_clients[ctx.guild.id] = voice_client
    await cog.play_media(ctx, query="test song")
    assert len(cog.queues[ctx.guild.id]) == 1
    assert cog.queues[ctx.guild.id][0]["query"] == "test song"
    ctx.send.assert_called_with("Added to queue: test song")


@pytest.mark.asyncio
async def test_stop_playback(
    cog: MediaCommands,
    ctx: MagicMock,
    voice_client: MagicMock
) -> None:
    """Test stopping playback."""
    # Test stopping when not playing
    await cog.stop_playback(ctx)
    ctx.send.assert_called_with("Not playing anything!")
    voice_client.stop.assert_not_called()
    
    # Test stopping when playing
    cog.voice_clients[ctx.guild.id] = voice_client
    await cog.stop_playback(ctx)
    voice_client.stop.assert_called_once()
    ctx.send.assert_called_with("Stopped playback!")


@pytest.mark.asyncio
async def test_stop_playback_errors(
    cog: MediaCommands,
    ctx: MagicMock,
    voice_client: MagicMock
) -> None:
    """Test error cases when stopping playback."""
    # Test stop failure
    cog.voice_clients[ctx.guild.id] = voice_client
    voice_client.stop.side_effect = Exception("Stop failed")
    await cog.stop_playback(ctx)
    ctx.send.assert_called_with("Failed to stop playback!")


@pytest.mark.asyncio
async def test_show_queue(
    cog: MediaCommands,
    ctx: MagicMock
) -> None:
    """Test showing the queue."""
    # Test showing empty queue
    await cog.show_queue(ctx)
    ctx.send.assert_called_with("Queue is empty!")
    
    # Test showing queue with items
    cog.queues[ctx.guild.id] = [
        {"query": "song 1", "requester": ctx.author.id},
        {"query": "song 2", "requester": ctx.author.id}
    ]
    
    await cog.show_queue(ctx)
    ctx.send.assert_called_once()
    call_args = ctx.send.call_args
    assert len(call_args.args) == 1
    embed = call_args.args[0]
    assert isinstance(embed, Embed)
    assert embed.title == "Media Queue"
    assert len(embed.fields) == 2
    assert embed.fields[0].name == "1. song 1"
    assert embed.fields[1].name == "2. song 2"


@pytest.mark.asyncio
async def test_show_queue_errors(
    cog: MediaCommands,
    ctx: MagicMock
) -> None:
    """Test error cases when showing queue."""
    # Test with invalid requester
    cog.queues[ctx.guild.id] = [
        {"query": "song 1", "requester": 999999}  # Invalid user ID
    ]
    ctx.guild.get_member.return_value = None
    
    await cog.show_queue(ctx)
    embed = ctx.send.call_args.args[0]
    assert "Unknown" in embed.fields[0].value


@pytest.mark.asyncio
async def test_cog_load(bot: MagicMock) -> None:
    """Test cog loading."""
    cog = MediaCommands(bot)
    await cog.cog_load()
    assert isinstance(cog, MediaCommands)
    assert cog.bot == bot


@pytest.mark.asyncio
async def test_dm_commands(
    cog: MediaCommands,
    ctx: MagicMock
) -> None:
    """Test commands in DM context."""
    # Simulate DM context
    ctx.guild = None
    
    # Test each command
    await cog.join_voice(ctx)
    ctx.send.assert_called_with("This command can only be used in a server!")
    
    ctx.send.reset_mock()
    await cog.leave_voice(ctx)
    assert not ctx.send.called  # Should return silently
    
    ctx.send.reset_mock()
    await cog.play_media(ctx, query="test")
    assert not ctx.send.called  # Should return silently
    
    ctx.send.reset_mock()
    await cog.stop_playback(ctx)
    assert not ctx.send.called  # Should return silently
    
    ctx.send.reset_mock()
    await cog.show_queue(ctx)
    assert not ctx.send.called  # Should return silently
