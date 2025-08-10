import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from typing import Dict

from src.core.bot import Bot


class PokemonTrading(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.active_trades: Dict[int, Dict] = {}  # channel_id: trade_data
        self.trade_locks: Dict[int, bool] = {}  # user_id: is_trading

    trade = app_commands.Group(name="trade", description="Pokemon trading commands")

    @trade.command(name="start", description="Start a trade with another user")
    async def start_trade(self, interaction: discord.Interaction, user: discord.Member):
        """Start a trade with another user"""
        if interaction.user.id in self.trade_locks:
            return await interaction.response.send_message("You're already in a trade!", ephemeral=True)
        if user.id in self.trade_locks:
            return await interaction.response.send_message("That user is already in a trade!", ephemeral=True)
        if user.bot:
            return await interaction.response.send_message("You can't trade with bots!", ephemeral=True)
        if user == interaction.user:
            return await interaction.response.send_message("You can't trade with yourself!", ephemeral=True)

        try:
            trade_data = {
                "users": {
                    interaction.user.id: {"confirmed": False, "pokemon": []},
                    user.id: {"confirmed": False, "pokemon": []},
                },
                "message_id": None,
                "channel_id": interaction.channel_id,
            }
            self.active_trades[interaction.channel_id] = trade_data
            self.trade_locks[interaction.user.id] = True
            self.trade_locks[user.id] = True

            embed = discord.Embed(
                title="Pokemon Trade",
                description=f"Trade between {interaction.user.mention} and {user.mention}\n"
                f"Use `/trade add <pokemon>` to add Pokemon\n"
                f"Use `/trade confirm` when ready\n"
                f"Use `/trade cancel` to cancel",
                color=discord.Color.blue(),
            )
            await interaction.response.send_message(embed=embed)
            message = await interaction.original_response()
            trade_data["message_id"] = message.id

            await asyncio.sleep(300)
            if interaction.channel_id in self.active_trades:
                await self.cancel_trade_logic(interaction.channel_id)
                await interaction.followup.send("Trade timed out!")

        except Exception as e:
            await self.cancel_trade_logic(interaction.channel_id)
            await interaction.followup.send(f"Error starting trade: {e}", ephemeral=True)

    @trade.command(name="add", description="Add a Pokemon to the trade")
    @app_commands.describe(pokemon_name="The name of the pokemon to add.")
    async def add_pokemon(self, interaction: discord.Interaction, pokemon_name: str):
        """Add a Pokemon to the trade"""
        if interaction.channel_id not in self.active_trades:
            return await interaction.response.send_message("No active trade in this channel!", ephemeral=True)

        trade = self.active_trades[interaction.channel_id]
        if interaction.user.id not in trade["users"]:
            return await interaction.response.send_message("You're not part of this trade!", ephemeral=True)

        if trade["users"][interaction.user.id]["confirmed"]:
            return await interaction.response.send_message("You've already confirmed the trade! Use `/trade unconfirm` first.", ephemeral=True)

        try:
            pokemon = await self.bot.db.fetchrow(
                "SELECT * FROM pokemon WHERE user_id = $1 AND LOWER(name) = LOWER($2)",
                interaction.user.id,
                pokemon_name,
            )
            if not pokemon:
                return await interaction.response.send_message("You don't have that Pokemon!", ephemeral=True)

            if pokemon["id"] in [p["id"] for p in trade["users"][interaction.user.id]["pokemon"]]:
                return await interaction.response.send_message("That Pokemon is already in the trade!", ephemeral=True)

            trade["users"][interaction.user.id]["pokemon"].append(pokemon)
            await self.update_trade_embed(interaction)
            await interaction.response.send_message(f"Added {pokemon_name} to the trade.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"Error adding Pokemon: {e}", ephemeral=True)

    @trade.command(name="remove", description="Remove a Pokemon from the trade")
    @app_commands.describe(pokemon_name="The name of the pokemon to remove.")
    async def remove_pokemon(self, interaction: discord.Interaction, pokemon_name: str):
        """Remove a Pokemon from the trade"""
        if interaction.channel_id not in self.active_trades:
            return await interaction.response.send_message("No active trade in this channel!", ephemeral=True)

        trade = self.active_trades[interaction.channel_id]
        if interaction.user.id not in trade["users"]:
            return await interaction.response.send_message("You're not part of this trade!", ephemeral=True)

        if trade["users"][interaction.user.id]["confirmed"]:
            return await interaction.response.send_message("You've already confirmed the trade! Use `/trade unconfirm` first.", ephemeral=True)

        try:
            user_pokemon = trade["users"][interaction.user.id]["pokemon"]
            pokemon = next((p for p in user_pokemon if p["name"].lower() == pokemon_name.lower()), None)
            if not pokemon:
                return await interaction.response.send_message("That Pokemon isn't in the trade!", ephemeral=True)

            trade["users"][interaction.user.id]["pokemon"].remove(pokemon)

            await self.update_trade_embed(interaction)
            await interaction.response.send_message(f"Removed {pokemon_name} from the trade.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"Error removing Pokemon: {e}", ephemeral=True)

    @trade.command(name="confirm", description="Confirm the trade")
    async def confirm_trade(self, interaction: discord.Interaction):
        """Confirm the trade"""
        if interaction.channel_id not in self.active_trades:
            return await interaction.response.send_message("No active trade in this channel!", ephemeral=True)

        trade = self.active_trades[interaction.channel_id]
        if interaction.user.id not in trade["users"]:
            return await interaction.response.send_message("You're not part of this trade!", ephemeral=True)

        try:
            trade["users"][interaction.user.id]["confirmed"] = True
            await self.update_trade_embed(interaction)
            await interaction.response.send_message("You have confirmed the trade.", ephemeral=True)

            if all(user["confirmed"] for user in trade["users"].values()):
                await self.complete_trade(interaction)

        except Exception as e:
            await interaction.response.send_message(f"Error confirming trade: {e}", ephemeral=True)

    @trade.command(name="unconfirm", description="Unconfirm the trade")
    async def unconfirm_trade(self, interaction: discord.Interaction):
        """Unconfirm the trade"""
        if interaction.channel_id not in self.active_trades:
            return await interaction.response.send_message("No active trade in this channel!", ephemeral=True)

        trade = self.active_trades[interaction.channel_id]
        if interaction.user.id not in trade["users"]:
            return await interaction.response.send_message("You're not part of this trade!", ephemeral=True)

        try:
            trade["users"][interaction.user.id]["confirmed"] = False
            await self.update_trade_embed(interaction)
            await interaction.response.send_message("You have unconfirmed the trade.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error unconfirming trade: {e}", ephemeral=True)

    @trade.command(name="cancel", description="Cancel the trade")
    async def cancel_trade(self, interaction: discord.Interaction):
        """Cancel the trade"""
        if interaction.channel_id not in self.active_trades:
            return await interaction.response.send_message("No active trade in this channel!", ephemeral=True)

        trade = self.active_trades[interaction.channel_id]
        if interaction.user.id not in trade["users"]:
            return await interaction.response.send_message("You're not part of this trade!", ephemeral=True)

        await self.cancel_trade_logic(interaction.channel_id)
        await interaction.response.send_message("Trade cancelled!")

    async def cancel_trade_logic(self, channel_id: int):
        trade = self.active_trades.pop(channel_id, None)
        if trade:
            for user_id in trade["users"]:
                self.trade_locks.pop(user_id, None)

    async def update_trade_embed(self, interaction: discord.Interaction):
        """Update the trade embed"""
        trade = self.active_trades[interaction.channel_id]
        message = await interaction.channel.fetch_message(trade["message_id"])

        embed = discord.Embed(title="Pokemon Trade", color=discord.Color.blue())

        for user_id, data in trade["users"].items():
            user = await self.bot.fetch_user(user_id)
            pokemon_list = ("\n".join(f"Level {p['level']} {p['name'].title()}" for p in data["pokemon"]) or "No Pokemon added")
            embed.add_field(
                name=f"{user.display_name}'s Pokemon {'✅' if data['confirmed'] else '❌'}",
                value=pokemon_list,
                inline=True,
            )

        await message.edit(embed=embed)

    async def complete_trade(self, interaction: discord.Interaction):
        """Complete the trade"""
        trade = self.active_trades[interaction.channel_id]

        try:
            async with self.bot.db.acquire() as conn:
                async with conn.transaction():
                    user_ids = list(trade["users"].keys())
                    for i, user_id in enumerate(user_ids):
                        other_id = user_ids[1 - i]
                        for pokemon in trade["users"][user_id]["pokemon"]:
                            await conn.execute(
                                "UPDATE pokemon SET user_id = $1 WHERE id = $2",
                                other_id,
                                pokemon["id"],
                            )
            
            await self.cancel_trade_logic(interaction.channel_id)
            await interaction.followup.send("Trade completed successfully! 🤝")

        except Exception as e:
            await self.cancel_trade_logic(interaction.channel_id)
            await interaction.followup.send(f"Error completing trade: {e}")


async def setup(bot: Bot):
    await bot.add_cog(PokemonTrading(bot)) 