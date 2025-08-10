import discord
from discord.ext import commands
from discord import app_commands

from ..core.skills import SkillType
from ..core.processing import ProcessingManager, ProcessedItemType
from ..models import Player


class ProcessingCommands(commands.Cog):
    """Commands for OSRS processing activities"""

    def __init__(self, bot):
        self.bot = bot
        self.processing_manager = ProcessingManager()

    @app_commands.command(name="cook")
    @app_commands.describe(fish="The type of fish to cook")
    async def cook(self, interaction: discord.Interaction, fish: str):
        """Cook raw fish to gain Cooking experience"""
        # Get or create player
        player = await Player.get_or_create(interaction.user.id)

        # Convert fish name to processed item type
        try:
            item_type = ProcessedItemType[f"COOKED_{fish.upper()}"]
        except KeyError:
            await interaction.response.send_message(
                "Invalid fish type. Available fish: shrimp, sardine, herring, trout, salmon, lobster, swordfish, shark",
                ephemeral=True,
            )
            return

        # Get recipe
        recipe = self.processing_manager.get_recipe(item_type)
        if not recipe:
            await interaction.response.send_message("That item cannot be cooked.", ephemeral=True)
            return

        # Check if player has required level
        if not player.skills.meets_requirement(SkillType.COOKING, recipe.required_level):
            await interaction.response.send_message(
                f"You need level {recipe.required_level} Cooking to cook {fish.lower()}.",
                ephemeral=True,
            )
            return

        # TODO: Check if player has raw fish in inventory
        has_ingredients = True  # Placeholder until inventory system is implemented

        # Attempt to cook
        success, xp = self.processing_manager.attempt_process(
            item_type, player.skills, has_ingredients
        )

        if success:
            await interaction.response.send_message(
                f"You successfully cook the {fish.lower()} and gain {xp} Cooking XP!"
            )
        else:
            await interaction.response.send_message(
                f"You accidentally burn the {fish.lower()}.", ephemeral=True
            )

    @app_commands.command(name="smelt")
    @app_commands.describe(
        bar="The type of bar to smelt (bronze, iron, steel, mithril, adamant, rune)"
    )
    async def smelt(self, interaction: discord.Interaction, bar: str):
        """Smelt ores into bars to gain Smithing experience"""
        # Get or create player
        player = await Player.get_or_create(interaction.user.id)

        # Convert bar name to processed item type
        try:
            item_type = ProcessedItemType[f"{bar.upper()}_BAR"]
        except KeyError:
            await interaction.response.send_message(
                "Invalid bar type. Available bars: bronze, iron, steel, mithril, adamant, rune",
                ephemeral=True,
            )
            return

        # Get recipe
        recipe = self.processing_manager.get_recipe(item_type)
        if not recipe:
            await interaction.response.send_message("That item cannot be smelted.", ephemeral=True)
            return

        # Check if player has required level
        if not player.skills.meets_requirement(SkillType.SMITHING, recipe.required_level):
            await interaction.response.send_message(
                f"You need level {recipe.required_level} Smithing to smelt {bar.lower()} bars.",
                ephemeral=True,
            )
            return

        # Get required ingredients
        ingredients = self.processing_manager.get_required_ingredients(item_type)
        ingredient_names = [ing.name.lower().replace("_", " ") for ing in ingredients]

        # TODO: Check if player has required ores in inventory
        has_ingredients = True  # Placeholder until inventory system is implemented

        # Attempt to smelt
        success, xp = self.processing_manager.attempt_process(
            item_type, player.skills, has_ingredients
        )

        if success:
            # Format ingredient message
            if len(ingredients) > 1:
                ing_msg = f"Using {' and '.join(ingredient_names)}, you"
            else:
                ing_msg = "You"

            await interaction.response.send_message(
                f"{ing_msg} successfully smelt a {bar.lower()} bar and gain {xp} Smithing XP!"
            )
        else:
            await interaction.response.send_message(
                f"You need {' and '.join(ingredient_names)} to smelt {bar.lower()} bars.",
                ephemeral=True,
            )


async def setup(bot):
    await bot.add_cog(ProcessingCommands(bot))
