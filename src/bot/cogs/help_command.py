from discord.ext import commands
import discord

class HelpCommand(commands.Cog):
    """Custom help command implementation"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='help')
    async def help(self, ctx: commands.Context, command_name: str = None):
        """Show help about commands"""
        if command_name:
            # Show help for specific command
            command = self.bot.get_command(command_name)
            if command:
                embed = discord.Embed(
                    title=f"Help: {command.name}",
                    description=command.help or "No description available",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return
            await ctx.send(f"Command '{command_name}' not found.")
            return

        # Show general help
        embed = discord.Embed(
            title="Bot Commands",
            description="Here are all the available commands!",
            color=discord.Color.blue()
        )

        # Music & Audio Commands
        audio_commands = """`!play <song>` - Play a song from YouTube
`!queue` - Show music queue
`!skip` - Skip current song
`!pause` - Pause playback
`!resume` - Resume playback
`!stop` - Stop playing
`!clear` - Clear queue
`!sound <effect>` - Play sound effect
`!join` - Join voice channel
`!leave` - Leave voice channel"""
        embed.add_field(name="Music & Audio", value=audio_commands, inline=False)

        # Seasonal Events
        seasonal_commands = """`!advent` - Open advent calendar (Dec 1-25)
`!trickortreat` - Go trick or treating (Oct)
`!valentine @user` - Send valentine (Feb 14)
`!snowball @user` - Throw snowball (Dec)
`!newyear` - New Year countdown (Dec 31)"""
        embed.add_field(name="Seasonal Events", value=seasonal_commands, inline=False)

        # Fun & Interactive
        fun_commands = """`!dance` - Start dance party
`!choose <options>` - Choose between options
`!emojify <text>` - Convert text to emojis
`!boop @user` - Boop someone's nose
`!highfive @user` - Give a high five
`!wave @user` - Wave at someone
`!party [seconds]` - Start party animation
`!magic` - Magic card trick"""
        embed.add_field(name="Fun & Interactive", value=fun_commands, inline=False)

        # Social Commands
        social_commands = """`!vibe [@user]` - Vibe check
`!uwu` - UwU counter
`!mock <text>` - SpOnGeBoB text
`!rate <thing>` - Rate anything
`!bonk @user` - Horny jail
`!kiss @user` - Give kiss
`!hug @user` - Give hug
`!cuddle @user` - Cuddle
`!pat @user` - Give headpats
`!cookie @user` - Give cookie
`!marry @user` - Propose
`!divorce` - End marriage
`!ship @user1 @user2` - Ship compatibility"""
        embed.add_field(name="Social", value=social_commands, inline=False)

        # Pet System
        pet_commands = """`!adopt <name>` - Adopt pet
`!pets` - View pets
`!train` - Train pet
`!feed` - Feed pet
`!pet` - Pet your pet
`!rename <num> <name>` - Rename pet
`!battle @user` - Pet battle
`!daily` - Daily rewards
`!leaderboard` - Pet rankings"""
        embed.add_field(name="Pet System", value=pet_commands, inline=False)

        # Minigames
        minigame_commands = """`!hangman` - Play hangman
`!trivia` - Play trivia
`!wordle` - Play Wordle
`!8ball <question>` - Ask 8-ball
`!rps <choice>` - Rock paper scissors"""
        embed.add_field(name="Minigames", value=minigame_commands, inline=False)

        # Profile Commands
        profile_commands = """`!profile [@user]` - View profile
`!setcolor <hex>` - Set profile color
`!settitle <title>` - Set profile title
`!badges` - View badges
`!rank` - View your rank
`!leaderboard` - Server rankings"""
        embed.add_field(name="Profiles", value=profile_commands, inline=False)

        # Utility Commands
        utility_commands = """`!ping` - Check latency
`!afk [reason]` - Set AFK
`!remind <time> <msg>` - Set reminder
`!poll "Q" "O1" "O2"` - Create poll
`!userinfo [@user]` - User info
`!serverinfo` - Server info
`!avatar [@user]` - Get avatar"""
        embed.add_field(name="Utility", value=utility_commands, inline=False)

        # Basic Commands
        basic_commands = """`!help` - Show this help message
`!help <command>` - Show detailed help for a command"""
        embed.add_field(name="Basic Commands", value=basic_commands, inline=False)

        embed.set_footer(text="Use !help <command> for more details about a specific command!")
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCommand(bot))