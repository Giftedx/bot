"""
OSRS command cog for the unified bot.
"""
import logging
import discord
from discord.ext import commands
from typing import Optional
import random

from src.core.database import DatabaseManager
from src.core.models.player import Player
from src.core.models.osrs_data import (
    FISHING_SPOTS,
    MINING_SPOTS,
    WOODCUTTING_SPOTS,
    COOKABLE_ITEMS,
    CRAFTABLE_ITEMS,
    JEWELRY_ITEMS,
)
from src.data.osrs.data_manager import OSRSDataManager
from src.core.battle_manager import GenericBattleStateManager, BattleType
from src.core.trade_manager import TradeManager
from src.core.models.trade import TradeStatus

logger = logging.getLogger(__name__)


class OSRSCommands(commands.Cog, name="OSRS"):
    """OSRS game commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_manager: DatabaseManager = self.bot.db_manager
        self.data_manager = OSRSDataManager()
        self.battle_manager = GenericBattleStateManager()
        self.trade_manager = TradeManager()

    async def _get_player(self, user_id: int) -> Optional[Player]:
        """Helper function to get a player from the database."""
        player_data = self.db_manager.get_player(user_id)
        if player_data:
            return Player.from_dict(player_data)
        return None

    @commands.hybrid_command(name="create", description="Create a new OSRS character.")
    async def create(self, ctx: commands.Context, name: str):
        """Create a new OSRS character."""
        existing_player = await self._get_player(ctx.author.id)
        if existing_player:
            return await ctx.send("You already have a character!")

        self.db_manager.create_player(ctx.author.id, name)

        await ctx.send(f"Created new character: **{name}**")

    @commands.hybrid_command(name="inventory", description="View your inventory.")
    async def inventory(self, ctx: commands.Context):
        """View your inventory."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        embed = discord.Embed(title=f"{player.username}'s Inventory")
        if not player.inventory:
            embed.description = "Your inventory is empty."
        else:
            inventory_list = [f"{item.quantity}x {item.name}" for item in player.inventory]
            embed.description = "\n".join(inventory_list)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="bank", description="View your bank.")
    async def bank(self, ctx: commands.Context):
        """View your bank."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        embed = discord.Embed(title=f"{player.username}'s Bank")
        if not player.bank:
            embed.description = "Your bank is empty."
        else:
            bank_list = [f"{item.quantity}x {item.name}" for item in player.bank]
            embed.description = "\n".join(bank_list)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="equipment", description="Show equipped items.")
    async def equipment(self, ctx: commands.Context):
        """Show equipped items."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        embed = discord.Embed(title=f"{player.username}'s Equipment")
        if not player.equipment:
            embed.description = "You have nothing equipped."
        else:
            for slot, item in player.equipment.items():
                embed.add_field(name=slot.name.title(), value=item.name, inline=True)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="train", description="Train a skill.")
    async def train(self, ctx: commands.Context, skill: str, xp: int = 100):
        """Train a skill."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        skill_name = skill.lower()
        if skill_name not in player.skills:
            return await ctx.send(f"Invalid skill: {skill}")

        player.skills[skill_name].xp += xp
        # In a real implementation, we would recalculate the level based on XP.
        # For now, we'll just add the XP.

        self.db_manager.save_player(player)

        await ctx.send(f"You gained {xp} XP in {skill.title()}!")

    @commands.hybrid_command(name="fish", description="Go fishing.")
    async def fish(self, ctx: commands.Context, location: str):
        """Go fishing at a specific location."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        if location not in FISHING_SPOTS:
            return await ctx.send(f"Invalid fishing location: {location}")

        spot = FISHING_SPOTS[location]
        if player.skills["fishing"].level < spot.required_level:
            return await ctx.send(f"You need level {spot.required_level} Fishing to fish here.")

        # This is a simplified implementation. A real implementation would involve loops, timers, and randomness.
        fish_caught = spot.fish_types[0]
        player.skills["fishing"].xp += fish_caught["xp"]
        player.add_item_to_inventory(fish_caught["name"])

        self.db_manager.save_player(player)

        await ctx.send(
            f"You caught a {fish_caught['name']} and gained {fish_caught['xp']} Fishing XP!"
        )

    @commands.hybrid_command(name="mine", description="Go mining.")
    async def mine(self, ctx: commands.Context, location: str):
        """Go mining at a specific location."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        if location not in MINING_SPOTS:
            return await ctx.send(f"Invalid mining location: {location}")

        spot = MINING_SPOTS[location]
        if player.skills["mining"].level < spot.required_level:
            return await ctx.send(f"You need level {spot.required_level} Mining to mine here.")

        # Simplified implementation
        ore_mined = spot.ores[0]
        player.skills["mining"].xp += ore_mined["xp"]
        player.add_item_to_inventory(ore_mined["name"])

        self.db_manager.save_player(player)

        await ctx.send(
            f"You mined some {ore_mined['name']} and gained {ore_mined['xp']} Mining XP!"
        )

    @commands.hybrid_command(name="chop", description="Go woodcutting.")
    async def chop(self, ctx: commands.Context, location: str):
        """Go woodcutting at a specific location."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        if location not in WOODCUTTING_SPOTS:
            return await ctx.send(f"Invalid woodcutting location: {location}")

        spot = WOODCUTTING_SPOTS[location]
        if player.skills["woodcutting"].level < spot.required_level:
            return await ctx.send(f"You need level {spot.required_level} Woodcutting to chop here.")

        # Simplified implementation
        log_cut = spot.trees[0]
        player.skills["woodcutting"].xp += log_cut["xp"]
        player.add_item_to_inventory(log_cut["name"])

        self.db_manager.save_player(player)

        await ctx.send(
            f"You chopped some {log_cut['name']} and gained {log_cut['xp']} Woodcutting XP!"
        )

    @commands.hybrid_command(name="cook", description="Cook raw food.")
    async def cook(self, ctx: commands.Context, item_name: str):
        """Cook raw food."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        if item_name not in COOKABLE_ITEMS:
            return await ctx.send("You can't cook that!")

        cookable = COOKABLE_ITEMS[item_name]
        if player.skills["cooking"].level < cookable["level_req"]:
            return await ctx.send(f"You need level {cookable['level_req']} Cooking to cook this.")

        raw_food_name = f"Raw {item_name}"
        if not player.has_item(raw_food_name):
            return await ctx.send(f"You don't have any {raw_food_name} to cook.")

        player.remove_item_from_inventory(raw_food_name)
        player.skills["cooking"].xp += cookable["xp"]
        player.add_item_to_inventory(f"Cooked {item_name}")

        self.db_manager.save_player(player)

        await ctx.send(f"You cooked a {item_name} and gained {cookable['xp']} Cooking XP!")

    @commands.hybrid_command(name="smelt", description="Smelt ores into bars.")
    async def smelt(self, ctx: commands.Context, bar_name: str):
        """Smelt ores into bars."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        if bar_name not in CRAFTABLE_ITEMS:
            return await ctx.send("You can't smelt that!")

        craftable = CRAFTABLE_ITEMS[bar_name]
        if player.skills["smithing"].level < craftable["level_req"]:
            return await ctx.send(
                f"You need level {craftable['level_req']} Smithing to smelt this."
            )

        for material, quantity in craftable["materials"].items():
            if not player.has_item(material, quantity):
                return await ctx.send(f"You don't have enough {material} to smelt this.")

        for material, quantity in craftable["materials"].items():
            player.remove_item_from_inventory(material, quantity)

        player.skills["smithing"].xp += craftable["xp"]
        player.add_item_to_inventory(bar_name)

        self.db_manager.save_player(player)

        await ctx.send(f"You smelted a {bar_name} and gained {craftable['xp']} Smithing XP!")

    @commands.hybrid_command(name="craft", description="Craft items.")
    async def craft(self, ctx: commands.Context, item_name: str):
        """Craft items."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        if item_name not in JEWELRY_ITEMS:
            return await ctx.send("You can't craft that!")

        craftable = JEWELRY_ITEMS[item_name]
        if player.skills["crafting"].level < craftable["level_req"]:
            return await ctx.send(f"You need level {craftable['level_req']} Crafting to make this.")

        for material, quantity in craftable["materials"].items():
            if not player.has_item(material, quantity):
                return await ctx.send(f"You don't have enough {material} to craft this.")

        for material, quantity in craftable["materials"].items():
            player.remove_item_from_inventory(material, quantity)

        player.skills["crafting"].xp += craftable["xp"]
        player.add_item_to_inventory(item_name)

        self.db_manager.save_player(player)

        await ctx.send(f"You crafted a {item_name} and gained {craftable['xp']} Crafting XP!")

    @commands.hybrid_command(name="fight", description="Preview and start a fight with a monster.")
    async def fight(self, ctx: commands.Context, monster_name: str):
        """Preview and start a fight with a monster."""
        player = await self._get_player(ctx.author.id)
        if not player:
            await ctx.send("You need to create a character first!")
            return
        # Check if already in a battle
        if self.battle_manager.get_player_battle(ctx.author.id):
            await ctx.send("You are already in a battle!")
            return
        monster = self.data_manager.get_monster_info(monster_name)
        if not monster:
            await ctx.send(f"Monster '{monster_name}' not found.")
            return
        # Show preview
        embed = discord.Embed(
            title=f"Fight: {monster.get('name', monster_name)}",
            color=discord.Color.red(),
            description=monster.get("examine", "No description available."),
        )
        if monster.get("wiki_url"):
            embed.url = monster["wiki_url"]
        if monster.get("combat_level"):
            embed.add_field(name="Combat Level", value=monster["combat_level"], inline=True)
        if monster.get("hitpoints"):
            embed.add_field(name="Hitpoints", value=monster["hitpoints"], inline=True)
        if monster.get("max_hit"):
            embed.add_field(name="Max Hit", value=monster["max_hit"], inline=True)
        if monster.get("aggressive") is not None:
            embed.add_field(name="Aggressive", value=str(monster["aggressive"]), inline=True)
        if monster.get("poisonous") is not None:
            embed.add_field(name="Poisonous", value=str(monster["poisonous"]), inline=True)
        if monster.get("slayer_level"):
            embed.add_field(name="Slayer Level", value=monster["slayer_level"], inline=True)
        if monster.get("drops"):
            drops = monster["drops"]
            if isinstance(drops, list) and drops:
                drop_list = [
                    d["name"] if isinstance(d, dict) and "name" in d else str(d) for d in drops[:10]
                ]
                embed.add_field(name="Notable Drops", value="\n".join(drop_list), inline=False)
        await ctx.send(embed=embed)
        # Start the battle
        initial_data = {
            "monster": monster,
            "player_id": ctx.author.id,
            "monster_name": monster.get("name", monster_name),
        }
        battle = self.battle_manager.create_battle(
            battle_type=BattleType.OSRS,
            challenger_id=ctx.author.id,
            opponent_id=0,  # 0 or None for PvE
            initial_data=initial_data,
        )
        await ctx.send(
            f"Battle started with {monster.get('name', monster_name)}! Use /attack to fight."
        )

    @commands.hybrid_command(name="attack", description="Attack the monster you are fighting.")
    async def attack(self, ctx: commands.Context):
        """Attack the monster you are currently fighting."""
        player = await self._get_player(ctx.author.id)
        if not player:
            await ctx.send("You need to create a character first!")
            return
        battle = self.battle_manager.get_player_battle(ctx.author.id)
        if not battle:
            await ctx.send("You are not in a battle! Use /fight to start one.")
            return
        monster = battle.battle_data.get("monster")
        if not monster:
            await ctx.send("Battle state is corrupted. No monster found.")
            return
        # Get or initialize monster HP
        if "monster_hp" not in battle.battle_data:
            battle.battle_data["monster_hp"] = monster.get("hitpoints", 10)
        if "player_hp" not in battle.battle_data:
            battle.battle_data["player_hp"] = (
                player.skills.get("hitpoints", player.combat_level).level
                if "hitpoints" in player.skills
                else 10
            )
        # Simple damage formula
        player_attack = (
            player.skills.get("attack", player.combat_level).level
            if "attack" in player.skills
            else 1
        )
        player_strength = (
            player.skills.get("strength", player.combat_level).level
            if "strength" in player.skills
            else 1
        )
        monster_def = monster.get("defence_level", 1)
        monster_max_hit = monster.get("max_hit", 1) or 1
        # Player attacks monster
        player_damage = max(1, int((player_attack + player_strength) / 4 - monster_def / 6 + 1))
        battle.battle_data["monster_hp"] -= player_damage
        # Monster attacks player (simple random hit)
        monster_damage = random.randint(0, monster_max_hit)
        battle.battle_data["player_hp"] -= monster_damage
        # Build embed
        embed = discord.Embed(
            title=f"Combat with {monster.get('name', 'Monster')}", color=discord.Color.red()
        )
        embed.add_field(
            name="Your Attack",
            value=f"You hit the {monster.get('name', 'monster')} for {player_damage} damage!",
            inline=False,
        )
        embed.add_field(
            name="Monster Attack",
            value=f"The {monster.get('name', 'monster')} hit you for {monster_damage} damage!",
            inline=False,
        )
        embed.add_field(
            name="Status",
            value=f"Your HP: {battle.battle_data['player_hp']}\n{monster.get('name', 'Monster')}'s HP: {battle.battle_data['monster_hp']}",
            inline=False,
        )
        # Check for end of battle
        if battle.battle_data["monster_hp"] <= 0:
            embed.add_field(
                name="Victory!",
                value=f"You defeated the {monster.get('name', 'monster')}!",
                inline=False,
            )
            # Award XP (simple amount)
            xp_gain = monster.get("combat_level", 1) * 4
            if "attack" in player.skills:
                player.skills["attack"].xp += xp_gain
            if "strength" in player.skills:
                player.skills["strength"].xp += xp_gain
            if "hitpoints" in player.skills:
                player.skills["hitpoints"].xp += xp_gain
            self.db_manager.save_player(player)
            # Award drops (if any)
            drops = monster.get("drops", [])
            if isinstance(drops, list) and drops:
                # Give all drops for now (TODO: roll for drops)
                for drop in drops:
                    drop_name = (
                        drop["name"] if isinstance(drop, dict) and "name" in drop else str(drop)
                    )
                    player.add_item_to_inventory(drop_name)
                self.db_manager.save_player(player)
                embed.add_field(
                    name="Drops Received",
                    value="\n".join(
                        [
                            drop["name"] if isinstance(drop, dict) and "name" in drop else str(drop)
                            for drop in drops
                        ]
                    ),
                    inline=False,
                )
            # End battle
            self.battle_manager.end_battle(battle.battle_id, ctx.author.id)
        elif battle.battle_data["player_hp"] <= 0:
            embed.add_field(
                name="Defeat",
                value=f"You were defeated by the {monster.get('name', 'monster')}!",
                inline=False,
            )
            self.battle_manager.end_battle(battle.battle_id, None)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="flee", description="Attempt to flee from combat.")
    async def flee(self, ctx: commands.Context):
        """Attempt to flee from combat."""
        battle = self.battle_manager.get_battle(ctx.author.id)
        if not battle:
            return await ctx.send("You are not in combat!")

        flee_successful = random.random() < 0.5  # 50% chance to flee

        if flee_successful:
            self.battle_manager.end_battle(ctx.author.id)
            await ctx.send("You successfully fled from combat!")
        else:
            await ctx.send("You failed to flee!")

    @commands.hybrid_group(name="trade", invoke_without_command=True)
    async def trade(self, ctx: commands.Context):
        """Commands for trading with other players."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @trade.command(name="offer")
    async def trade_offer(
        self, ctx: commands.Context, recipient: discord.Member, item_name: str, quantity: int = 1
    ):
        """Offer to trade an item to another player."""
        if ctx.author.id == recipient.id:
            return await ctx.send("You can't trade with yourself!", ephemeral=True)

        offerer = await self._get_player(ctx.author.id)
        if not offerer:
            return await ctx.send("You need to create a character first!", ephemeral=True)

        receiver = await self._get_player(recipient.id)
        if not receiver:
            return await ctx.send(
                f"{recipient.display_name} has not created a character.", ephemeral=True
            )

        if not offerer.has_item(item_name, quantity):
            return await ctx.send(f"You do not have {quantity}x {item_name}.", ephemeral=True)

        trade = self.trade_manager.create_trade(
            offerer.user_id, receiver.user_id, item_name, quantity
        )

        try:
            await recipient.send(
                f"{ctx.author.display_name} has offered you {quantity}x {item_name}. "
                f"Use `/trade accept trade_id:{trade.id}` or `/trade decline trade_id:{trade.id}`."
            )
            await ctx.send(
                f"Trade offer sent to {recipient.display_name}. (Trade ID: {trade.id})",
                ephemeral=True,
            )
        except discord.Forbidden:
            await ctx.send(
                f"Could not send a DM to {recipient.display_name}. They may have DMs disabled.",
                ephemeral=True,
            )
            self.trade_manager.cancel_trade(trade.id, offerer.user_id)

    @trade.command(name="accept")
    async def trade_accept(self, ctx: commands.Context, trade_id: int):
        """Accept a trade offer."""
        trade = self.trade_manager.get_trade(trade_id)
        if not trade or trade.receiver_id != ctx.author.id:
            return await ctx.send("This trade offer is not for you or has expired.", ephemeral=True)

        if trade.status != TradeStatus.PENDING:
            return await ctx.send(
                f"This trade is no longer pending. Its status is: {trade.status.value}",
                ephemeral=True,
            )

        offerer = await self._get_player(trade.sender_id)
        receiver = await self._get_player(trade.receiver_id)

        if not offerer or not receiver:
            return await ctx.send(
                "One of the players in this trade no longer exists.", ephemeral=True
            )

        if not offerer.has_item(trade.item_name, trade.item_quantity):
            self.trade_manager.decline_trade(trade.id)
            return await ctx.send(
                "The offerer no longer has the required items. The trade has been declined.",
                ephemeral=True,
            )

        # Perform the trade
        offerer.remove_item_from_inventory(trade.item_name, trade.item_quantity)
        receiver.add_item_to_inventory(trade.item_name, trade.item_quantity)

        # Save both players
        self.db_manager.save_player(offerer)
        self.db_manager.save_player(receiver)

        self.trade_manager.accept_trade(trade.id)

        await ctx.send(
            f"You have accepted the trade for {trade.item_quantity}x {trade.item_name}.",
            ephemeral=True,
        )

        try:
            offerer_user = self.bot.get_user(offerer.user_id) or await self.bot.fetch_user(
                offerer.user_id
            )
            await offerer_user.send(
                f"{receiver.username} has accepted your trade for {trade.item_quantity}x {trade.item_name}."
            )
        except discord.NotFound:
            pass  # User might not be reachable

    @trade.command(name="decline")
    async def trade_decline(self, ctx: commands.Context, trade_id: int):
        """Decline a trade offer."""
        trade = self.trade_manager.get_trade(trade_id)
        if not trade or trade.receiver_id != ctx.author.id:
            return await ctx.send("This trade offer is not for you or has expired.", ephemeral=True)

        if trade.status != TradeStatus.PENDING:
            return await ctx.send(
                f"This trade is no longer pending. Its status is: {trade.status.value}",
                ephemeral=True,
            )

        self.trade_manager.decline_trade(trade.id)
        await ctx.send("You have declined the trade.", ephemeral=True)

    @trade.command(name="cancel")
    async def trade_cancel(self, ctx: commands.Context, trade_id: int):
        """Cancel a trade offer you sent."""
        trade = self.trade_manager.get_trade(trade_id)
        if not trade or trade.sender_id != ctx.author.id:
            return await ctx.send("This is not your trade offer to cancel.", ephemeral=True)

        if trade.status != TradeStatus.PENDING:
            return await ctx.send(
                f"This trade is no longer pending. Its status is: {trade.status.value}",
                ephemeral=True,
            )

        self.trade_manager.cancel_trade(trade.id, ctx.author.id)
        await ctx.send("You have cancelled your trade offer.", ephemeral=True)

    @trade.command(name="list")
    async def trade_list(self, ctx: commands.Context):
        """List your pending trades."""
        trades = self.trade_manager.get_player_trades(ctx.author.id)
        if not trades:
            return await ctx.send("You have no pending trades.")

        embed = discord.Embed(title="Your Trades")
        for trade in trades:
            embed.add_field(
                name=f"Trade ID: {trade.id}",
                value=f"With: <@{trade.receiver_id}>\nItem: {trade.item_quantity}x {trade.item_name}\nStatus: {trade.status.value}",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="achievements", description="View your achievements")
    async def achievements(
        self, ctx: commands.Context, category: Optional[str] = None, page: int = 1
    ):
        """View your achievements."""
        if page < 1:
            return await ctx.send("Page number must be positive.", ephemeral=True)

        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!", ephemeral=True)

        all_achievements = self.data_manager.get_all_achievements()
        if not all_achievements:
            return await ctx.send("No achievements are available in the game yet.", ephemeral=True)

        # Filter by category if specified
        if category:
            filtered_achievements = [
                a for a in all_achievements if a["category"].lower() == category.lower()
            ]
            if not filtered_achievements:
                return await ctx.send(
                    f"No achievements found in category '{category}'.", ephemeral=True
                )
        else:
            filtered_achievements = all_achievements

        # Paginate results
        per_page = 5
        total_pages = (len(filtered_achievements) + per_page - 1) // per_page
        if page > total_pages and total_pages > 0:
            return await ctx.send(
                f"Invalid page number. Total pages: {total_pages}", ephemeral=True
            )

        offset = (page - 1) * per_page
        page_achievements = filtered_achievements[offset : offset + per_page]

        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Achievements", color=discord.Color.gold()
        )

        for achievement in page_achievements:
            status = "🏆" if achievement["id"] in player.completed_achievements else "⭕"
            rewards_str = ", ".join(
                [f"{amt} {rwd.title()}" for rwd, amt in achievement.get("rewards", {}).items()]
            )
            embed.add_field(
                name=f"{status} {achievement['name']}",
                value=f"{achievement['description']}\n*Rewards: {rewards_str}*",
                inline=False,
            )

        completed_count = len(
            [
                a_id
                for a_id in player.completed_achievements
                if self.data_manager.get_achievement(a_id) in filtered_achievements
            ]
        )
        embed.set_footer(
            text=f"Page {page}/{total_pages} | Completed: {completed_count}/{len(filtered_achievements)}"
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="collection_log", description="View your collection log")
    async def collection_log(
        self, ctx: commands.Context, category: Optional[str] = None, page: int = 1
    ):
        """View your collection log with optional category filtering"""
        if page < 1:
            return await ctx.send("Page number must be positive.", ephemeral=True)

        player = await self._get_player(ctx.author.id)
        if not player or not player.collection_log:
            return await ctx.send("Your collection log is empty.", ephemeral=True)

        # The player's log is just {item_name: count}. We need details for category filtering.
        log_items_with_details = []
        for item_name, quantity in player.collection_log.items():
            item_details = self.data_manager.get_item_info(item_name=item_name)
            if item_details:
                log_items_with_details.append({"details": item_details, "quantity": quantity})

        if category:
            filtered_log = [
                i
                for i in log_items_with_details
                if i["details"].get("category", "").lower() == category.lower()
            ]
            if not filtered_log:
                return await ctx.send(
                    f"No collected items found in category '{category}'.", ephemeral=True
                )
        else:
            filtered_log = log_items_with_details

        per_page = 10
        total_pages = (len(filtered_log) + per_page - 1) // per_page
        if page > total_pages and total_pages > 0:
            return await ctx.send(
                f"Invalid page number. Total pages: {total_pages}", ephemeral=True
            )

        offset = (page - 1) * per_page
        page_items = filtered_log[offset : offset + per_page]

        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Collection Log", color=discord.Color.purple()
        )
        for item in page_items:
            embed.add_field(
                name=f"✅ {item['details']['name']}",
                value=f"Quantity: {item['quantity']}",
                inline=False,
            )

        embed.set_footer(
            text=f"Page {page}/{total_pages} | Unique Items Collected: {len(player.collection_log)}"
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(OSRSCommands(bot))
