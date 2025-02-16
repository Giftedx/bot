"""OSRS quest system implementation."""

from typing import Dict, List, Optional
import discord
from discord.ext import commands
from dataclasses import dataclass, field

from src.osrs.models import Player, SkillType, QuestStatus


@dataclass
class QuestRequirement:
    """Represents a requirement for a quest."""
    skill_type: Optional[SkillType] = None
    skill_level: int = 0
    quest_id: Optional[str] = None
    item_id: Optional[str] = None
    item_quantity: int = 0


@dataclass
class QuestReward:
    """Represents rewards for completing a quest."""
    xp_rewards: Dict[SkillType, int] = field(default_factory=dict)
    item_rewards: Dict[str, int] = field(default_factory=dict)  # item_id -> quantity
    quest_points: int = 1
    gold: int = 0


@dataclass
class Quest:
    """Represents an OSRS quest."""
    id: str
    name: str
    description: str
    difficulty: str  # Novice, Intermediate, Experienced, Master, Grandmaster
    requirements: List[QuestRequirement] = field(default_factory=list)
    rewards: QuestReward = field(default_factory=QuestReward)
    quest_points_required: int = 0


class QuestCommands(commands.Cog):
    """Quest-related commands for OSRS."""
    
    def __init__(self, bot):
        self.bot = bot
        self.quests: Dict[str, Quest] = self._initialize_quests()
    
    def _initialize_quests(self) -> Dict[str, Quest]:
        """Initialize quest data."""
        quests = {}
        
        # Cook's Assistant
        quests["cooks_assistant"] = Quest(
            id="cooks_assistant",
            name="Cook's Assistant",
            description="Help the cook make a cake for Duke Horacio.",
            difficulty="Novice",
            requirements=[],
            rewards=QuestReward(
                xp_rewards={SkillType.COOKING: 300},
                quest_points=1
            )
        )
        
        # Rune Mysteries
        quests["rune_mysteries"] = Quest(
            id="rune_mysteries",
            name="Rune Mysteries",
            description="Discover the secret of Runecrafting.",
            difficulty="Novice",
            requirements=[],
            rewards=QuestReward(
                xp_rewards={SkillType.RUNECRAFT: 250},
                quest_points=1
            )
        )
        
        # Dragon Slayer
        quests["dragon_slayer"] = Quest(
            id="dragon_slayer",
            name="Dragon Slayer",
            description="Prove yourself a true champion by slaying Elvarg.",
            difficulty="Experienced",
            requirements=[
                QuestRequirement(skill_type=SkillType.ATTACK, skill_level=30),
                QuestRequirement(skill_type=SkillType.DEFENCE, skill_level=30),
                QuestRequirement(quest_id="rune_mysteries"),
                QuestRequirement(quest_points_required=32)
            ],
            rewards=QuestReward(
                xp_rewards={
                    SkillType.STRENGTH: 18650,
                    SkillType.DEFENCE: 18650
                },
                quest_points=2,
                gold=10000
            )
        )
        
        return quests
    
    @commands.group(invoke_without_command=True)
    async def quest(self, ctx):
        """Quest commands"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="📜 Quest Commands",
                description="OSRS Quest System",
                color=discord.Color.gold()
            )
            
            commands = """
            `!quest list` - List all quests
            `!quest info <quest>` - View quest details
            `!quest start <quest>` - Start a quest
            `!quest progress` - View quest progress
            """
            embed.add_field(name="Commands", value=commands, inline=False)
            
            await ctx.send(embed=embed)
    
    @quest.command(name="list")
    async def list_quests(self, ctx):
        """List all available quests"""
        player = self.bot.get_player(ctx.author.id)
        if not player:
            return await ctx.send(
                "You don't have a character! Use `!osrs create <name>` to make one."
            )
        
        embed = discord.Embed(
            title="Available Quests",
            color=discord.Color.blue()
        )
        
        # Group quests by difficulty
        difficulties = {
            "Novice": [],
            "Intermediate": [],
            "Experienced": [],
            "Master": [],
            "Grandmaster": []
        }
        
        for quest in self.quests.values():
            status = player.get_quest_status(quest.id)
            status_emoji = "✅" if status == QuestStatus.COMPLETED else (
                "🔄" if status == QuestStatus.IN_PROGRESS else "❌"
            )
            difficulties[quest.difficulty].append(
                f"{status_emoji} {quest.name}"
            )
        
        for difficulty, quests in difficulties.items():
            if quests:
                embed.add_field(
                    name=difficulty,
                    value="\n".join(quests),
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    @quest.command(name="info")
    async def quest_info(self, ctx, *, quest_name: str):
        """View details about a specific quest"""
        # Find quest
        quest = next(
            (q for q in self.quests.values() if q.name.lower() == quest_name.lower()),
            None
        )
        if not quest:
            return await ctx.send(f"Quest '{quest_name}' not found!")
        
        player = self.bot.get_player(ctx.author.id)
        if not player:
            return await ctx.send(
                "You don't have a character! Use `!osrs create <name>` to make one."
            )
        
        embed = discord.Embed(
            title=quest.name,
            description=quest.description,
            color=discord.Color.blue()
        )
        
        # Requirements
        if quest.requirements:
            reqs = []
            for req in quest.requirements:
                if req.skill_type:
                    current_level = player.skills[req.skill_type].level
                    emoji = "✅" if current_level >= req.skill_level else "❌"
                    reqs.append(
                        f"{emoji} {req.skill_type.value.title()} "
                        f"level {req.skill_level} ({current_level})"
                    )
                elif req.quest_id:
                    req_quest = self.quests[req.quest_id]
                    status = player.get_quest_status(req.quest_id)
                    emoji = "✅" if status == QuestStatus.COMPLETED else "❌"
                    reqs.append(f"{emoji} Complete '{req_quest.name}'")
            
            embed.add_field(
                name="Requirements",
                value="\n".join(reqs) or "None",
                inline=False
            )
        
        # Rewards
        rewards = []
        for skill, xp in quest.rewards.xp_rewards.items():
            rewards.append(f"{skill.value.title()} XP: {xp:,}")
        if quest.rewards.gold:
            rewards.append(f"Gold: {quest.rewards.gold:,}")
        if quest.rewards.quest_points:
            rewards.append(f"Quest Points: {quest.rewards.quest_points}")
        for item_id, quantity in quest.rewards.item_rewards.items():
            item = self.bot.item_db.get_item(item_id)
            if item:
                rewards.append(f"{item.name}: {quantity:,}")
        
        embed.add_field(
            name="Rewards",
            value="\n".join(rewards),
            inline=False
        )
        
        # Status
        status = player.get_quest_status(quest.id)
        embed.add_field(
            name="Status",
            value=status.value.title().replace("_", " "),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @quest.command(name="start")
    async def start_quest(self, ctx, *, quest_name: str):
        """Start a quest"""
        # Find quest
        quest = next(
            (q for q in self.quests.values() if q.name.lower() == quest_name.lower()),
            None
        )
        if not quest:
            return await ctx.send(f"Quest '{quest_name}' not found!")
        
        player = self.bot.get_player(ctx.author.id)
        if not player:
            return await ctx.send(
                "You don't have a character! Use `!osrs create <name>` to make one."
            )
        
        # Check if already started/completed
        status = player.get_quest_status(quest.id)
        if status == QuestStatus.COMPLETED:
            return await ctx.send(f"You've already completed '{quest.name}'!")
        elif status == QuestStatus.IN_PROGRESS:
            return await ctx.send(f"You've already started '{quest.name}'!")
        
        # Check requirements
        missing_reqs = []
        for req in quest.requirements:
            if req.skill_type:
                if player.skills[req.skill_type].level < req.skill_level:
                    missing_reqs.append(
                        f"{req.skill_type.value.title()} level {req.skill_level}"
                    )
            elif req.quest_id:
                if player.get_quest_status(req.quest_id) != QuestStatus.COMPLETED:
                    req_quest = self.quests[req.quest_id]
                    missing_reqs.append(f"Complete '{req_quest.name}'")
            elif req.quest_points_required:
                if player.quest_points < req.quest_points_required:
                    missing_reqs.append(
                        f"{req.quest_points_required} Quest Points"
                    )
        
        if missing_reqs:
            return await ctx.send(
                f"You don't meet the requirements for '{quest.name}':\n"
                + "\n".join(f"• {req}" for req in missing_reqs)
            )
        
        # Start quest
        player.start_quest(quest.id)
        
        embed = discord.Embed(
            title=f"Started: {quest.name}",
            description=quest.description,
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @quest.command(name="progress")
    async def quest_progress(self, ctx):
        """View quest progress"""
        player = self.bot.get_player(ctx.author.id)
        if not player:
            return await ctx.send(
                "You don't have a character! Use `!osrs create <name>` to make one."
            )
        
        embed = discord.Embed(
            title=f"{player.name}'s Quest Progress",
            color=discord.Color.blue()
        )
        
        # Count quests by status
        total = len(self.quests)
        completed = sum(
            1 for q in self.quests
            if player.get_quest_status(q) == QuestStatus.COMPLETED
        )
        in_progress = sum(
            1 for q in self.quests
            if player.get_quest_status(q) == QuestStatus.IN_PROGRESS
        )
        not_started = total - completed - in_progress
        
        stats = f"""
        Completed: {completed}
        In Progress: {in_progress}
        Not Started: {not_started}
        Total Quests: {total}
        Quest Points: {player.quest_points}
        """
        embed.add_field(name="Statistics", value=stats, inline=False)
        
        # Show in-progress quests
        in_progress_quests = [
            q.name for q in self.quests.values()
            if player.get_quest_status(q.id) == QuestStatus.IN_PROGRESS
        ]
        if in_progress_quests:
            embed.add_field(
                name="In Progress",
                value="\n".join(in_progress_quests),
                inline=False
            )
        
        await ctx.send(embed=embed)


async def setup(bot):
    """Set up the quest commands cog."""
    await bot.add_cog(QuestCommands(bot)) 