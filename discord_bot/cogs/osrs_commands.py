from discord.ext import commands
import discord
import logging
import aiohttp
import json

logger = logging.getLogger(__name__)

class OSRSCommands(commands.Cog, name="OSRS"):
    """Old School RuneScape related commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.osrs_ge_api = "https://prices.runescape.wiki/api/v1/osrs"
        self.headers = {
            'User-Agent': 'Discord Bot - Price Checker'
        }
    
    @commands.command(name='price')
    async def check_price(self, ctx, *, item_name: str):
        """Check the current GE price of an OSRS item.
        
        Parameters:
        -----------
        item_name: The name of the item to look up
        
        Example:
        --------
        !price Dragon bones
        """
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(f"{self.osrs_ge_api}/latest") as response:
                    if response.status == 200:
                        data = await response.json()
                        # This is a simplified version - would need proper item ID mapping
                        await ctx.send(f"Price checking for {item_name} (Note: This is a placeholder. Need item ID mapping)")
                    else:
                        await ctx.send("Failed to fetch price data from OSRS API")
        except Exception as e:
            logger.error(f"Error checking OSRS price: {e}")
            await ctx.send("An error occurred while checking the price.")

    @commands.command(name='stats')
    async def check_stats(self, ctx, *, username: str):
        """Check the stats of an OSRS player.
        
        Parameters:
        -----------
        username: The RuneScape username to look up
        
        Example:
        --------
        !stats Zezima
        """
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(f"https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws?player={username}") as response:
                    if response.status == 200:
                        stats_data = await response.text()
                        # Create an embed with the player's stats
                        embed = discord.Embed(title=f"OSRS Stats for {username}", color=discord.Color.gold())
                        
                        # Parse the stats data (this is a simplified version)
                        skills = ["Overall", "Attack", "Defence", "Strength", "Hitpoints", "Ranged", "Prayer", "Magic"]
                        stats_lines = stats_data.split("\n")
                        
                        for i, skill in enumerate(skills):
                            if i < len(stats_lines):
                                rank, level, xp = stats_lines[i].split(",")
                                embed.add_field(
                                    name=skill,
                                    value=f"Level: {level}\nXP: {xp}\nRank: {rank}",
                                    inline=True
                                )
                        
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f"Could not find stats for player: {username}")
        except Exception as e:
            logger.error(f"Error checking OSRS stats: {e}")
            await ctx.send("An error occurred while checking the stats.")

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(OSRSCommands(bot)) 