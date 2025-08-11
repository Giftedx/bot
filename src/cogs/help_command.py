import discord
from discord.ext import commands

from src.lib.cog_utils import CogBase


class ModernHelpCommand(commands.MinimalHelpCommand):
    """A modern, dynamic, and embed-based help command."""

    def get_command_signature(self, command):
        return f"{self.context.clean_prefix}{command.qualified_name} {command.signature}"

    async def _help_embed(self, title, description, command_set):
        embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
        for command in command_set:
            embed.add_field(
                name=self.get_command_signature(command),
                value=command.short_doc or "No help found...",
                inline=False,
            )
        return embed

    async def send_bot_help(self, mapping):
        ctx = self.context
        title = "Help"
        description = "Here are the available commands:"
        embed = discord.Embed(title=title, description=description, color=discord.Color.blue())

        for cog, commands in mapping.items():
            if filtered_commands := await self.filter_commands(commands, sort=True):
                cog_name = getattr(cog, "qualified_name", "No Category")
                command_signatures = [self.get_command_signature(c) for c in filtered_commands]
                if command_signatures:
                    embed.add_field(
                        name=cog_name, value="\n".join(command_signatures), inline=False
                    )

        await ctx.send(embed=embed)

    async def send_cog_help(self, cog):
        title = cog.qualified_name or "No Category"
        await self.context.send(
            embed=await self._help_embed(
                title=f"{title} Commands",
                description=cog.description,
                command_set=cog.get_commands(),
            )
        )

    async def send_command_help(self, command):
        embed = discord.Embed(
            title=self.get_command_signature(command),
            description=command.help or "No description provided.",
            color=discord.Color.blue(),
        )
        await self.context.send(embed=embed)

    async def send_group_help(self, group):
        title = self.get_command_signature(group)
        await self.context.send(
            embed=await self._help_embed(
                title=title,
                description=group.help,
                command_set=group.commands,
            )
        )


class HelpCog(CogBase):
    """A cog to host the new help command."""

    def __init__(self, bot):
        super().__init__(bot)
        self._original_help_command = bot.help_command
        bot.help_command = ModernHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
