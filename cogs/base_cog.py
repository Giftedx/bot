from discord.ext import commands
import logging

logger = logging.getLogger('DiscordBot')

class BaseCog(commands.Cog):
    """Base cog with common functionality"""
    
    def __init__(self, bot):
        self.bot = bot

    async def cog_command_error(self, ctx, error):
        """Handle errors in cog commands"""
        logger.error(f"Error in {ctx.command}: {str(error)}", exc_info=error)
        await ctx.send("An error occurred while processing your command.")