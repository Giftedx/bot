from typing import Optional

import discord
from discord.ext import commands


class BaseSelfBot(commands.Bot):
    """Base class for selfbot functionality"""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.voice_states = True

        super().__init__(command_prefix="!", self_bot=True, intents=intents)

    async def join_voice_channel(
        self, ctx: commands.Context
    ) -> Optional[discord.VoiceChannel]:
        """Join the user's voice channel"""
        if not isinstance(ctx.author, discord.Member):
            await ctx.send("This command can only be used in a server.")
            return None

        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("You need to be in a voice channel!")
            return None

        voice_channel = ctx.author.voice.channel

        if not ctx.voice_client:
            try:
                await voice_channel.connect()
            except Exception as e:
                await ctx.send(f"Error connecting to voice: {e}")
                return None

        return voice_channel

    async def enable_camera(self, ctx: commands.Context) -> bool:
        """Enable camera mode in voice channel"""
        if not ctx.voice_client or not ctx.voice_client.channel:
            return False

        try:
            await ctx.guild.change_voice_state(
                channel=ctx.voice_client.channel, self_video=True
            )
            return True
        except Exception as e:
            await ctx.send(f"Error enabling camera: {e}")
            return False

    async def disable_camera(self, ctx: commands.Context) -> bool:
        """Disable camera mode in voice channel"""
        if not ctx.voice_client or not ctx.voice_client.channel:
            return False

        try:
            await ctx.guild.change_voice_state(
                channel=ctx.voice_client.channel, self_video=False
            )
            return True
        except Exception as e:
            await ctx.send(f"Error disabling camera: {e}")
            return False
