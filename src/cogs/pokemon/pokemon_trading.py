import discord
from discord.ext import commands
import asyncio
import json
from typing import Dict, Optional


class PokemonTrading(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_trades: Dict[int, Dict] = {}  # channel_id: trade_data
        self.trade_locks: Dict[int, bool] = {}  # user_id: is_trading

    @commands.group(invoke_without_command=True)
    async def trade(self, ctx):
        """Pokemon trading commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @trade.command(name="start")
    async def start_trade(self, ctx, user: discord.Member):
        """Start a trade with another user"""
        if ctx.author.id in self.trade_locks:
            return await ctx.send("You're already in a trade!")
        if user.id in self.trade_locks:
            return await ctx.send("That user is already in a trade!")
        if user.bot:
            return await ctx.send("You can't trade with bots!")
        if user == ctx.author:
            return await ctx.send("You can't trade with yourself!")

        try:
            # Create trade session
            trade_data = {
                "users": {
                    ctx.author.id: {"confirmed": False, "pokemon": []},
                    user.id: {"confirmed": False, "pokemon": []},
                },
                "message": None,
            }
            self.active_trades[ctx.channel.id] = trade_data
            self.trade_locks[ctx.author.id] = True
            self.trade_locks[user.id] = True

            # Create trade embed
            embed = discord.Embed(
                title="Pokemon Trade",
                description=f"Trade between {ctx.author.mention} and {user.mention}\n"
                f"Use `!trade add <pokemon>` to add Pokemon\n"
                f"Use `!trade confirm` when ready\n"
                f"Use `!trade cancel` to cancel",
                color=discord.Color.blue(),
            )
            trade_data["message"] = await ctx.send(embed=embed)

            # Wait for trade completion or timeout
            try:
                await asyncio.sleep(300)  # 5 minute timeout
                if ctx.channel.id in self.active_trades:
                    await ctx.send("Trade timed out!")
                    await self.cancel_trade(ctx)
            except Exception:
                pass

        except Exception as e:
            await ctx.send(f"Error starting trade: {e}")
            await self.cancel_trade(ctx)

    @trade.command(name="add")
    async def add_pokemon(self, ctx, pokemon_name: str):
        """Add a Pokemon to the trade"""
        if ctx.channel.id not in self.active_trades:
            return await ctx.send("No active trade in this channel!")

        trade = self.active_trades[ctx.channel.id]
        if ctx.author.id not in trade["users"]:
            return await ctx.send("You're not part of this trade!")

        if trade["users"][ctx.author.id]["confirmed"]:
            return await ctx.send(
                "You've already confirmed the trade! Use `!trade unconfirm` first."
            )

        try:
            # Get Pokemon
            pokemon = await self.bot.db.fetchrow(
                "SELECT * FROM pokemon WHERE user_id = $1 AND LOWER(name) = LOWER($2)",
                ctx.author.id,
                pokemon_name,
            )
            if not pokemon:
                return await ctx.send("You don't have that Pokemon!")

            # Check if Pokemon is already in trade
            if pokemon["id"] in [p["id"] for p in trade["users"][ctx.author.id]["pokemon"]]:
                return await ctx.send("That Pokemon is already in the trade!")

            # Add Pokemon to trade
            trade["users"][ctx.author.id]["pokemon"].append(pokemon)

            # Update trade embed
            await self.update_trade_embed(ctx)
            await ctx.message.add_reaction("✅")

        except Exception as e:
            await ctx.send(f"Error adding Pokemon: {e}")

    @trade.command(name="remove")
    async def remove_pokemon(self, ctx, pokemon_name: str):
        """Remove a Pokemon from the trade"""
        if ctx.channel.id not in self.active_trades:
            return await ctx.send("No active trade in this channel!")

        trade = self.active_trades[ctx.channel.id]
        if ctx.author.id not in trade["users"]:
            return await ctx.send("You're not part of this trade!")

        if trade["users"][ctx.author.id]["confirmed"]:
            return await ctx.send(
                "You've already confirmed the trade! Use `!trade unconfirm` first."
            )

        try:
            # Find Pokemon in trade
            user_pokemon = trade["users"][ctx.author.id]["pokemon"]
            pokemon = next(
                (p for p in user_pokemon if p["name"].lower() == pokemon_name.lower()), None
            )
            if not pokemon:
                return await ctx.send("That Pokemon isn't in the trade!")

            # Remove Pokemon from trade
            trade["users"][ctx.author.id]["pokemon"].remove(pokemon)

            # Update trade embed
            await self.update_trade_embed(ctx)
            await ctx.message.add_reaction("✅")

        except Exception as e:
            await ctx.send(f"Error removing Pokemon: {e}")

    @trade.command(name="confirm")
    async def confirm_trade(self, ctx):
        """Confirm the trade"""
        if ctx.channel.id not in self.active_trades:
            return await ctx.send("No active trade in this channel!")

        trade = self.active_trades[ctx.channel.id]
        if ctx.author.id not in trade["users"]:
            return await ctx.send("You're not part of this trade!")

        try:
            trade["users"][ctx.author.id]["confirmed"] = True
            await self.update_trade_embed(ctx)

            # Check if both users have confirmed
            if all(user["confirmed"] for user in trade["users"].values()):
                await self.complete_trade(ctx)

        except Exception as e:
            await ctx.send(f"Error confirming trade: {e}")

    @trade.command(name="unconfirm")
    async def unconfirm_trade(self, ctx):
        """Unconfirm the trade"""
        if ctx.channel.id not in self.active_trades:
            return await ctx.send("No active trade in this channel!")

        trade = self.active_trades[ctx.channel.id]
        if ctx.author.id not in trade["users"]:
            return await ctx.send("You're not part of this trade!")

        try:
            trade["users"][ctx.author.id]["confirmed"] = False
            await self.update_trade_embed(ctx)
        except Exception as e:
            await ctx.send(f"Error unconfirming trade: {e}")

    @trade.command(name="cancel")
    async def cancel_trade(self, ctx):
        """Cancel the trade"""
        if ctx.channel.id not in self.active_trades:
            return await ctx.send("No active trade in this channel!")

        trade = self.active_trades[ctx.channel.id]
        if ctx.author.id not in trade["users"]:
            return await ctx.send("You're not part of this trade!")

        try:
            # Clean up trade
            for user_id in trade["users"]:
                if user_id in self.trade_locks:
                    del self.trade_locks[user_id]
            del self.active_trades[ctx.channel.id]

            await ctx.send("Trade cancelled!")
        except Exception as e:
            await ctx.send(f"Error cancelling trade: {e}")

    async def update_trade_embed(self, ctx):
        """Update the trade embed"""
        trade = self.active_trades[ctx.channel.id]

        embed = discord.Embed(title="Pokemon Trade", color=discord.Color.blue())

        for user_id, data in trade["users"].items():
            user = ctx.guild.get_member(user_id)
            pokemon_list = (
                "\n".join(f"Level {p['level']} {p['name'].title()}" for p in data["pokemon"])
                or "No Pokemon added"
            )

            embed.add_field(
                name=f"{user.display_name}'s Pokemon {'✅' if data['confirmed'] else '❌'}",
                value=pokemon_list,
                inline=True,
            )

        await trade["message"].edit(embed=embed)

    async def complete_trade(self, ctx):
        """Complete the trade"""
        trade = self.active_trades[ctx.channel.id]

        try:
            # Start transaction
            async with self.bot.db.acquire() as conn:
                async with conn.transaction():
                    # Swap Pokemon ownership
                    user_ids = list(trade["users"].keys())
                    for i, user_id in enumerate(user_ids):
                        other_id = user_ids[1 - i]  # Get the other user's ID
                        for pokemon in trade["users"][user_id]["pokemon"]:
                            await conn.execute(
                                "UPDATE pokemon SET user_id = $1 WHERE id = $2",
                                other_id,
                                pokemon["id"],
                            )

            # Clean up trade
            for user_id in trade["users"]:
                if user_id in self.trade_locks:
                    del self.trade_locks[user_id]
            del self.active_trades[ctx.channel.id]

            await ctx.send("Trade completed successfully! 🤝")

        except Exception as e:
            await ctx.send(f"Error completing trade: {e}")
            await self.cancel_trade(ctx)


async def setup(bot):
    await bot.add_cog(PokemonTrading(bot))
