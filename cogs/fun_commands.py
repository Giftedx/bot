import discord
from discord.ext import commands
import random
from typing import List, Dict
from dotenv import load_dotenv

class FunCommands(commands.Cog):
    """A collection of fun commands for entertainment"""
    
    def __init__(self, bot):
        self.bot = bot
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
            "僕が来た!\n*(I AM HERE!)* 💪",
            "掛かって来い!\n*(Come at me!)* ⚔️"
        ]
        self.DOUBT_GIFS = [
            "https://tenor.com/view/doubt-press-x-la-noire-gif-11674382",
            "https://tenor.com/view/doubt-x-gif-19284783",
            "https://tenor.com/view/la-noire-doubt-x-to-doubt-cole-phelps-gif-22997643"
        ]

    @commands.command(name='hello')
    async def hello(self, ctx):
        """Basic greeting"""
        embed = discord.Embed(
            title="Hello! 👋",
            description="This is your friendly neighborhood Discord-Plex bot!",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}")
        await ctx.send(embed=embed)
        await ctx.message.add_reaction('👋')

    @commands.command(name='nani')
    async def nani(self, ctx):
        """NANI?! response"""
        embed = discord.Embed(
            title="⚡ NANI?! ⚡",
            description=random.choice(self.NANI_RESPONSES),
            color=discord.Color.red()
        )
        reactions = ['💥', '⚡', '🗡️', '👊', '😱']
        for reaction in reactions:
            await ctx.message.add_reaction(reaction)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(FunCommands(bot))

class CustomBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=discord.Intents.all(),
            help_command=None
        )
        self.logger = BotLogger()
        self.rate_limiter = RateLimiter()

    async def setup_hook(self):
        """Initialize cogs and services when bot starts"""
        await self.load_extension('cogs.fun_commands')
        await self.load_extension('cogs.game_commands')
        await self.load_extension('cogs.plex_commands')

        # Initialize services
        self.plex = None
        self.text_channel = None
        self.chat_log = []

    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"Command on cooldown. Try again in {error.retry_after:.1f} seconds."
            )
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command!")
        else:
            self.logger.log_command(ctx, error)
            await ctx.send("An error occurred while processing your command.")

# --- Cooldown and Rate Limiting System ---
class RateLimiter:
    def __init__(self):
        self.command_cooldowns = {
            'train': 3600,  # 1 hour
            'daily': 86400,  # 24 hours
            'battle': 300,   # 5 minutes
            'shop': 60,      # 1 minute
            'adopt': 1800    # 30 minutes
        }
        self.user_cooldowns = defaultdict(dict)

    def check_cooldown(self, user_id: int, command: str) -> Tuple[bool, Optional[int]]:
        """Check if command is on cooldown. Returns (can_use, seconds_remaining)"""
        if command not in self.command_cooldowns:
            return True, None

        cooldown = self.command_cooldowns[command]
        last_used = self.user_cooldowns[user_id].get(command)

        if not last_used:
            return True, None

        time_passed = (datetime.now() - last_used).total_seconds()
        if time_passed < cooldown:
            return False, int(cooldown - time_passed)

        return True, None

    def update_cooldown(self, user_id: int, command: str):
        """Update the cooldown for a command"""
        self.user_cooldowns[user_id][command] = datetime.now()

# Add cooldown decorator
def cooldown(command_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, ctx: commands.Context, *args, **kwargs):
            can_use, time_left = bot.rate_limiter.check_cooldown(ctx.author.id, command_name)

            if not can_use:
                minutes = int(time_left / 60)
                seconds = time_left % 60
                await ctx.send(
                    f"This command is on cooldown. Try again in "
                    f"{minutes} minutes and {seconds} seconds."
                )
                return

            try:
                result = await func(self, ctx, *args, **kwargs)
                bot.rate_limiter.update_cooldown(ctx.author.id, command_name)
                return result
            except Exception as e:
                bot_logger.log_command(ctx, e)
                await ctx.send("An error occurred while processing your command.")

        return wrapper
    return decorator

# --- Enhanced Error Handling and Logging ---
class BotLogger:
    def __init__(self):
        self.logger = logging.getLogger('DiscordBot')
        self.logger.setLevel(logging.INFO)

        # File handler
        file_handler = RotatingFileHandler(
            'bot_logs/discord_bot.log',
            maxBytes=5_000_000,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(levelname)s: %(message)s'
        ))

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log_command(self, ctx: commands.Context, error: Optional[Exception] = None):
        """Log command usage and any errors"""
        command_name = ctx.command.name if ctx.command else 'Unknown'
        msg = f"Command '{command_name}' used by {ctx.author} (ID: {ctx.author.id})"

        if error:
            self.logger.error(f"{msg} - Error: {str(error)}\n{traceback.format_exc()}")
        else:
            self.logger.info(msg)

    def log_event(self, event_name: str, details: Any):
        """Log Discord events"""
        self.logger.info(f"Event '{event_name}' occurred: {details}")

# Initialize logger
bot_logger = BotLogger()

# --- Enhanced Logging Setup ---
def setup_logging():
    logger = logging.getLogger('discord_bot')
    logger.setLevel(logging.INFO)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        'discord_bot.log',
        maxBytes=5_000_000,  # 5MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(message)s'
    ))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logging()

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEXT_CHANNEL_ID = int(os.getenv('DISCORD_TEXT_CHANNEL_ID', '0'))
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

# Configure bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True  # Added for member-related features

bot = CustomBot()
plex = None  # Initialize plex object
text_channel = None # initialize global text_channel object
chat_log = []

# --- Constants for Fun Responses ---
NANI_RESPONSES = [
    "お前はもう死んでいる。\n*(Omae wa mou shindeiru)*\n**NANI?!** 💥",
    "*teleports behind you*\nNothing personal, kid... 🗡️",
    "このDIOだ!\n*(KONO DIO DA!)* 🧛‍♂️",
    "MUDA MUDA MUDA MUDA! 👊",
    "ROAD ROLLER DA! 🚛",
    "ゴゴゴゴ\n*(Menacing...)* ゴゴゴゴ",
    "やれやれだぜ...\n*(Yare yare daze...)* 🎭",
    "NANI?! BAKANA! MASAKA! 😱",
    "You expect me to believe that?",
    "Why don't you tell me what REALLY happened?",
    "*flips notebook dramatically* Something's not right here..."
]
EVIDENCE_TYPES = [
    "👞 Suspicious footprints",
    "🚬 Half-smoked cigarette",
    "📱 Mysterious phone call",
    "💼 Missing briefcase",
    "🗝️ Unknown key",
    "📝 Torn note",
    "🎭 False alibi",
    "🎲 Loaded dice",
    "💄 Lipstick stain",
    "🎩 Abandoned hat"
]
WIZARD_SPELLS = [
    "*Wingardium Leviosa!* `(Your messages float up)` ⬆️",
    "*Lumos!* `(The chat brightens)` 💡",
    "*Expecto Patronum!* `(A spirit animal appears)` 🦌",
    "*Alohomora!* `(Unlocks hidden channels)` 🔓",
    "*Riddikulus!* `(Turns fear into laughter)` 😂"
]
WIZARD_HOUSES = {
    "Gryffindor": "🦁 Brave and chivalrous!",
    "Hufflepuff": "🦡 Loyal and dedicated!",
    "Ravenclaw": "🦅 Wise and creative!",
    "Slytherin": "🐍 Cunning and ambitious!"
}
WIZARD_QUOTES = [
    "You're a wizard, {user}!",
    "Mischief managed!",
    "I solemnly swear that I am up to no good...",
    "Ten points to {house}!",
    "Alas, earwax!"
]

# Game Systems - Base Enums and Classes
class PetType(Enum):
    FIRE = "🔥"
    WATER = "💧"
    EARTH = "🌍"
    AIR = "💨"
    LIGHT = "✨"
    DARK = "🌑"

class StatusEffect(Enum):
    BURN = "🔥"
    POISON = "🤢"
    PARALYZE = "⚡"
    SLEEP = "💤"
    NONE = ""

@dataclass
class PetMove:
    name: str
    damage: int
    element: PetType
    accuracy: int
    cooldown: int
    emoji: str
    status_effect: StatusEffect = StatusEffect.NONE
    status_chance: int = 0
    current_cooldown: int = 0

@dataclass
class BattlePet:
    pet: 'Pet'
    moves: List[PetMove]
    current_hp: int
    max_hp: int
    element: PetType
    status: StatusEffect = StatusEffect.NONE
    status_turns: int = 0

    def apply_status(self, effect: StatusEffect, turns: int = 3):
        self.status = effect
        self.status_turns = turns

    def update_status(self):
        if self.status_turns > 0:
            self.status_turns -= 1
            if self.status_turns == 0:
                self.status = StatusEffect.NONE

# --- Game Systems and Pet Battle ---
@dataclass
class Pet:
    name: str
    element: PetType
    level: int = 1
    experience: int = 0
    moves: List<PetMove> = field(default_factory=list)
    health: int = 100
    max_health: int = 100

    def __post_init__(self):
        if not self.moves:
            self.moves = generate_moves_for_element(self.element)

    def add_experience(self, amount: int) -> bool:
        """Returns True if leveled up"""
        self.experience += amount
        if self.experience >= self.level * 100:
            self.level_up()
            return True
        return False

    def level_up(self):
        self.level += 1
        self.experience = 0
        self.max_health += 10
        self.health = self.max_health

@dataclass
class PlayerData:
    user_id: int
    pets: List['Pet'] = field(default_factory=list)
    coins: int = 1000
    inventory: Dict[str, int] = field(default_factory=dict)
    active_pet: Optional[int] = None
    last_daily: Optional[datetime] = None

    def can_claim_daily(self) -> bool:
        if not self.last_daily:
            return True
        return datetime.now() - self.last_daily > timedelta(days=1)

@dataclass
class Item:
    name: str
    description: str
    price: int
    emoji: str
    effect: Optional[str] = None

class Shop:
    def __init__(self):
        self.items = [
            Item("Health Potion", "Restores 50 HP", 100, "🧪"),
            Item("Experience Boost", "2x EXP for 1 hour", 200, "⭐"),
            Item("Element Stone", "Change pet's element", 500, "💎"),
            Item("Revival Token", "Revive fainted pet", 1000, "💫")
        ]
        self.refresh_time = datetime.now()

    def refresh_inventory(self):
        self.refresh_time = datetime.now() + timedelta(hours=1)

@dataclass
class BotConfig:
    prefix: str = "!"
    version: str = "1.0"
    cooldown: int = 60
    max_inventory: int = 50
    shop_refresh_hours: int = 1
    starting_coins: int = 1000

@dataclass
class Achievement:
    name: str
    description: str
    reward: int
    completed: bool = False
    progress: int = 0
    target: int = 1

@dataclass
class Quest:
    name: str
    description: str
    reward: int
    type: str
    target: int
    progress: int = 0
    completed: bool = False
    expiry: Optional[datetime] = None

# --- Level System ---
class LevelSystem:
    def __init__(self):
        self.levels = {}
        self.xp_per_message = 5
        self.level_threshold = 100

    def add_xp(self, user_id: int, amount: int) -> Optional[int]:
        if user_id not in self.levels:
            self.levels[user_id] = {"xp": 0, "level": 1}

        self.levels[user_id]["xp"] += amount
        current_xp = self.levels[user_id]["xp"]
        current_level = self.levels[user_id]["level"]

        if current_xp >= current_level * self.level_threshold:
            self.levels[user_id]["level"] += 1
            self.levels[user_id]["xp"] = 0
            return self.levels[user_id]["level"]
        return None

    def get_level(self, user_id: int) -> dict:
        return self.levels.get(user_id, {"xp": 0, "level": 1})

# --- Combat System ---
@dataclass
class Battle:
    player1_id: int
    player2_id: int
    pet1: Pet
    pet2: Pet
    current_turn: int = 1
    last_move: Optional[str] = None
    status: str = "active"

    def get_current_player(self) -> int:
        return self.player1_id if self.current_turn % 2 == 1 else self.player2_id

    def get_current_pet(self) -> Pet:
        return self.pet1 if self.current_turn % 2 == 1 else self.pet2

    def get_opponent_pet(self) -> Pet:
        return self.pet2 if self.current_turn % 2 == 1 else self.pet1

class BattleManager:
    def __init__(self):
        self.active_battles: Dict[int, Battle] = {}
        self.battle_requests: Dict[int, Tuple[int, int]] = {}  # channel_id: (challenger_id, target_id)

    def create_battle(self, channel_id: int, player1_id: int, player2_id: int, pet1: Pet, pet2: Pet) -> Battle:
        battle = Battle(player1_id, player2_id, pet1, pet2)
        self.active_battles[channel_id] = battle
        return battle

    def end_battle(self, channel_id: int):
        if channel_id in self.active_battles:
            del self.active_battles[channel_id]

# --- Trading and Economy Systems ---
@dataclass
class Trade:
    initiator_id: int
    target_id: int
    initiator_items: List[Item] = field(default_factory=list)
    target_items: List[Item] = field(default_factory.list)
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)

    def validate(self) -> bool:
        return len(self.initiator_items) > 0 or len(self.target_items) > 0

class TradeManager:
    def __init__(self):
        self.active_trades: Dict[int, Trade] = {}

    async def create_trade(self, ctx: commands.Context, target: discord.Member) -> Optional[Trade]:
        if ctx.author.id == target.id:
            await ctx.send("You can't trade with yourself!")
            return None

        trade = Trade(ctx.author.id, target.id)
        self.active_trades[ctx.channel.id] = trade
        return trade

    async def cancel_trade(self, ctx: commands.Context):
        if ctx.channel.id in self.active_trades:
            del self.active_trades[ctx.channel.id]
            await ctx.send("Trade cancelled.")

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trade_manager = TradeManager()

    @commands.hybrid_command()
    async def balance(self, ctx: commands.Context):
        """Check your current balance"""
        player_data = await self.get_player_data(ctx.author.id)
        embed = discord.Embed(
            title="💰 Balance",
            description=f"You have {player_data.coins} coins",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def daily(self, ctx: commands.Context):
        """Claim your daily reward"""
        player_data = await self.get_player_data(ctx.author.id)
        if player_data.can_claim_daily():
            coins = random.randint(100, 500)
            player_data.coins += coins
            player_data.last_daily = datetime.now()
            await self.save_player_data(player_data)

            embed = discord.Embed(
                title="Daily Reward! 🎁",
                description=f"You received {coins} coins!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            time_left = timedelta(days=1) - (datetime.now() - player_data.last_daily)
            await ctx.send(f"You can claim your next daily reward in {time_left.seconds//3600} hours!")

    @commands.hybrid_command()
    async def trade(self, ctx: commands.Context, member: discord.Member):
        """Start a trade with another member"""
        trade = await self.trade_manager.create_trade(ctx, member)
        if trade:
            embed = discord.Embed(
                title="🤝 Trade Request",
                description=f"{ctx.author.mention} wants to trade with {member.mention}!",
                color=discord.Color.blue()
            )
            msg = await ctx.send(embed=embed, view=TradeView(self.trade_manager, trade))
            await msg.add_reaction('🤝')

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.refresh_stock.start()
        self.items = []
        self.refresh_inventory()

    def cog_unload(self):
        self.refresh_stock.cancel()

    @tasks.loop(hours=1)
    async def refresh_stock(self):
        self.refresh_inventory()

    def refresh_inventory(self):
        """Refreshes shop inventory with random items"""
        basic_items = [
            Item("Health Potion", "Restores 50 HP", 100, "🧪"),
            Item("Mana Potion", "Restores 50 MP", 100, "🔮"),
            Item("Experience Scroll", "2x EXP for 1 hour", 500, "📜"),
            Item("Pet Food", "Feeds your pet", 50, "🥩"),
            Item("Training Weight", "Boosts training gains", 300, "🏋️"),
            Item("Element Stone", "Change pet's element", 1000, "💎")
        ]
        rare_items = [
            Item("Golden Ticket", "Special rewards", 5000, "🎫"),
            Item("Rainbow Crystal", "Rare pet evolution", 10000, "🌈"),
            Item("Time Turner", "Reset daily cooldowns", 2000, "⌛")
        ]
        self.items = basic_items + random.sample(rare_items, k=2)

    @commands.hybrid_command()
    async def shop(self, ctx: commands.Context):
        """Display the shop inventory"""
        embed = discord.Embed(
            title="🏪 Shop",
            description="Welcome to the shop! Use `!buy <item>` to purchase.",
            color=discord.Color.green()
        )

        for item in self.items:
            embed.add_field(
                name=f"{item.emoji} {item.name}",
                value=f"Price: {item.price} coins\n{item.description}",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def buy(self, ctx: commands.Context, *, item_name: str):
        """Buy an item from the shop"""
        player_data = await self.bot.get_player_data(ctx.author.id)

        item = next((i for i in self.items if i.name.lower() == item_name.lower()), None)
        if not item:
            await ctx.send("Item not found in shop!")
            return

        if player_data.coins < item.price:
            await ctx.send("You don't have enough coins!")
            return

        player_data.coins -= item.price
        player_data.inventory[item.name] = player_data.inventory.get(item.name, 0) + 1
        await self.bot.save_player_data(player_data)

        embed = discord.Embed(
            title="Purchase Successful!",
            description=f"You bought {item.emoji} {item.name} for {item.price} coins!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def inventory(self, ctx: commands.Context):
        """Display your inventory"""
        player_data = await self.bot.get_player_data(ctx.author.id)

        embed = discord.Embed(
            title="🎒 Inventory",
            description=f"Coins: {player_data.coins} 💰",
            color=discord.Color.blue()
        )

        if not player_data.inventory:
            embed.add_field(name="Items", value="Your inventory is empty!")
        else:
            items_text = "\n".join(f"{name} x{count}" for name, count in player_data.inventory.items())
            embed.add_field(name="Items", value=items_text)

        await ctx.send(embed=embed)

# --- Utility Functions ---
async def get_chat_history(channel):
    try:
        messages = []
        async for msg in channel.history(limit=1000):
            messages.append(msg)
        return messages
    except discord.errors.Forbidden:
        print(f"Error: No permission to read history in {channel.name}")
        return None
    except Exception as e:
        print(f"Error retrieving history from {channel.name}: {e}")
        return None

# --- Bot Events ---
@bot.event
async def on_ready():
    global plex, text_channel
    bot_logger.logger.info(f"Bot connected as {bot.user.name}")
    print(f"\nBehold, mortals! {bot.user} has connected to Discord!")
    await bot.change_presence(activity=discord.Game(name="Plex with friends"))
    text_channel = bot.get_channel(TEXT_CHANNEL_ID)
    if text_channel:
        print(f"Listening for commands in channel: {text_channel.name} ({text_channel.id})")
    for reaction in reactions:
        await ctx.message.add_reaction(reaction)

@bot.command(name='doubt')
async def doubt(ctx):
    class DoubtButtons(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30)

        @discord.ui.button(label="Press X", style=discord.ButtonStyle.danger)
        async def press_x(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message(random.choice(DOUBT_RESPONSES))

        @discord.ui.button(label="Interrogate 🔍", style=discord.ButtonStyle.secondary)
        async def interrogate(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message(random.choice(LA_NOIRE_QUOTES))

    doubt_evidence = discord.Embed(
        title="🚨 DOUBT FILED - CASE #" + ''.join(random.choices('0123456789', k=4)),
        description="A new case of doubt has been registered at the Los Santos Police Department",
        color=discord.Color.red()
    )
    doubt_evidence.add_field(
        name="Investigating Officer",
        value=f"Detective {ctx.author.name}\nBadge #" + ''.join(random.choices('0123456789', k=6))
    )
    doubt_evidence.add_field(
        name="Doubt Level",
        value=random.choice([
            "🔴 EXTREME DOUBT",
            "🟡 SUBSTANTIAL DOUBT",
            "🟢 REASONABLE DOUBT",
            "⚫ TERMINAL DOUBT"
        ])
    )
    doubt_evidence.add_field(
        name="Evidence Collected",
        value='\n'.join(random.sample(EVIDENCE_TYPES, 3)),
        inline=False
    )
    doubt_evidence.set_footer(
        text="LA Noire Detective Bureau | 'Press X to Doubt' Division | Est. 1947"
    )
    doubt_evidence.set_image(url=random.choice(DOUBT_GIFS))

    thread = await ctx.message.create_thread(
        name=f"Case #{random.randint(100, 999)} - Ongoing Investigation",
        auto_archive_duration=60
    )
    await ctx.send(embed=doubt_evidence, view=DoubtButtons())
    await thread.send(
        "*Detective's Notes:* A new investigation has been opened. Press X to register your doubt, "
        "or use the Interrogate button to question the suspect."
    )
    doubt_reactions = ['🚔', '🕵️', '❌', '🔍', '📝']
    for reaction in doubt_reactions:
        await ctx.message.add_reaction(reaction)

@bot.command(name='wizard')
async def wizard(ctx):
    class SpellButtons(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30)

        @discord.ui.button(label="Cast Spell ✨", style=discord.ButtonStyle.primary)
        async def cast_spell(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message(random.choice(WIZARD_SPELLS))

        @discord.ui.button(label="Summon Hat 🎩", style=discord.ButtonStyle.secondary)
        async def sorting_hat(self, interaction: discord.Interaction, button: discord.ui.Button):
            house = random.choice(list(WIZARD_HOUSES.keys()))
            await interaction.response.send_message(
                f"*The Sorting Hat has chosen...* **{house}**! {WIZARD_HOUSES[house]}"
            )

    embed = discord.Embed(
        title="🧙‍♂️ Wizarding Academy of Plex and Discord",
        description="A wild wizard appears! What magical feats shall we perform today?",
        color=discord.Color.purple()
    )
    embed.add_field(
        name="Ancient Words",
        value=random.choice(WIZARD_QUOTES).format(
            user=ctx.author.name,
            house=random.choice(list(WIZARD_HOUSES.keys()))
        )
    )
    wizard_level = random.randint(1, 100)
    embed.add_field(
        name="Wizard Stats",
        value=f"Level: {wizard_level}\nExperience: {wizard_level * 100}/10000"
    )
    thread = await ctx.message.create_thread(
        name=f"{ctx.author.name}'s Spell Practice",
        auto_archive_duration=60
    )
    await ctx.send(embed=embed, view=SpellButtons())
    await thread.send(
        "Welcome to spell practice! Cast spells here without disturbing the main chat."
    )
    magical_reactions = ['🧙‍♂️', '✨', '🔮', '⚡', '🎩']
    for reaction in magical_reactions:
        await ctx.message.add_reaction(reaction)

@bot.command(name='rickroll')
async def rickroll(ctx):
    embed = discord.Embed(title="🎵 You've been Rick Rolled! 🎵", color=discord.Color.red())
    embed.add_field(name="Never gonna:", value="- Give you up\n- Let you down\n- Run around\n- Desert you", inline=False)
    embed.add_field(name="Never gonna:", value="- Make you cry\n- Say goodbye\n- Tell a lie\n- Hurt you", inline=False)
    embed.set_thumbnail(url="https://i.imgur.com/dQw4w9w.jpg")
    await ctx.send(embed=embed)
    await ctx.message.add_reaction('🎵')

@bot.command(name='cowbell')
async def cowbell(ctx):
    bell_count = random.randint(1, 10)
    bells = "🔔" * bell_count
    embed = discord.Embed(
        title="I GOT A FEVER!",
        description=f"And the only prescription is...\n{bells}\nMORE COWBELL!",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)
    await ctx.message.add_reaction('🔔')

@bot.command(name='peepee')
async def peepee(ctx):
    PEEPEE_SIZES = [
        "8D",
        "8=D",
        "8==D",
        "8===D",
        "8====D",
        "8=====D",
        "8======D",
        "8=======D",
        "8========D",
        "ERROR: TOO LARGE TO DISPLAY 😳"
    ]
    size = random.choice(PEEPEE_SIZES)
    embed = discord.Embed(
        title="PP Size Calculator",
        description=f"Your PP size is:\n```\n{size}\n```",
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)
    await ctx.message.add_reaction('📏')

@bot.command(name='fortnite')
async def fortnite(ctx):
    responses = [
        "Victory Royale! 🏆",
        "Where we dropping boys? 🪂",
        "*default dances* 💃",
        "Squad up! 👥",
        "*builds aggressively* 🏗️"
    ]
    response = random.choice(responses)
    embed = discord.Embed(description=response, color=discord.Color.green())
    await ctx.send(embed=embed)
    await ctx.message.add_reaction('🎮')

@bot.command(name='beans')
async def beans(ctx):
    bean_types = ["🫘", "🫛", "🥫"]
    bean_count = random.randint(3, 10)
    beans = " ".join(random.choices(bean_types, k=bean_count))
    embed = discord.Embed(
        title="Bean Adequacy Check",
        description=f"Bean level: {beans}\nVerdict: ADEQUATE",
        color=discord.Color.from_rgb(139, 69, 19)
    )
    await ctx.send(embed=embed)
    await ctx.message.add_reaction('🫘')

@bot.command(name='lol')
async def lol(ctx):
    responses = [
        "lmao 🤣",
        "rofl 🤣",
        "lmfao 🤣",
        "*wheeze* 😂",
        "kekw"
    ]
    await ctx.send(random.choice(responses))
    await ctx.message.add_reaction('🤣')

@bot.command(name='triggered')
async def triggered(ctx):
    embed = discord.Embed(
        title="TRIGGERED",
        description="*angry NPC noises* 😤",
        color=discord.Color.red()
    )
    embed.set_image(url="https://tenor.com/view/triggered-trigger-triggered-gif-gif-8974546")
    await ctx.send(embed=embed)
    await ctx.message.add_reaction('😤')

@bot.command(name='yelling')
async def yelling(ctx):
    responses = [
        "WHY ARE WE YELLING?! 📢",
        "LOUD NOISES! 📣",
        "I DON'T KNOW WHAT WE'RE YELLING ABOUT! 🗣️",
        "AHHHHHHHHHHH! 😱",
        "*incoherent screaming* 🙀"
    ]
    response = random.choice(responses)
    embed = discord.Embed(description=response, color=discord.Color.orange())
    await ctx.send(embed=embed)
    await ctx.message.add_reaction('📢')

@bot.command(name='noot')
async def noot(ctx):
    embed = discord.Embed(
        title="🐧 NOOT NOOT! 🐧",
        description="*angry penguin noises*",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)
    await ctx.message.add_reaction('🐧')

@bot.command(name='sad')
async def sad(ctx):
    responses = ["😭", "😢", "😪", "😥", "*sobs uncontrollably*"]
    await ctx.send(random.choice(responses))
    await ctx.message.add_reaction('😭')

@bot.command(name='coffee')
async def coffee(ctx):
    coffee_types = ["☕", "🫖", "🍵"]
    embed = discord.Embed(
        title="Coffee Time!",
        description=f"{random.choice(coffee_types)} Coffee first, everything else second.",
        color=discord.Color.from_rgb(139, 69, 19)
    )
    await ctx.send(embed=embed)
    await ctx.message.add_reaction('☕')

@bot.command(name='banana')
async def banana(ctx):
    BANANA_RESPONSES = [
        "🎵 IT'S PEANUT BUTTER JELLY TIME! 🎵",
        "PEANUT BUTTER JELLY! PEANUT BUTTER JELLY! 🍌",
        "*dancing banana intensifies* 🍌💃",
        "WHERE HE AT? WHERE HE AT? WHERE HE AT? WHERE HE AT? 👀",
        "DO THE PEANUT BUTTER JELLY! PEANUT BUTTER JELLY! 🥜"
    ]
    response = random.choice(BANANA_RESPONSES)
    embed = discord.Embed(
        title="🍌 PEANUT BUTTER JELLY TIME! 🍌",
        description=response,
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)
    await ctx.message.add_reaction('🍌')

# --- Plex Commands (placeholders) ---
@bot.command(name='play')
async def play(ctx, *, query):
    if not plex:
        await ctx.send("Plex server not connected. Try again later.")
        return
    try:
        results = plex.library.search(query, limit=1)
        if results:
            await ctx.send(f"Found: {results[0].title}")  # Basic feedback
        else:
            await ctx.send("No results found.")
    except Exception as e:
        await ctx.send(f"Error searching Plex: {e}")

@bot.command(name='search')
async def search(ctx, *, query):
    if not plex:
        await ctx.send("Plex server not connected. Try again later.")
        return
    try:
        results = plex.library.search(query, limit=5)
        if results:
            response = "Found:\n" + "\n".join([f"- {item.title}" for item in results])
            await ctx.send(response)
        else:
            await ctx.send("No results found.")
    except Exception as e:
        await ctx.send(f"Error searching Plex: {e}")

# --- Help Command ---
@bot.command(name='help')
async def help(ctx):
    embed = discord.Embed(
        title="Available Commands",
        description="Here are all the fun commands you can use!",
        color=discord.Color.blue()
    )

    fun_commands = """`!hello` - Basic greeting
`!wizard` - Magical greeting
`!rickroll` - Never gonna give you up...
`!doubt` - X to doubt
`!nani` - Omae wa mou shindeiru
`!cowbell` - More cowbell
`!peepee` - PP size check
`!fortnite` - Gaming preference
`!beans` - Bean adequacy check
`!lol` - lmao
`!triggered` - 🤣
`!yelling` - WHY ARE WE YELLING?
`!noot` - Pingu's greeting
`!sad` - 😭
`!coffee` - Coffee first
`!banana` - Peanut butter jelly time!"""
    embed.add_field(name="Fun Commands", value=fun_commands, inline=False)

    plex_commands = """`!play <query>` - Play media matching query
`!search <query>` - Search for media"""
    embed.add_field(name="Plex Commands", value=plex_commands, inline=False)

    game_commands = """`!adopt <name>` - Adopt a new pet
`!pets` - View your pets
`!train` - Train your active pet
`!battle <@user>` - Challenge someone to a pet battle
`!shop` - View available items
`!inventory` - Check your inventory
`!daily` - Claim daily reward
`!quests` - View active quests"""
    embed.add_field(name="Game Commands", value=game_commands, inline=False)

    embed.set_footer(text=f"Requested by {ctx.author.name} | Bot Version 1.0")

    await ctx.send(embed=embed)

class Quest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_quests = {}
        self.check_quests.start()

    def cog_unload(self):
        self.check_quests.cancel()

    @tasks.loop(minutes=5)
    async def check_quests(self):
        """Check and update quest progress"""
        current_time = datetime.now()
        expired_quests = []

        for user_id, quests in self.active_quests.items():
            for quest in quests[:]:  # Copy list for safe iteration
                if quest.expiry and current_time > quest.expiry:
                    expired_quests.append((user_id, quest))
                    quests.remove(quest)

        for user_id, quest in expired_quests:
            if user := self.bot.get_user(user_id):
                await user.send(f"Quest expired: {quest.name}")

    @commands.hybrid_command()
    async def daily_quest(self, ctx: commands.Context):
        """Get a new daily quest"""
        player_data = await self.bot.get_player_data(ctx.author.id)

        daily_quests = [
            Quest("Message Master", "Send 10 messages", 100, "message", 10),
            Quest("Pet Trainer", "Train your pet 3 times", 150, "train", 3),
            Quest("Shop Till You Drop", "Buy 2 items from shop", 200, "shop", 2),
            Quest("Social Butterfly", "React to 5 messages", 75, "react", 5)
        ]

        new_quest = random.choice(daily_quests)
        new_quest.expiry = datetime.now() + timedelta(days=1)

        if ctx.author.id not in self.active_quests:
            self.active_quests[ctx.author.id] = []

        self.active_quests[ctx.author.id].append(new_quest)

        embed = discord.Embed(
            title="📜 New Daily Quest!",
            description=f"**{new_quest.name}**\n{new_quest.description}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Reward", value=f"{new_quest.reward} coins")
        embed.add_field(name="Expires", value="in 24 hours")

        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def quests(self, ctx: commands.Context):
        """View your active quests"""
        if ctx.author.id not in self.active_quests or not self.active_quests[ctx.author.id]:
            await ctx.send("You have no active quests! Use `!daily_quest` to get one.")
            return

        embed = discord.Embed(
            title="📋 Active Quests",
            color=discord.Color.blue()
        )

        for quest in self.active_quests[ctx.author.id]:
            progress = f"{quest.progress}/{quest.target}"
            time_left = quest.expiry - datetime.now() if quest.expiry else "No expiry"

            embed.add_field(
                name=quest.name,
                value=f"{quest.description}\nProgress: {progress}\nReward: {quest.reward} coins\nTime left: {time_left}",
                inline=False
            )

        await ctx.send(embed=embed)

class Achievement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.achievements = {
            "First Steps": Achievement("First Steps", "Use your first command", 100),
            "Social Butterfly": Achievement("Social Butterfly", "React to 50 messages", 250),
            "Pet Master": Achievement("Pet Master", "Raise a pet to level 10", 500),
            "Shop Addict": Achievement("Shop Addict", "Spend 10000 coins", 1000),
            "Quest Hero": Achievement("Quest Hero", "Complete 10 quests", 750)
        }
        self.check_achievements.start()

    def cog_unload(self):
        self.check_achievements.cancel()

    @tasks.loop(minutes=1)
    async def check_achievements(self):
        """Periodically check for completed achievements"""
        for guild in self.bot.guilds:
            for member in guild.members:
                player_data = await self.bot.get_player_data(member.id)
                if not player_data:
                    continue

                await self.check_player_achievements(member, player_data)

    async def check_player_achievements(self, member: discord.Member, player_data: 'PlayerData'):
        """Check achievements for a specific player"""
        if not hasattr(player_data, 'achievements'):
            player_data.achievements = {}
        # Check various achievement conditions
        if "First Steps" not in player_data.achievements:
            await self.award_achievement(member, "First Steps")
        if (hasattr(player_data, 'reaction_count') and
            player_data.reaction_count >= 50 and
            "Social Butterfly" not in player_data.achievements):
            await self.award_achievement(member, "Social Butterfly")
        # Check pet-related achievements
        if any(pet.level >= 10 for pet in player_data.pets):
            await self.award_achievement(member, "Pet Master")
        # Check spending achievements
        if hasattr(player_data, 'total_spent') and player_data.total_spent >= 10000:
            await self.award_achievement(member, "Shop Addict")
        # Check quest achievements
        if hasattr(player_data, 'quests_completed') and player_data.quests_completed >= 10:
            await self.award_achievement(member, "Quest Hero")

    async def award_achievement(self, member: discord.Member, achievement_name: str):
        """Award an achievement to a player"""
        player_data = await self.bot.get_player_data(member.id)
        if not player_data or achievement_name in player_data.achievements:
            return
        achievement = self.achievements[achievement_name]
        player_data.achievements[achievement_name] = datetime.now()
        player_data.coins += achievement.reward
        await self.bot.save_player_data(player_data)
        embed = discord.Embed(
            title="🏆 Achievement Unlocked!",
            description=f"**{achievement_name}**\n{achievement.description}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Reward", value=f"{achievement.reward} coins")

        if member.dm_channel:
            await member.dm_channel.send(embed=embed)
        else:
            dm_channel = await member.create_dm()
            await dm_channel.send(embed=embed)

    @commands.hybrid_command()
    async def achievements(self, ctx: commands.Context):
        """View your achievements"""
        player_data = await self.bot.get_player_data(ctx.author.id)
        if not player_data or not hasattr(player_data, 'achievements'):
            await ctx.send("You haven't earned any achievements yet!")
            return
        embed = discord.Embed(
            title="🏆 Achievements",
            description=f"Achievements earned by {ctx.author.name}",
            color=discord.Color.gold()
        )
        for name, timestamp in player_data.achievements.items():
            achievement = self.achievements[name]
            embed.add_field(
                name=f"{name} 🏅",
                value=f"{achievement.description}\nEarned: {timestamp.strftime('%Y-%m-%d')}",
                inline=False
            )
        await ctx.send(embed=embed)

# --- Level and Experience System ---
class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_cooldowns = {}
        self.check_level_ups.start()

    def cog_unload(self):
        self.check_level_ups.cancel()

    @tasks.loop(minutes=1)
    async def check_level_ups(self):
        """Check for level ups periodically"""
        for guild in self.bot.guilds:
            for member in guild.members:
                player_data = await self.bot.get_player_data(member.id)
                if player_data and player_data.xp >= self.calculate_xp_needed(player_data.level):
                    await self.level_up(member, player_data)

    def calculate_xp_needed(self, level: int) -> int:
        """Calculate XP needed for next level"""
        return 100 * (level ** 1.5)

    async def add_xp(self, member: discord.Member, amount: int):
        """Add XP to a member"""
        now = datetime.now()
        if member.id in self.xp_cooldowns:
            if now - self.xp_cooldowns[member.id] < timedelta(minutes=1):
                return

        self.xp_cooldowns[member.id] = now
        player_data = await self.bot.get_player_data(member.id)
        player_data.xp += amount
        await self.bot.save_player_data(player_data)

        if player_data.xp >= self.calculate_xp_needed(player_data.level):
            await self.level_up(member, player_data)

    async def level_up(self, member: discord.Member, player_data: 'PlayerData'):
        """Handle level up event"""
        old_level = player_data.level
        player_data.level += 1
        player_data.xp = 0
        coins_reward = player_data.level * 100
        player_data.coins += coins_reward
        await self.bot.save_player_data(player_data)
        embed = discord.Embed(
            title="🎉 Level Up!",
            description=f"{member.mention} has reached level {player_data.level}!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Rewards", value=f"+ {coins_reward} coins")

        if channel := member.guild.system_channel:
            await channel.send(embed=embed)

    @commands.hybrid_command()
    async def level(self, ctx: commands.Context):
        """Check your current level and XP"""
        player_data = await self.bot.get_player_data(ctx.author.id)
        xp_needed = self.calculate_xp_needed(player_data.level)
        progress = (player_data.xp / xp_needed) * 100
        embed = discord.Embed(
            title=f"Level Status for {ctx.author.name}",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Current Level",
            value=f"Level {player_data.level}",
            inline=False
        )
        embed.add_field(
            name="Experience",
            value=f"{player_data.xp}/{xp_needed} XP ({progress:.1f}%)",
            inline=False
        )
        embed.add_field(
            name="Total Coins",
            value=f"{player_data.coins} 💰",
            inline=False
        )

        await ctx.send(embed=embed)

# --- Pet System and Battles ---
class PetCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_battles = {}

    @commands.hybrid_command()
    async def adopt(self, ctx: commands.Context, pet_name: str):
        """Adopt a new pet"""
        player_data = await self.bot.get_player_data(ctx.author.id)
        if len(player_data.pets) >= 3:
            await ctx.send("You can't have more than 3 pets!")
            return
        element = random.choice(list(PetType))
        new_pet = Pet(
            name=pet_name,
            element=element,
            level=1,
            experience=0
        )
        player_data.pets.append(new_pet)
        await self.bot.save_player_data(player_data)
        embed = discord.Embed(
            title="🎉 New Pet Adopted!",
            description=f"Welcome {pet_name} to the family!",
            color=discord.Color.green()
        )
        embed.add_field(name="Element", value=f"{element.value} {element.name}")
        embed.add_field(name="Level", value="1")
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def pets(self, ctx: commands.Context):
        """View your pets"""
        player_data = await self.bot.get_player_data(ctx.author.id)
        if not player_data.pets:
            await ctx.send("You don't have any pets yet! Use `!adopt` to get one.")
            return
        embed = discord.Embed(
            title="🐾 Your Pets",
            color=discord.Color.blue()
        )
        for pet in player_data.pets:
            embed.add_field(
                name=f"{pet.element.value} {pet.name}",
                value=f"Level: {pet.level}\nXP: {pet.experience}/100\nHealth: {pet.health}/{pet.max_health}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @cooldown('battle')
    async def battle(self, ctx: commands.Context, opponent: discord.Member):
        """Challenge another player to a pet battle"""
        if opponent.id == ctx.author.id:
            await ctx.send("You can't battle yourself!")
            return
        player1_data = await self.bot.get_player_data(ctx.author.id)
        player2_data = await self.bot.get_player_data(opponent.id)
        if not player1_data.pets or not player2_data.pets:
            await ctx.send("Both players need to have pets to battle!")
            return
        embed = discord.Embed(
            title="⚔️ Pet Battle Challenge!",
            description=f"{ctx.author.mention} challenges {opponent.mention} to a pet battle!",
            color=discord.Color.red()
        )
        class BattleButtons(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)

            @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
            async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != opponent.id:
                    await interaction.response.send_message("This isn't your battle to accept!", ephemeral=True)
                    return
                await self.start_battle(ctx, player1_data, player2_data)

            @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
            async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != opponent.id:
                    await interaction.response.send_message("This isn't your battle to decline!", ephemeral=True)
                    return
                await interaction.response.send_message("Battle declined!")

        await ctx.send(embed=embed, view=BattleButtons())

async def setup(bot):
    await bot.add_cog(PetCommands(bot))

# --- Battle System Implementation ---
class BattleSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_battles = {}
        self.battle_timeouts = {}

    class BattleView(discord.ui.View):
        def __init__(self, battle_obj):
            super().__init__(timeout=30)
            self.battle = battle_obj

        @discord.ui.button(label="Attack", style=discord.ButtonStyle.danger)
        async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.battle.current_turn:
                await interaction.response.send_message("It's not your turn!", ephemeral=True)
                return
            moves = self.battle.get_current_pet().moves
            move = random.choice(moves)
            damage = await self.battle.execute_move(move)
            await interaction.response.send_message(
                f"Used {move.name} {move.emoji}! Dealt {damage} damage!"
            )

        @discord.ui.button(label="Heal", style=discord.ButtonStyle.success)
        async def heal(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.battle.current_turn:
                await interaction.response.send_message("It's not your turn!", ephemeral=True)
                return
            heal_amount = random.randint(20, 40)
            current_pet = self.battle.get_current_pet()
            current_pet.health = min(current_pet.max_health, current_pet.health + heal_amount)
            await interaction.response.send_message(f"Healed for {heal_amount} HP!")

    async def start_battle(self, ctx: commands.Context, player1: discord.Member, player2: discord.Member):
        """Initialize and start a battle between two players"""
        battle_id = f"{ctx.channel.id}-{random.randint(1000, 9999)}"

        player1_data = await self.bot.get_player_data(player1.id)
        player2_data = await self.bot.get_player_data(player2.id)
        if not player1_data.pets or not player2_data.pets:
            await ctx.send("Both players need active pets to battle!")
            return
        battle = Battle(
            player1_id=player1.id,
            player2_id=player2.id,
            pet1=player1_data.pets[0],
            pet2=player2_data.pets[0]
        )
        self.active_battles[battle_id] = battle
        embed = discord.Embed(
            title="⚔️ Battle Start! ⚔️",
            description=f"{player1.mention}'s {battle.pet1.name} VS {player2.mention}'s {battle.pet2.name}",
            color=discord.Color.red()
        )
        battle_view = self.BattleView(battle)
        battle_msg = await ctx.send(embed=embed, view=battle_view)
        # Set battle timeout
        self.battle_timeouts[battle_id] = self.bot.loop.create_task(
            self.battle_timeout(ctx, battle_id, battle_msg)
        )

    async def battle_timeout(self, ctx: commands.Context, battle_id: str, battle_msg: discord.Message):
        """Handle battle timeout after 5 minutes"""
        await asyncio.sleep(300)  # 5 minutes
        if battle_id in self.active_battles:
            del self.active_battles[battle_id]
            await battle_msg.edit(content="Battle timed out!", view=None)
            await ctx.send("The battle has timed out due to inactivity!")

    @commands.Cog.listener()
    async def on_battle_end(self, ctx: commands.Context, winner: discord.Member, loser: discord.Member):
        """Handle battle end events"""
        embed = discord.Embed(
            title="🏆 Battle Ended!",
            description=f"{winner.mention} is victorious!",
            color=discord.Color.gold()
        )

        # Award XP and coins
        winner_data = await self.bot.get_player_data(winner.id)
        winner_data.coins += 100
        winner_data.pets[0].add_experience(50)
        await self.bot.save_player_data(winner_data)

        embed.add_field(name="Rewards", value="Winner received:\n- 100 coins\n- 50 pet XP")
        await ctx.send(embed=embed)

    def cog_unload(self):
        """Cancel all active battle timeouts when cog is unloaded"""
        for timeout in self.battle_timeouts.values():
            timeout.cancel()

class Training(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.training_cooldowns = {}

    @commands.hybrid_command()
    @cooldown('train')
    async def train(self, ctx: commands.Context):
        """Train your active pet"""
        player_data = await self.bot.get_player_data(ctx.author.id)
        if not player_data.pets:
            await ctx.send("You don't have any pets to train! Use `!adopt` to get one.")
            return
        active_pet = player_data.pets[0]
        training_options = [
            ("Speed Training 🏃", "speed", random.randint(10, 30)),
            ("Strength Training 💪", "strength", random.randint(15, 35)),
            ("Special Move Training ⚡", "special", random.randint(20, 40))
        ]
        class TrainingView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)

            @discord.ui.select(
                placeholder="Choose training type",
                options=[
                    discord.SelectOption(label=name, value=stat)
                    for name, stat, _ in training_options
                ]
            )
            async def select_training(self, interaction: discord.Interaction, select: discord.ui.Select):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("This isn't your training session!", ephemeral=True)
                    return
                selected = next(opt for opt in training_options if opt[1] == select.values[0])
                xp_gain = selected[2]
                active_pet.experience += xp_gain

                # Check for level up
                if active_pet.experience >= 100:
                    active_pet.level += 1
                    active_pet.experience -= 100
                    await self.bot.save_player_data(player_data)

                    embed = discord.Embed(
                        title="🎉 Level Up!",
                        description=f"{active_pet.name} reached level {active_pet.level}!",
                        color=discord.Color.gold()
                    )
                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.response.send_message(
                        f"{active_pet.name} gained {xp_gain} XP from {selected[0]}!"
                    )

        embed = discord.Embed(
            title="🏋️ Pet Training",
            description=f"Choose a training type for {active_pet.name}",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Current Stats",
            value=f"Level: {active_pet.level}\nXP: {active_pet.experience}/100",
            inline=False
        )
        await ctx.send(embed=embed, view=TrainingView())

# Add these new constants after the existing ones
EXPERIENCE_ACTIONS = {
    "MESSAGE": 5,
    "COMMAND": 10,
    "REACTION": 2,
    "BATTLE_WIN": 50,
    "DAILY_BONUS": 25,
    "PET_TRAIN": 15
}
LEVEL_REWARDS = {
    5: {"coins": 500, "title": "Novice"},
    10: {"coins": 1000, "title": "Apprentice"},
    25: {"coins": 2500, "title": "Expert"},
    50: {"coins": 5000, "title": "Master"},
    100: {"coins": 10000, "title": "Legend"}
}

# Add this new class before the bot commands
class RewardSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_rewards.start()

    def cog_unload(self):
        self.check_rewards.cancel()

    @tasks.loop(minutes=5)
    async def check_rewards(self):
        """Check and distribute rewards periodically"""
        for guild in self.bot.guilds:
            for member in guild.members:
                player_data = await self.bot.get_player_data(member.id)
                if not player_data:
                    continue

                await self.check_level_rewards(member, player_data)
                await self.check_activity_rewards(member, player_data)

    async def add_experience(self, member: discord.Member, action: str):
        """Add experience for various actions"""
        if action not in EXPERIENCE_ACTIONS:
            return

        player_data = await self.bot.get_player_data(member.id)
        xp_gain = EXPERIENCE_ACTIONS[action]
        player_data.experience += xp_gain

        # Check for level up
        level_up = False
        while player_data.experience >= self.calculate_xp_needed(player_data.level):
            player_data.level += 1
            level_up = True

        await self.bot.save_player_data(player_data)

        if level_up:
            await self.handle_level_up(member, player_data)

    def calculate_xp_needed(self, level: int) -> int:
        """Calculate XP needed for next level"""
        return 100 * (level ** 1.5)

    async def handle_level_up(self, member: discord.Member, player_data: 'PlayerData'):
        """Handle level up rewards and notifications"""
        embed = discord.Embed(
            title="🎉 Level Up!",
            description=f"{member.mention} has reached level {player_data.level}!",
            color=discord.Color.gold()
        )

        # Check for milestone rewards
        if player_data.level in LEVEL_REWARDS:
            reward = LEVEL_REWARDS[player_data.level]
            player_data.coins += reward["coins"]
            embed.add_field(
                name="Milestone Reward!",
                value=f"+ {reward['coins']} coins\nNew Title: {reward['title']}"
            )

        await self.bot.save_player_data(player_data)

        if channel := member.guild.system_channel:
            await channel.send(embed=embed)

if __name__ == "__main__":
    bot.run(TOKEN)

# Add after the existing event handlers
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    # Add XP for messages
    reward_system = bot.get_cog('RewardSystem')
    if reward_system:
        await reward_system.add_experience(message.author, "MESSAGE")
        await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    reward_system = bot.get_cog('RewardSystem')
    if reward_system:
        await reward_system.add_experience(user, "REACTION")

# Update the help command to include all new features
@bot.command(name='help')
async def help(ctx):
    embed = discord.Embed(
        title="Available Commands",
        description="Here are all the commands you can use!",
        color=discord.Color.blue()
    )

    fun_commands = """`!hello` - Basic greeting
`!wizard` - Magical greeting
`!rickroll` - Never gonna give you up...
`!doubt` - X to doubt
`!nani` - Omae wa mou shindeiru
`!cowbell` - More cowbell
`!peepee` - PP size check
`!fortnite` - Gaming preference
`!beans` - Bean adequacy check
`!lol` - lmao
`!triggered` - 🤣
`!yelling` - WHY ARE WE YELLING?
`!noot` - Pingu's greeting
`!sad` - 😭
`!coffee` - Coffee first
`!banana` - Peanut butter jelly time!"""
    embed.add_field(name="Fun Commands", value=fun_commands, inline=False)

    game_commands = """`!adopt <name>` - Adopt a new pet
`!pets` - View your pets
`!train` - Train your active pet
`!battle <@user>` - Challenge someone to a pet battle
`!shop` - View available items
`!inventory` - Check your inventory
`!daily` - Claim daily reward
`!quests` - View active quests
`!achievements` - View your achievements
`!level` - Check your current level"""
    embed.add_field(name="Game Commands", value=game_commands, inline=False)

    plex_commands = """`!play <query>` - Play media matching query
`!search <query>` - Search for media"""
    embed.add_field(name="Plex Commands", value=plex_commands, inline=False)

    embed.set_footer(text=f"Requested by {ctx.author.name} | Bot Version 1.0")
    await ctx.send(embed=embed)

# Add setup function at the bottom of the file
async def setup(bot):
    await bot.add_cog(RewardSystem(bot))
    await bot.add_cog(PetCommands(bot))
    await bot.add_cog(Training(bot))
    await bot.add_cog(BattleSystem(bot))
    await bot.add_cog(Shop(bot))

if __name__ == "__main__":
    asyncio.run(setup(bot))
    bot.run(TOKEN)

# --- Error Handling ---
class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            minutes = error.retry_after / 60
            await ctx.send(f"This command is on cooldown. Try again in {minutes:.1f} minutes.")
            logger.warning(f"Cooldown hit for {ctx.command} by {ctx.author}")

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command!")
            logger.warning(f"Permission denied for {ctx.command} to {ctx.author}")

        elif isinstance(error, commands.UserInputError):
            await ctx.send(f"Invalid input: {str(error)}")
            logger.warning(f"Invalid input for {ctx.command} by {ctx.author}: {error}")

        else:
            await ctx.send("An error occurred! The bot owner has been notified.")
            logger.error(f"Unhandled error in {ctx.command}: {str(error)}", exc_info=error)

# --- Error Handler Cog ---
class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Global error handler for commands"""
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = int(error.retry_after)
            await ctx.send(f"This command is on cooldown. Try again in {retry_after} seconds.")

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command!")

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")

        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid argument provided. Check !help for proper usage.")

        else:
            await ctx.send("An error occurred while processing your command.")
            bot_logger.log_command(ctx, error)

# Update the existing bot events with logging
@bot.event
async def on_ready():
    bot_logger.logger.info(f"Bot connected as {bot.user.name}")
    # ...rest of existing on_ready code...

@bot.event
async def on_command(ctx):
    bot_logger.log_command(ctx)

# Add to the setup function
async def setup(bot):
    # ...existing setup code...
    await bot.add_cog(CommandErrorHandler(bot))
    await bot.add_cog(ErrorHandler(bot))

# Add exception handling to existing commands
@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"Error in {event}", exc_info=True)

# Add error catching decorators to critical functions
def catch_errors(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=e)
            if len(args) > 0 and isinstance(args[0], commands.Context):
                await args[0].send("An error occurred while processing your command.")
    return wrapper

# Add decorator for command error handling
def handle_command_errors(func):
    async def wrapper(ctx, *args, **kwargs):
        try:
            return await func(ctx, *args, **kwargs)
        except Exception as e:
            bot.logger.log_command(ctx, e)
            await ctx.send("An error occurred while processing your command.")
    return wrapper

# Update the main execution
if __name__ == "__main__":
    async def main():
        try:
            # Initialize Plex connection
            if PLEX_URL and PLEX_TOKEN:
                try:
                    bot.plex = PlexServer(PLEX_URL, PLEX_TOKEN)
                    print("Connected to Plex Server successfully!")
                except Exception as e:
                    print(f"Error connecting to Plex server: {e}")

            # Start bot
            print("Starting bot...")
            await bot.start(TOKEN)
        except Exception as e:
            print(f"Fatal error: {e}")
        finally:
            if not bot.is_closed():
                await bot.close()

    # Run the bot with proper asyncio handling
    asyncio.run(main())