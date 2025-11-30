import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.osrs.commands.processing_commands import ProcessingCommands
from src.osrs.models import Player

@pytest.mark.asyncio
async def test_cook_without_ingredients():
    # Setup
    bot = MagicMock()
    cog = ProcessingCommands(bot)

    # Mock Interaction
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response.send_message = AsyncMock()

    # Mock Player
    mock_player = MagicMock(spec=Player)
    mock_player.id = 123
    # Mock skills as an object that has meets_requirement
    mock_player.skills = MagicMock()
    mock_player.skills.meets_requirement.return_value = True
    mock_player.skills.get_level.return_value = 1

    # Empty inventory
    mock_player.inventory = {}
    mock_player.has_item_in_inventory.side_effect = lambda item, qty=1: False

    # Patch Player.get_or_create to return our mock
    with patch('src.osrs.models.Player.get_or_create', new=AsyncMock(return_value=mock_player), create=True):
        # Execute
        await cog.cook.callback(cog, interaction, "shrimp")

        # Verify
        args, kwargs = interaction.response.send_message.call_args
        message = args[0]

        # If the code proceeds to cook/burn, it means the check is missing
        if "successfully cook" in message or "accidentally burn" in message:
            pytest.fail(f"Processing attempted despite missing ingredients. Message: {message}")

@pytest.mark.asyncio
async def test_smelt_without_ingredients():
    # Setup
    bot = MagicMock()
    cog = ProcessingCommands(bot)

    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response.send_message = AsyncMock()

    mock_player = MagicMock(spec=Player)
    mock_player.id = 123
    mock_player.skills = MagicMock()
    mock_player.skills.meets_requirement.return_value = True
    mock_player.inventory = {}
    mock_player.has_item_in_inventory.side_effect = lambda item, qty=1: False

    with patch('src.osrs.models.Player.get_or_create', new=AsyncMock(return_value=mock_player), create=True):
        await cog.smelt.callback(cog, interaction, "bronze")

        args, kwargs = interaction.response.send_message.call_args
        message = args[0]

        if "successfully smelt" in message:
            pytest.fail(f"Processing attempted despite missing ingredients. Message: {message}")

@pytest.mark.asyncio
async def test_smelt_insufficient_quantity():
    # Setup
    bot = MagicMock()
    cog = ProcessingCommands(bot)

    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response.send_message = AsyncMock()

    mock_player = MagicMock(spec=Player)
    mock_player.id = 123
    mock_player.skills = MagicMock()
    mock_player.skills.meets_requirement.return_value = True
    mock_player.skills.get_level.return_value = 1

    # Player has 1 coal
    # We mock has_item_in_inventory to return True for quantity 1, False for 2
    def has_item_side_effect(item, qty=1):
        if item == "coal":
            return qty <= 1
        return False
    mock_player.has_item_in_inventory.side_effect = has_item_side_effect

    # Mock recipe to require 2 coal
    # We need to mock processing_manager.get_required_ingredients
    # Since processing_manager is created in __init__, we need to access it from cog
    mock_coal = MagicMock()
    mock_coal.name = "COAL"
    cog.processing_manager.get_required_ingredients = MagicMock(return_value=[mock_coal, mock_coal])
    # Also need to ensure get_recipe returns something so checks pass
    cog.processing_manager.get_recipe = MagicMock(return_value=MagicMock(required_level=1))

    with patch('src.osrs.models.Player.get_or_create', new=AsyncMock(return_value=mock_player), create=True):
        await cog.smelt.callback(cog, interaction, "steel")

        args, kwargs = interaction.response.send_message.call_args
        message = args[0]

        # Expect failure message
        if "successfully smelt" in message:
            pytest.fail(f"Processing succeeded despite missing quantity. Message: {message}")

        assert "Missing: 2x coal" in message
