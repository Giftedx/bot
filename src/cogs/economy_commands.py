import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from ..lib.economy.grand_exchange import GrandExchange, OfferType, OfferStatus
from ..lib.items.items import ItemManager

class EconomyCommands(commands.Cog):
    """Grand Exchange and Economy Commands"""

    def __init__(self, bot):
        self.bot = bot
        self.ge = GrandExchange()
        self.items = ItemManager()

    @app_commands.command(name='ge_buy', description='Place a buy offer on the Grand Exchange')
    async def ge_buy(
        self, 
        interaction: discord.Interaction, 
        item: str,
        quantity: int,
        price: int
    ):
        """Place a buy offer on the Grand Exchange"""
        # Find item
        item_obj = self.items.get_item_by_name(item)
        if not item_obj:
            await interaction.response.send_message(f"Item '{item}' not found.", ephemeral=True)
            return

        if quantity <= 0 or price <= 0:
            await interaction.response.send_message("Quantity and price must be positive numbers.", ephemeral=True)
            return

        # Place offer
        offer = await self.ge.place_offer(
            player_id=interaction.user.id,
            item_id=item_obj.id,
            quantity=quantity,
            price_per_item=price,
            offer_type=OfferType.BUY
        )

        embed = discord.Embed(
            title="Buy Offer Placed",
            description=f"Buying {quantity}x {item_obj.name} at {price:,} coins each",
            color=discord.Color.green()
        )
        embed.add_field(name="Total Cost", value=f"{quantity * price:,} coins")
        embed.add_field(name="Offer ID", value=str(offer["id"]))
        embed.set_footer(text="Use /ge_status to check your offers")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='ge_sell', description='Place a sell offer on the Grand Exchange')
    async def ge_sell(
        self, 
        interaction: discord.Interaction, 
        item: str,
        quantity: int,
        price: int
    ):
        """Place a sell offer on the Grand Exchange"""
        # Find item
        item_obj = self.items.get_item_by_name(item)
        if not item_obj:
            await interaction.response.send_message(f"Item '{item}' not found.", ephemeral=True)
            return

        if quantity <= 0 or price <= 0:
            await interaction.response.send_message("Quantity and price must be positive numbers.", ephemeral=True)
            return

        # Place offer
        offer = await self.ge.place_offer(
            player_id=interaction.user.id,
            item_id=item_obj.id,
            quantity=quantity,
            price_per_item=price,
            offer_type=OfferType.SELL
        )

        embed = discord.Embed(
            title="Sell Offer Placed",
            description=f"Selling {quantity}x {item_obj.name} at {price:,} coins each",
            color=discord.Color.blue()
        )
        embed.add_field(name="Total Value", value=f"{quantity * price:,} coins")
        embed.add_field(name="Offer ID", value=str(offer["id"]))
        embed.set_footer(text="Use /ge_status to check your offers")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='ge_status', description='Check your Grand Exchange offers')
    async def ge_status(self, interaction: discord.Interaction):
        """Check your Grand Exchange offers"""
        offers = self.ge.get_player_offers(interaction.user.id)
        
        if not offers:
            await interaction.response.send_message("You have no active Grand Exchange offers.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Your Grand Exchange Offers",
            color=discord.Color.gold()
        )

        for offer in offers:
            item = self.items.get_item(offer["item_id"])
            if not item:
                continue

            offer_type = "Buying" if offer["offer_type"] == OfferType.BUY else "Selling"
            progress = f"{offer['quantity_filled']}/{offer['quantity']}"
            
            field_name = f"{offer_type} {item.name} ({progress})"
            field_value = (
                f"Price: {offer['price_per_item']:,} coins each\n"
                f"Total: {offer['quantity'] * offer['price_per_item']:,} coins\n"
                f"Status: {offer['status'].value.title()}\n"
                f"ID: {offer['id']}"
            )
            embed.add_field(name=field_name, value=field_value, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='ge_cancel', description='Cancel a Grand Exchange offer')
    async def ge_cancel(self, interaction: discord.Interaction, offer_id: int):
        """Cancel a Grand Exchange offer"""
        # Check if offer exists and belongs to player
        offers = self.ge.get_player_offers(interaction.user.id)
        offer = next((o for o in offers if o["id"] == offer_id), None)
        
        if not offer:
            await interaction.response.send_message("Offer not found or doesn't belong to you.", ephemeral=True)
            return

        # Cancel offer
        if await self.ge.cancel_offer(offer_id):
            item = self.items.get_item(offer["item_id"])
            offer_type = "buy" if offer["offer_type"] == OfferType.BUY else "sell"
            
            embed = discord.Embed(
                title="Offer Cancelled",
                description=f"Cancelled your {offer_type} offer for {item.name}",
                color=discord.Color.red()
            )
            embed.add_field(name="Progress", value=f"{offer['quantity_filled']}/{offer['quantity']} completed")
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to cancel offer.", ephemeral=True)

    @app_commands.command(name='ge_price', description='Check the current price of an item')
    async def ge_price(self, interaction: discord.Interaction, item: str):
        """Check the current price of an item"""
        # Find item
        item_obj = self.items.get_item_by_name(item)
        if not item_obj:
            await interaction.response.send_message(f"Item '{item}' not found.", ephemeral=True)
            return

        # Get price data
        price_data = self.ge.get_price_data(item_obj.id)
        if not price_data:
            await interaction.response.send_message(f"No price data available for {item_obj.name}.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Price Check: {item_obj.name}",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Current Price", 
            value=f"{price_data['current_price']:,} coins"
        )
        
        change_color = "🟢" if price_data['price_change'] >= 0 else "🔴"
        embed.add_field(
            name="Price Change",
            value=f"{change_color} {price_data['price_change']:,} ({price_data['price_change_percentage']:.1f}%)"
        )
        
        embed.add_field(
            name="Daily Volume",
            value=f"{price_data['daily_volume']:,} traded"
        )
        
        embed.set_footer(text=f"Last updated: {price_data['last_update'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='ge_history', description='View price history for an item')
    async def ge_history(self, interaction: discord.Interaction, item: str):
        """View price history for an item"""
        # Find item
        item_obj = self.items.get_item_by_name(item)
        if not item_obj:
            await interaction.response.send_message(f"Item '{item}' not found.", ephemeral=True)
            return

        # Get active offers
        offers = self.ge.get_item_offers(item_obj.id)
        
        embed = discord.Embed(
            title=f"Market Overview: {item_obj.name}",
            color=discord.Color.gold()
        )

        # Buy offers
        buy_offers = offers[OfferType.BUY]
        if buy_offers:
            buy_offers.sort(key=lambda x: -x["price_per_item"])
            buy_text = "\n".join(
                f"{o['price_per_item']:,} gp x{o['quantity'] - o['quantity_filled']}"
                for o in buy_offers[:5]
            )
        else:
            buy_text = "No buy offers"
        embed.add_field(name="Buy Offers", value=buy_text, inline=True)

        # Sell offers
        sell_offers = offers[OfferType.SELL]
        if sell_offers:
            sell_offers.sort(key=lambda x: x["price_per_item"])
            sell_text = "\n".join(
                f"{o['price_per_item']:,} gp x{o['quantity'] - o['quantity_filled']}"
                for o in sell_offers[:5]
            )
        else:
            sell_text = "No sell offers"
        embed.add_field(name="Sell Offers", value=sell_text, inline=True)

        # Add price data if available
        price_data = self.ge.get_price_data(item_obj.id)
        if price_data:
            embed.add_field(
                name="Current Price",
                value=f"{price_data['current_price']:,} coins",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(EconomyCommands(bot)) 