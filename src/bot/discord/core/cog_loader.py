import logging
from discord.ext import commands

logger = logging.getLogger('DiscordBot')

async def load_cogs(bot: commands.Bot, cog_names: list[str]):
    """Loads cogs for the bot."""
    for cog_name in cog_names:
        try:
            await bot.load_extension(cog_name)
            logger.info(f"Loaded cog: {cog_name}")
        except Exception as e:
            logger.error(f"Failed to load cog {cog_name}: {e}")