"""Test OSRS Discord commands."""
import pytest
from unittest.mock import MagicMock

from src.bot.cogs.osrs_commands import OSRSCommands
from src.osrs.models import Player
from .conftest import (
    assert_embed_matches,
    EmbedField
)


@pytest.fixture
def cog(bot: MagicMock) -> OSRSCommands:
    """Create an OSRS commands cog instance."""
    return OSRSCommands(bot)


@pytest.mark.asyncio
async def test_create_character(
    cog: OSRSCommands,
    ctx: MagicMock
) -> None:
    """Test character creation command."""
    # Test creating a new character
    await cog.create_character(ctx, "TestPlayer")
    
    # Verify character was created
    assert ctx.author.id in cog.players
    player = cog.players[ctx.author.id]
    assert player.name == "TestPlayer"
    
    # Verify embed
    ctx.send.assert_called_once()
    embed = ctx.send.call_args.args[0]
    assert_embed_matches(
        embed,
        title="Character Created!",
        color=0x00ff00,
        fields=[
            EmbedField("Name", "TestPlayer"),
            EmbedField(
                "Combat Level",
                str(player.get_combat_level())
            ),
            EmbedField(
                "World",
                "World 301 (Default)",
                inline=False
            )
        ]
    )
    
    # Test creating duplicate character
    ctx.send.reset_mock()
    await cog.create_character(ctx, "AnotherName")
    ctx.send.assert_called_once_with("You already have a character!")


@pytest.mark.asyncio
async def test_show_stats(
    cog: OSRSCommands,
    ctx: MagicMock,
    player: Player
) -> None:
    """Test stats display command."""
    # Test without character
    await cog.show_stats(ctx)
    ctx.send.assert_called_once_with(
        "You don't have a character! Use !create [name] to make one."
    )
    
    # Add player and test stats
    ctx.send.reset_mock()
    cog.players[ctx.author.id] = player
    
    await cog.show_stats(ctx)
    ctx.send.assert_called_once()
    embed = ctx.send.call_args.args[0]
    
    # Verify basic embed properties
    assert_embed_matches(
        embed,
        title=f"{player.name}'s Stats",
        color=0x00ff00
    )
    
    # Verify fields exist
    assert any(f.name == "Combat Skills" for f in embed.fields)
    assert any(f.name == "Other Skills" for f in embed.fields)
    assert any(f.name == "Combat Level" for f in embed.fields)
    
    # Verify field values are non-empty strings
    for field in embed.fields:
        assert isinstance(field.value, str)
        assert field.value != ""


@pytest.mark.asyncio
async def test_world_commands(
    cog: OSRSCommands,
    ctx: MagicMock,
    player: Player,
    test_world: MagicMock
) -> None:
    """Test world-related commands."""
    # Test world command without character
    await cog.show_world(ctx)
    ctx.send.assert_called_once_with(
        "You don't have a character! Use !create [name] to make one."
    )
    
    # Add player and test world commands
    ctx.send.reset_mock()
    cog.players[ctx.author.id] = player
    
    # Test listing worlds
    await cog.list_worlds(ctx)
    ctx.send.assert_called_once()
    embed = ctx.send.call_args.args[0]
    assert_embed_matches(
        embed,
        title="OSRS Worlds",
        color=0x00ff00
    )
    
    # Test joining world
    ctx.send.reset_mock()
    await cog.join_world(ctx, 301)
    ctx.send.assert_called_once()
    embed = ctx.send.call_args.args[0]
    assert_embed_matches(
        embed,
        title="World Change Successful!",
        color=0x00ff00,
        fields=[
            EmbedField("New World", test_world.name),
            EmbedField("Type", test_world.type.title()),
            EmbedField(
                "Players",
                f"{test_world.player_count}/{test_world.max_players}"
            )
        ]
    )


@pytest.mark.asyncio
async def test_cog_load(bot: MagicMock) -> None:
    """Test cog loading."""
    cog = OSRSCommands(bot)
    await cog.cog_load()
    assert isinstance(cog, OSRSCommands)
    assert cog.bot == bot


@pytest.mark.asyncio
async def test_invalid_world_join(
    cog: OSRSCommands,
    ctx: MagicMock,
    player: Player
) -> None:
    """Test joining invalid world."""
    cog.players[ctx.author.id] = player
    
    # Test joining non-existent world
    await cog.join_world(ctx, 999)
    ctx.send.assert_called_once()
    assert "Could not join that world!" in ctx.send.call_args.args[0]


@pytest.mark.asyncio
async def test_filtered_world_list(
    cog: OSRSCommands,
    ctx: MagicMock
) -> None:
    """Test listing worlds with type filter."""
    # Test listing PvP worlds
    await cog.list_worlds(ctx, "pvp")
    ctx.send.assert_called_once()
    embed = ctx.send.call_args.args[0]
    assert_embed_matches(
        embed,
        title="OSRS Worlds",
        color=0x00ff00
    )
    
    # Test listing non-existent world type
    ctx.send.reset_mock()
    await cog.list_worlds(ctx, "invalid_type")
    ctx.send.assert_called_once_with("No worlds found!")


@pytest.mark.asyncio
async def test_skill_requirements(
    cog: OSRSCommands,
    ctx: MagicMock,
    player: Player,
    high_level_player: Player
) -> None:
    """Test skill total world requirements."""
    # Add players
    cog.players[ctx.author.id] = player
    
    # Try joining skill total world with low level player
    await cog.join_world(ctx, 353)  # World 353 (1250+)
    ctx.send.assert_called_once()
    assert "Could not join that world!" in ctx.send.call_args.args[0]
    
    # Try with high level player
    ctx.send.reset_mock()
    cog.players[ctx.author.id] = high_level_player
    await cog.join_world(ctx, 353)
    ctx.send.assert_called_once()
    embed = ctx.send.call_args.args[0]
    assert embed.title == "World Change Successful!"
