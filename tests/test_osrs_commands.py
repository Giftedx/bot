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


@pytest.mark.asyncio
async def test_fight_command_valid_monster(cog: OSRSCommands, ctx: MagicMock, player: Player):
    # Mock player retrieval
    cog._get_player = MagicMock(return_value=player)
    # Ensure not already in a battle
    cog.battle_manager.get_player_battle = MagicMock(return_value=None)
    # Mock monster data
    cog.data_manager.get_monster_info = MagicMock(return_value={
        'name': 'Goblin', 'combat_level': 2, 'hitpoints': 5, 'max_hit': 1, 'aggressive': False, 'poisonous': False, 'drops': [], 'wiki_url': 'https://wiki', 'examine': 'A small green creature.'
    })
    await cog.fight(ctx, 'Goblin')
    ctx.send.assert_any_call(embed=pytest.helpers.any_embed_with_title("Fight: Goblin"))
    ctx.send.assert_any_call("Battle started with Goblin! Use /attack to fight.")


@pytest.mark.asyncio
async def test_fight_command_invalid_monster(cog: OSRSCommands, ctx: MagicMock, player: Player):
    cog._get_player = MagicMock(return_value=player)
    cog.battle_manager.get_player_battle = MagicMock(return_value=None)
    cog.data_manager.get_monster_info = MagicMock(return_value=None)
    await cog.fight(ctx, 'FakeMonster')
    ctx.send.assert_called_once_with("Monster 'FakeMonster' not found.")


@pytest.mark.asyncio
async def test_fight_command_already_in_battle(cog: OSRSCommands, ctx: MagicMock, player: Player):
    cog._get_player = MagicMock(return_value=player)
    cog.battle_manager.get_player_battle = MagicMock(return_value=MagicMock())
    await cog.fight(ctx, 'Goblin')
    ctx.send.assert_called_once_with("You are already in a battle!")


@pytest.mark.asyncio
async def test_attack_command_not_in_battle(cog: OSRSCommands, ctx: MagicMock, player: Player):
    cog._get_player = MagicMock(return_value=player)
    cog.battle_manager.get_player_battle = MagicMock(return_value=None)
    await cog.attack(ctx)
    ctx.send.assert_called_once_with("You are not in a battle! Use /fight to start one.")


@pytest.mark.asyncio
async def test_flee_command_not_in_battle(cog: OSRSCommands, ctx: MagicMock, player: Player):
    cog._get_player = MagicMock(return_value=player)
    cog.battle_manager.get_player_battle = MagicMock(return_value=None)
    await cog.flee(ctx)
    ctx.send.assert_called_once_with("You are not in a battle! Use /fight to start one.")


@pytest.mark.asyncio
async def test_quests_command(cog: OSRSCommands, ctx: MagicMock, player: Player):
    cog._get_player = MagicMock(return_value=player)
    cog.data_manager.get_all_quests = MagicMock(return_value={'1': {'id': 1, 'name': 'Cooks Assistant', 'difficulty': 'Novice'}})
    player.quest_progress = {1: 'completed'}
    await cog.quests(ctx)
    ctx.send.assert_called_once()
    embed = ctx.send.call_args.kwargs['embed']
    assert "Cooks Assistant" in embed.fields[0].name
    assert "✅" in embed.fields[0].name


@pytest.mark.asyncio
async def test_quest_info_command(cog: OSRSCommands, ctx: MagicMock, player: Player):
    cog._get_player = MagicMock(return_value=player)
    cog.data_manager.get_quest_info = MagicMock(return_value={'id': 1, 'name': 'Cooks Assistant', 'difficulty': 'Novice', 'description': 'Help the cook.', 'quest_points': 1, 'rewards': {}, 'requirements': {}})
    await cog.quest_info(ctx, "Cooks Assistant")
    ctx.send.assert_called_once()
    embed = ctx.send.call_args.kwargs['embed']
    assert embed.title == "Cooks Assistant"


@pytest.mark.asyncio
async def test_achievements_command(cog: OSRSCommands, ctx: MagicMock, player: Player):
    cog._get_player = MagicMock(return_value=player)
    cog.data_manager.get_all_achievements = MagicMock(return_value=[{'id': 1, 'name': 'First Kill', 'description': 'Defeat your first monster.', 'category': 'Combat', 'rewards': {'xp': 50}}])
    cog.data_manager.get_achievement = MagicMock(return_value={'id': 1, 'name': 'First Kill'})
    player.completed_achievements = [1]
    await cog.achievements(ctx)
    ctx.send.assert_called_once()
    embed = ctx.send.call_args.kwargs['embed']
    assert "First Kill" in embed.fields[0].name
    assert "🏆" in embed.fields[0].name


@pytest.mark.asyncio
async def test_collection_log_command(cog: OSRSCommands, ctx: MagicMock, player: Player):
    cog._get_player = MagicMock(return_value=player)
    player.collection_log = {'Tuna': 5}
    cog.data_manager.get_item_info = MagicMock(return_value={'name': 'Tuna', 'category': 'Fish'})
    await cog.collection_log(ctx)
    ctx.send.assert_called_once()
    embed = ctx.send.call_args.kwargs['embed']
    assert "Tuna" in embed.fields[0].name


@pytest.mark.asyncio
async def test_trade_offer_and_accept(cog: OSRSCommands, ctx: MagicMock, player: Player):
    # Setup
    sender_player = player
    sender_player.add_item_to_inventory("Tuna", 1)
    
    receiver_player = Player(user_id=12346, username="Receiver")
    receiver_ctx = MagicMock()
    receiver_ctx.author.id = 12346

    cog._get_player = MagicMock(side_effect=[sender_player, receiver_player, sender_player, receiver_player])
    cog.db_manager.save_player = MagicMock()

    # 1. Sender offers the trade
    await cog.trade_offer(ctx, receiver_ctx.author, "Tuna", 1)
    ctx.send.assert_called_once()
    embed = ctx.send.call_args.kwargs['embed']
    trade_id = int(embed.footer.text.split("ID: ")[1])

    # 2. Receiver accepts the trade
    await cog.trade_accept(receiver_ctx, trade_id)
    receiver_ctx.send.assert_called_once()

    # 3. Verify item transfer
    assert sender_player.has_item_in_inventory("Tuna", 1) is False
    assert receiver_player.has_item_in_inventory("Tuna", 1) is True
    cog.db_manager.save_player.assert_any_call(sender_player)
    cog.db_manager.save_player.assert_any_call(receiver_player)
