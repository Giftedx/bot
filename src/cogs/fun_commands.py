import asyncio
import json
import os
import random
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import aiohttp
import discord
from discord.ext import commands

from src.core.bot import Bot

# --- Helper Classes: UI Modals and Views ---

class PollModal(discord.ui.Modal, title="Create a New Poll"):
    """A UI Modal for creating a poll with up to 4 options."""
    question: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(label="Poll Question", style=discord.TextStyle.short, placeholder="What should we play tonight?", required=True)
    option1: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(label="Option 1", style=discord.TextStyle.short, placeholder="Valorant", required=True)
    option2: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(label="Option 2", style=discord.TextStyle.short, placeholder="League of Legends", required=True)
    option3: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(label="Option 3", style=discord.TextStyle.short, placeholder="Minecraft", required=False)
    option4: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(label="Option 4", style=discord.TextStyle.short, placeholder="OSRS", required=False)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        options = [self.option1.value, self.option2.value]
        if self.option3.value:
            options.append(self.option3.value)
        if self.option4.value:
            options.append(self.option4.value)

        embed = discord.Embed(
            title=f"📊 Poll: {self.question.value}",
            description="Vote by clicking the corresponding number!",
            color=discord.Color.blurple(),
            timestamp=interaction.created_at,
        )
        for i, option in enumerate(options):
            embed.add_field(name=f"Option {i+1}", value=option, inline=False)

        embed.set_footer(text=f"Poll created by {interaction.user.display_name}")

        # Send the poll and add reactions
        await interaction.response.send_message(embed=embed)
        # Get the message object to add reactions
        message = await interaction.original_response()
        for i in range(len(options)):
            await message.add_reaction(f"{i+1}\u20e3")


def get_data_dir() -> Path:
    """Gets the path to the data directory, creating it if necessary."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir

def load_json_data(filename: str, default_factory: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
    """Loads data from a JSON file, creating it with a default if it doesn't exist."""
    path = get_data_dir() / filename
    if not path.exists():
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default_factory(), f)
        return default_factory()
    with open(path, 'r', encoding='utf-8') as f:
        data: Dict[str, Any] = json.load(f)
        return data

# --- Main Cog Class ---

class FunCommands(commands.Cog):
    """A collection of fun commands and mini-games."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = bot.db
        self.giphy_api_key = os.getenv("GIPHY_API_KEY")
        self.session = aiohttp.ClientSession()
        self.fun_data = load_json_data("fun_data.json", self._get_default_fun_data)
        self.trivia_questions: list[dict[str, str]] = self.fun_data.get("trivia_questions", [])

    async def cog_unload(self) -> None:
        """Cog cleanup."""
        await self.session.close()

    # --- Helper Methods ---

    def _get_default_fun_data(self) -> Dict[str, Any]:
        """Returns the default structure for fun_data.json."""
        return {
            "trivia_questions": [
                {"category": "gaming", "question": "In what year was the first 'The Legend of Zelda' game released?", "answer": "1986"},
                {"category": "anime", "question": "What is the name of the Titan that ate Eren's mother?", "answer": "The Smiling Titan"},
                {"category": "coding", "question": "What does API stand for?", "answer": "Application Programming Interface"},
            ],
            "pp_sizes": ["8D", "8=D", "8==D", "8===D", "8====D", "8=====D"],
            "eightball_responses": ["It is certain.", "Without a doubt.", "You may rely on it.", "Ask again later.", "My reply is no.", "Very doubtful."],
            "rate_emojis": {"0": "💩", "5": "😐", "10": "💯"},
        }

    async def get_random_gif(self, tag: str) -> Optional[str]:
        """Fetches a random GIF from Giphy based on a tag."""
        if not self.giphy_api_key:
            return None
        url = "https://api.giphy.com/v1/gifs/random"
        params = {"api_key": self.giphy_api_key, "tag": tag, "rating": "pg-13"}
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and "data" in data and "images" in data["data"] and "original" in data["data"]["images"]:
                        return str(data["data"]["images"]["original"]["url"])
        except Exception as e:
            self.bot.logger.error(f"Giphy API error: {e}")
        return None

    # --- Commands ---

    @commands.hybrid_group(name="fun", fallback="help")
    async def fun_group(self, ctx: commands.Context[Bot]) -> None:
        """A group for fun commands."""
        await ctx.send_help(ctx.command)

    @fun_group.command(name="poll")
    async def poll(self, ctx: commands.Context[Bot]) -> None:
        """Creates a poll with up to 4 options using a pop-up."""
        if ctx.interaction is None:
            await ctx.send("This command can only be used as a slash command.")
            return
        await ctx.interaction.response.send_modal(PollModal())

    @fun_group.command(name="trivia")
    async def trivia(self, ctx: commands.Context[Bot], category: str = "random") -> None:
        """Starts a trivia game.

        Categories can be 'gaming', 'anime', 'coding', or 'random'.
        """
        questions = self.trivia_questions
        if category != "random":
            questions = [q for q in questions if q.get("category") == category]

        if not questions:
            await ctx.send(f"Sorry, I couldn't find any trivia questions for the '{category}' category.")
            return

        question_data = random.choice(questions)
        q_text = question_data["question"]
        q_answer = question_data["answer"]

        await ctx.send(f"**Trivia Time!**\n\n**Question:** {q_text}")

        def check(message: discord.Message) -> bool:
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            guess = await self.bot.wait_for("message", check=check, timeout=30.0)
            if guess.content.lower() == q_answer.lower():
                new_score = await self.db.trivia.increment_score(ctx.author.id, ctx.author.name)
                await ctx.send(f"Correct! 🎉 You now have {new_score} points.")
            else:
                await ctx.send(f"Sorry, that's incorrect. The correct answer was **{q_answer}**.")
        except asyncio.TimeoutError:
            await ctx.send(f"Time's up! The correct answer was **{q_answer}**.")

    @fun_group.command(name="leaderboard")
    async def leaderboard(self, ctx: commands.Context[Bot]) -> None:
        """Shows the trivia leaderboard."""
        leaderboard_data = await self.db.trivia.get_leaderboard(limit=10)

        if not leaderboard_data:
            await ctx.send("The leaderboard is empty! Play some trivia to get on it.")
            return

        embed = discord.Embed(title="🏆 Trivia Leaderboard", color=discord.Color.gold())

        for i, entry in enumerate(leaderboard_data):
            embed.add_field(name=f"{i+1}. {entry['username']}", value=f"**{entry['score']}** points", inline=False)

        await ctx.send(embed=embed)


    @fun_group.command(name="hug")
    async def hug(self, ctx: commands.Context[Bot], member: discord.Member) -> None:
        """Gives someone a hug."""
        gif_url = await self.get_random_gif("anime hug")
        embed = discord.Embed(description=f"{ctx.author.mention} hugs {member.mention}!", color=discord.Color.pink())
        if gif_url:
            embed.set_image(url=gif_url)
        await ctx.send(embed=embed)

    @fun_group.command(name="pat")
    async def pat(self, ctx: commands.Context[Bot], member: discord.Member) -> None:
        """Gives someone a pat."""
        gif_url = await self.get_random_gif("anime headpat")
        embed = discord.Embed(description=f"{ctx.author.mention} pats {member.mention}!", color=discord.Color.light_grey())
        if gif_url:
            embed.set_image(url=gif_url)
        await ctx.send(embed=embed)

    @fun_group.command(name="ship")
    async def ship(self, ctx: commands.Context[Bot], user1: discord.Member, user2: Optional[discord.Member] = None) -> None:
        """Calculates the love compatibility between two users."""
        partner = user2 or ctx.author

        # Seed random with user IDs for consistent results
        seed = user1.id + partner.id
        random.seed(seed)
        love_percent = random.randint(0, 100)
        random.seed() # Reset seed

        if love_percent < 33:
            emoji = "💔"
            comment = "Not a great match..."
        elif love_percent < 66:
            emoji = "🤔"
            comment = "There might be a chance!"
        else:
            emoji = "💖"
            comment = "A match made in heaven!"

        embed = discord.Embed(
            title="Love Calculator",
            description=f"**{user1.display_name}** + **{partner.display_name}** = **{love_percent}%** {emoji}\n\n{comment}",
            color=discord.Color.dark_red()
        )
        await ctx.send(embed=embed)

    @fun_group.command(name="rate")
    async def rate(self, ctx: commands.Context[Bot], *, thing_to_rate: str) -> None:
        """Rates something on a scale of 0 to 10."""
        rating = random.randint(0, 10)
        emoji = self.fun_data["rate_emojis"].get(str(rating), "🤔")
        await ctx.send(f"I rate **{thing_to_rate}** a **{rating}/10** {emoji}")

    @fun_group.command(name="pp")
    async def pp(self, ctx: commands.Context[Bot], member: Optional[discord.Member] = None) -> None:
        """Shows a user's 'pp' size. For fun!"""
        target = member or ctx.author
        size = random.choice(self.fun_data.get("pp_sizes", ["8=D"]))
        await ctx.send(f"{target.mention}'s pp: {size}")

    @fun_group.command(name="8ball")
    async def eightball(self, ctx: commands.Context[Bot], *, question: str) -> None:
        """Asks the magic 8-ball a question."""
        response = random.choice(self.fun_data.get("eightball_responses", ["Signs point to yes."]))
        await ctx.send(f"🎱 **Question:** {question}\n**Answer:** {response}")

    @fun_group.command(name="emojify")
    async def emojify(self, ctx: commands.Context[Bot], *, text: str) -> None:
        """Converts text into emoji letters."""
        emoji_text = ""
        for char in text.lower():
            if 'a' <= char <= 'z':
                emoji_text += f":regional_indicator_{char}: "
            elif '0' <= char <= '9':
                num_map = {'0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'}
                emoji_text += f":{num_map[char]}: "
            elif char == ' ':
                emoji_text += "  "
            else:
                emoji_text += char

        if len(emoji_text) > 2000:
            await ctx.send("That text is too long to emojify!")
        else:
            await ctx.send(emoji_text)

async def setup(bot: Bot) -> None:
    await bot.add_cog(FunCommands(bot))