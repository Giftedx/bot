from discord.ext import commands
import discord
from discord import app_commands
from typing import Optional, Union
import asyncio
import yaml
import json


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.custom_commands = {}

    @commands.hybrid_group(
        name="config",
        invoke_without_command=True,
        help="Server configuration commands (admin only)",
    )
    @commands.has_permissions(administrator=True)
    async def config(self, ctx: commands.Context):
        """Server configuration commands (admin only). Use /config <subcommand> or !config <subcommand>."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @config.hybrid_command(
        name="prefix", help="Change the bot's prefix for this server (admin only)"
    )
    @app_commands.describe(new_prefix="The new prefix (max 5 characters)")
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx: commands.Context, new_prefix: str):
        """Change the bot's prefix for this server. Usage: /config prefix <new_prefix>"""
        if len(new_prefix) > 5:
            return await ctx.send("Prefix must be 5 characters or less!")
        try:
            await self.bot.db.execute(
                "INSERT INTO guild_settings (guild_id, prefix) VALUES ($1, $2) "
                "ON CONFLICT (guild_id) DO UPDATE SET prefix = $2",
                ctx.guild.id,
                new_prefix,
            )
            await ctx.send(f"Prefix changed to: `{new_prefix}`")
        except Exception as e:
            await ctx.send(f"Error changing prefix: {e}")

    @commands.hybrid_group(
        name="cmd", invoke_without_command=True, help="Custom command management (admin only)"
    )
    @commands.has_permissions(administrator=True)
    async def cmd(self, ctx: commands.Context):
        """Custom command management (admin only). Use /cmd <subcommand> or !cmd <subcommand>."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @cmd.hybrid_command(name="add", help="Add a custom command (admin only)")
    @app_commands.describe(
        name="Name of the custom command", response="Response text for the command"
    )
    @commands.has_permissions(administrator=True)
    async def add_command(self, ctx: commands.Context, name: str, *, response: str):
        """Add a custom command. Usage: /cmd add <name> <response>"""
        try:
            await self.bot.db.execute(
                "INSERT INTO custom_commands (guild_id, name, response) VALUES ($1, $2, $3) "
                "ON CONFLICT (guild_id, name) DO UPDATE SET response = $3",
                ctx.guild.id,
                name.lower(),
                response,
            )
            await ctx.send(f"Added custom command: `{name}`")
        except Exception as e:
            await ctx.send(f"Error adding command: {e}")

    @cmd.hybrid_command(name="remove", help="Remove a custom command (admin only)")
    @app_commands.describe(name="Name of the custom command to remove")
    @commands.has_permissions(administrator=True)
    async def remove_command(self, ctx: commands.Context, name: str):
        """Remove a custom command. Usage: /cmd remove <name>"""
        try:
            result = await self.bot.db.execute(
                "DELETE FROM custom_commands WHERE guild_id = $1 AND name = $2",
                ctx.guild.id,
                name.lower(),
            )
            if result == "DELETE 0":
                await ctx.send("Command not found!")
            else:
                await ctx.send(f"Removed command: `{name}`")
        except Exception as e:
            await ctx.send(f"Error removing command: {e}")

    @cmd.hybrid_command(name="list", help="List all custom commands (admin only)")
    @commands.has_permissions(administrator=True)
    async def list_commands(self, ctx: commands.Context):
        """List all custom commands. Usage: /cmd list"""
        try:
            commands_ = await self.bot.db.fetch(
                "SELECT name, response FROM custom_commands WHERE guild_id = $1", ctx.guild.id
            )
            if not commands_:
                return await ctx.send("No custom commands found!")
            # Create paginated embed
            commands_per_page = 10
            pages = []
            for i in range(0, len(commands_), commands_per_page):
                page_commands = commands_[i : i + commands_per_page]
                embed = discord.Embed(title="Custom Commands", color=discord.Color.blue())
                for cmd in page_commands:
                    embed.add_field(
                        name=cmd["name"], value=f"{cmd['response'][:100]}...", inline=False
                    )
                pages.append(embed)
            if len(pages) == 1:
                await ctx.send(embed=pages[0])
            else:
                current_page = 0
                message = await ctx.send(embed=pages[current_page])
                await message.add_reaction("◀️")
                await message.add_reaction("▶️")

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]

                while True:
                    try:
                        reaction, user = await self.bot.wait_for(
                            "reaction_add", timeout=60.0, check=check
                        )
                        if str(reaction.emoji) == "▶️":
                            current_page = (current_page + 1) % len(pages)
                        elif str(reaction.emoji) == "◀️":
                            current_page = (current_page - 1) % len(pages)
                        await message.edit(embed=pages[current_page])
                        await message.remove_reaction(reaction, user)
                    except asyncio.TimeoutError:
                        break
        except Exception as e:
            await ctx.send(f"Error listing commands: {e}")

    @commands.hybrid_command(name="welcome", help="Set up or view the welcome message (admin only)")
    @app_commands.describe(channel="Channel for welcome messages", message="Welcome message text")
    @commands.has_permissions(administrator=True)
    async def welcome(
        self,
        ctx: commands.Context,
        channel: Optional[discord.TextChannel] = None,
        *,
        message: Optional[str] = None,
    ):
        """Set up or view the welcome message. Usage: /welcome #channel <message>"""
        if channel is None or message is None:
            current = await self.bot.db.fetchrow(
                "SELECT channel_id, message FROM welcome_settings WHERE guild_id = $1", ctx.guild.id
            )
            if current:
                channel = ctx.guild.get_channel(current["channel_id"])
                return await ctx.send(
                    f"Current welcome:\nChannel: {channel.mention}\n"
                    f"Message: {current['message']}\n\n"
                    "Use `/welcome #channel message` to change"
                )
            else:
                return await ctx.send(
                    "No welcome message set!\n"
                    "Use `/welcome #channel message` to set one\n"
                    "Available variables: {user}, {server}, {count}"
                )
        try:
            await self.bot.db.execute(
                "INSERT INTO welcome_settings (guild_id, channel_id, message) "
                "VALUES ($1, $2, $3) ON CONFLICT (guild_id) "
                "DO UPDATE SET channel_id = $2, message = $3",
                ctx.guild.id,
                channel.id,
                message,
            )
            await ctx.send(
                f"Welcome message set!\nChannel: {channel.mention}\n" f"Message: {message}"
            )
        except Exception as e:
            await ctx.send(f"Error setting welcome message: {e}")

    @commands.hybrid_command(
        name="autorole", help="Set up or view the autorole for new members (admin only)"
    )
    @app_commands.describe(role="Role to assign to new members")
    @commands.has_permissions(administrator=True)
    async def autorole(self, ctx: commands.Context, role: Optional[discord.Role] = None):
        """Set up or view the autorole for new members. Usage: /autorole @role"""
        if role is None:
            current = await self.bot.db.fetchrow(
                "SELECT role_id FROM autorole WHERE guild_id = $1", ctx.guild.id
            )
            if current:
                role = ctx.guild.get_role(current["role_id"])
                return await ctx.send(f"Current autorole: {role.mention}")
            else:
                return await ctx.send("No autorole set! Use `/autorole @role` to set one")
        try:
            await self.bot.db.execute(
                "INSERT INTO autorole (guild_id, role_id) VALUES ($1, $2) "
                "ON CONFLICT (guild_id) DO UPDATE SET role_id = $2",
                ctx.guild.id,
                role.id,
            )
            await ctx.send(f"Autorole set to: {role.mention}")
        except Exception as e:
            await ctx.send(f"Error setting autorole: {e}")

    @commands.hybrid_command(name="backup", help="Create a backup of server settings (admin only)")
    @commands.has_permissions(administrator=True)
    async def backup(self, ctx: commands.Context):
        """Create a backup of server settings. Usage: /backup"""
        backup_data = {
            "guild_id": ctx.guild.id,
            "guild_name": ctx.guild.name,
            "timestamp": ctx.message.created_at.isoformat(),
            "settings": {},
        }
        try:
            commands_ = await self.bot.db.fetch(
                "SELECT name, response FROM custom_commands WHERE guild_id = $1", ctx.guild.id
            )
            backup_data["settings"]["custom_commands"] = [
                {"name": cmd["name"], "response": cmd["response"]} for cmd in commands_
            ]
            welcome = await self.bot.db.fetchrow(
                "SELECT channel_id, message FROM welcome_settings WHERE guild_id = $1", ctx.guild.id
            )
            if welcome:
                backup_data["settings"]["welcome"] = {
                    "channel_id": welcome["channel_id"],
                    "message": welcome["message"],
                }
            autorole = await self.bot.db.fetchrow(
                "SELECT role_id FROM autorole WHERE guild_id = $1", ctx.guild.id
            )
            if autorole:
                backup_data["settings"]["autorole"] = autorole["role_id"]
            filename = (
                f"backup_{ctx.guild.id}_{ctx.message.created_at.strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(filename, "w") as f:
                json.dump(backup_data, f, indent=2)
            await ctx.send("Backup created!", file=discord.File(filename))
        except Exception as e:
            await ctx.send(f"Error creating backup: {e}")

    @commands.hybrid_command(
        name="restore", help="Restore server settings from a backup (admin only)"
    )
    @commands.has_permissions(administrator=True)
    async def restore(self, ctx: commands.Context):
        """Restore server settings from a backup. Usage: /restore (attach backup file in classic mode)"""
        if not ctx.message.attachments:
            return await ctx.send("Please attach a backup file!")
        try:
            attachment = ctx.message.attachments[0]
            if not attachment.filename.endswith(".json"):
                return await ctx.send("Please provide a valid backup file!")
            backup_content = await attachment.read()
            backup_data = json.loads(backup_content)
            if backup_data["guild_id"] != ctx.guild.id:
                return await ctx.send("This backup is for a different server!")
            for cmd in backup_data["settings"].get("custom_commands", []):
                await self.bot.db.execute(
                    "INSERT INTO custom_commands (guild_id, name, response) "
                    "VALUES ($1, $2, $3) ON CONFLICT (guild_id, name) "
                    "DO UPDATE SET response = $3",
                    ctx.guild.id,
                    cmd["name"],
                    cmd["response"],
                )
            if "welcome" in backup_data["settings"]:
                welcome = backup_data["settings"]["welcome"]
                await self.bot.db.execute(
                    "INSERT INTO welcome_settings (guild_id, channel_id, message) "
                    "VALUES ($1, $2, $3) ON CONFLICT (guild_id) "
                    "DO UPDATE SET channel_id = $2, message = $3",
                    ctx.guild.id,
                    welcome["channel_id"],
                    welcome["message"],
                )
            if "autorole" in backup_data["settings"]:
                await self.bot.db.execute(
                    "INSERT INTO autorole (guild_id, role_id) VALUES ($1, $2) "
                    "ON CONFLICT (guild_id) DO UPDATE SET role_id = $2",
                    ctx.guild.id,
                    backup_data["settings"]["autorole"],
                )
            await ctx.send("Settings restored successfully!")
        except Exception as e:
            await ctx.send(f"Error restoring backup: {e}")


async def setup(bot):
    await bot.add_cog(Admin(bot))
