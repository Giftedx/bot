from discord.ext import commands
import discord
from typing import Optional
import logging
from datetime import datetime, timedelta
import random
import asyncio

logger = logging.getLogger(__name__)


class WatchCommands(commands.Cog):
    """Watch party commands"""

    def __init__(self, bot):
        self.bot = bot
        self.active_parties = {}
        self.party_tasks = {}

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        for task in self.party_tasks.values():
            task.cancel()

    @commands.group(name="watch", invoke_without_command=True)
    async def watch(self, ctx):
        """Watch party commands"""
        await ctx.send_help(ctx.command)

    @watch.command(name="start")
    async def watch_start(self, ctx, *, content: str):
        """Start a watch party"""
        player_id = str(ctx.author.id)

        # Generate unique party ID
        while True:
            party_id = str(random.randint(1000, 9999))
            if party_id not in self.active_parties:
                break

        # Create party
        self.active_parties[party_id] = {
            "host": player_id,
            "content": content,
            "members": [player_id],
            "started_at": datetime.now().isoformat(),
            "status": "waiting",
            "channel": ctx.channel.id,
            "voice_channel": None,
            "position": 0,
            "paused": False,
        }

        # Create embed
        embed = discord.Embed(
            title="Watch Party Created!",
            description=f"Content: {content}",
            color=discord.Color.blue(),
            timestamp=datetime.now(),
        )

        embed.add_field(name="Party ID", value=party_id, inline=True)

        embed.add_field(name="Host", value=ctx.author.display_name, inline=True)

        embed.add_field(name="Status", value="Waiting for members", inline=True)

        embed.add_field(name="Join Command", value=f"`!watch join {party_id}`", inline=False)

        await ctx.send(embed=embed)

        # Start cleanup task
        self.party_tasks[party_id] = asyncio.create_task(self.cleanup_party(party_id))

    @watch.command(name="join")
    async def watch_join(self, ctx, party_id: str):
        """Join a watch party"""
        player_id = str(ctx.author.id)

        # Check if party exists
        party = self.active_parties.get(party_id)
        if not party:
            await ctx.send("Watch party not found!")
            return

        # Check if already in party
        if player_id in party["members"]:
            await ctx.send("You're already in this watch party!")
            return

        # Check if party has started
        if party["status"] == "watching":
            await ctx.send("This watch party has already started!")
            return

        # Add to party
        party["members"].append(player_id)

        # Create embed
        embed = discord.Embed(
            title="Joined Watch Party",
            description=f"Content: {party['content']}",
            color=discord.Color.green(),
            timestamp=datetime.now(),
        )

        embed.add_field(
            name="Host", value=self.bot.get_user(int(party["host"])).display_name, inline=True
        )

        embed.add_field(name="Members", value=len(party["members"]), inline=True)

        await ctx.send(embed=embed)

    @watch.command(name="start_watching")
    async def watch_start_watching(self, ctx, party_id: str):
        """Start watching in a party"""
        player_id = str(ctx.author.id)

        # Check if party exists
        party = self.active_parties.get(party_id)
        if not party:
            await ctx.send("Watch party not found!")
            return

        # Check if host
        if player_id != party["host"]:
            await ctx.send("Only the host can start watching!")
            return

        # Check if already watching
        if party["status"] == "watching":
            await ctx.send("Already watching!")
            return

        # Check if in voice channel
        if not ctx.author.voice:
            await ctx.send("You need to be in a voice channel to start watching!")
            return

        # Update party status
        party["status"] = "watching"
        party["voice_channel"] = ctx.author.voice.channel.id
        started_at = datetime.now()

        # Record watch for all members
        for member_id in party["members"]:
            self.bot.db.add_watch_record(
                member_id,
                {
                    "id": party_id,
                    "type": "group_watch",
                    "title": party["content"],
                    "started_at": started_at.isoformat(),
                },
            )

        # Create embed
        embed = discord.Embed(
            title="Watch Party Started!",
            description=f"Content: {party['content']}",
            color=discord.Color.green(),
            timestamp=started_at,
        )

        embed.add_field(name="Voice Channel", value=ctx.author.voice.channel.name, inline=True)

        embed.add_field(name="Members", value=len(party["members"]), inline=True)

        # Add controls help
        embed.add_field(
            name="Controls",
            value=(
                "`!watch pause` - Pause playback\n"
                "`!watch resume` - Resume playback\n"
                "`!watch seek <time>` - Seek to time (e.g. 1:30:00)\n"
                "`!watch status` - Show current status"
            ),
            inline=False,
        )

        await ctx.send(embed=embed)

    @watch.command(name="pause")
    async def watch_pause(self, ctx):
        """Pause the current watch party"""
        player_id = str(ctx.author.id)

        # Find party where user is member
        party = next((p for p in self.active_parties.values() if player_id in p["members"]), None)

        if not party:
            await ctx.send("You're not in a watch party!")
            return

        if party["status"] != "watching":
            await ctx.send("The watch party hasn't started yet!")
            return

        if party["paused"]:
            await ctx.send("Already paused!")
            return

        # Update party status
        party["paused"] = True

        await ctx.send("⏸️ Playback paused")

    @watch.command(name="resume")
    async def watch_resume(self, ctx):
        """Resume the current watch party"""
        player_id = str(ctx.author.id)

        # Find party where user is member
        party = next((p for p in self.active_parties.values() if player_id in p["members"]), None)

        if not party:
            await ctx.send("You're not in a watch party!")
            return

        if party["status"] != "watching":
            await ctx.send("The watch party hasn't started yet!")
            return

        if not party["paused"]:
            await ctx.send("Already playing!")
            return

        # Update party status
        party["paused"] = False

        await ctx.send("▶️ Playback resumed")

    @watch.command(name="seek")
    async def watch_seek(self, ctx, timestamp: str):
        """Seek to a specific time"""
        player_id = str(ctx.author.id)

        # Find party where user is member
        party = next((p for p in self.active_parties.values() if player_id in p["members"]), None)

        if not party:
            await ctx.send("You're not in a watch party!")
            return

        if party["status"] != "watching":
            await ctx.send("The watch party hasn't started yet!")
            return

        # Parse timestamp (format: HH:MM:SS or MM:SS)
        try:
            parts = timestamp.split(":")
            if len(parts) == 2:
                minutes, seconds = map(int, parts)
                position = minutes * 60 + seconds
            elif len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
                position = hours * 3600 + minutes * 60 + seconds
            else:
                raise ValueError
        except ValueError:
            await ctx.send("Invalid timestamp format! Use HH:MM:SS or MM:SS")
            return

        # Update party position
        party["position"] = position

        await ctx.send(f"⏩ Seeking to {timestamp}")

    @watch.command(name="status")
    async def watch_status(self, ctx):
        """Show current watch party status"""
        player_id = str(ctx.author.id)

        # Find party where user is member
        party = next((p for p in self.active_parties.values() if player_id in p["members"]), None)

        if not party:
            await ctx.send("You're not in a watch party!")
            return

        # Create embed
        embed = discord.Embed(
            title="Watch Party Status",
            description=f"Content: {party['content']}",
            color=discord.Color.blue(),
            timestamp=datetime.now(),
        )

        # Add basic info
        embed.add_field(name="Status", value=party["status"].title(), inline=True)

        embed.add_field(
            name="Host", value=self.bot.get_user(int(party["host"])).display_name, inline=True
        )

        embed.add_field(name="Members", value=len(party["members"]), inline=True)

        # Add playback info if watching
        if party["status"] == "watching":
            # Format position
            hours = party["position"] // 3600
            minutes = (party["position"] % 3600) // 60
            seconds = party["position"] % 60
            position = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            embed.add_field(name="Position", value=position, inline=True)

            embed.add_field(
                name="State", value="Paused" if party["paused"] else "Playing", inline=True
            )

            # Add voice channel if set
            if party["voice_channel"]:
                channel = self.bot.get_channel(party["voice_channel"])
                if channel:
                    embed.add_field(name="Voice Channel", value=channel.name, inline=True)

        await ctx.send(embed=embed)

    @watch.command(name="leave")
    async def watch_leave(self, ctx):
        """Leave the current watch party"""
        player_id = str(ctx.author.id)

        # Find party where user is member
        party = next((p for p in self.active_parties.values() if player_id in p["members"]), None)

        if not party:
            await ctx.send("You're not in a watch party!")
            return

        # Remove from party
        party["members"].remove(player_id)

        # If host leaves, end party
        if player_id == party["host"]:
            # Find party ID
            party_id = next(pid for pid, p in self.active_parties.items() if p == party)
            await self.end_party(party_id, "Host left")
            return

        await ctx.send("Left the watch party!")

    async def cleanup_party(self, party_id: str):
        """Clean up a party after timeout"""
        try:
            # Wait for auto-end timeout
            timeout = self.bot.config.get_config(
                "watch_parties.auto_end_minutes", 360  # 6 hours default
            )
            await asyncio.sleep(timeout * 60)

            # End party if still active
            if party_id in self.active_parties:
                await self.end_party(party_id, "Party timed out")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in party cleanup: {e}")

    async def end_party(self, party_id: str, reason: str):
        """End a watch party"""
        try:
            party = self.active_parties[party_id]

            # Send end message
            channel = self.bot.get_channel(party["channel"])
            if channel:
                embed = discord.Embed(
                    title="Watch Party Ended",
                    description=reason,
                    color=discord.Color.red(),
                    timestamp=datetime.now(),
                )

                await channel.send(embed=embed)

            # Clean up
            del self.active_parties[party_id]
            if party_id in self.party_tasks:
                self.party_tasks[party_id].cancel()
                del self.party_tasks[party_id]

        except Exception as e:
            logger.error(f"Error ending party: {e}")


async def setup(bot):
    await bot.add_cog(WatchCommands(bot))
