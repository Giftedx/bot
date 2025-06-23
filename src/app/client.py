"""
Discord application client implementation.
"""

import logging
import asyncio
from typing import Dict, Optional, Any
import discord
from discord import app_commands

logger = logging.getLogger(__name__)


class DiscordAppClient:
    """Discord application client that handles all app interactions."""

    def __init__(self, app_id: str, public_key: str):
        self.app_id = app_id
        self.public_key = public_key
        self.client = discord.Client(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self.client)
        self.interaction_handlers: Dict[str, Any] = {}

    async def setup(self):
        """Set up the application client and register commands."""

        @self.client.event
        async def on_ready():
            logger.info(f"Logged in as application {self.client.user}")
            # Sync commands with Discord
            await self.tree.sync()

        @self.client.event
        async def on_interaction(interaction: discord.Interaction):
            if not interaction.type:
                return

            try:
                # Route interaction to appropriate handler
                handler = self.interaction_handlers.get(str(interaction.type))
                if handler:
                    await handler(interaction)
                else:
                    logger.warning(f"No handler for interaction type {interaction.type}")

            except Exception as e:
                logger.error(f"Error handling interaction: {e}")
                await self.send_error_response(interaction)

    def add_interaction_handler(self, interaction_type: str, handler: Any):
        """Register a new interaction handler."""
        self.interaction_handlers[interaction_type] = handler

    async def send_error_response(self, interaction: discord.Interaction):
        """Send an error response to an interaction."""
        try:
            if interaction.response.is_done():
                await interaction.followup.send(
                    "An error occurred processing your request.", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "An error occurred processing your request.", ephemeral=True
                )
        except Exception as e:
            logger.error(f"Error sending error response: {e}")

    async def start(self, token: str):
        """Start the Discord application client."""
        await self.setup()
        await self.client.start(token)

    async def close(self):
        """Close the Discord application client."""
        await self.client.close()
