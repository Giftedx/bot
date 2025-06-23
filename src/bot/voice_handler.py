import logging
from typing import Optional

import discord

logger = logging.getLogger(__name__)


class VoiceHandler:
    """Handle voice channel and camera state"""

    @staticmethod
    async def join_voice(
        ctx: discord.ext.commands.Context,
    ) -> Optional[discord.VoiceChannel]:
        """Join a voice channel"""
        if not isinstance(ctx.author, discord.Member):
            await ctx.send("This command can only be used in a server.")
            return None

        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("You need to be in a voice channel!")
            return None

        voice_channel = ctx.author.voice.channel
        if not isinstance(voice_channel, discord.VoiceChannel):
            await ctx.send("You need to be in a voice channel!")
            return None

        if not ctx.voice_client:
            try:
                await voice_channel.connect()
            except Exception as e:
                logger.error(f"Failed to connect to voice channel: {e}")
                await ctx.send(f"Error connecting to voice: {e}")
                return None

        return voice_channel

    @staticmethod
    async def set_video(ctx: discord.ext.commands.Context, enabled: bool) -> bool:
        """Enable or disable video in voice channel"""
        if not isinstance(ctx.guild, discord.Guild) or not ctx.voice_client:
            return False

        try:
            if not ctx.voice_client.channel:
                return False

            await ctx.guild.change_voice_state(channel=ctx.voice_client.channel, self_video=enabled)
            return True
        except Exception as e:
            logger.error(f"Failed to {'enable' if enabled else 'disable'} video: {e}")
            return False
