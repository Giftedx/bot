"""
Discord cog for Plex media playback commands.
Allows users to control Plex media playback in voice channels using Discord Activities.
"""
import discord
from discord.ext import commands
from .plex_activity import PlexActivity


class PlexCog(commands.Cog):
    """Commands for playing Plex media in voice channels using Discord Activities."""

    def __init__(self, bot: commands.Bot, plex_url: str, plex_token: str):
        self.bot = bot
        self.activity = PlexActivity(bot, plex_url, plex_token)

    @commands.group(name="plex", invoke_without_command=True)
    async def plex(self, ctx: commands.Context):
        """Plex media playback commands."""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Plex Watch Together",
                description="Watch Plex media together in voice channels:",
                color=discord.Color.blue(),
            )
            embed.add_field(
                name="!plex start", value="Start a Plex Watch Together activity", inline=False
            )
            embed.add_field(
                name="!plex play <media_id>",
                value="Play media in the current activity",
                inline=False,
            )
            embed.add_field(name="!plex stop", value="Stop the current activity", inline=False)
            embed.add_field(name="!plex pause", value="Pause the current media", inline=False)
            embed.add_field(name="!plex resume", value="Resume paused media", inline=False)
            embed.add_field(
                name="!plex seek <timestamp>",
                value="Seek to a specific time (HH:MM:SS or MM:SS)",
                inline=False,
            )
            await ctx.send(embed=embed)

    @plex.command(name="start")
    async def start(self, ctx: commands.Context):
        """Start a new Plex Watch Together activity."""
        async with ctx.typing():
            activity_config = await self.activity.initialize_activity(ctx)
            if activity_config:
                embed = discord.Embed(
                    title="Plex Watch Together Started",
                    description="Use `!plex play <media_id>` to start playing media",
                    color=discord.Color.green(),
                )
                embed.add_field(
                    name="Voice Channel", value=ctx.author.voice.channel.name, inline=False
                )
                await ctx.send(embed=embed)

    @plex.command(name="play")
    async def play(self, ctx: commands.Context, media_id: str):
        """Play media in the current Plex activity."""
        async with ctx.typing():
            success = await self.activity.start_media(ctx, media_id)
            if success:
                # Activity presence will be updated automatically
                await ctx.message.add_reaction("▶️")

    @plex.command(name="stop")
    async def stop(self, ctx: commands.Context):
        """Stop the current Plex activity."""
        if not ctx.author.voice:
            await ctx.send("You need to be in a voice channel!")
            return

        channel_id = ctx.author.voice.channel.id
        await self.activity.cleanup_activity(channel_id)
        await ctx.message.add_reaction("⏹️")

    @plex.command(name="pause")
    async def pause(self, ctx: commands.Context):
        """Pause the current media."""
        if not ctx.author.voice:
            await ctx.send("You need to be in a voice channel!")
            return

        channel_id = ctx.author.voice.channel.id
        if channel_id not in self.activity.active_activities:
            await ctx.send("No active Plex activity in this channel!")
            return

        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            activity = self.activity.active_activities[channel_id]
            activity["state"] = "PAUSED"
            await self.activity._update_activity_presence(channel_id)
            await ctx.message.add_reaction("⏸️")

    @plex.command(name="resume")
    async def resume(self, ctx: commands.Context):
        """Resume paused media."""
        if not ctx.author.voice:
            await ctx.send("You need to be in a voice channel!")
            return

        channel_id = ctx.author.voice.channel.id
        if channel_id not in self.activity.active_activities:
            await ctx.send("No active Plex activity in this channel!")
            return

        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            activity = self.activity.active_activities[channel_id]
            activity["state"] = "PLAYING"
            await self.activity._update_activity_presence(channel_id)
            await ctx.message.add_reaction("▶️")

    @plex.command(name="seek")
    async def seek(self, ctx: commands.Context, timestamp: str):
        """
        Seek to a specific time in the media.

        Args:
            timestamp: Time in format HH:MM:SS or MM:SS
        """
        if not ctx.author.voice:
            await ctx.send("You need to be in a voice channel!")
            return

        channel_id = ctx.author.voice.channel.id
        if channel_id not in self.activity.active_activities:
            await ctx.send("No active Plex activity in this channel!")
            return

        activity = self.activity.active_activities[channel_id]
        if not activity["current_media"]:
            await ctx.send("No media currently playing!")
            return

        try:
            # Get current media and create new stream URL with offset
            media = activity["current_media"]
            stream_url = media.getStreamURL(
                offset=self._parse_timestamp(timestamp) * 1000,  # Convert to milliseconds
                videoQuality="1080p",
                audioQuality="high",
                maxAudioChannels=2,
            )

            # Stop current playback
            if ctx.voice_client:
                ctx.voice_client.stop()

            # Start new playback from offset
            ffmpeg_options = {
                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                "options": "-vn -b:a 192k",
            }
            audio_source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_options)
            ctx.voice_client.play(audio_source)

            await ctx.message.add_reaction("⏩")

        except ValueError:
            await ctx.send("Invalid timestamp format! Use HH:MM:SS or MM:SS")
        except Exception as e:
            await ctx.send(f"Error seeking: {str(e)}")

    def _parse_timestamp(self, timestamp: str) -> int:
        """Parse a timestamp string into seconds."""
        parts = timestamp.split(":")
        if len(parts) == 2:  # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        else:
            raise ValueError("Invalid timestamp format")

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ):
        """Handle voice channel state changes."""
        # Handle users joining activity
        if after and after.channel and after.channel.id in self.activity.active_activities:
            await self.activity.handle_activity_join(member, after.channel.id)

        # Handle users leaving activity
        if before and before.channel and before.channel.id in self.activity.active_activities:
            if not after or after.channel != before.channel:
                await self.activity.handle_activity_leave(member, before.channel.id)


def setup(bot: commands.Bot):
    """Set up the Plex cog."""
    if not hasattr(bot, "config"):
        raise AttributeError("Bot instance must have a 'config' attribute with Plex settings")

    plex_url = bot.config.get("plex_url", "http://localhost:32400")
    plex_token = bot.config.get("plex_token")

    if not plex_token:
        raise ValueError("Plex token not found in bot config")

    bot.add_cog(PlexCog(bot, plex_url, plex_token))
