import logging
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List, Dict, Any
import aiohttp
import re
import random

from src.core.database import DatabaseManager
from src.core.models.player import Player
from src.data.osrs.data_manager import OSRSDataManager
from src.data.osrs.enhanced_data_manager import EnhancedOSRSDataManager
from src.core.trade_manager import TradeManager
from src.core.ge_manager import GrandExchangeManager
from src.core.models.quest import QuestStatus
from src.osrs.core import game_math
from src.core.pet_system import Pet, PetManager, PetOrigin, PetRarity

logger = logging.getLogger(__name__)


class OSRSPetData:
    """OSRS Pet data and drop rates"""

    BOSS_PETS = {
        "Baby Mole": {
            "boss": "Giant Mole",
            "base_rate": 3000,
            "rarity": PetRarity.RARE,
            "abilities": ["Dig", "Burrow"],
            "base_stats": {"hp": 10, "defense": 5, "cuteness": 8},
        },
        "Prince Black Dragon": {
            "boss": "King Black Dragon",
            "base_rate": 3000,
            "rarity": PetRarity.RARE,
            "abilities": ["Fire Breath", "Fly"],
            "base_stats": {"hp": 15, "attack": 8, "defense": 8},
        },
        "Vorki": {
            "boss": "Vorkath",
            "base_rate": 3000,
            "rarity": PetRarity.VERY_RARE,
            "abilities": ["Frost Breath", "Undead Resistance"],
            "base_stats": {"hp": 20, "magic": 10, "defense": 12},
        },
    }

    SKILLING_PETS = {
        "Rocky": {
            "skill": "Thieving",
            "base_rate": 247886,
            "rarity": PetRarity.VERY_RARE,
            "abilities": ["Pickpocket", "Stealth"],
            "base_stats": {"agility": 10, "stealth": 15, "luck": 8},
        },
        "Beaver": {
            "skill": "Woodcutting",
            "base_rate": 69846,
            "rarity": PetRarity.RARE,
            "abilities": ["Wood Sense", "Tree Climb"],
            "base_stats": {"woodcutting": 10, "agility": 5, "strength": 3},
        },
    }


class OsrsSlash(commands.Cog, name="OSRS"):
    """OSRS slash commands (migrated)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_manager: DatabaseManager = self.bot.db_manager
        self.data_manager = OSRSDataManager()
        self.enhanced_data_manager = EnhancedOSRSDataManager()
        self.trade_manager = TradeManager()
        self.ge_manager = GrandExchangeManager()
        self.pet_manager = PetManager()
        self.session = aiohttp.ClientSession()
        self.wiki_base_url = "https://oldschool.runescape.wiki/w"

    def cog_unload(self):
        """Clean up the aiohttp session when the cog is unloaded."""
        self.bot.loop.create_task(self.session.close())

    async def _get_player(self, user_id: int) -> Optional[Player]:
        """Helper function to get a player from the database."""
        player_data = self.db_manager.get_player(user_id)
        if player_data:
            return Player.from_dict(player_data)
        return None

    @app_commands.command(name="osrs_stats", description="Show a player's stats.")
    @app_commands.describe(member="The player whose stats you want to see (defaults to you).")
    async def osrs_stats(
        self, interaction: discord.Interaction, member: Optional[discord.Member] = None
    ):
        """Shows a player's stats."""
        target_user = member or interaction.user
        player = await self._get_player(target_user.id)

        if not player:
            await interaction.response.send_message(
                "That player has not created a character yet!", ephemeral=True
            )
            return

        embed = discord.Embed(title=f"{player.username}'s Stats", color=discord.Color.blue())
        embed.set_author(name=target_user.display_name, icon_url=target_user.avatar.url)
        embed.add_field(name="Combat Level", value=player.combat_level, inline=False)

        for skill_name, skill_data in player.skills.items():
            embed.add_field(
                name=skill_name.title(),
                value=f"**Level:** {skill_data.level}\n**XP:** {skill_data.xp:,}",
                inline=True,
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="osrs_price", description="Check the Grand Exchange price of an item."
    )
    @app_commands.describe(item_name="The name of the item to check.")
    async def osrs_price(self, interaction: discord.Interaction, item_name: str):
        """Checks the GE price of an item."""
        try:
            item_data = self.data_manager.get_item_by_name(item_name)
            if not item_data:
                await interaction.response.send_message(
                    f"Could not find an item named '{item_name}'.", ephemeral=True
                )
                return

            price_info = self.data_manager.get_price_data(item_data["id"])
            if not price_info:
                await interaction.response.send_message(
                    f"Could not find price information for '{item_name}'.", ephemeral=True
                )
                return

            embed = discord.Embed(
                title=f"Price Check: {item_data['name']}", color=discord.Color.gold()
            )
            embed.set_thumbnail(url=item_data["icon_url"])
            embed.add_field(name="Price", value=f"{price_info['price']:,} GP", inline=False)
            embed.add_field(
                name="High Alch", value=f"{item_data.get('high_alch', 'N/A')} GP", inline=True
            )
            embed.add_field(
                name="Low Alch", value=f"{item_data.get('low_alch', 'N/A')} GP", inline=True
            )
            embed.set_footer(text=f"Item ID: {item_data['id']}")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error checking price for '{item_name}': {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while checking the price.", ephemeral=True
            )

    osrs_ge = app_commands.Group(name="osrs_ge", description="Grand Exchange commands")

    @osrs_ge.command(name="buy", description="Place a buy offer on the Grand Exchange.")
    @app_commands.describe(
        item_name="The name of the item to buy.",
        quantity="The amount to buy.",
        price="The price per item.",
    )
    async def osrs_ge_buy(
        self, interaction: discord.Interaction, item_name: str, quantity: int, price: int
    ):
        """Places a buy offer on the GE."""
        player = await self._get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message(
                "You need to create a character first!", ephemeral=True
            )
            return

        item_data = self.data_manager.get_item_by_name(item_name)
        if not item_data:
            await interaction.response.send_message(
                f"Could not find an item named '{item_name}'.", ephemeral=True
            )
            return

        try:
            offer_id = self.ge_manager.place_buy_offer(
                player_id=player.user_id, item_id=item_data["id"], quantity=quantity, price=price
            )
            await interaction.response.send_message(
                f"Placed a buy offer for {quantity}x {item_name} at {price} GP each. Offer ID: {offer_id}",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Error placing GE buy offer: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while placing your buy offer.", ephemeral=True
            )

    @osrs_ge.command(name="sell", description="Place a sell offer on the Grand Exchange.")
    @app_commands.describe(
        item_name="The name of the item to sell.",
        quantity="The amount to sell.",
        price="The price per item.",
    )
    async def osrs_ge_sell(
        self, interaction: discord.Interaction, item_name: str, quantity: int, price: int
    ):
        """Places a sell offer on the GE."""
        player = await self._get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message(
                "You need to create a character first!", ephemeral=True
            )
            return

        item_data = self.data_manager.get_item_by_name(item_name)
        if not item_data:
            await interaction.response.send_message(
                f"Could not find an item named '{item_name}'.", ephemeral=True
            )
            return

        if not player.has_item(item_name, quantity):
            await interaction.response.send_message(
                f"You do not have {quantity}x {item_name} to sell.", ephemeral=True
            )
            return

        try:
            offer_id = self.ge_manager.place_sell_offer(
                player_id=player.user_id, item_id=item_data["id"], quantity=quantity, price=price
            )
            player.remove_item_from_inventory(item_name, quantity)
            self.db_manager.save_player(player)
            await interaction.response.send_message(
                f"Placed a sell offer for {quantity}x {item_name} at {price} GP each. Offer ID: {offer_id}",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Error placing GE sell offer: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while placing your sell offer.", ephemeral=True
            )

    @osrs_ge.command(name="status", description="Check your Grand Exchange offers.")
    async def osrs_ge_status(self, interaction: discord.Interaction):
        """Checks your GE offers."""
        player = await self._get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message(
                "You need to create a character first!", ephemeral=True
            )
            return

        offers = self.ge_manager.get_offers_for_player(player.user_id)

        if not offers:
            await interaction.response.send_message("You have no active offers.", ephemeral=True)
            return

        embed = discord.Embed(title="Your Grand Exchange Offers", color=discord.Color.blue())
        embed.set_author(name=player.username, icon_url=interaction.user.avatar.url)

        for offer in offers:
            offer_type = "Buy" if offer.is_buy_offer else "Sell"
            item_data = self.data_manager.get_item_by_id(offer.item_id)
            item_name = item_data["name"] if item_data else f"Unknown Item (ID: {offer.item_id})"

            embed.add_field(
                name=f"Offer #{offer.offer_id} - {offer_type}ing {item_name}",
                value=f"**Quantity:** {offer.quantity}\n**Price:** {offer.price} GP each",
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    osrs_quest = app_commands.Group(name="osrs_quest", description="Quest-related commands")

    @osrs_quest.command(name="list", description="View your quest list.")
    @app_commands.describe(
        filter_str="Filter quests by status (e.g., 'completed', 'in_progress').",
        page="The page number to view.",
    )
    async def osrs_quest_list(
        self, interaction: discord.Interaction, filter_str: Optional[str] = None, page: int = 1
    ):
        """Lists player quests."""
        player = await self._get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message(
                "You need to create a character first!", ephemeral=True
            )
            return

        all_quests = self.data_manager.get_all_quests().values()

        player_quests = []
        for quest_data in all_quests:
            quest_id = quest_data["id"]
            status = player.get_quest_status(quest_id)
            player_quests.append({"quest": quest_data, "status": status})

        if filter_str:
            try:
                filter_status = QuestStatus(filter_str.lower())
                player_quests = [q for q in player_quests if q["status"] == filter_status]
            except ValueError:
                await interaction.response.send_message(
                    f"Invalid filter: '{filter_str}'. Use 'not_started', 'in_progress', or 'completed'.",
                    ephemeral=True,
                )
                return

        player_quests.sort(key=lambda q: q["quest"]["name"])

        items_per_page = 10
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        paginated_quests = player_quests[start_index:end_index]

        if not paginated_quests:
            await interaction.response.send_message(
                "No quests found for the specified filter and page.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"Quest List (Page {page})",
            description=f"Showing quests for {player.username}",
            color=discord.Color.dark_purple(),
        )

        for quest_info in paginated_quests:
            quest = quest_info["quest"]
            status_emoji = {
                QuestStatus.COMPLETED: "✅",
                QuestStatus.IN_PROGRESS: "▶️",
                QuestStatus.NOT_STARTED: "❌",
            }
            status = quest_info["status"]
            embed.add_field(
                name=f"{status_emoji.get(status, '')} {quest['name']}",
                value=f"**Difficulty:** {quest['difficulty']}",
                inline=False,
            )

        total_pages = (len(player_quests) + items_per_page - 1) // items_per_page
        embed.set_footer(text=f"Page {page}/{total_pages}")

        await interaction.response.send_message(embed=embed)

    @osrs_quest.command(name="info", description="View details about a specific quest.")
    @app_commands.describe(quest_name="The name of the quest to view.")
    async def osrs_quest_info(self, interaction: discord.Interaction, quest_name: str):
        """Shows info about a quest."""
        quest_data = self.data_manager.get_quest_info(quest_name)

        if not quest_data:
            await interaction.response.send_message(
                f"Could not find a quest named '{quest_name}'.", ephemeral=True
            )
            return

        player = await self._get_player(interaction.user.id)
        quest_status = (
            player.get_quest_status(quest_data["id"]) if player else QuestStatus.NOT_STARTED
        )

        status_emoji = {
            QuestStatus.COMPLETED: "✅",
            QuestStatus.IN_PROGRESS: "▶️",
            QuestStatus.NOT_STARTED: "❌",
        }

        embed = discord.Embed(
            title=quest_data["name"],
            description=quest_data["description"],
            color=discord.Color.dark_blue(),
        )

        embed.add_field(
            name="Status",
            value=f"{status_emoji.get(quest_status, '')} {quest_status.value.replace('_', ' ').title()}",
            inline=True,
        )
        embed.add_field(name="Difficulty", value=quest_data["difficulty"], inline=True)
        embed.add_field(name="Quest Points", value=quest_data["quest_points"], inline=True)

        if quest_data["requirements"]:
            req_text = "\n".join(
                [
                    f"- {skill.title()}: {level}"
                    for skill, level in quest_data["requirements"].items()
                ]
            )
            embed.add_field(name="Requirements", value=req_text, inline=False)

        if quest_data["rewards"]:
            rewards_text = "\n".join(
                [
                    f"- {reward.title()}: {amount}"
                    for reward, amount in quest_data["rewards"].items()
                ]
            )
            embed.add_field(name="Rewards", value=rewards_text, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="osrs_hiscore", description="Look up a player's hiscores.")
    @app_commands.describe(username="The OSRS username to look up.")
    async def osrs_hiscore(self, interaction: discord.Interaction, username: str):
        """Looks up a player's hiscores."""
        await interaction.response.defer()
        hiscores = await self.enhanced_data_manager.fetch_hiscores(username)

        if not hiscores:
            await interaction.followup.send(
                f"Could not find hiscores for player '{username}'. They may not be ranked.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(title=f"Hiscores for {username}", color=discord.Color.dark_gold())

        for skill, data in hiscores.items():
            embed.add_field(
                name=skill.title(),
                value=f"**Rank:** {data['rank']:,}\n**Level:** {data['level']}\n**XP:** {data['xp']:,}",
                inline=True,
            )

        await interaction.followup.send(embed=embed)

    osrs_calc = app_commands.Group(name="osrs_calc", description="Various OSRS calculators")

    @osrs_calc.command(name="xp", description="Calculate OSRS XP and levels.")
    @app_commands.describe(level="The target level (1-99).", xp="The total XP you have.")
    async def osrs_calc_xp(
        self,
        interaction: discord.Interaction,
        level: Optional[int] = None,
        xp: Optional[int] = None,
    ):
        """Calculates OSRS XP."""
        if level is None and xp is None:
            await interaction.response.send_message(
                "Please provide either a level or an XP amount to calculate.", ephemeral=True
            )
            return

        embed = discord.Embed(title="OSRS XP Calculator", color=discord.Color.dark_green())

        if level is not None:
            if not 1 <= level <= 99:
                await interaction.response.send_message(
                    "Please enter a level between 1 and 99.", ephemeral=True
                )
                return
            xp_needed = game_math.calculate_xp_for_level(level)
            embed.add_field(name=f"XP for Level {level}", value=f"{xp_needed:,} XP", inline=False)

        if xp is not None:
            if xp < 0:
                await interaction.response.send_message("XP cannot be negative.", ephemeral=True)
                return
            level_at_xp = game_math.calculate_level_for_xp(xp)
            embed.add_field(name=f"Level at {xp:,} XP", value=f"Level {level_at_xp}", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="osrs-wiki", description="Search the OSRS Wiki.")
    @app_commands.describe(query="The term to search for on the wiki.")
    async def osrs_wiki(self, interaction: discord.Interaction, query: str):
        """Searches the OSRS Wiki."""
        safe_query = re.sub(r"[^a-zA-Z0-9_ ()-]", "", query)
        url = f"{self.wiki_base_url}/w/Special:Search?search={safe_query.replace(' ', '+')}"
        await interaction.response.send_message(url)

    async def get_drop_data(self, monster_name: str) -> Optional[List[Dict[str, Any]]]:
        """Helper to get drop data from the wiki."""
        # This is a simplified example; a real implementation would parse the wiki
        url = f"{self.wiki_base_url}/w/{monster_name.replace(' ', '_')}"
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    # In a real scenario, you'd parse the HTML here
                    # For now, we'll return mock data
                    if "goblin" in monster_name.lower():
                        return [{"item": "Coins", "quantity": "1-100", "rarity": "Common"}]
        except Exception:
            return None
        return None

    @app_commands.command(name="osrs-drop", description="Get the drop table for an OSRS monster.")
    @app_commands.describe(monster_name="The name of the monster to look up.")
    async def osrs_drop(self, interaction: discord.Interaction, monster_name: str):
        """Gets the drop table for an OSRS monster."""
        await interaction.response.defer()
        drop_data = await self.get_drop_data(monster_name)

        if not drop_data:
            await interaction.followup.send(
                f"Could not find drop data for '{monster_name}'.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"Drop Table for {monster_name.title()}", color=discord.Color.dark_orange()
        )
        for drop in drop_data:
            embed.add_field(
                name=drop["item"],
                value=f"Quantity: {drop['quantity']}\nRarity: {drop['rarity']}",
                inline=False,
            )
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="osrs-map", description="Get information about a location on the OSRS map."
    )
    @app_commands.describe(location_name="The name of the location to look up.")
    async def osrs_map(self, interaction: discord.Interaction, location_name: str):
        """Gets information about a location on the OSRS map."""
        # This is a simplified example; a real implementation would use a map API or database
        await interaction.response.send_message(
            f"Showing map information for **{location_name}**\n"
            f"https://oldschool.runescape.wiki/w/File:OSRS_Map_of_{location_name.replace(' ', '_')}.png"
        )
        
    # Pet commands
    osrs_pets = app_commands.Group(name="osrs_pets", description="OSRS pet commands")

    def _calculate_drop_chance(self, base_rate: int, level: int) -> float:
        """Calculate drop chance based on level and base rate"""
        # Slight boost based on level
        level_modifier = 1 + (level * 0.01)
        return 1 / (base_rate / level_modifier)

    @osrs_pets.command(name="boss_hunt", description="Hunt for a boss pet")
    @app_commands.describe(boss_name="The name of the boss to hunt.")
    async def boss_hunt(self, interaction: discord.Interaction, boss_name: str):
        """Hunt for a boss pet"""
        boss_name_title = boss_name.title()
        if boss_name_title not in OSRSPetData.BOSS_PETS:
            await interaction.response.send_message(f"Unknown boss: {boss_name_title}", ephemeral=True)
            return

        player = await self._get_player(interaction.user.id)
        if not player:
             await interaction.response.send_message("You need to create a character first!", ephemeral=True)
             return
        
        combat_level = player.combat_level

        pet_data = OSRSPetData.BOSS_PETS[boss_name_title]
        drop_chance = self._calculate_drop_chance(pet_data["base_rate"], combat_level)

        if random.random() < drop_chance:
            pet_id = f"osrs_boss_{boss_name.lower()}_{interaction.user.id}"
            new_pet = Pet(
                pet_id=pet_id,
                name=boss_name_title,
                origin=PetOrigin.OSRS,
                rarity=pet_data["rarity"],
                owner_id=interaction.user.id,
                base_stats=pet_data["base_stats"],
                abilities=pet_data["abilities"],
                metadata={"boss": pet_data["boss"]},
            )

            self.pet_manager.register_pet(new_pet)

            embed = discord.Embed(
                title="🎉 Rare Drop!",
                description=f"Congratulations! You received {boss_name_title} pet!",
                color=discord.Color.gold(),
            )
            embed.add_field(name="Rarity", value=pet_data["rarity"].name)
            embed.add_field(name="Abilities", value=", ".join(pet_data["abilities"]))

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"No pet this time! Keep hunting {boss_name_title}!", ephemeral=True)

    @osrs_pets.command(name="skill_pet", description="Try to get a skilling pet")
    @app_commands.describe(skill="The skill to train for a pet.")
    async def skill_pet(self, interaction: discord.Interaction, skill: str):
        """Try to get a skilling pet"""
        skill_title = skill.title()
        relevant_pets = {
            name: data
            for name, data in OSRSPetData.SKILLING_PETS.items()
            if data["skill"].lower() == skill_title.lower()
        }

        if not relevant_pets:
            await interaction.response.send_message(f"No pets available for skill: {skill_title}", ephemeral=True)
            return

        player = await self._get_player(interaction.user.id)
        if not player:
             await interaction.response.send_message("You need to create a character first!", ephemeral=True)
             return

        skill_level = player.skills.get(skill.lower(), 1)

        for pet_name, pet_data in relevant_pets.items():
            drop_chance = self._calculate_drop_chance(pet_data["base_rate"], skill_level)

            if random.random() < drop_chance:
                pet_id = f"osrs_skill_{pet_name.lower()}_{interaction.user.id}"
                new_pet = Pet(
                    pet_id=pet_id,
                    name=pet_name,
                    origin=PetOrigin.OSRS,
                    rarity=pet_data["rarity"],
                    owner_id=interaction.user.id,
                    base_stats=pet_data["base_stats"],
                    abilities=pet_data["abilities"],
                    metadata={"skill": pet_data["skill"]},
                )

                self.pet_manager.register_pet(new_pet)

                embed = discord.Embed(
                    title="🎉 Skilling Pet!",
                    description=f"Congratulations! While training {skill_title}, you received {pet_name}!",
                    color=discord.Color.green(),
                )
                embed.add_field(name="Rarity", value=pet_data["rarity"].name)
                embed.add_field(name="Abilities", value=", ".join(pet_data["abilities"]))

                await interaction.response.send_message(embed=embed)
                return

        await interaction.response.send_message(f"No pet this time! Keep training {skill_title}!", ephemeral=True)

    @osrs_pets.command(name="my_pets", description="Display all OSRS pets you own")
    async def my_pets(self, interaction: discord.Interaction):
        """Display all OSRS pets owned by the user"""
        pets = self.pet_manager.get_pets_by_owner(interaction.user.id)
        osrs_pets = [p for p in pets if p.origin == PetOrigin.OSRS]

        if not osrs_pets:
            await interaction.response.send_message("You don't have any OSRS pets yet!", ephemeral=True)
            return

        embed = discord.Embed(
            title="Your OSRS Pets",
            description=f"You have {len(osrs_pets)} OSRS pets!",
            color=discord.Color.blue(),
        )

        for pet in osrs_pets:
            pet_info = (
                f"Level: {pet.stats.level}\n"
                f"Happiness: {pet.stats.happiness}/100\n"
                f"Loyalty: {pet.stats.loyalty}\n"
                f"Abilities: {', '.join(pet.abilities)}"
            )
            embed.add_field(name=pet.name, value=pet_info, inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(OsrsSlash(bot))
