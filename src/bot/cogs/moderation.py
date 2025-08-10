import discord
from discord.ext import commands
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio


class InfractionManager:
    def __init__(self):
        self.warnings: Dict[int, Dict[int, List[Dict]]] = defaultdict(lambda: defaultdict(list))
        self.mutes: Dict[int, Dict[int, datetime]] = defaultdict(dict)
        self.temp_bans: Dict[int, Dict[int, datetime]] = defaultdict(dict)

    def add_warning(self, guild_id: int, user_id: int, reason: str, mod_id: int) -> Dict:
        warning = {
            "reason": reason,
            "mod_id": mod_id,
            "timestamp": datetime.now().isoformat(),
            "id": len(self.warnings[guild_id][user_id]) + 1,
        }
        self.warnings[guild_id][user_id].append(warning)
        return warning

    def get_warnings(self, guild_id: int, user_id: int) -> List[Dict]:
        return self.warnings[guild_id][user_id]

    def remove_warning(self, guild_id: int, user_id: int, warning_id: int) -> bool:
        warnings = self.warnings[guild_id][user_id]
        for i, warning in enumerate(warnings):
            if warning["id"] == warning_id:
                warnings.pop(i)
                return True
        return False


class Moderation(commands.Cog):
    """Advanced moderation commands and infraction tracking"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.infraction_manager = InfractionManager()
        self.raid_protection = defaultdict(
            lambda: {"enabled": False, "join_threshold": 5, "time_threshold": 10}
        )
        self.auto_mod_settings = defaultdict(
            lambda: {
                "enabled": False,
                "spam_threshold": 5,
                "mention_threshold": 5,
                "emoji_threshold": 10,
                "caps_threshold": 0.7,
                "invite_filter": True,
                "link_filter": False,
            }
        )
        self.active_mutes = {}
        self.spam_tracker = defaultdict(lambda: defaultdict(list))

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str):
        """Warn a member"""
        if member.bot:
            await ctx.send("Cannot warn bots!")
            return

        warning = self.infraction_manager.add_warning(
            ctx.guild.id, member.id, reason, ctx.author.id
        )
        warnings = self.infraction_manager.get_warnings(ctx.guild.id, member.id)

        embed = discord.Embed(title="⚠️ Warning Issued", color=discord.Color.yellow())
        embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Warning ID", value=str(warning["id"]), inline=True)
        embed.add_field(name="Total Warnings", value=str(len(warnings)), inline=True)
        embed.set_footer(text=f"Warned by {ctx.author}")

        await ctx.send(embed=embed)
        try:
            await member.send(f"You were warned in {ctx.guild.name} for: {reason}")
        except discord.HTTPException:
            pass

        # Auto-escalation
        if len(warnings) >= 5:
            try:
                await member.ban(reason="Exceeded warning threshold (5 warnings)")
                await ctx.send(f"{member} has been banned for exceeding the warning threshold.")
            except discord.Forbidden:
                await ctx.send("I don't have permission to ban this user!")
        elif len(warnings) >= 3:
            try:
                duration = timedelta(hours=12)
                await self.mute_member(
                    ctx, member, duration, "Exceeded warning threshold (3 warnings)"
                )
            except discord.Forbidden:
                await ctx.send("I don't have permission to mute this user!")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx: commands.Context, member: discord.Member):
        """View a member's warnings"""
        warnings = self.infraction_manager.get_warnings(ctx.guild.id, member.id)

        if not warnings:
            await ctx.send(f"{member} has no warnings!")
            return

        embed = discord.Embed(title=f"Warnings for {member}", color=discord.Color.yellow())

        for warning in warnings:
            mod = ctx.guild.get_member(warning["mod_id"])
            mod_name = mod.name if mod else "Unknown Moderator"
            timestamp = datetime.fromisoformat(warning["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")

            embed.add_field(
                name=f"Warning #{warning['id']}",
                value=f"**Reason:** {warning['reason']}\n**By:** {mod_name}\n**When:** {timestamp}",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def delwarn(self, ctx: commands.Context, member: discord.Member, warning_id: int):
        """Delete a warning"""
        if self.infraction_manager.remove_warning(ctx.guild.id, member.id, warning_id):
            await ctx.send(f"Removed warning #{warning_id} from {member}")
        else:
            await ctx.send(f"Warning #{warning_id} not found for {member}")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clearwarnings(self, ctx: commands.Context, member: discord.Member):
        """Clear all warnings for a member"""
        self.infraction_manager.warnings[ctx.guild.id][member.id].clear()
        await ctx.send(f"Cleared all warnings for {member}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: str,
        *,
        reason: str = "No reason provided",
    ):
        """Temporarily mute a member"""
        try:
            value = int(duration[:-1])
            unit = duration[-1].lower()

            if unit == "h":
                delta = timedelta(hours=value)
            elif unit == "m":
                delta = timedelta(minutes=value)
            elif unit == "d":
                delta = timedelta(days=value)
            else:
                await ctx.send("Invalid duration! Use format: 10m, 2h, 1d")
                return

            await self.mute_member(ctx, member, delta, reason)

        except ValueError:
            await ctx.send("Invalid duration format! Use format: 10m, 2h, 1d")

    async def mute_member(
        self, ctx: commands.Context, member: discord.Member, duration: timedelta, reason: str
    ):
        """Helper function to mute members"""
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not mute_role:
            # Create muted role if it doesn't exist
            try:
                mute_role = await ctx.guild.create_role(
                    name="Muted", reason="Created for mute command"
                )

                # Set up permissions for the muted role
                for channel in ctx.guild.channels:
                    await channel.set_permissions(
                        mute_role, send_messages=False, add_reactions=False
                    )
            except discord.Forbidden:
                await ctx.send("I don't have permission to create and set up the Muted role!")
                return

        try:
            await member.add_roles(mute_role, reason=reason)

            embed = discord.Embed(title="🔇 Member Muted", color=discord.Color.red())
            embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=False)
            embed.add_field(name="Duration", value=str(duration), inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Muted by {ctx.author}")

            await ctx.send(embed=embed)

            # Schedule unmute
            self.active_mutes[member.id] = asyncio.create_task(
                self.auto_unmute(member, mute_role, duration)
            )

        except discord.Forbidden:
            await ctx.send("I don't have permission to mute this user!")

    async def auto_unmute(
        self, member: discord.Member, mute_role: discord.Role, duration: timedelta
    ):
        """Helper function to handle auto-unmute"""
        await asyncio.sleep(duration.total_seconds())
        if member.get_role(mute_role.id):
            try:
                await member.remove_roles(mute_role, reason="Mute duration expired")
                try:
                    await member.send(f"You have been unmuted in {member.guild.name}")
                except discord.HTTPException:
                    pass
            except discord.Forbidden:
                pass
        self.active_mutes.pop(member.id, None)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        """Unmute a member"""
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not mute_role:
            await ctx.send("No mute role found!")
            return

        if member.id in self.active_mutes:
            self.active_mutes[member.id].cancel()
            del self.active_mutes[member.id]

        await member.remove_roles(mute_role, reason=f"Unmuted by {ctx.author}")
        await ctx.send(f"Unmuted {member.mention}")

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def raidprotection(self, ctx: commands.Context):
        """View or modify raid protection settings"""
        settings = self.raid_protection[ctx.guild.id]

        embed = discord.Embed(title="🛡️ Raid Protection Settings", color=discord.Color.blue())
        embed.add_field(
            name="Status", value="Enabled" if settings["enabled"] else "Disabled", inline=False
        )
        embed.add_field(
            name="Join Threshold", value=f"{settings['join_threshold']} joins", inline=True
        )
        embed.add_field(
            name="Time Threshold", value=f"{settings['time_threshold']} seconds", inline=True
        )

        await ctx.send(embed=embed)

    @raidprotection.command(name="toggle")
    async def raidprotection_toggle(self, ctx: commands.Context):
        """Toggle raid protection"""
        self.raid_protection[ctx.guild.id]["enabled"] = not self.raid_protection[ctx.guild.id][
            "enabled"
        ]
        status = "enabled" if self.raid_protection[ctx.guild.id]["enabled"] else "disabled"
        await ctx.send(f"Raid protection {status}")

    @raidprotection.command(name="threshold")
    async def raidprotection_threshold(self, ctx: commands.Context, joins: int, seconds: int):
        """Set raid protection thresholds"""
        self.raid_protection[ctx.guild.id]["join_threshold"] = joins
        self.raid_protection[ctx.guild.id]["time_threshold"] = seconds
        await ctx.send(f"Raid protection will trigger on {joins} joins within {seconds} seconds")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle raid protection"""
        if not self.raid_protection[member.guild.id]["enabled"]:
            return

        now = datetime.now()
        threshold_time = timedelta(seconds=self.raid_protection[member.guild.id]["time_threshold"])

        # Track recent joins
        recent_joins = [
            j
            for j in self.spam_tracker[member.guild.id]["joins"]
            if now - datetime.fromisoformat(j) < threshold_time
        ]
        recent_joins.append(now.isoformat())
        self.spam_tracker[member.guild.id]["joins"] = recent_joins

        # Check if raid detection was triggered
        if len(recent_joins) >= self.raid_protection[member.guild.id]["join_threshold"]:
            try:
                await member.guild.edit(verification_level=discord.VerificationLevel.high)

                # Try to notify moderators
                mod_role = discord.utils.get(member.guild.roles, name="Moderator")
                if mod_role:
                    channel = member.guild.system_channel or member.guild.text_channels[0]
                    await channel.send(
                        f"{mod_role.mention} Potential raid detected! "
                        f"{len(recent_joins)} members joined in {threshold_time.seconds} seconds. "
                        "Verification level has been increased."
                    )
            except discord.Forbidden:
                pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))
