"""Main Discord bot for Plex media playback."""

import asyncio
import logging
import discord
from discord.ext import commands
from .config import Config
from .bot_commands import PlexCommands

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlexBot(commands.Bot):
    """Discord bot for Plex media playback."""

    def __init__(self):
        """Initialize the Plex bot."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True

        super().__init__(
            command_prefix="!", intents=intents, application_id=Config.DISCORD_CLIENT_ID
        )

    async def setup_hook(self):
        """Set up the bot's extensions and sync commands."""
        # Load the Plex commands cog
        await self.add_cog(PlexCommands(self))

        # Sync application commands
        await self.tree.sync()

    async def on_ready(self):
        """Handle bot ready event."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("------")

    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Handle command errors.

        Args:
            ctx: The command context.
            error: The error that occurred.
        """
        if isinstance(error, commands.errors.CommandNotFound):
            return

        if isinstance(error, commands.errors.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
            return

        logger.error(f"Error in command {ctx.command}: {str(error)}")
        await ctx.send(f"An error occurred: {str(error)}")


async def run_bot():
    """Run the Discord bot."""
    # Validate configuration
    if error := Config.validate():
        logger.error(f"Configuration error: {error}")
        return

    # Create and run bot
    bot = PlexBot()

    try:
        async with bot:
            await bot.start(Config.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")


def main():
    """Main entry point."""
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
