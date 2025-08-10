import discord
from discord.ext import commands, tasks
from typing import Optional
import logging
from datetime import datetime, timedelta
import random
import json

from .unified_database import UnifiedDatabaseManager
from .personal_system import PersonalSystem
from .unified_config import init_config, UnifiedConfigSettings
from .error_manager import setup_error_handling

logger = logging.getLogger(__name__)


class PersonalBot(commands.Bot):
    """Discord bot for personal content and cross-game features"""

    def __init__(self, config_settings: Optional[UnifiedConfigSettings] = None):
        # Initialize unified configuration
        self.config = init_config(config_settings)

        # Set up Discord intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        # Get bot configuration
        command_prefix = self.config.get("bot.command_prefix", "!")
        description = self.config.get(
            "bot.description", "Personal content and cross-game features bot"
        )

        super().__init__(
            command_prefix=command_prefix,
            intents=intents,
            help_command=commands.DefaultHelpCommand(no_category="General Commands"),
            description=description,
        )

        # Initialize unified systems
        self.db = UnifiedDatabaseManager()
        self.personal_system = PersonalSystem()
        self.error_manager = setup_error_handling(self)

        # Runtime state
        self.active_sessions = {}
        self.watch_parties = {}
        self.roast_cooldowns = {}

        # Load configuration-driven settings
        self.roast_cooldown_minutes = self.config.get("bot.roast_cooldown_minutes", 5)
        self.roast_min_score = self.config.get("bot.roast_min_score", 0.7)
        self.roast_chance = self.config.get("bot.roast_chance", 0.3)

        # Load commands
        self.load_commands()

        # Start background tasks
        self.cleanup_expired_effects.start()
        self.check_events.start()
        self.process_roasts.start()

    async def setup_hook(self) -> None:
        """Set up the bot before it starts running."""
        try:
            # Validate configuration
            if not self.config.get("discord.token"):
                raise ValueError("Discord token not configured")

            # Set bot status
            status_message = self.config.get("bot.status_message", "Watching for roastable moments")
            await self.change_presence(activity=discord.Game(name=status_message))

            logger.info("PersonalBot setup completed successfully")

        except Exception as e:
            await self.error_manager.handle_error(e, {"component": "setup_hook"})
            raise

    def load_commands(self) -> None:
        """Load bot commands with error handling"""

        @self.command(name="pet")
        async def pet_command(ctx, action: str, pet_name: Optional[str] = None):
            """Pet system commands"""
            try:
                player_id = str(ctx.author.id)

                if action == "list":
                    pets = self.db.pets.get_by_owner(player_id)
                    if not pets:
                        await ctx.send("You don't have any pets yet!")
                        return

                    pet_list = "\n".join(f"• {pet.name} ({pet.type})" for pet in pets)
                    await ctx.send(f"Your pets:\n{pet_list}")

                elif action == "info" and pet_name:
                    pets = self.db.pets.get_by_owner(player_id)
                    pet = next((p for p in pets if p.name.lower() == pet_name.lower()), None)

                    if not pet:
                        await ctx.send(f"You don't have a pet named {pet_name}!")
                        return

                    pet_data = pet.to_dict()
                    info = (
                        f"**{pet.name}** ({pet.type})\n"
                        f"Stats:\n"
                        f"• Happiness: {pet_data['stats']['happiness']}/100\n"
                        f"• Loyalty: {pet_data['stats']['loyalty']}/100\n"
                        f"• Experience: {pet_data['stats']['experience']}\n\n"
                        f"Abilities:"
                    )

                    for ability, data in pet_data["abilities"].items():
                        status = "✅" if data["unlocked"] else "❌"
                        info += f"\n• {ability}: {status}"

                    await ctx.send(info)

                elif action == "interact" and pet_name:
                    result = self.personal_system.pet_manager.interact_with_pet(
                        player_id, pet_name, "basic_interaction"
                    )

                    if not result["success"]:
                        await ctx.send(result["message"])
                        return

                    response = f"You interact with {pet_name}!"
                    if "effects" in result:
                        for effect in result["effects"]:
                            response += f"\n• {effect['type']}"

                    if "special_event" in result:
                        response += f"\n\n**Special Event!**\n{result['special_event']['message']}"

                    await ctx.send(response)

            except Exception as e:
                error_msg = await self.error_manager.handle_error(
                    e, {"command": "pet", "action": action, "user": str(ctx.author)}
                )
                if error_msg:
                    await ctx.send(error_msg)

        @self.command(name="watch")
        async def watch_command(ctx, action: str, *, args: Optional[str] = None):
            """Plex watch party commands"""
            try:
                player_id = str(ctx.author.id)
                max_members = self.config.get("watch_parties.max_members", 10)
                auto_end_minutes = self.config.get("watch_parties.auto_end_minutes", 360)

                if action == "start":
                    if not args:
                        await ctx.send("Please specify what you want to watch!")
                        return

                    # Create watch party
                    party_id = str(random.randint(1000, 9999))
                    self.watch_parties[party_id] = {
                        "host": player_id,
                        "content": args,
                        "members": [player_id],
                        "started_at": datetime.now().isoformat(),
                        "status": "waiting",
                        "max_members": max_members,
                        "auto_end_at": (
                            datetime.now() + timedelta(minutes=auto_end_minutes)
                        ).isoformat(),
                    }

                    await ctx.send(
                        f"Watch party created! ID: {party_id}\n"
                        f"Content: {args}\n"
                        f"Max members: {max_members}\n"
                        f"Use `!watch join {party_id}` to join!"
                    )

                elif action == "join":
                    if not args:
                        await ctx.send("Please specify the watch party ID!")
                        return

                    party = self.watch_parties.get(args)
                    if not party:
                        await ctx.send("Watch party not found!")
                        return

                    if player_id in party["members"]:
                        await ctx.send("You're already in this watch party!")
                        return

                    if len(party["members"]) >= party["max_members"]:
                        await ctx.send("This watch party is full!")
                        return

                    party["members"].append(player_id)
                    await ctx.send(f"Joined watch party {args}!")

                elif action == "start_watching" and args:
                    party = self.watch_parties.get(args)
                    if not party:
                        await ctx.send("Watch party not found!")
                        return

                    if player_id != party["host"]:
                        await ctx.send("Only the host can start watching!")
                        return

                    party["status"] = "watching"
                    started_at = datetime.now()

                    # Record watch for all members using unified database
                    for member_id in party["members"]:
                        with self.db.transaction() as cursor:
                            cursor.execute(
                                """
                                INSERT INTO watch_history 
                                (player_id, content_id, content_type, title, duration, watched_at, data)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    member_id,
                                    args,
                                    "group_watch",
                                    party["content"],
                                    0,  # Duration will be updated when finished
                                    started_at.isoformat(),
                                    json.dumps({"party_id": args, "members": party["members"]}),
                                ),
                            )

                    await ctx.send("Watch party started! Enjoy!")

            except Exception as e:
                error_msg = await self.error_manager.handle_error(
                    e, {"command": "watch", "action": action, "user": str(ctx.author)}
                )
                if error_msg:
                    await ctx.send(error_msg)

        @self.command(name="roast")
        async def roast_command(ctx, target: Optional[discord.Member] = None):
            """Generate a roast with improved cooldown management"""
            try:
                player_id = str(ctx.author.id)

                # Check cooldown using configuration
                if player_id in self.roast_cooldowns:
                    remaining = self.roast_cooldowns[player_id] - datetime.now()
                    if remaining.total_seconds() > 0:
                        await ctx.send(
                            f"Please wait {int(remaining.total_seconds())} seconds before roasting again!"
                        )
                        return

                # Get roastable messages from unified database
                with self.db.get_cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT * FROM chat_logs 
                        WHERE score >= ? AND used_in_roast = FALSE 
                        ORDER BY created_at DESC 
                        LIMIT 10
                        """,
                        (self.roast_min_score,),
                    )
                    messages = cursor.fetchall()

                if not messages:
                    await ctx.send("No roastable messages found!")
                    return

                # Filter by target if specified
                if target:
                    target_messages = [m for m in messages if m["player_id"] == str(target.id)]
                    if target_messages:
                        messages = target_messages

                # Select message and generate roast
                selected_message = random.choice(messages)
                roast_text = self._generate_roast(selected_message["message"])

                # Record roast in database
                with self.db.transaction() as cursor:
                    cursor.execute(
                        "INSERT INTO roasts (message_id, roast_text, created_at) VALUES (?, ?, ?)",
                        (selected_message["message_id"], roast_text, datetime.now().isoformat()),
                    )
                    cursor.execute(
                        "UPDATE chat_logs SET used_in_roast = TRUE WHERE message_id = ?",
                        (selected_message["message_id"],),
                    )

                # Set cooldown
                cooldown_duration = timedelta(minutes=self.roast_cooldown_minutes)
                self.roast_cooldowns[player_id] = datetime.now() + cooldown_duration

                await ctx.send(f"🔥 {roast_text}")

            except Exception as e:
                error_msg = await self.error_manager.handle_error(
                    e, {"command": "roast", "user": str(ctx.author)}
                )
                if error_msg:
                    await ctx.send(error_msg)

        @self.command(name="effects")
        async def effects_command(ctx):
            """Show active effects for the player"""
            try:
                player_id = str(ctx.author.id)

                with self.db.get_cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT * FROM active_effects 
                        WHERE player_id = ? AND active = TRUE 
                        ORDER BY started_at DESC
                        """,
                        (player_id,),
                    )
                    effects = cursor.fetchall()

                if not effects:
                    await ctx.send("You have no active effects.")
                    return

                effect_list = []
                for effect in effects:
                    effect_data = json.loads(effect["data"])
                    expires_text = "Permanent"
                    if effect["expires_at"]:
                        expires_at = datetime.fromisoformat(effect["expires_at"])
                        remaining = expires_at - datetime.now()
                        if remaining.total_seconds() > 0:
                            expires_text = f"{int(remaining.total_seconds() / 60)} minutes"
                        else:
                            expires_text = "Expired"

                    effect_list.append(f"• {effect['type']} - {expires_text}")

                await ctx.send("Your active effects:\n" + "\n".join(effect_list))

            except Exception as e:
                error_msg = await self.error_manager.handle_error(
                    e, {"command": "effects", "user": str(ctx.author)}
                )
                if error_msg:
                    await ctx.send(error_msg)

    def _generate_roast(self, message: str) -> str:
        """Generate a roast for a message"""
        roast_templates = [
            "That message was so bad, even my error handler couldn't parse it!",
            "I've seen better messages from a corrupted database!",
            "Your message processing needs a serious upgrade!",
            "That take was colder than my cache expiration time!",
            "I've processed thousands of messages, and that was definitely one of them!",
        ]
        return random.choice(roast_templates)

    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f"Logged in as {self.user}")

        # Perform automatic database backup if enabled
        if self.config.get("database.auto_backup", True):
            self.db.backup_database()

    async def on_message(self, message):
        """Process incoming messages with enhanced logging"""
        if message.author.bot:
            return

        try:
            # Enhanced message processing with unified database
            player_id = str(message.author.id)

            # Initialize player if needed
            player = self.db.players.get_by_discord_id(message.author.id)
            if not player:
                from .models.player import Player

                player = Player(discord_id=message.author.id, username=message.author.display_name)
                self.db.players.create(player)

            # Log message for roast generation
            with self.db.transaction() as cursor:
                # Calculate message score (simplified)
                score = self._calculate_message_score(message.content)

                cursor.execute(
                    """
                    INSERT INTO chat_logs 
                    (player_id, channel_id, message, score, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        player_id,
                        str(message.channel.id),
                        message.content,
                        score,
                        datetime.now().isoformat(),
                    ),
                )

            # Process Easter eggs and jokes
            if random.random() < self.config.get("easter_eggs.trigger_chance", 0.1):
                joke_result = self.personal_system.joke_manager.check_triggers(
                    {
                        "message": message.content,
                        "author": message.author.display_name,
                        "channel": message.channel.name,
                    }
                )

                if joke_result:
                    await message.channel.send(joke_result["response"])

            # Process commands
            await self.process_commands(message)

        except Exception as e:
            await self.error_manager.handle_error(
                e, {"component": "on_message", "message_id": message.id}
            )

    def _calculate_message_score(self, content: str) -> float:
        """Calculate roastability score for a message"""
        score = 0.0

        # Length factor
        if len(content) > 100:
            score += 0.2

        # Emotional indicators
        emotional_words = ["hate", "love", "amazing", "terrible", "best", "worst"]
        score += sum(0.1 for word in emotional_words if word in content.lower())

        # Question marks and exclamations
        score += content.count("?") * 0.05
        score += content.count("!") * 0.05

        return min(score, 1.0)

    @tasks.loop(minutes=5)
    async def cleanup_expired_effects(self):
        """Clean up expired effects using unified database"""
        try:
            with self.db.transaction() as cursor:
                cursor.execute(
                    """
                    UPDATE active_effects 
                    SET active = FALSE 
                    WHERE expires_at IS NOT NULL 
                    AND datetime(expires_at) <= datetime('now')
                    AND active = TRUE
                    """
                )

                if cursor.rowcount > 0:
                    logger.info(f"Cleaned up {cursor.rowcount} expired effects")

        except Exception as e:
            await self.error_manager.handle_error(e, {"task": "cleanup_expired_effects"})

    @tasks.loop(minutes=1)
    async def check_events(self):
        """Check for and trigger events"""
        try:
            events = self.personal_system.event_manager.update_events()

            if events:
                # Get event channel from configuration
                event_channel_id = self.config.get("channels.event_channel_id")
                if event_channel_id:
                    channel = self.get_channel(int(event_channel_id))
                    if channel:
                        for event in events:
                            await channel.send(
                                f"🎉 **Event Started:** {event['title']}\n{event['description']}"
                            )

                            # Record event in database
                            with self.db.transaction() as cursor:
                                cursor.execute(
                                    """
                                    INSERT INTO events (type, status, data, started_at)
                                    VALUES (?, ?, ?, ?)
                                    """,
                                    (
                                        event["type"],
                                        "active",
                                        json.dumps(event),
                                        datetime.now().isoformat(),
                                    ),
                                )

        except Exception as e:
            await self.error_manager.handle_error(e, {"task": "check_events"})

    @tasks.loop(minutes=15)
    async def process_roasts(self):
        """Automatically generate roasts based on configuration"""
        try:
            if random.random() > self.roast_chance:
                return

            # Get roast channel from configuration
            roast_channel_ids = self.config.get("channels.roast_channel_ids", [])
            if not roast_channel_ids:
                return

            channel_id = random.choice(roast_channel_ids)
            channel = self.get_channel(int(channel_id))
            if not channel:
                return

            # Get recent roastable messages
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * FROM chat_logs 
                    WHERE score >= ? 
                    AND used_in_roast = FALSE 
                    AND datetime(created_at) >= datetime('now', '-1 hour')
                    ORDER BY score DESC 
                    LIMIT 5
                    """,
                    (self.roast_min_score,),
                )
                messages = cursor.fetchall()

            if messages:
                selected_message = random.choice(messages)
                roast_text = self._generate_roast(selected_message["message"])

                # Record roast
                with self.db.transaction() as cursor:
                    cursor.execute(
                        "INSERT INTO roasts (message_id, roast_text, created_at) VALUES (?, ?, ?)",
                        (selected_message["message_id"], roast_text, datetime.now().isoformat()),
                    )
                    cursor.execute(
                        "UPDATE chat_logs SET used_in_roast = TRUE WHERE message_id = ?",
                        (selected_message["message_id"],),
                    )

                await channel.send(f"🔥 Auto-roast: {roast_text}")

        except Exception as e:
            await self.error_manager.handle_error(e, {"task": "process_roasts"})

    def run(self, **kwargs):
        """Run the bot with enhanced error handling"""
        try:
            token = self.config.get("discord.token")
            if not token:
                raise ValueError("Discord token not found in configuration")

            logger.info("Starting PersonalBot with unified configuration...")
            super().run(token, **kwargs)

        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise

    async def close(self):
        """Clean shutdown with unified systems cleanup"""
        try:
            logger.info("Shutting down PersonalBot...")

            # Stop tasks
            self.cleanup_expired_effects.cancel()
            self.check_events.cancel()
            self.process_roasts.cancel()

            # Close database
            self.db.close()

            # Final backup if enabled
            if self.config.get("database.auto_backup", True):
                self.db.backup_database()

            await super().close()
            logger.info("PersonalBot shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
