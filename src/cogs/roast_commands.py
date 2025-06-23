from discord.ext import commands
import discord
from typing import Optional
import logging
from datetime import datetime, timedelta
import random
import asyncio

logger = logging.getLogger(__name__)


class RoastCommands(commands.Cog):
    """Roast system commands"""

    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        self.roast_tasks = {}

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        for task in self.roast_tasks.values():
            task.cancel()

    @commands.group(name="roast", invoke_without_command=True)
    async def roast(self, ctx, target: Optional[discord.Member] = None):
        """Generate a roast"""
        player_id = str(ctx.author.id)

        # Check cooldown
        if player_id in self.cooldowns:
            remaining = self.cooldowns[player_id] - datetime.now()
            if remaining.total_seconds() > 0:
                await ctx.send(
                    f"Please wait {int(remaining.total_seconds())} seconds "
                    "before roasting again!"
                )
                return

        # Get roastable messages
        messages = self.bot.db.get_roastable_messages(min_score=0.7, limit=10)
        if not messages:
            await ctx.send("No roastable messages found!")
            return

        # Filter by target if specified
        if target:
            messages = [m for m in messages if m["player_id"] == str(target.id)]
            if not messages:
                await ctx.send(f"No roastable messages found for {target.display_name}!")
                return

        # Select message and generate roast
        message = random.choice(messages)
        roast = self.bot.personal_system.joke_manager.generate_roast(message)

        # Record roast
        self.bot.db.add_roast(message["message_id"], roast["message"])

        # Set cooldown
        cooldown = self.bot.config.get_config("bot.roast_cooldown_minutes", 5)
        self.cooldowns[player_id] = datetime.now() + timedelta(minutes=cooldown)

        # Create embed
        user = self.bot.get_user(int(message["player_id"]))
        username = user.display_name if user else "someone"

        embed = discord.Embed(
            title="Roast Generated",
            description=f"Remember when {username} said...",
            color=discord.Color.orange(),
            timestamp=datetime.now(),
        )

        embed.add_field(name="Original Message", value=message["message"], inline=False)

        embed.add_field(name="Roast", value=roast["message"], inline=False)

        if "context" in roast:
            embed.add_field(name="Context", value=roast["context"], inline=False)

        await ctx.send(embed=embed)

    @roast.command(name="stats")
    async def roast_stats(self, ctx, target: Optional[discord.Member] = None):
        """Show roast statistics"""
        player_id = str(target.id if target else ctx.author.id)

        # Get roast history
        roasts = self.bot.db.get_player_roasts(player_id)
        if not roasts:
            await ctx.send(
                f"No roast history found for " f"{target.display_name if target else 'you'}!"
            )
            return

        # Create embed
        embed = discord.Embed(
            title="Roast Statistics", color=discord.Color.blue(), timestamp=datetime.now()
        )

        # Add basic stats
        embed.add_field(name="Total Roasts", value=len(roasts), inline=True)

        embed.add_field(
            name="Average Score",
            value=f"{sum(r['score'] for r in roasts) / len(roasts):.2f}",
            inline=True,
        )

        embed.add_field(name="Best Score", value=max(r["score"] for r in roasts), inline=True)

        # Add recent roasts
        recent = sorted(roasts, key=lambda r: r["created_at"])[-5:]
        recent_list = []
        for roast in recent:
            date = datetime.fromisoformat(roast["created_at"]).strftime("%Y-%m-%d")
            recent_list.append(f"• {date}: {roast['message'][:100]}...")

        embed.add_field(name="Recent Roasts", value="\n".join(recent_list) or "None", inline=False)

        await ctx.send(embed=embed)

    @roast.command(name="top")
    async def roast_top(self, ctx):
        """Show top roasts"""
        # Get top roasts
        roasts = self.bot.db.get_top_roasts(limit=5)
        if not roasts:
            await ctx.send("No roasts found!")
            return

        # Create embed
        embed = discord.Embed(
            title="Top Roasts", color=discord.Color.gold(), timestamp=datetime.now()
        )

        for i, roast in enumerate(roasts, 1):
            user = self.bot.get_user(int(roast["player_id"]))
            username = user.display_name if user else "someone"

            embed.add_field(
                name=f"#{i} (Score: {roast['score']:.2f})",
                value=(
                    f"**Original:** {roast['message']}\n"
                    f"**Roast:** {roast['roast_text']}\n"
                    f"**Target:** {username}"
                ),
                inline=False,
            )

        await ctx.send(embed=embed)

    @roast.command(name="search")
    async def roast_search(self, ctx, *, query: str):
        """Search roast history"""
        # Search roasts
        roasts = self.bot.db.search_roasts(query, limit=5)
        if not roasts:
            await ctx.send("No matching roasts found!")
            return

        # Create embed
        embed = discord.Embed(
            title=f"Roast Search: {query}", color=discord.Color.blue(), timestamp=datetime.now()
        )

        for roast in roasts:
            user = self.bot.get_user(int(roast["player_id"]))
            username = user.display_name if user else "someone"
            date = datetime.fromisoformat(roast["created_at"]).strftime("%Y-%m-%d")

            embed.add_field(
                name=f"Score: {roast['score']:.2f}",
                value=(
                    f"**Original:** {roast['message']}\n"
                    f"**Roast:** {roast['roast_text']}\n"
                    f"**Target:** {username}\n"
                    f"**Date:** {date}"
                ),
                inline=False,
            )

        await ctx.send(embed=embed)

    @roast.command(name="channel")
    @commands.has_permissions(manage_channels=True)
    async def roast_channel(self, ctx, enabled: bool = None):
        """Enable/disable roasts in this channel"""
        channel_id = str(ctx.channel.id)

        if enabled is None:
            # Show current status
            is_enabled = channel_id in self.bot.config.get_config("channels.roast_channel_ids", [])
            await ctx.send(
                f"Roasts are currently "
                f"{'enabled' if is_enabled else 'disabled'} "
                f"in this channel."
            )
            return

        # Update config
        roast_channels = set(self.bot.config.get_config("channels.roast_channel_ids", []))

        if enabled:
            roast_channels.add(channel_id)
        else:
            roast_channels.discard(channel_id)

        self.bot.config.update_config({"channels": {"roast_channel_ids": list(roast_channels)}})

        await ctx.send(f"Roasts {'enabled' if enabled else 'disabled'} " f"in this channel.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Message listener for auto-roasts"""
        # Ignore bot messages
        if message.author.bot:
            return

        # Check if channel allows roasts
        if str(message.channel.id) not in self.bot.config.get_config(
            "channels.roast_channel_ids", []
        ):
            return

        try:
            # Score message
            score = self.bot.personal_system.joke_manager.score_message(message.content)

            # Log message
            message_id = self.bot.db.log_chat_message(
                str(message.author.id), str(message.channel.id), message.content, score
            )

            # Check for auto-roast
            if score >= self.bot.config.get_config("bot.roast_min_score", 0.7):
                # Random chance to roast
                if random.random() < self.bot.config.get_config("bot.roast_chance", 0.3):
                    # Add delay for more natural feel
                    delay = random.randint(5, 15)
                    self.roast_tasks[message_id] = asyncio.create_task(
                        self.delayed_roast(message, message_id, delay)
                    )

        except Exception as e:
            logger.error(f"Error processing message for roasts: {e}")

    async def delayed_roast(self, message, message_id: int, delay: int):
        """Generate and send a delayed roast"""
        try:
            await asyncio.sleep(delay)

            # Generate roast
            roast = self.bot.personal_system.joke_manager.generate_roast(
                {
                    "message_id": message_id,
                    "message": message.content,
                    "player_id": str(message.author.id),
                }
            )

            # Record roast
            self.bot.db.add_roast(message_id, roast["message"])

            # Create embed
            embed = discord.Embed(
                description=roast["message"], color=discord.Color.orange(), timestamp=datetime.now()
            )

            await message.channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Error generating delayed roast: {e}")
        finally:
            # Clean up task
            if message_id in self.roast_tasks:
                del self.roast_tasks[message_id]


async def setup(bot):
    await bot.add_cog(RoastCommands(bot))
