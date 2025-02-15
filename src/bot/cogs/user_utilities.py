"""Custom commands and user utility features."""

import discord
from discord.ext import commands
from typing import Dict, Optional, DefaultDict
from collections import defaultdict
import time
import asyncio


class UserUtilities(commands.Cog):
    """User utility commands and custom command management."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.custom_commands: Dict[int, Dict[str, str]] = defaultdict(dict)
        self.custom_aliases: DefaultDict[int, Dict[str, str]] = defaultdict(dict)
        self.tags: Dict[int, Dict[str, str]] = {}
        self.afk_users: Dict[int, str] = {}
        self._deleted_messages = {}
        self.cooldowns: Dict[str, Dict[int, float]] = defaultdict(dict)
        self.cooldown_times = {
            'tag': 3,
            'bookmark': 3,
            'suggest': 30,
            'poll': 30,
        }

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Global checks for all utility commands"""
        if ctx.command.name in self.cooldown_times:
            cooldown = self.cooldown_times[ctx.command.name]
            last_use = self.cooldowns[ctx.command.name].get(ctx.author.id, 0)
            if time.time() - last_use < cooldown:
                remaining = int(cooldown - (time.time() - last_use))
                raise commands.CommandOnCooldown(
                    commands.BucketType.user,
                    remaining
                )
            self.cooldowns[ctx.command.name][ctx.author.id] = time.time()
        return True

    @commands.group(name='cc')
    @commands.has_permissions(manage_messages=True)
    async def custom_command(self, ctx: commands.Context):
        """Manage custom commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @custom_command.command(name='add')
    async def add_custom_command(self, ctx: commands.Context, name: str, *, response: str):
        """Add a custom command"""
        if name in [c.name for c in ctx.bot.commands]:
            return await ctx.send("That would conflict with an existing command!")

        if name in self.custom_commands[ctx.guild.id]:
            return await ctx.send("A custom command with that name already exists!")

        self.custom_commands[ctx.guild.id][name] = response
        await ctx.send(f"Added custom command: !{name}")

    @custom_command.command(name='edit')
    async def edit_custom_command(self, ctx: commands.Context, name: str, *, response: str):
        """Edit a custom command"""
        if name not in self.custom_commands[ctx.guild.id]:
            return await ctx.send("Custom command not found!")

        self.custom_commands[ctx.guild.id][name] = response
        await ctx.send(f"Updated custom command: !{name}")

    @custom_command.command(name='remove')
    async def remove_custom_command(self, ctx: commands.Context, name: str):
        """Remove a custom command"""
        if name not in self.custom_commands[ctx.guild.id]:
            return await ctx.send("Custom command not found!")

        del self.custom_commands[ctx.guild.id][name]
        await ctx.send(f"Removed custom command: !{name}")

    @custom_command.command(name='list')
    async def list_custom_commands(self, ctx: commands.Context):
        """List all custom commands"""
        commands = self.custom_commands[ctx.guild.id]
        if not commands:
            return await ctx.send("No custom commands set up!")

        embed = discord.Embed(title="Custom Commands", color=discord.Color.blue())
        for name, response in commands.items():
            embed.add_field(
                name=f"!{name}",
                value=f"Response: {response[:100]}...",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.group(name='alias')
    @commands.has_permissions(manage_guild=True)
    async def alias(self, ctx: commands.Context):
        """Manage custom command aliases"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @alias.command(name='add')
    @commands.has_permissions(manage_guild=True)
    async def add_alias(self, ctx: commands.Context, alias: str, *, command: str):
        """Add a custom alias for a command"""
        if alias in [c.name for c in self.bot.commands]:
            return await ctx.send("That alias would conflict with an existing command!")

        if command.split()[0] in self.custom_aliases[ctx.guild.id]:
            return await ctx.send("You can't create an alias of another alias!")

        self.custom_aliases[ctx.guild.id][alias] = command
        await ctx.send(f"Added alias '{alias}' for command '{command}'")

    @alias.command(name='remove')
    @commands.has_permissions(manage_guild=True)
    async def remove_alias(self, ctx: commands.Context, alias: str):
        """Remove a custom alias"""
        if alias in self.custom_aliases[ctx.guild.id]:
            del self.custom_aliases[ctx.guild.id][alias]
            await ctx.send(f"Removed alias '{alias}'")
        else:
            await ctx.send("Alias not found!")

    @alias.command(name='list')
    async def list_aliases(self, ctx: commands.Context):
        """List all custom aliases"""
        aliases = self.custom_aliases[ctx.guild.id]
        if not aliases:
            return await ctx.send("No aliases set up!")

        embed = discord.Embed(title="Custom Command Aliases", color=discord.Color.blue())
        for alias, command in aliases.items():
            embed.add_field(
                name=f"!{alias}",
                value=f"→ !{command}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(name='afk')
    async def afk(self, ctx: commands.Context, *, reason: str = "AFK"):
        """Set your AFK status"""
        self.afk_users[ctx.author.id] = reason
        await ctx.send(f"I set your AFK: {reason}")

    @commands.command(name='snipe')
    async def snipe(self, ctx: commands.Context):
        """Show the last deleted message in the channel"""
        deleted = self._deleted_messages.get(ctx.channel.id)
        
        if not deleted:
            await ctx.send("No recently deleted messages!")
            return
            
        author, content, deleted_at = deleted
        
        embed = discord.Embed(
            description=content,
            color=discord.Color.red(),
            timestamp=deleted_at
        )
        embed.set_author(
            name=f"{author.name}#{author.discriminator}",
            icon_url=author.avatar.url if author.avatar else None
        )
        embed.set_footer(text="Deleted at")
        
        await ctx.send(embed=embed)

    @commands.command(name='userinfo')
    async def userinfo(
        self,
        ctx: commands.Context,
        target: Optional[discord.Member] = None
    ):
        """Get information about a user"""
        user = target or ctx.author
        embed = discord.Embed(
            title=f"User Info - {user.name}",
            color=discord.Color.blue()
        )
        
        # Handle both Member and User objects
        if isinstance(user, discord.Member):
            roles = [role.mention for role in user.roles[1:]]
            embed.add_field(name="Nickname", value=user.nick or "None")
            embed.add_field(
                name="Joined Server",
                value=user.joined_at.strftime("%Y-%m-%d") if user.joined_at else "Unknown"
            )
            if roles:
                embed.add_field(
                    name=f"Roles [{len(roles)}]",
                    value=" ".join(roles[:5]) + ("..." if len(roles) > 5 else ""),
                    inline=False
                )
        
        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="ID", value=user.id)
        embed.add_field(name="Account Created", value=user.created_at.strftime("%Y-%m-%d"))
        
        await ctx.send(embed=embed)

    @commands.group(name='tag', invoke_without_command=True)
    async def tag(self, ctx: commands.Context, *, name: str = None):
        """Tag system to store and recall text snippets"""
        if name is None:
            return await ctx.send_help(ctx.command)

        guild_tags = self.tags.get(ctx.guild.id, {})
        if name in guild_tags:
            await ctx.send(guild_tags[name])
        else:
            await ctx.send(f"Tag '{name}' not found!")

    @tag.command(name='create')
    async def tag_create(self, ctx: commands.Context, name: str, *, content: str):
        """Create a new tag"""
        if ctx.guild.id not in self.tags:
            self.tags[ctx.guild.id] = {}

        if name in self.tags[ctx.guild.id]:
            await ctx.send("A tag with that name already exists!")
            return

        self.tags[ctx.guild.id][name] = content
        await ctx.send(f"Created tag '{name}'")

    @tag.command(name='delete')
    async def tag_delete(self, ctx: commands.Context, name: str):
        """Delete a tag"""
        if name in self.tags.get(ctx.guild.id, {}):
            del self.tags[ctx.guild.id][name]
            await ctx.send(f"Deleted tag '{name}'")
        else:
            await ctx.send("Tag not found!")

    @tag.command(name='list')
    async def tag_list(self, ctx: commands.Context):
        """List all tags in the server"""
        guild_tags = self.tags.get(ctx.guild.id, {})
        if not guild_tags:
            return await ctx.send("No tags found in this server!")

        embed = discord.Embed(title="Server Tags", color=discord.Color.blue())
        for name, content in guild_tags.items():
            embed.add_field(
                name=name,
                value=f"{content[:100]}..." if len(content) > 100 else content,
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle AFK status and custom commands"""
        if message.author.bot:
            return

        # Handle AFK
        if message.author.id in self.afk_users:
            del self.afk_users[message.author.id]
            await message.channel.send(
                f"Welcome back {message.author.mention}! "
                "AFK status removed."
            )

        for mention in message.mentions:
            if mention.id in self.afk_users:
                reason = self.afk_users[mention.id]
                await message.channel.send(f"{mention.name} is AFK: {reason}")

        # Handle custom commands and aliases
        if not message.guild:
            return

        if not message.content.startswith(await self.bot.get_prefix(message)):
            return

        cmd = message.content[1:].split()[0]
        if cmd in self.custom_commands[message.guild.id]:
            await message.channel.send(self.custom_commands[message.guild.id][cmd])
            return

        if cmd in self.custom_aliases[message.guild.id]:
            new_content = message.content.replace(
                cmd,
                self.custom_aliases[message.guild.id][cmd],
                1
            )
            new_message = discord.Message._copy(message)
            new_message._update({"content": new_content})
            await self.bot.process_commands(new_message)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Store deleted messages for snipe command"""
        if not message.author.bot and message.content:
            self._deleted_messages[message.channel.id] = (
                message.author,
                message.content,
                message.created_at
            )


async def setup(bot: commands.Bot) -> None:
    """Set up the UserUtilities cog."""
    await bot.add_cog(UserUtilities(bot))