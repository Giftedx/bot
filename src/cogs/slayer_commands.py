import discord
from discord.ext import commands
from typing import Optional

from ..osrs.core.slayer_system import SlayerSystem, SlayerTask
from ..osrs.database.database_manager import DatabaseManager

class SlayerCommands(commands.Cog):
    """Slayer skill commands"""
    
    def __init__(self, bot: commands.Bot, db: DatabaseManager):
        self.bot = bot
        self.db = db
        self.slayer_system = SlayerSystem()
    
    @commands.group(name='slayer', invoke_without_command=True)
    async def slayer(self, ctx: commands.Context):
        """Slayer commands"""
        await ctx.send_help(ctx.command)
    
    @slayer.command(name='task')
    async def get_task(self, ctx: commands.Context):
        """View your current slayer task"""
        # Get player's current task
        task = self.slayer_system.current_task
        if not task:
            await ctx.send("You don't have a slayer task. Use `!slayer master` to get one!")
            return
            
        embed = discord.Embed(
            title="Slayer Task",
            color=discord.Color.blue()
        )
        
        # Format monster name
        monster_name = task.monster_id.replace('_', ' ').title()
        
        embed.add_field(
            name="Assignment",
            value=f"{monster_name} ({task.amount_remaining}/{task.amount_assigned})",
            inline=False
        )
        
        if task.experience_gained > 0:
            embed.add_field(
                name="XP Gained",
                value=f"{task.experience_gained:,.1f}",
                inline=True
            )
            
        await ctx.send(embed=embed)
    
    @slayer.command(name='master')
    async def get_master_task(self, ctx: commands.Context, master_name: str):
        """Get a new task from a slayer master"""
        # Get player's slayer level
        stats = self.bot.get_player_stats(ctx.author.id)
        if not stats:
            await ctx.send("You need to create a character first!")
            return
            
        # Get blocked tasks
        blocked_tasks = []  # TODO: Implement blocked tasks from database
        
        # Assign new task
        task = self.slayer_system.assign_task(
            master_name,
            stats.slayer,
            blocked_tasks
        )
        
        if not task:
            # Check if it failed due to level requirement
            master = self.slayer_system.MASTERS.get(master_name.lower())
            if master and stats.slayer < master.level_req:
                await ctx.send(
                    f"You need level {master.level_req} Slayer to use {master.name}."
                )
            else:
                await ctx.send(
                    "You already have a task! Use `!slayer task` to view it, "
                    "or `!slayer cancel` to cancel it."
                )
            return
            
        # Format monster name
        monster_name = task.monster_id.replace('_', ' ').title()
        
        embed = discord.Embed(
            title="New Slayer Task",
            description=f"Your new task is to kill {task.amount_assigned} {monster_name}.",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @slayer.command(name='masters')
    async def list_masters(self, ctx: commands.Context):
        """List available slayer masters"""
        # Get player's slayer level
        stats = self.bot.get_player_stats(ctx.author.id)
        if not stats:
            await ctx.send("You need to create a character first!")
            return
            
        embed = discord.Embed(
            title="Slayer Masters",
            color=discord.Color.blue()
        )
        
        # Group masters by availability
        available = []
        locked = []
        
        for master in self.slayer_system.MASTERS.values():
            if stats.slayer >= master.level_req:
                available.append(
                    f"• {master.name} (Level {master.level_req})"
                )
            else:
                locked.append(
                    f"• {master.name} (Level {master.level_req})"
                )
        
        if available:
            embed.add_field(
                name="Available Masters",
                value="\n".join(available),
                inline=False
            )
            
        if locked:
            embed.add_field(
                name="Locked Masters",
                value="\n".join(locked),
                inline=False
            )
            
        await ctx.send(embed=embed)
    
    @slayer.command(name='points')
    async def check_points(self, ctx: commands.Context):
        """Check your slayer points"""
        embed = discord.Embed(
            title="Slayer Points",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Points",
            value=str(self.slayer_system.points),
            inline=True
        )
        
        embed.add_field(
            name="Task Streak",
            value=str(self.slayer_system.task_streak),
            inline=True
        )
        
        embed.add_field(
            name="Total Tasks",
            value=str(self.slayer_system.total_tasks),
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @slayer.command(name='rewards')
    async def list_rewards(self, ctx: commands.Context):
        """List available slayer rewards"""
        embed = discord.Embed(
            title="Slayer Rewards",
            description=f"You have {self.slayer_system.points} points",
            color=discord.Color.blue()
        )
        
        # List unlockable rewards
        unlockables = []
        for name, reward in self.slayer_system.REWARDS['unlocks'].items():
            status = "✅" if name in self.slayer_system.unlocks else "❌"
            unlockables.append(
                f"{status} {name.replace('_', ' ').title()} "
                f"({reward['points']} points)\n"
                f"└ {reward['description']}"
            )
            
        if unlockables:
            embed.add_field(
                name="Unlockable Rewards",
                value="\n".join(unlockables),
                inline=False
            )
            
        # List point costs
        costs = [
            "• Cancel task: 30 points",
            "• Block task: 100 points",
            "• Unblock task: 50 points"
        ]
        
        embed.add_field(
            name="Point Costs",
            value="\n".join(costs),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @slayer.command(name='cancel')
    async def cancel_task(self, ctx: commands.Context):
        """Cancel your current slayer task"""
        if self.slayer_system.cancel_task():
            await ctx.send("Your slayer task has been cancelled for 30 points.")
        else:
            await ctx.send(
                "You don't have a task to cancel, or you don't have enough points!"
            )
    
    @slayer.command(name='block')
    async def block_task(self, ctx: commands.Context):
        """Block your current slayer task"""
        blocked = self.slayer_system.block_task()
        if blocked:
            monster_name = blocked.replace('_', ' ').title()
            await ctx.send(
                f"{monster_name} tasks have been blocked for 100 points."
            )
        else:
            await ctx.send(
                "You don't have a task to block, or you don't have enough points!"
            )
    
    @slayer.command(name='unlock')
    async def unlock_reward(self, ctx: commands.Context, *, reward_name: str):
        """Unlock a slayer reward"""
        if self.slayer_system.unlock_reward(reward_name.lower().replace(' ', '_')):
            await ctx.send(f"You have unlocked {reward_name}!")
        else:
            await ctx.send(
                "Invalid reward, already unlocked, or not enough points!"
            )

async def setup(bot: commands.Bot):
    """Set up the slayer commands cog."""
    db = DatabaseManager()
    await bot.add_cog(SlayerCommands(bot, db)) 