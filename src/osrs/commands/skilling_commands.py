import discord
from discord.ext import commands
from discord import app_commands

from ..core.skills import SkillType
from ..core.skilling import ResourceType, SkillingManager
from ..models import Player


class SkillingCommands(commands.Cog):
    """Commands for OSRS skilling activities"""

    def __init__(self, bot):
        self.bot = bot
        self.skilling_manager = SkillingManager()

    @app_commands.command(name="stats")
    async def stats(self, interaction: discord.Interaction):
        """View your skill levels and experience"""
        # Get or create player
        player = await Player.get_or_create(interaction.user.id)

        # Create embed with all skills
        embed = discord.Embed(
            title=f"{interaction.user.name}'s Skills", color=discord.Color.green()
        )

        # Add combat level
        combat_level = player.skills.get_combat_level()
        embed.add_field(name="Combat Level", value=str(combat_level), inline=False)

        # Add all skills
        for skill in SkillType:
            level = player.skills.get_level(skill)
            xp = player.skills.get_xp(skill)
            embed.add_field(
                name=skill.name.capitalize(), value=f"Level: {level}\nXP: {int(xp):,}", inline=True
            )

        # Add total level and XP
        total_level = player.skills.get_total_level()
        total_xp = player.skills.get_total_xp()
        embed.add_field(
            name="Totals",
            value=f"Total Level: {total_level:,}\nTotal XP: {int(total_xp):,}",
            inline=False,
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="chop")
    @app_commands.describe(tree="The type of tree to chop")
    async def chop(self, interaction: discord.Interaction, tree: str):
        """Chop down trees to gain Woodcutting experience"""
        # Get or create player
        player = await Player.get_or_create(interaction.user.id)

        # Convert tree name to resource type
        try:
            tree_type = ResourceType[f"{tree.upper()}_TREE"]
        except KeyError:
            await interaction.response.send_message(
                "Invalid tree type. Available trees: normal, oak, willow, maple, yew, magic",
                ephemeral=True,
            )
            return

        # Attempt to chop the tree
        success, xp = self.skilling_manager.attempt_gather(tree_type, player.skills)

        if success:
            await interaction.response.send_message(
                f"You successfully chop down the {tree.lower()} tree and gain {xp} Woodcutting XP!"
            )
        else:
            resource = self.skilling_manager.get_resource(tree_type)
            if not player.skills.meets_requirement(SkillType.WOODCUTTING, resource.required_level):
                await interaction.response.send_message(
                    f"You need level {resource.required_level} Woodcutting to chop {tree.lower()} trees.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"You fail to chop down the {tree.lower()} tree.", ephemeral=True
                )

    @app_commands.command(name="mine")
    @app_commands.describe(ore="The type of ore to mine")
    async def mine(self, interaction: discord.Interaction, ore: str):
        """Mine ores to gain Mining experience"""
        # Get or create player
        player = await Player.get_or_create(interaction.user.id)

        # Convert ore name to resource type
        try:
            ore_type = ResourceType[f"{ore.upper()}_ORE"]
        except KeyError:
            if ore.upper() == "COAL":
                ore_type = ResourceType.COAL
            else:
                await interaction.response.send_message(
                    "Invalid ore type. Available ores: copper, tin, iron, coal, mithril, adamantite, runite",
                    ephemeral=True,
                )
                return

        # Attempt to mine the ore
        success, xp = self.skilling_manager.attempt_gather(ore_type, player.skills)

        if success:
            await interaction.response.send_message(
                f"You successfully mine some {ore.lower()} and gain {xp} Mining XP!"
            )
        else:
            resource = self.skilling_manager.get_resource(ore_type)
            if not player.skills.meets_requirement(SkillType.MINING, resource.required_level):
                await interaction.response.send_message(
                    f"You need level {resource.required_level} Mining to mine {ore.lower()}.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"You fail to mine the {ore.lower()}.", ephemeral=True
                )

    @app_commands.command(name="fish")
    @app_commands.describe(fish="The type of fish to catch")
    async def fish(self, interaction: discord.Interaction, fish: str):
        """Fish to gain Fishing experience"""
        # Get or create player
        player = await Player.get_or_create(interaction.user.id)

        # Convert fish name to resource type
        try:
            fish_type = ResourceType[fish.upper()]
        except KeyError:
            await interaction.response.send_message(
                "Invalid fish type. Available fish: shrimp, sardine, herring, trout, salmon, lobster, swordfish, shark",
                ephemeral=True,
            )
            return

        # Attempt to catch the fish
        success, xp = self.skilling_manager.attempt_gather(fish_type, player.skills)

        if success:
            await interaction.response.send_message(
                f"You successfully catch a {fish.lower()} and gain {xp} Fishing XP!"
            )
        else:
            resource = self.skilling_manager.get_resource(fish_type)
            if not player.skills.meets_requirement(SkillType.FISHING, resource.required_level):
                await interaction.response.send_message(
                    f"You need level {resource.required_level} Fishing to catch {fish.lower()}.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"You fail to catch the {fish.lower()}.", ephemeral=True
                )


async def setup(bot):
    await bot.add_cog(SkillingCommands(bot))
