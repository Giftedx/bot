from discord.ext import commands
import discord
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Union

logger = logging.getLogger(__name__)

class ModerationCommands(commands.Cog, name="Moderation"):
    """Server moderation and management commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.warning_counts = {}  # Track warnings per user

    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Kick a member from the server.
        
        Parameters:
        -----------
        member: The member to kick (mention or ID)
        reason: The reason for the kick
        
        Example:
        --------
        !kick @username Spamming in chat
        """
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You can't kick someone with a higher or equal role!")
            return
            
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="Member Kicked",
                description=f"{member.mention} has been kicked by {ctx.author.mention}",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason or "No reason provided")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick that member!")

    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Ban a member from the server.
        
        Parameters:
        -----------
        member: The member to ban (mention or ID)
        reason: The reason for the ban
        
        Example:
        --------
        !ban @username Repeated rule violations
        """
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You can't ban someone with a higher or equal role!")
            return
            
        try:
            await member.ban(reason=reason, delete_message_days=1)
            embed = discord.Embed(
                title="Member Banned",
                description=f"{member.mention} has been banned by {ctx.author.mention}",
                color=discord.Color.dark_red()
            )
            embed.add_field(name="Reason", value=reason or "No reason provided")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban that member!")

    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member):
        """Unban a member from the server.
        
        Parameters:
        -----------
        member: The username#discriminator of the banned member
        
        Example:
        --------
        !unban username#1234
        """
        banned_users = [entry async for entry in ctx.guild.bans()]
        name, discriminator = member.split('#')
        
        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (name, discriminator):
                await ctx.guild.unban(user)
                embed = discord.Embed(
                    title="Member Unbanned",
                    description=f"{user.mention} has been unbanned by {ctx.author.mention}",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return
                
        await ctx.send(f"Could not find banned user {member}")

    @commands.command(name='mute')
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: str = None, *, reason=None):
        """Mute a member in the server.
        
        Parameters:
        -----------
        member: The member to mute (mention or ID)
        duration: Optional duration (e.g., 1h, 30m, 1d)
        reason: The reason for the mute
        
        Example:
        --------
        !mute @username 1h Excessive spam
        """
        # Check for muted role or create it
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            try:
                muted_role = await ctx.guild.create_role(name="Muted", reason="Created for mute command")
                for channel in ctx.guild.channels:
                    await channel.set_permissions(muted_role, speak=False, send_messages=False)
            except discord.Forbidden:
                await ctx.send("I don't have permission to create and configure the Muted role!")
                return
        
        if muted_role in member.roles:
            await ctx.send(f"{member.mention} is already muted!")
            return
            
        # Parse duration if provided
        if duration:
            time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
            unit = duration[-1].lower()
            try:
                amount = int(duration[:-1])
                seconds = amount * time_units[unit]
            except (ValueError, KeyError):
                await ctx.send("Invalid duration format! Use something like: 1h, 30m, 1d")
                return
        
        try:
            await member.add_roles(muted_role, reason=reason)
            embed = discord.Embed(
                title="Member Muted",
                description=f"{member.mention} has been muted by {ctx.author.mention}",
                color=discord.Color.orange()
            )
            embed.add_field(name="Duration", value=duration or "Indefinite")
            embed.add_field(name="Reason", value=reason or "No reason provided")
            await ctx.send(embed=embed)
            
            if duration:
                await asyncio.sleep(seconds)
                if muted_role in member.roles:
                    await member.remove_roles(muted_role)
                    await ctx.send(f"{member.mention} has been automatically unmuted.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to mute that member!")

    @commands.command(name='unmute')
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        """Unmute a muted member.
        
        Parameters:
        -----------
        member: The member to unmute (mention or ID)
        
        Example:
        --------
        !unmute @username
        """
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            await ctx.send("No Muted role found!")
            return
            
        if muted_role not in member.roles:
            await ctx.send(f"{member.mention} is not muted!")
            return
            
        try:
            await member.remove_roles(muted_role)
            embed = discord.Embed(
                title="Member Unmuted",
                description=f"{member.mention} has been unmuted by {ctx.author.mention}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I don't have permission to unmute that member!")

    @commands.command(name='warn')
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason):
        """Warn a member and track their warning count.
        
        Parameters:
        -----------
        member: The member to warn (mention or ID)
        reason: The reason for the warning
        
        Example:
        --------
        !warn @username Inappropriate language
        """
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You can't warn someone with a higher or equal role!")
            return
            
        # Initialize warning count for user
        if member.id not in self.warning_counts:
            self.warning_counts[member.id] = []
            
        self.warning_counts[member.id].append({
            'reason': reason,
            'time': datetime.now(),
            'warner': ctx.author.id
        })
        
        count = len(self.warning_counts[member.id])
        
        embed = discord.Embed(
            title="Member Warned",
            description=f"{member.mention} has been warned by {ctx.author.mention}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Warning Count", value=str(count))
        await ctx.send(embed=embed)
        
        # DM the warned user
        try:
            await member.send(f"You have been warned in {ctx.guild.name} for: {reason}")
        except discord.Forbidden:
            pass
            
        # Auto-punish based on warning count
        if count == 3:
            await ctx.invoke(self.mute, member, "1h", reason="Automatic mute: 3 warnings")
        elif count == 5:
            await ctx.invoke(self.kick, member, reason="Automatic kick: 5 warnings")
        elif count >= 7:
            await ctx.invoke(self.ban, member, reason="Automatic ban: 7+ warnings")

    @commands.command(name='warnings')
    @commands.has_permissions(kick_members=True)
    async def list_warnings(self, ctx, member: discord.Member):
        """List all warnings for a member.
        
        Parameters:
        -----------
        member: The member to check warnings for (mention or ID)
        
        Example:
        --------
        !warnings @username
        """
        if member.id not in self.warning_counts or not self.warning_counts[member.id]:
            await ctx.send(f"{member.mention} has no warnings.")
            return
            
        embed = discord.Embed(
            title=f"Warnings for {member.display_name}",
            color=discord.Color.gold()
        )
        
        for i, warning in enumerate(self.warning_counts[member.id], 1):
            warner = ctx.guild.get_member(warning['warner'])
            warner_name = warner.display_name if warner else "Unknown"
            embed.add_field(
                name=f"Warning {i}",
                value=f"Reason: {warning['reason']}\n"
                      f"Time: {warning['time'].strftime('%Y-%m-%d %H:%M')}\n"
                      f"Warned by: {warner_name}",
                inline=False
            )
            
        await ctx.send(embed=embed)

    @commands.command(name='clearwarnings')
    @commands.has_permissions(administrator=True)
    async def clear_warnings(self, ctx, member: discord.Member):
        """Clear all warnings for a member.
        
        Parameters:
        -----------
        member: The member to clear warnings for (mention or ID)
        
        Example:
        --------
        !clearwarnings @username
        """
        if member.id not in self.warning_counts:
            await ctx.send(f"{member.mention} has no warnings to clear.")
            return
            
        count = len(self.warning_counts[member.id])
        self.warning_counts[member.id] = []
        
        embed = discord.Embed(
            title="Warnings Cleared",
            description=f"Cleared {count} warnings from {member.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='purge')
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int, member: discord.Member = None):
        """Delete a number of messages from the channel.
        
        Parameters:
        -----------
        amount: Number of messages to delete (1-100)
        member: Optional member to delete messages from
        
        Example:
        --------
        !purge 10
        !purge 20 @username
        """
        if amount < 1 or amount > 100:
            await ctx.send("Please specify a number between 1 and 100.")
            return
            
        def check_message(message):
            return member is None or message.author == member
            
        try:
            deleted = await ctx.channel.purge(limit=amount + 1, check=check_message)
            msg = await ctx.send(
                f"Deleted {len(deleted) - 1} messages" + 
                (f" from {member.mention}" if member else "")
            )
            await asyncio.sleep(3)
            await msg.delete()
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete messages!")

    @commands.command(name='slowmode')
    @commands.has_permissions(manage_channels=True)
    async def set_slowmode(self, ctx, seconds: int):
        """Set the slowmode delay for the current channel.
        
        Parameters:
        -----------
        seconds: The slowmode delay in seconds (0 to disable)
        
        Example:
        --------
        !slowmode 5
        !slowmode 0
        """
        if seconds < 0 or seconds > 21600:
            await ctx.send("Slowmode delay must be between 0 and 21600 seconds (6 hours).")
            return
            
        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            if seconds == 0:
                await ctx.send("Slowmode disabled.")
            else:
                await ctx.send(f"Slowmode set to {seconds} seconds.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to change channel settings!")

    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Lock a channel."""
        channel = channel or ctx.channel
        
        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                send_messages=False,
                reason=f"Channel locked by {ctx.author}"
            )
            await ctx.send(f"🔒 {channel.mention} has been locked.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to manage channel permissions.")

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Unlock a channel."""
        channel = channel or ctx.channel
        
        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                send_messages=None,  # Reset to default
                reason=f"Channel unlocked by {ctx.author}"
            )
            await ctx.send(f"🔓 {channel.mention} has been unlocked.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to manage channel permissions.")

    @commands.command(name="role")
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, member: discord.Member, *, role: discord.Role):
        """Add or remove a role from a member."""
        try:
            if role in member.roles:
                await member.remove_roles(role)
                action = "removed from"
            else:
                await member.add_roles(role)
                action = "added to"
                
            embed = discord.Embed(
                title="Role Updated",
                description=f"Role {role.mention} has been {action} {member.mention}",
                color=role.color
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I don't have permission to manage roles.")

    @commands.command(name="nickname")
    @commands.has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member: discord.Member, *, new_nick: str = None):
        """Change a member's nickname."""
        try:
            old_nick = member.nick or member.name
            await member.edit(nick=new_nick)
            
            embed = discord.Embed(
                title="Nickname Changed",
                color=discord.Color.blue()
            )
            embed.add_field(name="Member", value=member.mention, inline=False)
            embed.add_field(name="Old Nickname", value=old_nick, inline=True)
            embed.add_field(name="New Nickname", value=new_nick or "Reset to username", inline=True)
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I don't have permission to change nicknames.")

    @commands.command(name="cleanup")
    @commands.has_permissions(manage_messages=True)
    async def cleanup(self, ctx, *, args: str = ""):
        """Clean up messages based on criteria."""
        # Parse arguments
        args = args.lower().split()
        amount = 100  # Default amount
        bot_only = False
        user = None
        contains = None
        
        for arg in args:
            if arg.isdigit():
                amount = min(int(arg), 1000)
            elif arg == "bots":
                bot_only = True
            elif arg.startswith("user:"):
                try:
                    user_id = int(arg.split(":")[1])
                    user = ctx.guild.get_member(user_id)
                except (ValueError, IndexError):
                    await ctx.send("Invalid user ID format. Use user:123456789")
                    return
            elif arg.startswith("contains:"):
                contains = arg.split(":", 1)[1]
        
        def check_message(message):
            if bot_only and not message.author.bot:
                return False
            if user and message.author != user:
                return False
            if contains and contains.lower() not in message.content.lower():
                return False
            return True
        
        try:
            deleted = await ctx.channel.purge(
                limit=amount + 1,  # +1 to include command message
                check=check_message
            )
            
            # Create summary embed
            embed = discord.Embed(
                title="Cleanup Summary",
                color=discord.Color.green()
            )
            embed.add_field(name="Messages Deleted", value=len(deleted)-1, inline=False)
            if bot_only:
                embed.add_field(name="Type", value="Bot Messages", inline=True)
            if user:
                embed.add_field(name="User Filter", value=user.mention, inline=True)
            if contains:
                embed.add_field(name="Content Filter", value=contains, inline=True)
                
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await msg.delete()
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete messages.")
        except discord.HTTPException:
            await ctx.send("Failed to delete messages. They might be too old (>14 days).")

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(ModerationCommands(bot)) 