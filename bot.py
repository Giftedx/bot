import asyncio
import logging
import os
import platform
from typing import Dict, List, Optional

import asyncpg
import discord
import yaml
from discord.ext import commands
from dotenv import load_dotenv

from cogs.database import osrs_db

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("discord.log")],
)
logger = logging.getLogger("DiscordBot")

# Load environment variables
load_dotenv()


class CustomBot(commands.Bot):
    def __init__(self):
        # Load config
        with open("config.yaml", "r") as f:
            self.config = yaml.safe_load(f)

        # Set up intents
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=self.config["discord"]["prefix"],
            intents=intents,
            case_insensitive=True,
        )

        # Initialize attributes
        self.db = osrs_db
        self.initial_extensions = [
            "cogs.admin",
            "cogs.games",
            "cogs.media",
            "cogs.plex",
            "cogs.fun",
            "cogs.osrs_commands",
            "cogs.battle_system",
            "cogs.game_commands",
            "cogs.fun_commands",
        ]

    async def setup_hook(self):
        """Setup hook that runs before the bot starts"""
        # Connect to database
        try:
            self.db = await asyncpg.create_pool(
                self.config["database"]["url"],
                min_size=5,
                max_size=self.config["database"].get("pool_size", 20),
            )
            logger.info("Connected to database successfully")
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            return

        # Load extensions
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")

    async def on_ready(self):
        """Event that fires when the bot is ready"""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Discord.py version: {discord.__version__}")
        logger.info(f"Python version: {platform.python_version()}")

        # Set activity
        activity = discord.Game(name=f"{self.config['discord']['prefix']}help")
        await self.change_presence(activity=activity)

    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            # Check for custom command
            command_name = ctx.message.content[len(self.command_prefix) :].split()[0]
            try:
                custom_command = await self.db.fetchrow(
                    "SELECT response FROM custom_commands WHERE name = $1",
                    command_name.lower(),
                )
                if custom_command:
                    return await ctx.send(custom_command["response"])
            except Exception as e:
                logger.error(f"Error checking custom command: {e}")

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command!")

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"This command is on cooldown. Try again in {error.retry_after:.2f}s"
            )

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")

        else:
            # Log unexpected errors
            logger.error(f"Unexpected error in command {ctx.command}: {error}")
            await ctx.send("An unexpected error occurred! The error has been logged.")

    async def on_message(self, message):
        """Event that fires when a message is received"""
        # Ignore messages from bots
        if message.author.bot:
            return

        # Process commands
        await self.process_commands(message)

    async def close(self):
        """Clean up when the bot is shutting down"""
        # Close database connection
        if self.db:
            await self.db.close()
            logger.info("Closed database connection")

        # Close any voice clients
        for voice_client in self.voice_clients:
            try:
                await voice_client.disconnect()
            except:
                pass

        await super().close()


async def main():
    """Main entry point for the bot"""
    # Create bot instance
    bot = CustomBot()

    # Start the bot
    try:
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise ValueError("DISCORD_TOKEN not found in environment")

        await bot.start(token)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    finally:
        await bot.close()


if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
