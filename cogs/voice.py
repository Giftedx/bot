import discord
from discord.ext import commands
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class VoiceCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='join', help='Joins the user\'s voice channel')
    async def join(self, ctx: commands.Context) -> None:
        """Join the user's voice channel with error handling and logging"""
        if not ctx.author.voice:
            await ctx.send("You need to be in a voice channel first!")
            return

        try:
            channel = ctx.author.voice.channel
            if ctx.voice_client is not None:
                await ctx.voice_client.move_to(channel)
            else:
                await channel.connect()
            
            logger.info(f'Joined voice channel {channel.name} in guild {ctx.guild.name}')
            await ctx.send(f'Joined {channel.name}!')
        except Exception as e:
            logger.error(f'Failed to join voice channel: {str(e)}', exc_info=True)
            await ctx.send('Failed to join the voice channel. Please try again later.')

    @commands.command(name='leave', help='Leaves the voice channel')
    async def leave(self, ctx: commands.Context) -> None:
        """Leave the current voice channel with error handling and logging"""
        if ctx.voice_client is not None:
            try:
                channel_name = ctx.voice_client.channel.name
                await ctx.voice_client.disconnect()
                logger.info(f'Left voice channel {channel_name} in guild {ctx.guild.name}')
                await ctx.send('Left the voice channel!')
            except Exception as e:
                logger.error(f'Failed to leave voice channel: {str(e)}', exc_info=True)
                await ctx.send('Failed to leave the voice channel. Please try again later.')
        else:
            await ctx.send('I am not in a voice channel!')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        """Handle voice state updates with auto-disconnect when alone"""
        if member.id != self.bot.user.id:  # Don't handle bot's own state changes
            return

        if before.channel and not after.channel:  # Bot disconnected
            return

        if after.channel:
            voice_client = discord.utils.get(self.bot.voice_clients, guild=member.guild)
            if voice_client and len(voice_client.channel.members) == 1:
                try:
                    await voice_client.disconnect()
                    logger.info(f'Auto-disconnected from empty voice channel in guild {member.guild.name}')
                except Exception as e:
                    logger.error(f'Failed to auto-disconnect from voice channel: {str(e)}', exc_info=True)

async def setup(bot: commands.Bot) -> None:
    """Add the cog to the bot"""
    await bot.add_cog(VoiceCommands(bot)) 