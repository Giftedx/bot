"""Media integration cog for Plex and Discord integration."""
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import uuid
import aiohttp

import discord
from discord.ext import commands, tasks
from plexapi.server import PlexServer
from plexapi.video import Movie, Show, Episode
from plexapi.exceptions import NotFound, Unauthorized

from ..core.base_cog import BaseCog, check_permissions
from ..media.data.data_manager import MediaDataManager


class MediaCog(BaseCog):
    """Media commands for Plex integration."""

    def setup_cog(self) -> None:
        """Set up the media cog."""
        self.plex: Optional[PlexServer] = None
        self.data_manager = MediaDataManager(self.config)
        self._connect_to_plex()
        self.check_media_status.start()

    def _connect_to_plex(self) -> None:
        """Connect to Plex server."""
        try:
            baseurl = self.config.plex.url
            token = self.config.plex.token
            self.plex = PlexServer(baseurl, token)
        except Exception as e:
            self.logger.error(f"Failed to connect to Plex: {e}")
            self.plex = None

    @tasks.loop(minutes=1)
    async def check_media_status(self) -> None:
        """Check status of currently playing media."""
        if not self.plex:
            return

        try:
            sessions = self.plex.sessions()
            current_sessions = {s.sessionKey: s for s in sessions}

            # Check for ended sessions
            for session_key, session in self.data_manager.get_active_watch_parties():
                if session_key not in current_sessions:
                    # Add to watch history
                    self.data_manager.add_watch_history(
                        user_id=session["user_id"],
                        media_id=session["media_id"],
                        title=session["title"],
                        media_type=session["type"],
                        duration=session["duration"],
                        watched_duration=session["progress"],
                    )

                    # End watch party if exists
                    if "party_id" in session:
                        self.data_manager.end_watch_party(session["party_id"])

                    # Send notification
                    if session.get("channel_id"):
                        channel = self.bot.get_channel(session["channel_id"])
                        if channel:
                            await channel.send(
                                f"📺 {session['user']} finished watching: " f"{session['title']}"
                            )

            # Update current sessions
            for session in sessions:
                self.data_manager.update_session(
                    session_key=session.sessionKey,
                    user_id=session.usernames[0],
                    media_id=session.ratingKey,
                    title=session.title,
                    media_type="show" if hasattr(session, "grandparentTitle") else "movie",
                    progress=session.viewOffset,
                    duration=session.duration,
                )

        except Exception as e:
            self.logger.error(f"Error checking media status: {e}")

    @commands.hybrid_group(name="plex")
    async def plex_group(self, ctx: commands.Context) -> None:
        """Plex media commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @plex_group.command(name="stats")
    async def view_stats(
        self, ctx: commands.Context, user: Optional[discord.Member] = None
    ) -> None:
        """View media statistics for a user.

        Args:
            user: User to view stats for (default: command user)
        """
        user = user or ctx.author
        stats = self.data_manager.get_user_stats(str(user.id))

        embed = discord.Embed(
            title=f"📊 Media Stats for {user.display_name}", color=discord.Color.blue()
        )

        # Basic stats
        watch_time = timedelta(milliseconds=stats["watch_time"])
        embed.add_field(name="Total Watched", value=str(stats["total_watched"]))
        embed.add_field(name="Movies", value=str(stats["movies_watched"]))
        embed.add_field(name="TV Shows", value=str(stats["shows_watched"]))
        embed.add_field(
            name="Total Watch Time",
            value=f"{watch_time.days}d {watch_time.seconds//3600}h {(watch_time.seconds//60)%60}m",
        )

        # Last watched
        if stats["last_watched"]:
            last_watched = datetime.fromisoformat(stats["last_watched"])
            embed.add_field(name="Last Watched", value=discord.utils.format_dt(last_watched, "R"))

        await ctx.send(embed=embed)

    @plex_group.command(name="history")
    async def view_history(self, ctx: commands.Context, limit: int = 10) -> None:
        """View your watch history.

        Args:
            limit: Number of entries to show
        """
        history = self.data_manager.get_watch_history(str(ctx.author.id), limit=limit)

        if not history:
            await ctx.send("No watch history found.")
            return

        # Create embed list
        embed_list = []
        for entry in history:
            watched_time = datetime.fromisoformat(entry["timestamp"])
            duration = timedelta(milliseconds=entry["duration"])
            watched_duration = timedelta(milliseconds=entry["watched_duration"])

            embed_list.append(
                f"**{entry['title']}** ({entry['type']})\n"
                f"Watched: {discord.utils.format_dt(watched_time, 'R')}\n"
                f"Progress: {entry['completion_percentage']:.1f}% "
                f"({watched_duration} / {duration})"
            )

        # Send paginated results
        await self.send_paginated_embed(
            ctx, "📺 Watch History", embed_list, items_per_page=5, color=discord.Color.blue()
        )

    @plex_group.command(name="popular")
    async def view_popular(
        self, ctx: commands.Context, days: Optional[int] = 30, limit: int = 10
    ) -> None:
        """View popular media.

        Args:
            days: Time period in days (default: 30, 0 for all time)
            limit: Number of items to show
        """
        popular = self.data_manager.get_popular_media(
            time_period=days if days > 0 else None, limit=limit
        )

        if not popular:
            await ctx.send("No popular media found.")
            return

        # Create embed list
        embed_list = []
        for i, media in enumerate(popular, 1):
            watch_time = timedelta(milliseconds=media["total_duration"])
            embed_list.append(
                f"{i}. **{media['title']}** ({media['type']})\n"
                f"👥 {media['watch_count']} watches\n"
                f"⏱️ {watch_time.days}d {watch_time.seconds//3600}h total watch time"
            )

        # Send paginated results
        period = f"Past {days} days" if days > 0 else "All Time"
        await self.send_paginated_embed(
            ctx,
            f"🏆 Popular Media ({period})",
            embed_list,
            items_per_page=5,
            color=discord.Color.blue(),
        )

    @plex_group.command(name="recommend")
    async def recommend_media(
        self, ctx: commands.Context, user: discord.Member, *, title: str
    ) -> None:
        """Recommend media to another user.

        Args:
            user: User to recommend to
            title: Media to recommend
        """
        if not self.plex:
            await ctx.send("⚠️ Plex connection not available")
            return

        try:
            # Search for the media
            results = self.plex.library.search(title, limit=1)
            if not results:
                await ctx.send(f"No results found for: {title}")
                return

            media = results[0]

            # Add recommendation
            self.data_manager.add_recommendation(
                user_id=str(user.id),
                media_id=str(media.ratingKey),
                title=media.title,
                reason=f"Recommended by {ctx.author.display_name}",
                score=1.0,  # Direct user recommendations get highest score
            )

            # Create recommendation embed
            embed = discord.Embed(
                title="📝 Media Recommendation",
                description=f"{ctx.author.mention} recommended: **{media.title}**",
                color=discord.Color.green(),
            )

            if hasattr(media, "summary"):
                embed.add_field(name="Summary", value=media.summary[:1024], inline=False)

            if media.thumb:
                embed.set_thumbnail(url=self.plex.url(media.thumb))

            await ctx.send(content=user.mention, embed=embed)

        except Exception as e:
            await ctx.send(f"Error recommending media: {e}")

    @plex_group.command(name="recommendations")
    async def view_recommendations(self, ctx: commands.Context, status: str = "pending") -> None:
        """View your media recommendations.

        Args:
            status: Filter by status (pending/accepted/rejected)
        """
        recommendations = self.data_manager.get_recommendations(str(ctx.author.id), status=status)

        if not recommendations:
            await ctx.send(f"No {status} recommendations found.")
            return

        # Create embed list
        embed_list = []
        for rec in recommendations:
            timestamp = datetime.fromisoformat(rec["timestamp"])
            embed_list.append(
                f"**{rec['title']}**\n"
                f"Reason: {rec['reason']}\n"
                f"Added: {discord.utils.format_dt(timestamp, 'R')}"
            )

        # Send paginated results
        await self.send_paginated_embed(
            ctx,
            f"💡 {status.title()} Recommendations",
            embed_list,
            items_per_page=5,
            color=discord.Color.blue(),
        )

    @plex_group.command(name="watch")
    @commands.guild_only()
    async def watch_party(self, ctx: commands.Context, *, title: str) -> None:
        """Start a watch party for a movie or show.

        Args:
            title: Title to watch
        """
        if not self.plex:
            await ctx.send("⚠️ Plex connection not available")
            return

        try:
            # Search for the media
            results = self.plex.library.search(title)
            if not results:
                await ctx.send(f"No results found for: {title}")
                return

            # Create selection embed
            options = []
            for i, item in enumerate(results[:5], 1):
                media_type = "Movie" if isinstance(item, Movie) else "TV Show"
                options.append(f"{i}. **{item.title}** ({media_type}, {item.year})")

            embed = discord.Embed(
                title="🎬 Watch Party Selection",
                description="\n".join(options),
                color=discord.Color.blue(),
            )
            embed.set_footer(text="React with the number to select, or ❌ to cancel")

            # Send selection message
            message = await ctx.send(embed=embed)

            # Add selection reactions
            reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "❌"]
            for i in range(min(len(results), 5)):
                await message.add_reaction(reactions[i])
            await message.add_reaction("❌")

            def check(reaction: discord.Reaction, user: discord.User) -> bool:
                return (
                    user == ctx.author
                    and str(reaction.emoji) in reactions
                    and reaction.message.id == message.id
                )

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=30, check=check)

                if str(reaction.emoji) == "❌":
                    await message.delete()
                    return

                # Get selected item
                selection = reactions.index(str(reaction.emoji))
                selected_item = results[selection]

                # Create watch party
                party_id = str(uuid.uuid4())
                self.data_manager.create_watch_party(
                    party_id=party_id,
                    host_id=str(ctx.author.id),
                    media_id=str(selected_item.ratingKey),
                    title=selected_item.title,
                    channel_id=str(ctx.channel.id),
                )

                watch_party_embed = discord.Embed(
                    title="🎬 Watch Party Started!",
                    description=f"Watching: **{selected_item.title}**",
                    color=discord.Color.green(),
                )
                watch_party_embed.add_field(name="Host", value=ctx.author.mention)
                watch_party_embed.add_field(
                    name="Duration", value=str(timedelta(milliseconds=selected_item.duration))
                )

                if selected_item.thumb:
                    watch_party_embed.set_thumbnail(url=self.plex.url(selected_item.thumb))

                await ctx.send(
                    content="React with 👋 to join the watch party!", embed=watch_party_embed
                )

            except asyncio.TimeoutError:
                await message.clear_reactions()
                await ctx.send("Watch party selection timed out")

        except Exception as e:
            await ctx.send(f"Error starting watch party: {e}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User) -> None:
        """Handle reactions for watch party joins."""
        if user.bot:
            return

        message = reaction.message
        if str(reaction.emoji) == "👋":
            # Check if this is a watch party message
            active_parties = self.data_manager.get_active_watch_parties()
            for party in active_parties:
                if (
                    str(message.channel.id) == party["channel_id"]
                    and str(user.id) != party["host_id"]
                ):
                    if self.data_manager.join_watch_party(party["party_id"], str(user.id)):
                        await message.channel.send(f"{user.mention} joined the watch party!")


async def setup(bot: commands.Bot) -> None:
    """Add the cog to the bot."""
    await bot.add_cog(MediaCog(bot))
