import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List

from ..lib.items.items import ItemManager, Bank, ItemSlot

class ItemCommands(commands.Cog):
    """Item and Bank Management Commands"""

    def __init__(self, bot):
        self.bot = bot
        self.items = ItemManager()

    @app_commands.command(name='bank', description='View your bank')
    async def view_bank(
        self,
        interaction: discord.Interaction,
        tab: Optional[int] = None,
        page: int = 1
    ):
        """View your bank contents"""
        if page < 1:
            await interaction.response.send_message("Page number must be positive.", ephemeral=True)
            return

        # Get player's bank from database
        bank = await self.get_player_bank(interaction.user.id)
        if not bank:
            await interaction.response.send_message(
                "You don't have a bank account yet. Start collecting items!",
                ephemeral=True
            )
            return

        per_page = 10
        offset = (page - 1) * per_page

        if tab is not None:
            # View specific tab
            if tab not in bank.tabs:
                await interaction.response.send_message(f"Tab {tab} doesn't exist.", ephemeral=True)
                return
            
            items = bank.get_tab_contents(tab)
            title = f"Bank Tab {tab}"
        else:
            # View all items
            items = bank.items
            title = "Bank"

        # Sort items by value
        sorted_items = sorted(
            items.items(),
            key=lambda x: (
                self.items.get_item(x[0]).data["cost"] * x[1]
                if self.items.get_item(x[0]) else 0
            ),
            reverse=True
        )

        # Paginate items
        total_pages = (len(sorted_items) + per_page - 1) // per_page
        if page > total_pages:
            await interaction.response.send_message(
                f"Invalid page number. Total pages: {total_pages}",
                ephemeral=True
            )
            return

        page_items = sorted_items[offset:offset + per_page]

        embed = discord.Embed(
            title=title,
            color=discord.Color.gold()
        )

        for item_id, quantity in page_items:
            item = self.items.get_item(item_id)
            if not item:
                continue

            value = item.data["cost"] * quantity
            embed.add_field(
                name=f"{item.name} x{quantity:,}",
                value=f"Value: {value:,} coins",
                inline=False
            )

        total_value = bank.get_total_value(self.items)
        embed.set_footer(text=f"Page {page}/{total_pages} | Total Value: {total_value:,} coins")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='price', description='Check the price of an item')
    async def price_check(self, interaction: discord.Interaction, item: str):
        """Check the price and details of an item"""
        item_obj = self.items.get_item_by_name(item)
        if not item_obj:
            await interaction.response.send_message(f"Item '{item}' not found.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Item Details: {item_obj.name}",
            color=discord.Color.blue()
        )

        # Basic info
        embed.add_field(name="ID", value=str(item_obj.id), inline=True)
        embed.add_field(name="Cost", value=f"{item_obj.data['cost']:,} coins", inline=True)
        
        if item_obj.data["examine"]:
            embed.add_field(name="Examine", value=item_obj.data["examine"], inline=False)

        # Properties
        properties = []
        if item_obj.data["tradeable"]:
            properties.append("Tradeable")
        if item_obj.data["stackable"]:
            properties.append("Stackable")
        if item_obj.data["noted"]:
            properties.append("Noted")
        if item_obj.data["noteable"]:
            properties.append("Noteable")
        if item_obj.data["quest_item"]:
            properties.append("Quest Item")
        
        if properties:
            embed.add_field(name="Properties", value=", ".join(properties), inline=False)

        # Equipment info
        if item_obj.data["equipment_slot"]:
            slot = item_obj.data["equipment_slot"]
            embed.add_field(name="Equipment Slot", value=slot.value.title(), inline=True)

            if item_obj.data["equipment_stats"]:
                stats = []
                for stat, value in item_obj.data["equipment_stats"].items():
                    if value != 0:
                        stats.append(f"{stat.title()}: {value:+d}")
                if stats:
                    embed.add_field(name="Equipment Stats", value="\n".join(stats), inline=False)

        # Requirements
        if item_obj.data["requirements"]:
            reqs = []
            for skill, level in item_obj.data["requirements"].items():
                reqs.append(f"{skill.title()}: {level}")
            embed.add_field(name="Requirements", value="\n".join(reqs), inline=False)

        # Alchemy values
        if item_obj.data["high_alch"]:
            embed.add_field(
                name="Alchemy",
                value=f"High: {item_obj.data['high_alch']:,}\nLow: {item_obj.data['low_alch']:,}",
                inline=True
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='search', description='Search for items')
    async def search_items(
        self,
        interaction: discord.Interaction,
        query: str,
        page: int = 1
    ):
        """Search for items by name"""
        if page < 1:
            await interaction.response.send_message("Page number must be positive.", ephemeral=True)
            return

        # Search items
        matches = []
        query = query.lower()
        for item in self.items.items.values():
            if query in item.name.lower() or any(query in alias for alias in item.aliases):
                matches.append(item)

        if not matches:
            await interaction.response.send_message(
                f"No items found matching '{query}'.",
                ephemeral=True
            )
            return

        # Sort by name
        matches.sort(key=lambda x: x.name)

        # Paginate results
        per_page = 10
        offset = (page - 1) * per_page
        total_pages = (len(matches) + per_page - 1) // per_page

        if page > total_pages:
            await interaction.response.send_message(
                f"Invalid page number. Total pages: {total_pages}",
                ephemeral=True
            )
            return

        page_items = matches[offset:offset + per_page]

        embed = discord.Embed(
            title=f"Item Search: {query}",
            color=discord.Color.blue()
        )

        for item in page_items:
            value_text = f"Cost: {item.data['cost']:,} coins"
            if item.data["equipment_slot"]:
                value_text += f"\nSlot: {item.data['equipment_slot'].value.title()}"
            
            embed.add_field(
                name=item.name,
                value=value_text,
                inline=False
            )

        embed.set_footer(text=f"Page {page}/{total_pages} | Found {len(matches)} items")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='equipment', description='View your equipment')
    async def view_equipment(self, interaction: discord.Interaction):
        """View your equipped items"""
        # Get player's equipment from database
        equipment = await self.get_player_equipment(interaction.user.id)
        if not equipment:
            await interaction.response.send_message(
                "You have no equipment. Start gearing up!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{interaction.user.name}'s Equipment",
            color=discord.Color.blue()
        )

        total_value = 0
        for slot in ItemSlot:
            item_id = equipment.get(slot)
            if item_id:
                item = self.items.get_item(item_id)
                if item:
                    value = item.data["cost"]
                    total_value += value
                    
                    # Add stats if available
                    stats_text = ""
                    if item.data["equipment_stats"]:
                        stats = []
                        for stat, value in item.data["equipment_stats"].items():
                            if value != 0:
                                stats.append(f"{stat.title()}: {value:+d}")
                        if stats:
                            stats_text = f"\n{', '.join(stats)}"
                    
                    embed.add_field(
                        name=slot.value.title(),
                        value=f"{item.name}\nValue: {value:,} coins{stats_text}",
                        inline=True
                    )
            else:
                embed.add_field(
                    name=slot.value.title(),
                    value="Empty",
                    inline=True
                )

        embed.set_footer(text=f"Total Value: {total_value:,} coins")
        await interaction.response.send_message(embed=embed)

    async def get_player_bank(self, player_id: int) -> Optional[Bank]:
        """Get a player's bank from the database"""
        # TODO: Implement database retrieval
        # For now, return a new Bank instance
        return Bank()

    async def get_player_equipment(self, player_id: int) -> Optional[dict]:
        """Get a player's equipment from the database"""
        # TODO: Implement database retrieval
        # Return format: Dict[ItemSlot, int] (slot -> item_id)
        return {}

async def setup(bot):
    await bot.add_cog(ItemCommands(bot)) 