"""
Component handlers for Discord application interactions.
"""

import logging
from typing import Optional
import discord
from discord.ui import View, Button

logger = logging.getLogger(__name__)


class MediaControlView(View):
    """Media control buttons view for Plex playback."""

    def __init__(self, player, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.player = player

        # Add control buttons with proper styling and accessibility
        self.add_item(
            Button(
                label="Play/Pause",
                emoji="⏯️",
                custom_id="toggle_play",
                style=discord.ButtonStyle.primary,
            )
        )
        self.add_item(
            Button(label="Stop", emoji="⏹️", custom_id="stop", style=discord.ButtonStyle.danger)
        )
        self.add_item(
            Button(
                label="Rewind 10s",
                emoji="⏪",
                custom_id="rewind",
                style=discord.ButtonStyle.secondary,
            )
        )
        self.add_item(
            Button(
                label="Forward 10s",
                emoji="⏩",
                custom_id="forward",
                style=discord.ButtonStyle.secondary,
            )
        )

    async def handle_interaction(self, interaction: discord.Interaction) -> bool:
        """Handle button interaction events."""
        if not interaction.data:
            return False

        custom_id = interaction.data.get("custom_id", "")
        guild_id = str(interaction.guild_id) if interaction.guild_id else None

        try:
            if custom_id == "toggle_play":
                state = self.player.get_current_state(guild_id)
                if state and state.is_playing:
                    await self.player.pause_playback(interaction)
                    await interaction.response.send_message("Media paused", ephemeral=True)
                else:
                    await self.player.resume_playback(interaction)
                    await interaction.response.send_message("Media resumed", ephemeral=True)

            elif custom_id == "stop":
                await self.player.stop_playback(interaction)
                await interaction.response.send_message("Media stopped", ephemeral=True)
                self.stop()

            elif custom_id == "rewind":
                state = self.player.get_current_state(guild_id)
                if state:
                    new_pos = max(0, state.position - 10)
                    await self.player.seek(interaction, new_pos)
                    await interaction.response.send_message(
                        f"Rewound to {new_pos//60}:{new_pos%60:02d}", ephemeral=True
                    )

            elif custom_id == "forward":
                state = self.player.get_current_state(guild_id)
                if state:
                    new_pos = min(state.duration, state.position + 10)
                    await self.player.seek(interaction, new_pos)
                    await interaction.response.send_message(
                        f"Forwarded to {new_pos//60}:{new_pos%60:02d}", ephemeral=True
                    )

            return True

        except Exception as e:
            logger.error(f"Error handling media control interaction: {e}")
            await interaction.response.send_message(
                "Error processing media control", ephemeral=True
            )
            return False

    async def on_timeout(self):
        """Handle view timeout by disabling all buttons."""
        for item in self.children:
            if isinstance(item, Button):
                item.disabled = True
