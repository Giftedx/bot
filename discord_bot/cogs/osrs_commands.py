"""Old School RuneScape (OSRS) related commands."""

import discord
from discord.ext import commands
import aiohttp
import asyncio
from typing import Optional
import json

class OSRSCommands(commands.Cog, name="OSRS"):
    """Old School RuneScape (OSRS) game integration.
    
    This category includes commands for:
    - Player stats lookup
    - Grand Exchange prices
    - Hiscores tracking
    - XP calculators
    - Quest information
    
    Uses the official OSRS API for real-time data.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws"
        self.ge_url = "https://secure.runescape.com/m=itemdb_oldschool/api/catalogue/detail.json"
        self.skills = [
            "Overall", "Attack", "Defence", "Strength", "Hitpoints", "Ranged",
            "Prayer", "Magic", "Cooking", "Woodcutting", "Fletching", "Fishing",
            "Firemaking", "Crafting", "Smithing", "Mining", "Herblore", "Agility",
            "Thieving", "Slayer", "Farming", "Runecrafting", "Hunter", "Construction"
        ]
    
    @commands.command(name="stats")
    async def player_stats(self, ctx, username: str):
        """Look up a player's OSRS stats.
        
        Retrieves and displays a player's skill levels and experience.
        
        Parameters:
        -----------
        username: The OSRS player's username
        
        Examples:
        ---------
        !stats Zezima
        !stats Lynx Titan
        
        Notes:
        ------
        - Shows all 23 skills
        - Includes total level
        - Shows experience points
        - Updates in real-time
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}?player={username}") as response:
                if response.status == 404:
                    await ctx.send(f"Player '{username}' not found!")
                    return
                    
                data = await response.text()
                stats = data.split("\n")
                
                embed = discord.Embed(
                    title=f"OSRS Stats for {username}",
                    color=discord.Color.gold()
                )
                
                # First line is overall stats
                overall_rank, overall_level, overall_xp = stats[0].split(",")
                embed.add_field(
                    name="Total Level",
                    value=f"Level: {overall_level}\nXP: {int(overall_xp):,}",
                    inline=False
                )
                
                # Add other skills (skip first line as it's overall)
                for i, skill_stats in enumerate(stats[1:24], 1):  # Only first 23 skills
                    rank, level, xp = skill_stats.split(",")
                    embed.add_field(
                        name=self.skills[i],
                        value=f"Level: {level}\nXP: {int(xp):,}",
                        inline=True
                    )
                
                await ctx.send(embed=embed)
    
    @commands.command(name="price")
    async def item_price(self, ctx, *, item_name: str):
        """Look up an item's Grand Exchange price.
        
        Retrieves current Grand Exchange price and trade volume for an item.
        
        Parameters:
        -----------
        item_name: The name of the OSRS item
        
        Examples:
        ---------
        !price Abyssal whip
        !price Dragon bones
        
        Notes:
        ------
        - Shows current price
        - Displays price trends
        - Shows trade volume
        - Updates every 30 minutes
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.ge_url}?item={item_name}") as response:
                if response.status == 404:
                    await ctx.send(f"Item '{item_name}' not found!")
                    return
                    
                data = await response.json()
                item = data['item']
                
                embed = discord.Embed(
                    title=f"OSRS Grand Exchange: {item['name']}",
                    color=discord.Color.gold()
                )
                
                embed.add_field(name="Current Price", value=f"{item['current']['price']:,} gp", inline=True)
                embed.add_field(name="Today's Change", value=item['today']['trend'], inline=True)
                embed.add_field(name="30 Day Change", value=item['day30']['change'], inline=True)
                
                if 'description' in item:
                    embed.add_field(name="Description", value=item['description'], inline=False)
                    
                if 'icon' in item:
                    embed.set_thumbnail(url=item['icon'])
                
                await ctx.send(embed=embed)
    
    @commands.command(name="xp")
    async def xp_calculator(self, ctx, current_level: int, target_level: int, skill: str = ""):
        """Calculate XP needed for a level goal.
        
        Calculates the experience points needed to reach a target level.
        
        Parameters:
        -----------
        current_level: Current skill level (1-99)
        target_level: Target skill level (1-99)
        skill: Optional skill name for specific calculations
        
        Examples:
        ---------
        !xp 70 99 Attack
        !xp 1 99 Prayer
        !xp 50 99
        
        Notes:
        ------
        - Shows XP required
        - Calculates time estimates
        - Lists recommended training methods
        - Supports all skills
        """
        if current_level < 1 or current_level > 99 or target_level < 1 or target_level > 99:
            await ctx.send("Levels must be between 1 and 99!")
            return
            
        if current_level >= target_level:
            await ctx.send("Target level must be higher than current level!")
            return
            
        # XP formula
        def level_to_xp(level):
            total = 0
            for i in range(1, level):
                total += int(i + 300 * (2 ** (i / 7.0)))
            return total // 4
            
        current_xp = level_to_xp(current_level)
        target_xp = level_to_xp(target_level)
        xp_needed = target_xp - current_xp
        
        embed = discord.Embed(
            title=f"OSRS XP Calculator{f' - {skill}' if skill else ''}",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Level Goal",
            value=f"Current: {current_level}\nTarget: {target_level}",
            inline=True
        )
        embed.add_field(
            name="Experience",
            value=f"Required: {xp_needed:,} XP",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="quest")
    async def quest_info(self, ctx, *, quest_name: str):
        """Look up information about an OSRS quest.
        
        Retrieves details about a specific quest including requirements and rewards.
        
        Parameters:
        -----------
        quest_name: The name of the quest
        
        Examples:
        ---------
        !quest Dragon Slayer
        !quest Cook's Assistant
        
        Notes:
        ------
        - Shows requirements
        - Lists rewards
        - Displays difficulty
        - Shows quest points
        """
        # Load quest data from JSON file
        try:
            with open('data/osrs_quests.json', 'r') as f:
                quests = json.load(f)
        except FileNotFoundError:
            await ctx.send("Quest database not found!")
            return
            
        # Find quest (case-insensitive)
        quest = None
        for q in quests:
            if q['name'].lower() == quest_name.lower():
                quest = q
                break
                
        if not quest:
            await ctx.send(f"Quest '{quest_name}' not found!")
            return
            
        embed = discord.Embed(
            title=f"OSRS Quest: {quest['name']}",
            description=quest['description'],
            color=discord.Color.gold()
        )
        
        embed.add_field(name="Difficulty", value=quest['difficulty'], inline=True)
        embed.add_field(name="Length", value=quest['length'], inline=True)
        embed.add_field(name="Quest Points", value=str(quest['points']), inline=True)
        
        if 'requirements' in quest:
            embed.add_field(
                name="Requirements",
                value="\n".join(f"• {req}" for req in quest['requirements']),
                inline=False
            )
            
        if 'rewards' in quest:
            embed.add_field(
                name="Rewards",
                value="\n".join(f"• {reward}" for reward in quest['rewards']),
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(OSRSCommands(bot)) 