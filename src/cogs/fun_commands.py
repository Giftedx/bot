import asyncio
import os
import random
from typing import Dict, List, Optional

import discord
import giphy_client
from discord.ext import commands
from giphy_client.rest import ApiException


class FunCommands(commands.Cog):
    """Fun commands and casual mini-games"""

    def __init__(self, bot):
        self.bot = bot
        self.giphy_api = giphy_client.DefaultApi()
        self.giphy_api_key = os.getenv("GIPHY_API_KEY")
        # Move all constants here from main file
        self.NANI_RESPONSES = [
            "お前はもう死んでいる。\n*(Omae wa mou shindeiru)*\n**NANI?!** 💥",
            "*teleports behind you*\nNothing personal, kid... 🗡️",
            "このDIOだ!\n*(KONO DIO DA!)* 🧛‍♂️",
            "MUDA MUDA MUDA MUDA! 👊",
            "ROAD ROLLER DA! 🚛",
            "ゴゴゴゴ\n*(Menacing...)* ゴゴゴゴ",
            "やれやれだぜ...\n*(Yare yare daze...)* 🎭",
            "NANI?! BAKANA! MASAKA! 😱",
        ]
        self.DOUBT_GIFS = [
            "https://tenor.com/view/doubt-press-x-la-noire-gif-11674382",
            "https://tenor.com/view/doubt-x-gif-19284783",
            "https://tenor.com/view/la-noire-doubt-x-to-doubt-cole-phelps-gif-22997643",
        ]
        self.WIZARD_RESPONSES = [
            "🧙‍♂️ *waves wand* Wingardium Leviosa!",
            "🧙‍♂️ By the power of ancient magic... ✨",
            "🧙‍♂️ Abracadabra! ✨",
            "🧙‍♂️ *adjusts pointy hat* Magical greetings! ✨",
            "🧙‍♂️ *strokes long beard thoughtfully* Hmmmm... magic! ✨",
            "🧙‍♂️ YOU SHALL NOT PASS! ...just kidding, hello there! ✨",
        ]
        # Add new response collections
        self.COFFEE_RESPONSES = [
            "☕ *sips coffee* Ahhh, perfect morning brew!",
            "☕ Coffee is always the answer!",
            "☕ ERROR 418: I'm a teapot... just kidding, here's your coffee!",
            "☕ *inhales coffee aroma* Now that's what I call a morning boost!",
            "☕ One does not simply code without coffee...",
        ]
        self.SAD_RESPONSES = [
            "😢 There there, have a virtual hug!",
            "😢 Everything will be okay!",
            "😢 Don't be sad, have a cookie! 🍪",
            "😢 Turn that frown upside down!",
            "😢 You're awesome, remember that!",
        ]
        self.TRIGGERED_RESPONSES = [
            "*[TRIGGERED INTENSIFIES]* 😤",
            "REEEEEEEEEEEEE! 😠",
            "*heavy breathing* 😤",
            "*eye twitching intensifies* 😠",
            "That's it, I'm done! 😤",
        ]
        # Add interaction responses
        self.BOOP_RESPONSES = [
            "*boop!* Right on the nose! 👉👃",
            "*boop!* Gotcha! 👆",
            "*boop!* Hehe! 👋",
            "*sneaky boop!* 🤫",
            "*gentle boop!* 🥰",
        ]
        self.WAVE_RESPONSES = [
            "*waves energetically* 👋",
            "*jumps up and down while waving* 🦘👋",
            "*waves shyly* 😊👋",
            "*waves with both hands* 👐",
            "*royal wave* 👑👋",
        ]
        self.HIGH_FIVE_RESPONSES = [
            "High five! ✋ *SLAP*",
            "Up high! ✋ *epic high five*",
            "✋ *perfect high five*",
            "✋ *misses completely* Oops...",
            "✋ *too slow!*",
        ]
        self.DOUBT_RESPONSES = [
            "🤔 Press X to doubt",
            "🤔 *doubting intensifies*",
            "🤔 Seems kinda sus...",
            "🤔 [X] Doubt",
            "🤔 Not sure if serious...",
        ]
        self.MOCK_RESPONSES = [
            "nOt LiKe ThIs",
            "Oh ReAlLy?",
            "*mOcKiNg NoIsEs*",
            "wHaTeVeR yOu SaY",
            "sUrE tHiNg BuDdY",
        ]
        self.PP_SIZES = [
            "8D",
            "8=D",
            "8==D",
            "8===D",
            "8====D",
            "8=====D",
            "8======D",
            "8=======D",
            "8========D",
            "8=========D",
        ]
        self.EIGHTBALL_RESPONSES = [
            # Positive responses
            "🎱 It is certain",
            "🎱 It is decidedly so",
            "🎱 Without a doubt",
            "🎱 Yes definitely",
            "🎱 You may rely on it",
            "🎱 As I see it, yes",
            "🎱 Most likely",
            "🎱 Outlook good",
            "🎱 Yes",
            "🎱 Signs point to yes",
            # Neutral responses
            "🎱 Reply hazy, try again",
            "🎱 Ask again later",
            "🎱 Better not tell you now",
            "🎱 Cannot predict now",
            "🎱 Concentrate and ask again",
            # Negative responses
            "🎱 Don't count on it",
            "🎱 My reply is no",
            "🎱 My sources say no",
            "🎱 Outlook not so good",
            "🎱 Very doubtful",
        ]
        self.RATE_RESPONSES = [
            "I rate that a {}/10 {}",
            "Hmm... that's a {}/10 {}",
            "Let me think... {}/10 {}",
            "According to my calculations... {}/10 {}",
            "My sophisticated rating algorithm says {}/10 {}",
        ]
        self.RATE_EMOJIS = {
            0: "💩",
            1: "😱",
            2: "😨",
            3: "😰",
            4: "😕",
            5: "😐",
            6: "🙂",
            7: "😊",
            8: "😄",
            9: "😍",
            10: "💯",
        }
        self.SHIP_RESPONSES = [
            "💘 Love Meter: {}% - {}",
            "💗 Compatibility: {}% - {}",
            "💖 Ship Rating: {}% - {}",
            "💝 Love Calculator: {}% - {}",
        ]
        self.SHIP_COMMENTS = {
            range(0, 20): "Yikes... maybe just be friends? 😅",
            range(20, 40): "There's... potential? Maybe? 🤔",
            range(40, 60): "Could work with some effort! 💪",
            range(60, 80): "Looking good! There's definitely something there! 😊",
            range(80, 100): "Perfect match! When's the wedding? 💍",
            range(100, 101): "SOULMATES ALERT! 💘",
        }
        self.trivia_questions = [
            {
                "category": "gaming",
                "question": "What year was Minecraft first released?",
                "answer": "2009",
            },
            {
                "category": "gaming",
                "question": "Who is Mario's dinosaur companion?",
                "answer": "yoshi",
            },
            {
                "category": "anime",
                "question": "What is the name of Naruto's signature technique?",
                "answer": "rasengan",
            },
            {
                "category": "coding",
                "question": "What programming language is Discord.py written in?",
                "answer": "python",
            },
        ]

    @commands.group(invoke_without_command=True)
    async def fun(self, ctx):
        """Fun Commands and Mini-Games

        Mini-Games:
        • !trivia [category] - Test your knowledge
        • !8ball <question> - Ask the magic 8-ball
        • !choice <options> - Let the bot decide
        • !rate <thing> - Get the bot's rating

        Social Commands:
        • !hug @user - Give someone a hug
        • !pat @user - Pat someone
        • !highfive @user - Give a high five
        • !ship @user1 @user2 - Check compatibility

        Use !help fun <command> for more details
        Example: !help fun trivia
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @commands.command()
    async def trivia(self, ctx, category: str = "random"):
        """Play a trivia game!

        Categories:
        • gaming - Video game knowledge
        • anime - Anime & manga trivia
        • coding - Programming questions
        • random - Random mix of categories

        Rules:
        1. Bot asks a question
        2. You have 30 seconds to answer
        3. First correct answer wins

        Usage: !trivia [category]
        Example: !trivia gaming
        """
        # Filter questions by category if specified
        available_questions = self.trivia_questions
        if category != "random":
            available_questions = [
                q for q in self.trivia_questions if q["category"] == category.lower()
            ]
            if not available_questions:
                await ctx.send(f"No questions available for category '{category}'!")
                return

        question = random.choice(available_questions)
        await ctx.send(f"**{question['category'].title()} Trivia**\n{question['question']}")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            guess = await self.bot.wait_for("message", check=check, timeout=30.0)
            if guess.content.lower() == question["answer"].lower():
                await ctx.send("Correct! 🎉")
            else:
                await ctx.send(f"Wrong! The answer was {question['answer']}.")
        except asyncio.TimeoutError:
            await ctx.send("Time's up! ⏰")

    @commands.command(name="8ball")
    async def eightball(self, ctx, *, question: str):
        """Ask the magic 8-ball a question!

        The 8-ball will give you a mystical answer
        to any yes/no question you ask.

        Usage: !8ball <question>
        Example: !8ball Will I win the lottery?
        """
        responses = [
            "🎱 It is certain",
            "🎱 Without a doubt",
            "🎱 Most likely",
            "🎱 Reply hazy, try again",
            "🎱 Better not tell you now",
            "🎱 Don't count on it",
            "🎱 My sources say no",
            "🎱 Very doubtful",
        ]
        response = random.choice(responses)
        embed = discord.Embed(
            title="Magic 8-Ball",
            description=f"Q: {question}\nA: {response}",
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def choice(self, ctx, *, options: str):
        """Let the bot choose between multiple options

        Separate options with commas
        Bot will randomly select one option

        Usage: !choice option1, option2, option3
        Example: !choice pizza, burger, sushi
        """
        choices = [choice.strip() for choice in options.split(",")]
        if len(choices) < 2:
            await ctx.send("Please provide at least 2 options!")
            return

        choice = random.choice(choices)
        embed = discord.Embed(
            title="🤔 Making a choice...",
            description=f"I choose... **{choice}**!",
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="hello")
    async def hello(self, ctx):
        """Basic greeting"""
        greetings = [
            "Hello! 👋",
            "Hi there! 😊",
            "Greetings! 🌟",
            "Hey! How's it going? 😄",
            "Welcome! 🎉",
        ]
        embed = discord.Embed(
            title=random.choice(greetings),
            description="I'm your friendly neighborhood Discord-Plex bot!",
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}")
        await ctx.send(embed=embed)
        await ctx.message.add_reaction("👋")

    @commands.command(name="wizard")
    async def wizard(self, ctx):
        """Magical greeting"""
        embed = discord.Embed(
            title="✨ Magical Greeting! ✨",
            description=random.choice(self.WIZARD_RESPONSES),
            color=discord.Color.purple(),
        )
        embed.set_footer(text=f"Summoned by {ctx.author.name}")
        msg = await ctx.send(embed=embed)
        # Add sparkle animation with reactions
        reactions = ["🧙‍♂️", "✨", "🌟", "💫"]
        for reaction in reactions:
            await msg.add_reaction(reaction)
            await asyncio.sleep(0.5)

    @commands.command(name="coffee")
    async def coffee(self, ctx):
        """For coffee lovers"""
        embed = discord.Embed(
            title="Coffee Time! ☕",
            description=random.choice(self.COFFEE_RESPONSES),
            color=discord.Color.from_rgb(139, 69, 19),  # Coffee brown
        )
        embed.set_footer(text="Brewed with ❤️")
        await ctx.send(embed=embed)
        await ctx.message.add_reaction("☕")

    @commands.command(name="sad")
    async def sad(self, ctx):
        """Cheer up command"""
        embed = discord.Embed(
            title="Cheer Up! 💖",
            description=random.choice(self.SAD_RESPONSES),
            color=discord.Color.blue(),
        )
        msg = await ctx.send(embed=embed)
        # Add heartwarming reactions
        reactions = ["💖", "🤗", "🌟", "🍪"]
        for reaction in reactions:
            await msg.add_reaction(reaction)
            await asyncio.sleep(0.5)

    @commands.command(name="triggered")
    async def triggered(self, ctx):
        """TRIGGERED response"""
        embed = discord.Embed(
            title="TRIGGERED!!! 😤",
            description=random.choice(self.TRIGGERED_RESPONSES),
            color=discord.Color.red(),
        )
        msg = await ctx.send(embed=embed)
        # Add triggered animation with reactions
        reactions = ["😠", "💢", "😤", "💥"]
        for reaction in reactions:
            await msg.add_reaction(reaction)
            await asyncio.sleep(0.5)

    @commands.command(name="nani")
    async def nani(self, ctx):
        """NANI?! response"""
        embed = discord.Embed(
            title="⚡ NANI?! ⚡",
            description=random.choice(self.NANI_RESPONSES),
            color=discord.Color.red(),
        )
        msg = await ctx.send(embed=embed)
        reactions = ["💥", "⚡", "🗡️", "👊", "😱"]
        for reaction in reactions:
            await msg.add_reaction(reaction)
            await asyncio.sleep(0.5)

    @commands.command(name="choose")
    async def choose(self, ctx, *, options: str):
        """Choose between multiple options (separate with commas)"""
        try:
            choices = [opt.strip() for opt in options.split(",") if opt.strip()]
            if len(choices) < 2:
                await ctx.send("Please provide at least 2 options separated by commas!")
                return

            embed = discord.Embed(
                title="🤔 Making a choice...",
                description=f"And the winner is...\n\n**{random.choice(choices)}**!",
                color=discord.Color.gold(),
            )
            embed.add_field(name="Options were", value="\n".join(f"• {opt}" for opt in choices))
            embed.set_footer(text="Choose wisely!")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send("Usage: !choose option1, option2, option3, ...")

    @commands.command(name="boop")
    async def boop(self, ctx, member: discord.Member = None):
        """Boop someone's nose!"""
        if member is None:
            await ctx.send("Who do you want to boop? Mention someone!")
            return

        if member.id == ctx.author.id:
            await ctx.send("You can't boop yourself! Boop someone else! 😄")
            return

        embed = discord.Embed(
            title="👉 Boop!",
            description=f"{ctx.author.mention} {random.choice(self.BOOP_RESPONSES)} {member.mention}",
            color=discord.Color.pink(),
        )
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("👉")
        await msg.add_reaction("👃")

    @commands.command(name="wave")
    async def wave(self, ctx, member: discord.Member = None):
        """Wave at someone!"""
        if member is None:
            member = ctx.author
            response = f"{random.choice(self.WAVE_RESPONSES)} to everyone!"
        else:
            response = f"{random.choice(self.WAVE_RESPONSES)} to {member.mention}!"

        embed = discord.Embed(
            title="👋 Wave!",
            description=f"{ctx.author.mention} {response}",
            color=discord.Color.blue(),
        )
        msg = await ctx.send(embed=embed)
        reactions = ["👋", "💫", "💝"]
        for reaction in reactions:
            await msg.add_reaction(reaction)
            await asyncio.sleep(0.5)

    @commands.command(name="highfive")
    async def highfive(self, ctx, member: discord.Member = None):
        """Give someone a high five!"""
        if member is None:
            await ctx.send("Who do you want to high five? Mention someone!")
            return

        if member.id == ctx.author.id:
            await ctx.send("You can't high five yourself! High five someone else! 😄")
            return

        embed = discord.Embed(
            title="✋ High Five!",
            description=f"{ctx.author.mention} gives {member.mention} a {random.choice(self.HIGH_FIVE_RESPONSES)}",
            color=discord.Color.green(),
        )
        msg = await ctx.send(embed=embed)
        reactions = ["✋", "👏", "💫"]
        for reaction in reactions:
            await msg.add_reaction(reaction)
            await asyncio.sleep(0.5)

    @commands.command(name="doubt")
    async def doubt(self, ctx):
        """Express your doubt with a classic meme"""
        embed = discord.Embed(
            title="Press X to Doubt",
            description=random.choice(self.DOUBT_RESPONSES),
            color=discord.Color.light_grey(),
        )
        try:
            # Search for a "press x to doubt" gif
            response = self.giphy_api.gifs_search_get(
                self.giphy_api_key, "press x to doubt", limit=1, rating="pg"
            )
            if response.data:
                gif_url = response.data[0].images.original.url
                embed.set_image(url=gif_url)
        except ApiException:
            # Fallback to a static gif if API fails
            embed.set_image(url=random.choice(self.DOUBT_GIFS))

        msg = await ctx.send(embed=embed)
        reactions = ["🤔", "❌", "🇽"]
        for reaction in reactions:
            await msg.add_reaction(reaction)
            await asyncio.sleep(0.5)

    @commands.command(name="mock")
    async def mock(self, ctx, *, text: str = None):
        """MoCk TeXt LiKe ThIs"""
        if not text:
            await ctx.send("Give me something to mock! Usage: !mock <text>")
            return

        mocked_text = "".join(c.upper() if i % 2 else c.lower() for i, c in enumerate(text))
        embed = discord.Embed(
            title="mOcKiNg SpOnGeBoB",
            description=f"{mocked_text}",
            color=discord.Color.gold(),
        )
        embed.set_footer(text=random.choice(self.MOCK_RESPONSES))
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("🤪")

    @commands.command(name="pp_size")
    async def pp_size(self, ctx, member: discord.Member = None):
        """Check pp size (100% accurate scientific measurement)"""
        target = member or ctx.author
        if target.bot:
            await ctx.send("Bots don't have that kind of hardware! 🤖")
            return

        # Use user ID as seed for consistent results
        random.seed(target.id)
        size = random.choice(self.PP_SIZES)
        random.seed()  # Reset seed

        embed = discord.Embed(
            title="PP Size Machine",
            description=f"{target.mention}'s pp size:\n{size}",
            color=discord.Color.purple(),
        )
        embed.set_footer(text="Results are 100% scientific and accurate*")
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("📏")

    @commands.command(name="emojify")
    async def emojify(self, ctx, *, text: str = None):
        """Convert text to regional indicator emojis"""
        if not text:
            await ctx.send("Give me text to emojify! Usage: !emojify <text>")
            return

        # Convert to lowercase and replace spaces
        text = text.lower().replace(" ", "   ")

        # Map characters to regional indicators
        char_to_emoji = {
            "a": "🇦",
            "b": "🇧",
            "c": "🇨",
            "d": "🇩",
            "e": "🇪",
            "f": "🇫",
            "g": "🇬",
            "h": "🇭",
            "i": "🇮",
            "j": "🇯",
            "k": "🇰",
            "l": "🇱",
            "m": "🇲",
            "n": "🇳",
            "o": "🇴",
            "p": "🇵",
            "q": "🇶",
            "r": "🇷",
            "s": "🇸",
            "t": "🇹",
            "u": "🇺",
            "v": "🇻",
            "w": "🇼",
            "x": "🇽",
            "y": "🇾",
            "z": "🇿",
            " ": "  ",
        }

        emojified = " ".join(char_to_emoji.get(c, c) for c in text)
        if len(emojified) > 2000:  # Discord message limit
            await ctx.send("Text too long to emojify!")
            return

        await ctx.send(emojified)

    @commands.command(name="8ball")
    async def eightball(self, ctx, *, question: str = None):
        """Ask the magic 8-ball a question"""
        if not question:
            await ctx.send("🎱 You need to ask a question! Usage: !8ball <question>")
            return

        # Add suspense with typing indicator
        async with ctx.typing():
            await asyncio.sleep(1.5)

        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            description=f"**Q:** {question}\n\n**A:** {random.choice(self.EIGHTBALL_RESPONSES)}",
            color=discord.Color.blue(),
        )
        embed.set_footer(text="The 8-ball has spoken!")
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("🎱")

    @commands.command(name="rate")
    async def rate(self, ctx, *, thing: str = None):
        """Rate anything out of 10"""
        if not thing:
            await ctx.send("What do you want me to rate? Usage: !rate <anything>")
            return

        # Use thing as seed for consistent ratings
        random.seed(thing.lower())
        rating = random.randint(0, 10)
        random.seed()  # Reset seed

        emoji = self.RATE_EMOJIS[rating]
        response = random.choice(self.RATE_RESPONSES).format(rating, emoji)

        embed = discord.Embed(
            title="Rating Machine",
            description=f"**{thing}**\n{response}",
            color=discord.Color.gold(),
        )
        embed.set_footer(text="Ratings are final and totally scientific!")
        msg = await ctx.send(embed=embed)
        await msg.add_reaction(emoji)

    @commands.command(name="ship")
    async def ship(self, ctx, member1: discord.Member = None, member2: discord.Member = None):
        """Check the love compatibility between two people"""
        if not member1 or not member2:
            await ctx.send("❤️ I need two people to ship! Usage: !ship @person1 @person2")
            return

        if member1 == member2:
            await ctx.send("😅 Self-love is important, but try shipping two different people!")
            return

        # Generate consistent ship percentage based on members' IDs
        random.seed(member1.id + member2.id)
        percentage = random.randint(0, 100)
        random.seed()  # Reset seed

        # Find appropriate comment based on percentage
        comment = next(
            comment for ranges, comment in self.SHIP_COMMENTS.items() if percentage in ranges
        )

        ship_name = f"{member1.name[:len(member1.name)//2]}{member2.name[len(member2.name)//2:]}"
        response = random.choice(self.SHIP_RESPONSES).format(percentage, comment)

        embed = discord.Embed(
            title="💘 Love Calculator",
            description=f"{member1.mention} x {member2.mention}\n{response}",
            color=discord.Color.red(),
        )
        embed.add_field(name="Ship Name", value=f"**{ship_name}**", inline=False)
        progress = "█" * (percentage // 10) + "░" * ((100 - percentage) // 10)
        embed.add_field(name="Love Meter", value=f"`{progress}` {percentage}%", inline=False)

        msg = await ctx.send(embed=embed)
        hearts = ["💝", "💖", "💗", "💓", "💘"]
        for heart in hearts:
            await msg.add_reaction(heart)
            await asyncio.sleep(0.5)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FunCommands(bot))
