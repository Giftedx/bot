"""Main bot module."""

import discord
from discord.ext import commands
import os
import logging
import asyncio
import aiohttp
from typing import Optional, Mapping, List
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bot')

class CustomHelpCommand(commands.HelpCommand):
    """Custom help command implementation."""
    
    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]]):
        """Send the bot help page."""
        embed = discord.Embed(
            title="Bot Commands",
            description="Here are all available commands organized by category.\nUse `!help <category>` for more details.",
            color=discord.Color.blue()
        )
        
        # Sort cogs by name
        sorted_mapping = sorted(mapping.items(), key=lambda x: x[0].qualified_name if x[0] else "No Category")
        
        for cog, commands_list in sorted_mapping:
            if not commands_list:
                continue
                
            name = cog.qualified_name if cog else "No Category"
            # Filter out hidden commands
            visible_commands = [cmd for cmd in commands_list if not cmd.hidden]
            if visible_commands:
                value = ", ".join(f"`{cmd.name}`" for cmd in visible_commands)
                embed.add_field(name=name, value=value, inline=False)
        
        await self.get_destination().send(embed=embed)
    
    async def send_cog_help(self, cog: commands.Cog):
        """Send help for a specific category."""
        embed = discord.Embed(
            title=f"{cog.qualified_name} Commands",
            description=cog.description or "No description available.",
            color=discord.Color.blue()
        )
        
        # Add command list
        for command in cog.get_commands():
            if not command.hidden:
                embed.add_field(
                    name=f"{command.name} {command.signature}",
                    value=command.help or "No description available.",
                    inline=False
                )
        
        await self.get_destination().send(embed=embed)
    
    async def send_command_help(self, command: commands.Command):
        """Send help for a specific command."""
        embed = discord.Embed(
            title=f"Command: {command.name}",
            color=discord.Color.blue()
        )
        
        # Add command details
        embed.add_field(
            name="Usage",
            value=f"`{self.context.prefix}{command.name} {command.signature}`",
            inline=False
        )
        
        if command.help:
            embed.add_field(name="Description", value=command.help, inline=False)
            
        if command.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{alias}`" for alias in command.aliases),
                inline=False
            )
        
        await self.get_destination().send(embed=embed)

class Config:
    """Bot configuration."""
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')
    PLEX_URL = os.getenv('PLEX_URL')
    PLEX_TOKEN = os.getenv('PLEX_TOKEN')
    LAVALINK_HOST = os.getenv('LAVALINK_HOST', 'localhost')
    LAVALINK_PORT = int(os.getenv('LAVALINK_PORT', '2333'))
    LAVALINK_PASSWORD = os.getenv('LAVALINK_PASSWORD', 'youshallnotpass')

class Bot(commands.Bot):
    """Custom bot class with enhanced functionality."""
    
    def __init__(self):
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        # Initialize the bot with custom help command
        super().__init__(
            command_prefix=Config.COMMAND_PREFIX,
            intents=intents,
            case_insensitive=True,
            help_command=CustomHelpCommand()
        )
        
        # Store configuration
        self.config = Config
        self.start_time = None
        
        # Create aiohttp session
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def setup_hook(self):
        """Initialize bot and load extensions."""
        # Create aiohttp session
        self.session = aiohttp.ClientSession()
        
        # Load all cogs
        await self.load_cogs()
    
    async def load_cogs(self):
        """Load all cogs from the cogs directory."""
        cogs = [
            'discord_bot.cogs.general_commands',
            'discord_bot.cogs.admin_commands',
            'discord_bot.cogs.pokemon_commands',
            'discord_bot.cogs.game_commands',
            'discord_bot.cogs.music_commands',
            'discord_bot.cogs.moderation_commands',
            'discord_bot.cogs.custom_commands',
            'discord_bot.cogs.media_commands',
            'discord_bot.cogs.osrs_commands',
            'discord_bot.cogs.fun_commands'
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f'Loaded extension: {cog}')
            except Exception as e:
                logger.error(f'Failed to load extension {cog}: {e}')
    
    async def on_ready(self):
        """Event triggered when the bot is ready."""
        self.start_time = datetime.datetime.utcnow()
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('------')
        
        # Set custom status
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{self.config.COMMAND_PREFIX}help"
        )
        await self.change_presence(activity=activity)
    
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Global error handler for command errors."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
            
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
            return
            
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send("This command cannot be used in private messages.")
            return
            
        if isinstance(error, commands.DisabledCommand):
            await ctx.send("This command is currently disabled.")
            return
            
        # Log the error
        logger.error(f'Error in command {ctx.command}: {error}', exc_info=error)
        
        # Send error message to user
        error_msg = f"An error occurred while processing the command:\n```{str(error)}```"
        if ctx.guild is None:  # In DMs, always show error
            await ctx.send(error_msg)
        elif ctx.author.guild_permissions.administrator:  # In guild, only show to admins
            await ctx.send(error_msg)
        else:
            await ctx.send("An error occurred while processing the command.")
    
    async def close(self):
        """Clean up resources when shutting down."""
        if self.session:
            await self.session.close()
        await super().close()

def main():
    """Main entry point for the bot."""
    # Create and run bot
    bot = Bot()
    
    try:
        bot.run(Config.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f'Error running bot: {e}')
        raise

if __name__ == '__main__':
    main() 