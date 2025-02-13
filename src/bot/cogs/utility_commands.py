import discord
from discord.ext import commands
import logging

logger = logging.getLogger('DiscordBot')

class UtilityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help')
    async def help(self, ctx):
        """Show all available commands"""
        embed = discord.Embed(
            title="Available Commands",
            description="Here are all the commands you can use!",
            color=discord.Color.blue()
        )
        
        fun_commands = """
`!hello` - Basic greeting
`!wizard` - Magical greeting
`!rickroll` - Never gonna give you up...
`!doubt` - X to doubt
`!nani` - Omae wa mou shindeiru
`!cowbell` - More cowbell
`!peepee` - PP size check
`!fortnite` - Gaming preference
`!beans` - Bean adequacy check
`!lol` - lmao
`!triggered` - 🤣
`!yelling` - WHY ARE WE YELLING?
`!noot` - Pingu's greeting
`!sad` - 😭
`!coffee` - Coffee first
`!banana` - Peanut butter jelly time!
"""
        embed.add_field(name="Fun Commands", value=fun_commands, inline=False)
        
        plex_commands = """
`!play <query>` - Play media matching query
`!search <query>` - Search for media
"""
        embed.add_field(name="Plex Commands", value=plex_commands, inline=False)
        
        game_commands = """
`!hangman` - Play a game of hangman
`!battle <@user>` - Challenge someone to a battle
`!daily` - Claim daily rewards
`!inventory` - Check your inventory
"""
        embed.add_field(name="Game Commands", value=game_commands, inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author.name} | Bot Version 1.0")
        await ctx.send(embed=embed)

    async def cog_command_error(self, ctx, error):
        """Handle errors in utility commands"""
        logger.error(f"Error in utility command {ctx.command}: {error}", exc_info=error)
        await ctx.send("An error occurred while processing your command.")

async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))