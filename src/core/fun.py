from discord.ext import commands
import discord
import random
import asyncio
import aiohttp


class FunCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.marriages = {}
        self.pet_cooldowns = {}
        self.eight_ball_responses = [
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes - definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful.",
        ]

    @commands.command()
    async def hug(self, ctx, member: discord.Member):
        """Hug someone"""
        hug_gifs = [
            "https://media.giphy.com/media/od5H3PmEG5EVq/giphy.gif",
            "https://media.giphy.com/media/3M4NpbLCTxBqU/giphy.gif",
            "https://media.giphy.com/media/PHZ7v9tfQu0o0/giphy.gif",
        ]
        embed = discord.Embed(
            description=f"{ctx.author.mention} hugs {member.mention} 🤗", color=discord.Color.pink()
        )
        embed.set_image(url=random.choice(hug_gifs))
        await ctx.send(embed=embed)

    @commands.command()
    async def pat(self, ctx, member: discord.Member):
        """Pat someone"""
        pat_gifs = [
            "https://media.giphy.com/media/5tmRHwTlHAA9WkVxTU/giphy.gif",
            "https://media.giphy.com/media/N0CIxcyPLputW/giphy.gif",
            "https://media.giphy.com/media/109ltuoSQT212w/giphy.gif",
        ]
        embed = discord.Embed(
            description=f"{ctx.author.mention} pats {member.mention} 🤚", color=discord.Color.blue()
        )
        embed.set_image(url=random.choice(pat_gifs))
        await ctx.send(embed=embed)

    @commands.command()
    async def marry(self, ctx, member: discord.Member):
        """Propose marriage to someone"""
        if ctx.author.id in self.marriages or member.id in self.marriages:
            return await ctx.send("One of you is already married!")

        await ctx.send(f"{member.mention}, do you accept {ctx.author.mention}'s proposal? (yes/no)")

        def check(m):
            return (
                m.author == member
                and m.channel == ctx.channel
                and m.content.lower() in ["yes", "no"]
            )

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30.0)
            if msg.content.lower() == "yes":
                self.marriages[ctx.author.id] = member.id
                self.marriages[member.id] = ctx.author.id
                await ctx.send(f"💕 {ctx.author.mention} and {member.mention} are now married! 💕")
            else:
                await ctx.send("💔 The proposal was declined...")
        except asyncio.TimeoutError:
            await ctx.send("No response received, proposal cancelled.")

    @commands.command()
    async def divorce(self, ctx):
        """Divorce your partner"""
        if ctx.author.id not in self.marriages:
            return await ctx.send("You're not married!")

        partner_id = self.marriages[ctx.author.id]
        del self.marriages[ctx.author.id]
        del self.marriages[partner_id]
        await ctx.send(f"{ctx.author.mention} is now divorced. 💔")

    @commands.group(invoke_without_command=True)
    async def pet(self, ctx):
        """Pet system commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @pet.command()
    async def adopt(self, ctx, name: str, type: str):
        """Adopt a pet"""
        try:
            await self.bot.db.execute(
                """INSERT INTO pets (owner_id, name, type)
                   VALUES ($1, $2, $3)""",
                ctx.author.id,
                name,
                type.lower(),
            )
            await ctx.send(f"You've adopted a {type} named {name}! 🐾")
        except Exception as e:
            await ctx.send(f"Error adopting pet: {e}")

    @pet.command()
    async def train(self, ctx, name: str):
        """Train your pet"""
        # Check cooldown
        if ctx.author.id in self.pet_cooldowns:
            remaining = self.pet_cooldowns[ctx.author.id] - ctx.message.created_at.timestamp()
            if remaining > 0:
                return await ctx.send(f"You can train again in {int(remaining)} seconds.")

        try:
            pet = await self.bot.db.fetchrow(
                "SELECT * FROM pets WHERE owner_id = $1 AND name = $2", ctx.author.id, name
            )
            if not pet:
                return await ctx.send("You don't have a pet with that name!")

            # Update pet stats
            stats = pet["stats"] or {}
            stats["level"] = stats.get("level", 0) + 1
            stats["experience"] = stats.get("experience", 0) + random.randint(10, 20)

            await self.bot.db.execute("UPDATE pets SET stats = $1 WHERE id = $2", stats, pet["id"])

            # Set cooldown (1 hour)
            self.pet_cooldowns[ctx.author.id] = ctx.message.created_at.timestamp() + 3600

            await ctx.send(
                f"{name} completed their training! 🎓\n"
                f"Level: {stats['level']}\n"
                f"Experience: {stats['experience']}"
            )
        except Exception as e:
            await ctx.send(f"Error training pet: {e}")

    @commands.command()
    async def hangman(self, ctx):
        """Play hangman"""
        words = ["discord", "python", "gaming", "computer", "internet", "programming"]
        word = random.choice(words)
        guessed = set()
        tries = 6

        def get_display():
            return " ".join(letter if letter in guessed else "_" for letter in word)

        message = await ctx.send(
            f"Hangman Game!\nWord: {get_display()}\n"
            f"Tries left: {tries}\nGuessed letters: {', '.join(sorted(guessed))}"
        )

        while tries > 0:
            if all(letter in guessed for letter in word):
                await ctx.send(f"You won! The word was {word}! 🎉")
                return

            try:
                guess = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author == ctx.author
                    and m.channel == ctx.channel
                    and len(m.content) == 1
                    and m.content.isalpha(),
                    timeout=30.0,
                )
            except asyncio.TimeoutError:
                await ctx.send("Game over - you took too long!")
                return

            letter = guess.content.lower()
            if letter in guessed:
                await ctx.send("You already guessed that letter!")
                continue

            guessed.add(letter)
            if letter not in word:
                tries -= 1
                if tries == 0:
                    await ctx.send(f"Game over! The word was {word}!")
                    return

            await message.edit(
                content=f"Hangman Game!\nWord: {get_display()}\n"
                f"Tries left: {tries}\nGuessed letters: {', '.join(sorted(guessed))}"
            )

    @commands.command()
    async def trivia(self, ctx):
        """Play a trivia game"""
        questions = [
            {"question": "What programming language is Discord.py written in?", "answer": "python"},
            {"question": "What year was Discord launched?", "answer": "2015"},
            {"question": "What is the maximum length of a Discord message?", "answer": "2000"},
        ]

        question = random.choice(questions)
        await ctx.send(f"**Trivia Time!**\n{question['question']}")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            guess = await self.bot.wait_for("message", check=check, timeout=30.0)
            if guess.content.lower() == question["answer"].lower():
                await ctx.send("Correct! 🎉")
            else:
                await ctx.send(f"Wrong! The answer was {question['answer']}.")
        except asyncio.TimeoutError:
            await ctx.send(f"Time's up! The answer was {question['answer']}.")

    @commands.command(name="8ball")
    async def eight_ball(self, ctx, *, question: str):
        """Ask the magic 8-ball a question"""
        response = random.choice(self.eight_ball_responses)
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            description=f"**Q:** {question}\n**A:** {response}",
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def roll(self, ctx, dice: str = "1d6"):
        """Roll dice in NdN format"""
        try:
            rolls, limit = map(int, dice.split("d"))
        except Exception:
            return await ctx.send("Format has to be in NdN!")

        if rolls > 25:
            return await ctx.send("Too many dice! Maximum is 25")
        if limit > 100:
            return await ctx.send("Too many sides! Maximum is 100")

        results = [random.randint(1, limit) for r in range(rolls)]
        total = sum(results)

        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"Rolling {dice}...\n"
            f"Results: {', '.join(map(str, results))}\n"
            f"Total: {total}",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def choose(self, ctx, *choices: str):
        """Choose between multiple options"""
        if len(choices) < 2:
            return await ctx.send("Please provide at least 2 choices!")

        embed = discord.Embed(
            title="🤔 Choice Maker",
            description=f"Options: {', '.join(choices)}\n"
            f"I choose: **{random.choice(choices)}**",
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def poll(self, ctx, question: str, *options: str):
        """Create a poll"""
        if len(options) > 10:
            return await ctx.send("Maximum 10 options allowed!")
        if len(options) < 2:
            return await ctx.send("Please provide at least 2 options!")

        # Number emojis for reactions
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        # Create the poll message
        description = [f"{number_emojis[idx]} {option}" for idx, option in enumerate(options)]
        embed = discord.Embed(
            title=f"📊 {question}", description="\n".join(description), color=discord.Color.blue()
        )
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")

        poll_msg = await ctx.send(embed=embed)

        # Add reactions
        for idx in range(len(options)):
            await poll_msg.add_reaction(number_emojis[idx])

    @commands.command()
    async def joke(self, ctx):
        """Tell a random joke"""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://official-joke-api.appspot.com/random_joke") as response:
                if response.status == 200:
                    joke = await response.json()
                    embed = discord.Embed(
                        title="😄 Random Joke",
                        description=f"{joke['setup']}\n\n||{joke['punchline']}||",
                        color=discord.Color.orange(),
                    )
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Couldn't fetch a joke right now!")

    @commands.command()
    async def countdown(self, ctx, seconds: int):
        """Start a countdown timer"""
        if not 0 < seconds <= 300:
            return await ctx.send("Please specify a time between 1 and 300 seconds!")

        message = await ctx.send(f"⏰ Countdown: {seconds}")

        while seconds > 0:
            await asyncio.sleep(1)
            seconds -= 1
            if seconds % 5 == 0 or seconds <= 5:  # Update every 5 seconds and last 5 seconds
                await message.edit(content=f"⏰ Countdown: {seconds}")

        await message.edit(content="🔔 Time's up!")

    @commands.command()
    async def emojify(self, ctx, *, text: str):
        """Convert text to emoji letters"""
        # Map for letter to emoji conversion
        emoji_map = {
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

        emojified = " ".join(emoji_map.get(c.lower(), c) for c in text)
        await ctx.send(emojified)


async def setup(bot):
    await bot.add_cog(FunCommands(bot))
