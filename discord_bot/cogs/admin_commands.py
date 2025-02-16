"""Administrative commands for bot management."""

import discord
from discord.ext import commands
import asyncio
from typing import Optional, Union
import datetime

class AdminCommands(commands.Cog):
    """Administrative commands for server management."""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx):
        """Check if user has admin permissions."""
        return ctx.author.guild_permissions.administrator
    
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        """Kick a member from the server."""
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="Member Kicked",
                description=f"{member.mention} has been kicked.",
                color=discord.Color.red()
            )
            if reason:
                embed.add_field(name="Reason", value=reason)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick that member.")
    
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        """Ban a member from the server."""
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="Member Banned",
                description=f"{member.mention} has been banned.",
                color=discord.Color.red()
            )
            if reason:
                embed.add_field(name="Reason", value=reason)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban that member.")
    
    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member):
        """Unban a member from the server."""
        banned_users = [entry async for entry in ctx.guild.bans()]
        member_name, member_discriminator = member.split('#')
        
        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                embed = discord.Embed(
                    title="Member Unbanned",
                    description=f"{user.mention} has been unbanned.",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return
        
        await ctx.send(f"Could not find banned user {member}")
    
    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 5):
        """Clear a specified number of messages."""
        if amount < 1:
            await ctx.send("Please specify a positive number of messages to delete.")
            return
            
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include command message
        msg = await ctx.send(f"Deleted {len(deleted)-1} messages.")
        await asyncio.sleep(3)
        await msg.delete()
    
    @commands.command(name="mute")
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: Optional[str] = None, *, reason: str = None):
        """Mute a member in the server."""
        # Check for or create muted role
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            try:
                muted_role = await ctx.guild.create_role(
                    name="Muted",
                    reason="Created for muting members"
                )
                
                # Set permissions for the muted role
                for channel in ctx.guild.channels:
                    await channel.set_permissions(muted_role, speak=False, send_messages=False)
            except discord.Forbidden:
                await ctx.send("I don't have permission to create roles.")
                return
        
        if muted_role in member.roles:
            await ctx.send(f"{member.mention} is already muted.")
            return
            
        # Parse duration if provided
        duration_seconds = 0
        if duration:
            try:
                unit = duration[-1].lower()
                value = int(duration[:-1])
                if unit == 's':
                    duration_seconds = value
                elif unit == 'm':
                    duration_seconds = value * 60
                elif unit == 'h':
                    duration_seconds = value * 3600
                elif unit == 'd':
                    duration_seconds = value * 86400
                else:
                    await ctx.send("Invalid duration format. Use s/m/h/d (e.g., 30s, 5m, 1h, 1d)")
                    return
            except ValueError:
                await ctx.send("Invalid duration format. Use s/m/h/d (e.g., 30s, 5m, 1h, 1d)")
                return
        
        try:
            await member.add_roles(muted_role, reason=reason)
            embed = discord.Embed(
                title="Member Muted",
                description=f"{member.mention} has been muted.",
                color=discord.Color.orange()
            )
            if reason:
                embed.add_field(name="Reason", value=reason)
            if duration:
                embed.add_field(name="Duration", value=duration)
            await ctx.send(embed=embed)
            
            if duration_seconds > 0:
                await asyncio.sleep(duration_seconds)
                if muted_role in member.roles:
                    await member.remove_roles(muted_role)
                    await ctx.send(f"{member.mention} has been unmuted.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to mute that member.")
    
    @commands.command(name="unmute")
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        """Unmute a muted member."""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            await ctx.send("No muted role found.")
            return
            
        if muted_role not in member.roles:
            await ctx.send(f"{member.mention} is not muted.")
            return
            
        try:
            await member.remove_roles(muted_role)
            embed = discord.Embed(
                title="Member Unmuted",
                description=f"{member.mention} has been unmuted.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I don't have permission to unmute that member.")

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(AdminCommands(bot)) 