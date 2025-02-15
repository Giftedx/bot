"""OSRS trading system implementation."""

from typing import Dict, Optional
import discord
from discord.ext import commands
from datetime import datetime, timedelta

from .models import Player, TradeOffer, TradeStatus


class TradeCommands(commands.Cog):
    """Trade-related commands for OSRS."""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_trades: Dict[int, TradeOffer] = {}  # trade_id -> TradeOffer
        self.next_trade_id = 1
    
    @commands.group(invoke_without_command=True)
    async def trade(self, ctx):
        """Trading commands"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="🤝 Trading Commands",
                description="OSRS Trading System",
                color=discord.Color.gold()
            )
            
            commands = """
            `!trade offer <player> <item> <amount>` - Offer a trade
            `!trade accept <trade_id>` - Accept a trade
            `!trade decline <trade_id>` - Decline a trade
            `!trade cancel <trade_id>` - Cancel your trade offer
            `!trade list` - List your active trades
            """
            embed.add_field(name="Commands", value=commands, inline=False)
            
            await ctx.send(embed=embed)
    
    @trade.command(name="offer")
    async def offer_trade(self, ctx, target: discord.Member, item: str, amount: int = 1):
        """Offer a trade to another player"""
        # Get players
        offerer = self.bot.get_player(ctx.author.id)
        if not offerer:
            return await ctx.send(
                "You don't have a character! Use `!osrs create <name>` to make one."
            )
        
        receiver = self.bot.get_player(target.id)
        if not receiver:
            return await ctx.send(f"{target.name} doesn't have a character!")
        
        # Check if in same world
        if not self.bot.world_manager.are_players_in_same_world(offerer, receiver):
            return await ctx.send(f"{target.name} is in a different world!")
        
        # Find item in inventory
        inventory_item = next(
            (i for i in offerer.inventory if i.item.name.lower() == item.lower()),
            None
        )
        if not inventory_item:
            return await ctx.send(f"You don't have any {item} in your inventory!")
        
        # Validate amount
        if amount > inventory_item.quantity:
            return await ctx.send(
                f"You only have {inventory_item.quantity}x {item}!"
            )
        
        # Create trade offer
        trade_id = self.next_trade_id
        self.next_trade_id += 1
        
        trade = TradeOffer(
            id=trade_id,
            offerer_id=ctx.author.id,
            receiver_id=target.id,
            item_id=inventory_item.item.id,
            amount=amount,
            status=TradeStatus.PENDING,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=5)
        )
        
        self.active_trades[trade_id] = trade
        
        # Create response embeds
        offerer_embed = discord.Embed(
            title="Trade Offer Sent",
            description=f"Offered {amount}x {inventory_item.item.name} to {target.name}",
            color=discord.Color.blue()
        )
        offerer_embed.add_field(name="Trade ID", value=str(trade_id))
        offerer_embed.set_footer(text="Trade expires in 5 minutes")
        
        receiver_embed = discord.Embed(
            title="Trade Offer Received",
            description=f"{ctx.author.name} offered {amount}x {inventory_item.item.name}",
            color=discord.Color.green()
        )
        receiver_embed.add_field(
            name="Accept",
            value=f"Use `!trade accept {trade_id}` to accept"
        )
        receiver_embed.add_field(
            name="Decline",
            value=f"Use `!trade decline {trade_id}` to decline"
        )
        receiver_embed.set_footer(text="Trade expires in 5 minutes")
        
        await ctx.send(embed=offerer_embed)
        await target.send(embed=receiver_embed)
    
    @trade.command(name="accept")
    async def accept_trade(self, ctx, trade_id: int):
        """Accept a trade offer"""
        trade = self.active_trades.get(trade_id)
        if not trade:
            return await ctx.send("Trade offer not found!")
        
        # Validate receiver
        if trade.receiver_id != ctx.author.id:
            return await ctx.send("This trade offer is not for you!")
        
        # Check if expired
        if datetime.now() > trade.expires_at:
            del self.active_trades[trade_id]
            return await ctx.send("This trade offer has expired!")
        
        # Check if still pending
        if trade.status != TradeStatus.PENDING:
            return await ctx.send("This trade offer is no longer pending!")
        
        # Get players
        offerer = self.bot.get_player(trade.offerer_id)
        receiver = self.bot.get_player(trade.receiver_id)
        
        # Check if still in same world
        if not self.bot.world_manager.are_players_in_same_world(offerer, receiver):
            return await ctx.send("Trade failed: Players are in different worlds!")
        
        # Find item in offerer's inventory
        inventory_item = next(
            (i for i in offerer.inventory if i.item.id == trade.item_id),
            None
        )
        if not inventory_item or inventory_item.quantity < trade.amount:
            return await ctx.send("Trade failed: Offerer no longer has the items!")
        
        # Check receiver's inventory space
        if len(receiver.inventory) >= 28:
            return await ctx.send("Trade failed: Your inventory is full!")
        
        # Transfer items
        # Remove from offerer
        inventory_item.quantity -= trade.amount
        if inventory_item.quantity == 0:
            offerer.inventory.remove(inventory_item)
        
        # Add to receiver
        receiver_item = next(
            (i for i in receiver.inventory if i.item.id == trade.item_id),
            None
        )
        if receiver_item:
            receiver_item.quantity += trade.amount
        else:
            receiver.inventory.append(
                InventoryItem(item=inventory_item.item, quantity=trade.amount)
            )
        
        # Update trade status
        trade.status = TradeStatus.COMPLETED
        trade.completed_at = datetime.now()
        
        # Create response embed
        embed = discord.Embed(
            title="Trade Completed",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Items Traded",
            value=f"{trade.amount}x {inventory_item.item.name}",
            inline=False
        )
        embed.add_field(
            name="From",
            value=self.bot.get_user(trade.offerer_id).name
        )
        embed.add_field(
            name="To",
            value=self.bot.get_user(trade.receiver_id).name
        )
        
        # Send confirmation to both players
        await ctx.send(embed=embed)
        await self.bot.get_user(trade.offerer_id).send(embed=embed)
        
        # Clean up
        del self.active_trades[trade_id]
    
    @trade.command(name="decline")
    async def decline_trade(self, ctx, trade_id: int):
        """Decline a trade offer"""
        trade = self.active_trades.get(trade_id)
        if not trade:
            return await ctx.send("Trade offer not found!")
        
        # Validate receiver
        if trade.receiver_id != ctx.author.id:
            return await ctx.send("This trade offer is not for you!")
        
        # Check if still pending
        if trade.status != TradeStatus.PENDING:
            return await ctx.send("This trade offer is no longer pending!")
        
        # Update trade status
        trade.status = TradeStatus.DECLINED
        
        # Create response embed
        embed = discord.Embed(
            title="Trade Declined",
            description=f"Trade offer {trade_id} has been declined.",
            color=discord.Color.red()
        )
        
        # Send notifications
        await ctx.send(embed=embed)
        await self.bot.get_user(trade.offerer_id).send(embed=embed)
        
        # Clean up
        del self.active_trades[trade_id]
    
    @trade.command(name="cancel")
    async def cancel_trade(self, ctx, trade_id: int):
        """Cancel your trade offer"""
        trade = self.active_trades.get(trade_id)
        if not trade:
            return await ctx.send("Trade offer not found!")
        
        # Validate offerer
        if trade.offerer_id != ctx.author.id:
            return await ctx.send("This is not your trade offer!")
        
        # Check if still pending
        if trade.status != TradeStatus.PENDING:
            return await ctx.send("This trade offer is no longer pending!")
        
        # Update trade status
        trade.status = TradeStatus.CANCELLED
        
        # Create response embed
        embed = discord.Embed(
            title="Trade Cancelled",
            description=f"Trade offer {trade_id} has been cancelled.",
            color=discord.Color.red()
        )
        
        # Send notifications
        await ctx.send(embed=embed)
        await self.bot.get_user(trade.receiver_id).send(embed=embed)
        
        # Clean up
        del self.active_trades[trade_id]
    
    @trade.command(name="list")
    async def list_trades(self, ctx):
        """List your active trades"""
        # Get player's trades
        player_trades = [
            t for t in self.active_trades.values()
            if (t.offerer_id == ctx.author.id or t.receiver_id == ctx.author.id)
            and t.status == TradeStatus.PENDING
        ]
        
        if not player_trades:
            return await ctx.send("You have no active trades!")
        
        embed = discord.Embed(
            title="Your Active Trades",
            color=discord.Color.blue()
        )
        
        for trade in player_trades:
            # Get item details
            item = self.bot.item_db.get_item(trade.item_id)
            if not item:
                continue
            
            # Format trade info
            if trade.offerer_id == ctx.author.id:
                partner = self.bot.get_user(trade.receiver_id)
                type_str = "Offering to"
            else:
                partner = self.bot.get_user(trade.offerer_id)
                type_str = "Offered by"
            
            value = f"""
            {type_str}: {partner.name}
            Item: {item.name} x{trade.amount}
            Expires: <t:{int(trade.expires_at.timestamp())}:R>
            """
            
            embed.add_field(
                name=f"Trade #{trade.id}",
                value=value,
                inline=False
            )
        
        await ctx.send(embed=embed)


def setup(bot):
    """Add the cog to the bot."""
    bot.add_cog(TradeCommands(bot)) 