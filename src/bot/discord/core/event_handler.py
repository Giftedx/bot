import logging
import discord
from discord.ext import commands

logger = logging.getLogger('DiscordBot')


def setup_event_handlers(bot: commands.Bot):
    """Sets up event handlers for the bot."""

    @bot.event
    async def on_ready():
        logger.info(f'Logged in as {bot.user.name} ({bot.user.id})')
        await bot.change_presence(activity=discord.Game(name="Plex with friends"))

    @bot.event
    async def on_command_error(ctx: commands.Context, error: Exception):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found! Use !help to see available commands.")
            return
        logger.error(f"Command error in {ctx.command}: {error}", exc_info=error)
        await ctx.send("An error occurred while processing your command.")

    @bot.event
    async def on_message(message: discord.Message):        
        if message.author == bot.user:  
            return
        await bot.process_commands(message)