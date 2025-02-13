import discord
from discord.ext import commands
import logging
import os

logger = logging.getLogger('DiscordService')

class DiscordService:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.token = os.environ.get('DISCORD_BOT_TOKEN')
        self.command_prefix = bot.command_prefix  # Get this dynamically