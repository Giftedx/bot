import discord
from discord.ext import commands
import logging
from datetime import datetime
import os
from .cog_loader import load_cogs
from .event_handler import setup_event_handlers


class Bot(commands.Bot):
    def __init__(self, config):
        self.config = config

        self.logger = logging.getLogger('DiscordBot')
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True

        super().__init__(
            command_prefix=config.COMMAND_PREFIX,
            intents=intents,
            description="Discord bot for media management."

        )

        self.start_time = datetime.now()
        self.command_usage = {}
        setup_event_handlers(self)

    async def setup_hook(self):
        """Load extensions on bot startup"""
        await load_cogs(self, [
           'src.bot.cogs.fun_commands',
            'src.bot.cogs.plex_cog',
            'src.bot.cogs.game_commands'
        ])