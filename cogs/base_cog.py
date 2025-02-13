from discord.ext import commands
import logging

logger = logging.getLogger('BaseCog')

class BaseCog(commands.Cog):
    """Base cog class with common functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def cog_load(self):
        """Called when cog is loaded"""
        self.logger.info(f"{self.__class__.__name__} loaded")
    
    async def cog_unload(self):
        """Called when cog is unloaded"""
        self.logger.info(f"{self.__class__.__name__} unloaded")
        
    async def cog_error(self, ctx, error):
        """Global error handler for the cog"""
        self.logger.error(f"Error in {ctx.command}: {str(error)}")
        await ctx.send(f"An error occurred: {str(error)}")