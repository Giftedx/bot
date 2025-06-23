from typing import Dict, Optional

import discord
from discord.ext import commands


class EconomySystem:
    """Shared currency system for cross-system interactions"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.currency_name = "Coins"
        self.currency_emoji = "🪙"
        self.balances: Dict[int, int] = {}  # user_id: balance

    def get_balance(self, user_id: int) -> int:
        """Get user's coin balance"""
        return self.balances.get(user_id, 0)

    async def add_coins(self, user_id: int, amount: int) -> bool:
        """Add coins to user's balance"""
        if amount <= 0:
            return False

        self.balances[user_id] = self.get_balance(user_id) + amount
        return True

    async def remove_coins(self, user_id: int, amount: int) -> bool:
        """Remove coins from user's balance"""
        if amount <= 0 or self.get_balance(user_id) < amount:
            return False

        self.balances[user_id] -= amount
        return True

    async def transfer_coins(self, from_id: int, to_id: int, amount: int) -> bool:
        """Transfer coins between users"""
        if not await self.remove_coins(from_id, amount):
            return False
        return await self.add_coins(to_id, amount)

    async def show_balance(
        self, ctx: commands.Context, user: Optional[discord.Member] = None
    ) -> None:
        """Show user's coin balance"""
        target_user = user or ctx.author
        balance = self.get_balance(target_user.id)

        embed = discord.Embed(
            title=f"{self.currency_emoji} {target_user.display_name}'s Balance",
            description=f"{balance} {self.currency_name}",
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed)


class EconomyCommands(commands.Cog):
    """Commands for the shared economy system"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.economy = EconomySystem(bot)

    @commands.command(name="coins")
    async def coins(self, ctx: commands.Context, user: Optional[discord.Member] = None) -> None:
        """Check your coin balance"""
        await self.economy.show_balance(ctx, user)

    @commands.command(name="transfer")
    async def transfer(self, ctx: commands.Context, amount: int, recipient: discord.Member) -> None:
        """Transfer coins to another user"""
        success = await self.economy.transfer_coins(ctx.author.id, recipient.id, amount)

        if success:
            msg = (
                f"✅ Transferred {amount} {self.economy.currency_name} "
                f"to {recipient.display_name}!"
            )
        else:
            msg = "❌ Transfer failed. Check your balance and try again."

        await ctx.send(msg)


async def setup(bot: commands.Bot) -> None:
    """Add the economy commands cog to the bot"""
    await bot.add_cog(EconomyCommands(bot))
