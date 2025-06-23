"""Voice connection handler for Discord."""
import logging
import asyncio
from typing import Optional
import discord
from discord.ext import commands, tasks

logger = logging.getLogger(__name__)


class VoiceHandler(commands.Cog):
    """Handler for voice connections."""

    def __init__(self, bot):
        """Initialize voice handler."""
        self.bot = bot
        self.check_voice_activity.start()
        self.inactive_timeouts = {}

    def cog_unload(self):
        """Clean up when cog is unloaded."""
        self.check_voice_activity.cancel()

    @tasks.loop(seconds=30)
    async def check_voice_activity(self):
        """Check for inactive voice connections."""
        for guild in self.bot.guilds:
            if not guild.voice_client:
                continue

            if len(guild.voice_client.channel.members) <= 1:
                # Only bot is in channel
                if guild.id not in self.inactive_timeouts:
                    self.inactive_timeouts[guild.id] = discord.utils.utcnow()
                elif (discord.utils.utcnow() - self.inactive_timeouts[guild.id]).seconds > 300:
                    # Inactive for more than 5 minutes
                    await guild.voice_client.disconnect()
                    del self.inactive_timeouts[guild.id]
            else:
                # Remove timeout if channel is active
                self.inactive_timeouts.pop(guild.id, None)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ):
        """Handle voice state updates."""
        if member.bot:
            return

        if before.channel and not after.channel:
            # Member left voice channel
            if len(before.channel.members) <= 1 and before.channel.guild.voice_client:
                # Only bot remains in channel
                self.inactive_timeouts[before.channel.guild.id] = discord.utils.utcnow()

        elif after.channel and not before.channel:
            # Member joined voice channel
            if after.channel.guild.id in self.inactive_timeouts:
                # Remove timeout if channel becomes active
                del self.inactive_timeouts[after.channel.guild.id]

    @commands.Cog.listener()
    async def on_voice_server_update(self, data: dict):
        """Handle voice server updates."""
        logger.debug(f"Voice server update: {data}")

    async def cleanup_voice_client(self, guild_id: int):
        """Clean up voice client resources."""
        if voice_client := self.bot.voice_clients.get(guild_id):
            try:
                if voice_client.is_playing():
                    voice_client.stop()
                await voice_client.disconnect()
            except Exception as e:
                logger.error(f"Error cleaning up voice client: {e}")
            finally:
                self.bot.voice_clients.pop(guild_id, None)


async def setup(bot):
    """Set up the voice handler cog."""
    await bot.add_cog(VoiceHandler(bot))
