from discord.ext import commands
import discord
import logging
import random
import datetime
import psutil
import platform
import time
import asyncio

logger = logging.getLogger(__name__)

class GeneralCommands(commands.Cog, name="General"):
    """General utility commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.datetime.utcnow()

    @commands.command(name='roll')
    async def roll_dice(self, ctx, dice: str = '1d6'):
        """Roll dice in NdN format.
        
        Parameters:
        -----------
        dice: The dice to roll in NdN format (e.g., 2d6 for two six-sided dice)
        
        Example:
        --------
        !roll 2d20
        """
        try:
            rolls, limit = map(int, dice.split('d'))
            if rolls > 100 or limit > 100:
                await ctx.send("I can't roll that many dice!")
                return
                
            results = [random.randint(1, limit) for r in range(rolls)]
            await ctx.send(f"🎲 Results: {', '.join(map(str, results))}\nTotal: {sum(results)}")
        except Exception as e:
            await ctx.send("Format has to be in NdN! Example: 1d6")

    @commands.command(name='8ball')
    async def eight_ball(self, ctx, *, question: str):
        """Ask the magic 8ball a question.
        
        Parameters:
        -----------
        question: The question to ask
        
        Example:
        --------
        !8ball Will I win the lottery?
        """
        responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.",
            "Yes - definitely.", "You may rely on it.", "As I see it, yes.",
            "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
            "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
            "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "My reply is no.", "My sources say no.",
            "Outlook not so good.", "Very doubtful."
        ]
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            description=f"Question: {question}\nAnswer: {random.choice(responses)}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name='serverinfo')
    async def server_info(self, ctx):
        """Get information about the current server."""
        guild = ctx.guild
        embed = discord.Embed(
            title=f"ℹ️ {guild.name} Server Information",
            color=discord.Color.blue()
        )
        
        # General info
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Created On", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        
        # Member info
        member_status = [len(list(filter(lambda m: str(m.status) == status, guild.members))) 
                        for status in ['online', 'idle', 'dnd', 'offline']]
        embed.add_field(
            name="Members",
            value=f"Total: {guild.member_count}\n"
                  f"Online: {member_status[0]}\n"
                  f"Idle: {member_status[1]}\n"
                  f"DND: {member_status[2]}\n"
                  f"Offline: {member_status[3]}",
            inline=True
        )
        
        # Channel info
        channels = guild.channels
        embed.add_field(
            name="Channels",
            value=f"Text: {len([c for c in channels if isinstance(c, discord.TextChannel)])}\n"
                  f"Voice: {len([c for c in channels if isinstance(c, discord.VoiceChannel)])}\n"
                  f"Categories: {len(guild.categories)}",
            inline=True
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        await ctx.send(embed=embed)

    @commands.command(name='userinfo')
    async def user_info(self, ctx, member: discord.Member = None):
        """Get information about a user.
        
        Parameters:
        -----------
        member: The member to get info about (defaults to command user)
        
        Example:
        --------
        !userinfo @username
        """
        member = member or ctx.author
        roles = [role.mention for role in member.roles if role != ctx.guild.default_role]
        
        embed = discord.Embed(
            title=f"👤 User Information for {member.display_name}",
            color=member.color
        )
        
        embed.add_field(name="User ID", value=member.id, inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Roles", value=" ".join(roles) if roles else "No roles", inline=False)
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
            
        await ctx.send(embed=embed)

    @commands.command(name='botinfo')
    async def bot_info(self, ctx):
        """Get information about the bot."""
        embed = discord.Embed(
            title="🤖 Bot Information",
            color=discord.Color.blue()
        )
        
        # Bot stats
        uptime = str(datetime.datetime.utcnow() - self.start_time)
        embed.add_field(name="Uptime", value=uptime, inline=True)
        embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
        embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
        
        # System stats
        embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent()}%", inline=True)
        embed.add_field(name="Memory Usage", 
                       value=f"{psutil.Process().memory_info().rss / 1024 / 1024:.2f} MB", 
                       inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        # Bot scope
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        total_members = sum(g.member_count for g in self.bot.guilds)
        embed.add_field(name="Total Members", value=total_members, inline=True)
        embed.add_field(name="Total Commands", 
                       value=len(set(self.bot.walk_commands())), 
                       inline=True)
        
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            
        await ctx.send(embed=embed)

    @commands.command(name='poll')
    async def create_poll(self, ctx, question: str, *options):
        """Create a poll with reactions.
        
        Parameters:
        -----------
        question: The poll question
        options: The poll options (up to 10)
        
        Example:
        --------
        !poll "What's your favorite color?" Red Blue Green
        """
        if len(options) < 2:
            await ctx.send("You need at least 2 options for a poll!")
            return
        if len(options) > 10:
            await ctx.send("You can only have up to 10 options!")
            return

        # Number emojis for reactions
        emoji_numbers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', 
                        '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

        # Create the poll embed
        embed = discord.Embed(
            title="📊 " + question,
            color=discord.Color.blue()
        )
        
        description = []
        for idx, option in enumerate(options):
            description.append(f"{emoji_numbers[idx]} {option}")
        
        embed.description = "\n".join(description)
        embed.set_footer(text=f"Poll created by {ctx.author.display_name}")
        
        # Send poll and add reactions
        poll_message = await ctx.send(embed=embed)
        for idx in range(len(options)):
            await poll_message.add_reaction(emoji_numbers[idx])

    @commands.command(name='remind')
    async def set_reminder(self, ctx, time: str, *, reminder: str):
        """Set a reminder.
        
        Parameters:
        -----------
        time: Time until reminder (e.g., 1h, 30m, 1d)
        reminder: What to remind you about
        
        Example:
        --------
        !remind 1h Take out the trash
        """
        time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        unit = time[-1].lower()
        try:
            amount = int(time[:-1])
            if unit not in time_units:
                raise ValueError
            
            seconds = amount * time_units[unit]
            if seconds > 2592000:  # 30 days
                await ctx.send("I can't remind you of something that far in the future!")
                return
                
            await ctx.send(f"I'll remind you about '{reminder}' in {time}!")
            
            await asyncio.sleep(seconds)
            await ctx.author.send(f"⏰ Reminder: {reminder}")
            
        except ValueError:
            await ctx.send("Invalid time format! Use something like: 1h, 30m, 1d")

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Get the bot's current latency."""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: {latency}ms")
    
    @commands.command(name="info")
    async def info(self, ctx):
        """Get information about the bot."""
        embed = discord.Embed(
            title="Bot Information",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        
        # System info
        embed.add_field(
            name="System",
            value=f"```\nPython: {platform.python_version()}\n"
                  f"OS: {platform.system()} {platform.release()}\n"
                  f"CPU Usage: {psutil.cpu_percent()}%\n"
                  f"Memory: {psutil.virtual_memory().percent}%```",
            inline=False
        )
        
        # Bot info
        embed.add_field(
            name="Bot",
            value=f"```\nUptime: {datetime.datetime.utcnow() - self.start_time}\n"
                  f"Latency: {round(self.bot.latency * 1000)}ms\n"
                  f"Guilds: {len(self.bot.guilds)}\n"
                  f"Users: {sum(g.member_count for g in self.bot.guilds)}```",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="help")
    async def help_command(self, ctx, command_name: str = None):
        """Get help for commands."""
        if command_name is None:
            # List all commands
            embed = discord.Embed(
                title="Available Commands",
                description="Here are all available commands:",
                color=discord.Color.blue()
            )
            
            for cog_name, cog in self.bot.cogs.items():
                command_list = [f"`{c.name}` - {c.help}" for c in cog.get_commands()]
                if command_list:
                    embed.add_field(
                        name=cog_name,
                        value="\n".join(command_list),
                        inline=False
                    )
        else:
            # Show help for specific command
            command = self.bot.get_command(command_name)
            if command is None:
                await ctx.send(f"Command `{command_name}` not found.")
                return
                
            embed = discord.Embed(
                title=f"Help: {command.name}",
                description=command.help or "No description available.",
                color=discord.Color.blue()
            )
            
            if command.aliases:
                embed.add_field(
                    name="Aliases",
                    value=", ".join(f"`{a}`" for a in command.aliases)
                )
                
        await ctx.send(embed=embed)

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(GeneralCommands(bot)) 