import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Dict, List, TypedDict
from enum import Enum

class QuestStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class QuestData(TypedDict):
    id: int
    name: str
    description: str
    difficulty: str
    quest_points: int
    requirements: Dict[str, int]  # skill_name -> level
    rewards: Dict[str, int]  # reward_type -> amount

class QuestCommands(commands.Cog):
    """Quest and Achievement Commands"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='quests', description='View your quest list')
    async def view_quests(
        self,
        interaction: discord.Interaction,
        filter: Optional[str] = None,
        page: int = 1
    ):
        """View your quest list with optional filtering"""
        if page < 1:
            await interaction.response.send_message("Page number must be positive.", ephemeral=True)
            return

        # Get player's quests from database
        quests = await self.get_player_quests(interaction.user.id)
        if not quests:
            await interaction.response.send_message(
                "You haven't started any quests yet!",
                ephemeral=True
            )
            return

        # Filter quests if specified
        if filter:
            filter = filter.lower()
            if filter in ["completed", "in_progress", "not_started"]:
                quests = [q for q in quests if q["status"].lower() == filter]
            else:
                quests = [q for q in quests if filter in q["name"].lower()]

        # Paginate results
        per_page = 10
        offset = (page - 1) * per_page
        total_pages = (len(quests) + per_page - 1) // per_page

        if page > total_pages:
            await interaction.response.send_message(
                f"Invalid page number. Total pages: {total_pages}",
                ephemeral=True
            )
            return

        page_quests = quests[offset:offset + per_page]

        # Create embed
        embed = discord.Embed(
            title=f"{interaction.user.name}'s Quest Log",
            color=discord.Color.blue()
        )

        for quest in page_quests:
            status_emoji = {
                QuestStatus.NOT_STARTED: "⚪",
                QuestStatus.IN_PROGRESS: "🟡",
                QuestStatus.COMPLETED: "🟢"
            }[quest["status"]]

            embed.add_field(
                name=f"{status_emoji} {quest['name']}",
                value=f"Difficulty: {quest['difficulty']}\nPoints: {quest['quest_points']}",
                inline=False
            )

        # Add summary footer
        completed = sum(1 for q in quests if q["status"] == QuestStatus.COMPLETED)
        total = len(quests)
        total_points = sum(q["quest_points"] for q in quests if q["status"] == QuestStatus.COMPLETED)
        
        embed.set_footer(
            text=f"Page {page}/{total_pages} | "
            f"Completed: {completed}/{total} | "
            f"Quest Points: {total_points}"
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='quest_info', description='View details about a specific quest')
    async def quest_info(self, interaction: discord.Interaction, quest_name: str):
        """View detailed information about a specific quest"""
        # Get quest data
        quest = await self.get_quest_info(quest_name)
        if not quest:
            await interaction.response.send_message(
                f"Quest '{quest_name}' not found.",
                ephemeral=True
            )
            return

        # Get player's quest status
        status = await self.get_quest_status(interaction.user.id, quest["id"])

        embed = discord.Embed(
            title=quest["name"],
            description=quest["description"],
            color=discord.Color.blue()
        )

        # Status
        status_emoji = {
            QuestStatus.NOT_STARTED: "⚪",
            QuestStatus.IN_PROGRESS: "🟡",
            QuestStatus.COMPLETED: "🟢"
        }[status]
        embed.add_field(
            name="Status",
            value=f"{status_emoji} {status.value.replace('_', ' ').title()}",
            inline=True
        )

        # Basic info
        embed.add_field(
            name="Difficulty",
            value=quest["difficulty"],
            inline=True
        )
        embed.add_field(
            name="Quest Points",
            value=str(quest["quest_points"]),
            inline=True
        )

        # Requirements
        if quest["requirements"]:
            reqs = []
            for skill, level in quest["requirements"].items():
                reqs.append(f"{skill.title()}: Level {level}")
            embed.add_field(
                name="Requirements",
                value="\n".join(reqs),
                inline=False
            )

        # Rewards
        if quest["rewards"]:
            rewards = []
            for reward_type, amount in quest["rewards"].items():
                if reward_type == "xp":
                    rewards.append(f"XP: {amount:,}")
                elif reward_type == "coins":
                    rewards.append(f"Coins: {amount:,}")
                else:
                    rewards.append(f"{reward_type.title()}: {amount}")
            embed.add_field(
                name="Rewards",
                value="\n".join(rewards),
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='achievements', description='View your achievements')
    async def view_achievements(
        self,
        interaction: discord.Interaction,
        category: Optional[str] = None,
        page: int = 1
    ):
        """View your achievements with optional category filtering"""
        if page < 1:
            await interaction.response.send_message("Page number must be positive.", ephemeral=True)
            return

        # Get player's achievements from database
        achievements = await self.get_player_achievements(interaction.user.id)
        if not achievements:
            await interaction.response.send_message(
                "You haven't earned any achievements yet!",
                ephemeral=True
            )
            return

        # Filter by category if specified
        if category:
            achievements = [a for a in achievements if a["category"].lower() == category.lower()]
            if not achievements:
                await interaction.response.send_message(
                    f"No achievements found in category '{category}'.",
                    ephemeral=True
                )
                return

        # Paginate results
        per_page = 10
        offset = (page - 1) * per_page
        total_pages = (len(achievements) + per_page - 1) // per_page

        if page > total_pages:
            await interaction.response.send_message(
                f"Invalid page number. Total pages: {total_pages}",
                ephemeral=True
            )
            return

        page_achievements = achievements[offset:offset + per_page]

        # Create embed
        embed = discord.Embed(
            title=f"{interaction.user.name}'s Achievements",
            color=discord.Color.gold()
        )

        for achievement in page_achievements:
            status = "🏆" if achievement["completed"] else "⭕"
            
            value = achievement["description"]
            if achievement["rewards"]:
                rewards = []
                for reward_type, amount in achievement["rewards"].items():
                    rewards.append(f"{reward_type.title()}: {amount}")
                value += f"\nRewards: {', '.join(rewards)}"
            
            if achievement["completed"]:
                value += f"\nCompleted: {achievement['completed_at'].strftime('%Y-%m-%d')}"

            embed.add_field(
                name=f"{status} {achievement['name']}",
                value=value,
                inline=False
            )

        # Add summary footer
        completed = sum(1 for a in achievements if a["completed"])
        total = len(achievements)
        embed.set_footer(
            text=f"Page {page}/{total_pages} | "
            f"Completed: {completed}/{total}"
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='collection_log', description='View your collection log')
    async def collection_log(
        self,
        interaction: discord.Interaction,
        category: Optional[str] = None,
        page: int = 1
    ):
        """View your collection log with optional category filtering"""
        if page < 1:
            await interaction.response.send_message("Page number must be positive.", ephemeral=True)
            return

        # Get player's collection log from database
        collection = await self.get_collection_log(interaction.user.id)
        if not collection:
            await interaction.response.send_message(
                "Your collection log is empty!",
                ephemeral=True
            )
            return

        # Filter by category if specified
        if category:
            collection = [c for c in collection if c["category"].lower() == category.lower()]
            if not collection:
                await interaction.response.send_message(
                    f"No items found in category '{category}'.",
                    ephemeral=True
                )
                return

        # Paginate results
        per_page = 10
        offset = (page - 1) * per_page
        total_pages = (len(collection) + per_page - 1) // per_page

        if page > total_pages:
            await interaction.response.send_message(
                f"Invalid page number. Total pages: {total_pages}",
                ephemeral=True
            )
            return

        page_items = collection[offset:offset + per_page]

        # Create embed
        embed = discord.Embed(
            title=f"{interaction.user.name}'s Collection Log",
            color=discord.Color.purple()
        )

        for item in page_items:
            status = "✅" if item["obtained"] else "❌"
            value = f"Category: {item['category']}"
            if item["obtained"]:
                value += f"\nQuantity: {item['quantity']:,}"
                value += f"\nObtained: {item['obtained_at'].strftime('%Y-%m-%d')}"

            embed.add_field(
                name=f"{status} {item['name']}",
                value=value,
                inline=False
            )

        # Add summary footer
        obtained = sum(1 for i in collection if i["obtained"])
        total = len(collection)
        embed.set_footer(
            text=f"Page {page}/{total_pages} | "
            f"Obtained: {obtained}/{total}"
        )

        await interaction.response.send_message(embed=embed)

    async def get_player_quests(self, player_id: int) -> List[Dict]:
        """Get a player's quests from the database"""
        # TODO: Implement database retrieval
        return []

    async def get_quest_info(self, quest_name: str) -> Optional[QuestData]:
        """Get information about a specific quest"""
        # TODO: Implement database retrieval
        return None

    async def get_quest_status(self, player_id: int, quest_id: int) -> QuestStatus:
        """Get a player's status for a specific quest"""
        # TODO: Implement database retrieval
        return QuestStatus.NOT_STARTED

    async def get_player_achievements(self, player_id: int) -> List[Dict]:
        """Get a player's achievements from the database"""
        # TODO: Implement database retrieval
        return []

    async def get_collection_log(self, player_id: int) -> List[Dict]:
        """Get a player's collection log from the database"""
        # TODO: Implement database retrieval
        return []

async def setup(bot):
    await bot.add_cog(QuestCommands(bot)) 