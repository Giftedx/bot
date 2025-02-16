"""Help commands for the OSRS Discord bot."""

import discord
from discord.ext import commands

class HelpCommands(commands.Cog):
    """Commands for getting help with the bot."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='help')
    async def help_command(self, ctx, command_name: str = None):
        """Get help with bot commands.
        
        Args:
            command_name: Optional name of command to get help with.
        """
        if command_name is None:
            # Show general help
            embed = discord.Embed(
                title="OSRS Bot Help",
                description="Here are the available command categories:",
                color=discord.Color.blue()
            )
            
            # Add command categories
            embed.add_field(
                name="Combat Commands",
                value="Use `!help combat` to see combat-related commands",
                inline=False
            )
            embed.add_field(
                name="Stats Commands", 
                value="Use `!help stats` to see stats-related commands",
                inline=False
            )
            embed.add_field(
                name="Skills Commands",
                value="Use `!help skills` to see skills-related commands",
                inline=False
            )
            embed.add_field(
                name="Economy Commands",
                value="Use `!help economy` to see economy-related commands",
                inline=False
            )
            embed.add_field(
                name="Quest Commands",
                value="Use `!help quests` to see quest-related commands",
                inline=False
            )
            embed.add_field(
                name="Pet Commands",
                value="Use `!help pets` to see pet-related commands",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        else:
            # Show help for specific command category
            command_name = command_name.lower()
            
            if command_name == 'combat':
                embed = discord.Embed(
                    title="Combat Commands",
                    description="Here are the available combat commands:",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="!attack [monster]",
                    value="Attack a monster",
                    inline=False
                )
                embed.add_field(
                    name="!equip [item]",
                    value="Equip an item",
                    inline=False
                )
                embed.add_field(
                    name="!gear",
                    value="View your current gear",
                    inline=False
                )
                
            elif command_name == 'stats':
                embed = discord.Embed(
                    title="Stats Commands",
                    description="Here are the available stats commands:",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="!stats",
                    value="View your stats",
                    inline=False
                )
                embed.add_field(
                    name="!highscores",
                    value="View the highscores",
                    inline=False
                )
                
            elif command_name == 'skills':
                embed = discord.Embed(
                    title="Skills Commands",
                    description="Here are the available skills commands:",
                    color=discord.Color.gold()
                )
                embed.add_field(
                    name="!train [skill]",
                    value="Train a skill",
                    inline=False
                )
                embed.add_field(
                    name="!level [skill]",
                    value="View your level in a skill",
                    inline=False
                )
                
            elif command_name == 'economy':
                embed = discord.Embed(
                    title="Economy Commands",
                    description="Here are the available economy commands:",
                    color=discord.Color.gold()
                )
                embed.add_field(
                    name="!balance",
                    value="Check your balance",
                    inline=False
                )
                embed.add_field(
                    name="!shop",
                    value="View the shop",
                    inline=False
                )
                embed.add_field(
                    name="!buy [item]",
                    value="Buy an item from the shop",
                    inline=False
                )
                
            elif command_name == 'quests':
                embed = discord.Embed(
                    title="Quest Commands",
                    description="Here are the available quest commands:",
                    color=discord.Color.purple()
                )
                embed.add_field(
                    name="!quests",
                    value="View available quests",
                    inline=False
                )
                embed.add_field(
                    name="!start [quest]",
                    value="Start a quest",
                    inline=False
                )
                
            elif command_name == 'pets':
                embed = discord.Embed(
                    title="Pet Commands",
                    description="Here are the available pet commands:",
                    color=discord.Color.purple()
                )
                embed.add_field(
                    name="!pets",
                    value="View your pets",
                    inline=False
                )
                embed.add_field(
                    name="!pet [name]",
                    value="View details about a specific pet",
                    inline=False
                )
                
            else:
                embed = discord.Embed(
                    title="Error",
                    description=f"Unknown command category: {command_name}",
                    color=discord.Color.red()
                )
            
            await ctx.send(embed=embed)

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(HelpCommands(bot)) 