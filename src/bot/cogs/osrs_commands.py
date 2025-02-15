"""OSRS game commands implementation."""
from discord.ext import commands
from discord import Embed
import logging
from typing import Dict, Optional, List
from discord.ext.commands import Context

import src.osrs.models as osrs_models
import src.osrs.core.world_manager as world_mgr


logger = logging.getLogger('OSRSCommands')


class OSRSCommands(commands.Cog):
    """OSRS game commands implementation."""
    
    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the cog with bot instance."""
        super().__init__()
        self.bot = bot
        self.players: Dict[int, osrs_models.Player] = {}
        
    async def cog_load(self) -> None:
        """Called when the cog is loaded."""
        logger.info("OSRS Commands cog loaded")
        
    @commands.command(name="create")
    async def create_character(
        self,
        ctx: Context,
        name: str
    ) -> None:
        """Create a new OSRS character."""
        player_id = ctx.author.id
        
        if player_id in self.players:
            await ctx.send("You already have a character!")
            return
            
        player = osrs_models.Player(id=player_id, name=name)
        self.players[player_id] = player
        
        # Join default world (301)
        world_mgr.world_manager.join_world(player, 301)
        
        embed = Embed(title="Character Created!", color=0x00ff00)
        embed.add_field(name="Name", value=name)
        embed.add_field(
            name="Combat Level",
            value=str(player.get_combat_level())
        )
        embed.add_field(
            name="World",
            value="World 301 (Default)",
            inline=False
        )
        await ctx.send(embed=embed)

    @commands.command(name="world")
    async def show_world(self, ctx: Context) -> None:
        """Show your current world."""
        player = self.players.get(ctx.author.id)
        if not player:
            await ctx.send(
                "You don't have a character! Use !create [name] to make one."
            )
            return
            
        current_world = world_mgr.world_manager.get_player_world(player)
        if not current_world:
            await ctx.send("You are not in any world!")
            return
            
        embed = Embed(
            title=f"{current_world.name}",
            color=0x00ff00
        )
        embed.add_field(name="Type", value=current_world.type.title())
        embed.add_field(name="Region", value=current_world.region.upper())
        embed.add_field(
            name="Players",
            value=f"{current_world.player_count}/{current_world.max_players}"
        )
        await ctx.send(embed=embed)

    @commands.command(name="worlds")
    async def list_worlds(
        self,
        ctx: Context,
        type_filter: Optional[str] = None
    ) -> None:
        """List available game worlds."""
        worlds: List[world_mgr.World] = (
            world_mgr.world_manager.get_available_worlds(
                type_filter=type_filter
            )
        )
        
        if not worlds:
            await ctx.send("No worlds found!")
            return
            
        embed = Embed(
            title="OSRS Worlds",
            color=0x00ff00
        )
        
        for world in worlds:
            name = f"{world.name} ({world.type.title()})"
            value = (
                f"Region: {world.region.upper()}\n"
                f"Players: {world.player_count}/{world.max_players}"
            )
            embed.add_field(
                name=name,
                value=value,
                inline=False
            )
            
        await ctx.send(embed=embed)

    @commands.command(name="join")
    async def join_world(
        self,
        ctx: Context,
        world_id: int
    ) -> None:
        """Join a different game world."""
        player = self.players.get(ctx.author.id)
        if not player:
            await ctx.send(
                "You don't have a character! Use !create [name] to make one."
            )
            return
            
        try:
            if world_mgr.world_manager.join_world(player, world_id):
                world = world_mgr.world_manager.get_world(world_id)
                assert world is not None  # We know it exists from join_world
                
                embed = Embed(
                    title="World Change Successful!",
                    color=0x00ff00
                )
                embed.add_field(
                    name="New World",
                    value=world.name
                )
                embed.add_field(
                    name="Type",
                    value=world.type.title()
                )
                embed.add_field(
                    name="Players",
                    value=f"{world.player_count}/{world.max_players}"
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(
                    "Could not join that world! "
                    "Check requirements and player count."
                )
        except ValueError as e:
            await ctx.send(str(e))

    @commands.command(name="stats")
    async def show_stats(self, ctx: Context) -> None:
        """Show your character's stats."""
        player = self.players.get(ctx.author.id)
        if not player:
            await ctx.send(
                "You don't have a character! Use !create [name] to make one."
            )
            return
            
        embed = Embed(title=f"{player.name}'s Stats", color=0x00ff00)
        
        # Add combat stats first
        combat_skills = [
            osrs_models.SkillType.ATTACK,
            osrs_models.SkillType.STRENGTH,
            osrs_models.SkillType.DEFENCE,
            osrs_models.SkillType.HITPOINTS,
            osrs_models.SkillType.RANGED,
            osrs_models.SkillType.PRAYER,
            osrs_models.SkillType.MAGIC
        ]
        
        combat_text = ""
        for skill_type in combat_skills:
            skill = player.skills[skill_type]
            combat_text += f"{skill_type.value.title()}: {skill.level}\n"
        embed.add_field(name="Combat Skills", value=combat_text)
        
        # Add other skills
        other_skills = [
            s for s in osrs_models.SkillType if s not in combat_skills
        ]
        other_text = ""
        for skill_type in other_skills:
            skill = player.skills[skill_type]
            other_text += f"{skill_type.value.title()}: {skill.level}\n"
        embed.add_field(name="Other Skills", value=other_text)
        
        # Add world info
        current_world = world_mgr.world_manager.get_player_world(player)
        if current_world:
            embed.add_field(
                name="Current World",
                value=current_world.name,
                inline=False
            )
        
        embed.add_field(
            name="Combat Level",
            value=str(player.get_combat_level())
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Add the cog to the bot."""
    await bot.add_cog(OSRSCommands(bot))
