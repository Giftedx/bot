from typing import Dict, Any, Optional, List, Callable
import logging
import discord
from discord import app_commands
from discord.ext import commands
import asyncio

from shared.utils.service_interface import BaseService
from infrastructure.database.database_service import DatabaseService
from infrastructure.cache.cache_service import CacheService
from services.game.src.service import GameService
from services.identity.src.service import IdentityService

from .models import (
    Command, CommandType, Interaction, InteractionResponse,
    Embed, EmbedField, ComponentButton, ComponentSelect, ActionRow,
    GAME_COMMANDS, UTILITY_COMMANDS, ERROR_EMBED, SUCCESS_EMBED, LOADING_EMBED,
    TRAINING_LOCATIONS, COMBAT_AREAS
)

class DiscordService(BaseService):
    """Service for managing Discord bot and interactions"""
    
    def __init__(self,
                 database_service: DatabaseService,
                 cache_service: CacheService,
                 game_service: GameService,
                 identity_service: IdentityService,
                 token: str,
                 guild_ids: List[int]):
        super().__init__("discord", "1.0.0")
        self.db = database_service
        self.cache = cache_service
        self.game_service = game_service
        self.identity_service = identity_service
        self.token = token
        self.guild_ids = guild_ids
        
        # Initialize Discord client
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.logger = logging.getLogger(__name__)
        
        # Command handlers
        self.command_handlers: Dict[str, Callable] = {
            # Game commands
            "stats": self._handle_stats_command,
            "inventory": self._handle_inventory_command,
            "equipment": self._handle_equipment_command,
            "train": self._handle_train_command,
            "combat": self._handle_combat_command,
            "gear": self._handle_gear_command,
            "location": self._handle_location_command,
            "bank": self._handle_bank_command,
            
            # Utility commands
            "help": self._handle_help_command,
            "profile": self._handle_profile_command
        }
        
    async def _init_dependencies(self) -> None:
        """Initialize service dependencies"""
        # Set up event handlers
        @self.bot.event
        async def on_ready():
            self.logger.info(f"Bot logged in as {self.bot.user}")
            
            # Sync commands with Discord
            for guild_id in self.guild_ids:
                guild = discord.Object(id=guild_id)
                self.bot.tree.copy_global_to(guild=guild)
                await self.bot.tree.sync(guild=guild)
        
        @self.bot.event
        async def on_command_error(ctx, error):
            self.logger.error(f"Command error: {error}")
            await ctx.send(embed=self._create_error_embed(str(error)))
        
        # Register commands
        for command in {**GAME_COMMANDS, **UTILITY_COMMANDS}.values():
            self._register_command(command)
    
    async def _start_service(self) -> None:
        """Start the Discord service"""
        self.logger.info("Starting Discord service")
        try:
            await self.bot.start(self.token)
        except Exception as e:
            self.logger.error(f"Failed to start Discord bot: {e}")
            raise
    
    async def _stop_service(self) -> None:
        """Stop the Discord service"""
        self.logger.info("Stopping Discord service")
        try:
            await self.bot.close()
        except Exception as e:
            self.logger.error(f"Error stopping Discord bot: {e}")
            raise
    
    async def _cleanup_resources(self) -> None:
        """Cleanup service resources"""
        pass
    
    def _register_command(self, command: Command) -> None:
        """Register a command with the Discord bot"""
        @self.bot.tree.command(
            name=command.name,
            description=command.description,
            guild=discord.Object(id=command.guild_id) if command.guild_id else None
        )
        async def command_handler(interaction: discord.Interaction, **kwargs):
            try:
                # Convert Discord interaction to our model
                interaction_data = Interaction(
                    id=str(interaction.id),
                    type=interaction.type,
                    data={
                        "name": command.name,
                        "options": kwargs
                    },
                    guild_id=str(interaction.guild_id) if interaction.guild_id else None,
                    channel_id=str(interaction.channel_id) if interaction.channel_id else None,
                    member=interaction.user.__dict__ if interaction.user else None
                )
                
                # Get handler and execute
                handler = self.command_handlers.get(command.name)
                if handler:
                    await interaction.response.defer()
                    result = await handler(interaction_data)
                    
                    # Send response
                    if isinstance(result, Embed):
                        await interaction.followup.send(embed=self._convert_embed(result))
                    else:
                        await interaction.followup.send(content=str(result))
                else:
                    await interaction.response.send_message(
                        embed=self._create_error_embed(f"No handler for command {command.name}")
                    )
                    
            except Exception as e:
                self.logger.error(f"Error handling command {command.name}: {e}")
                await interaction.followup.send(
                    embed=self._create_error_embed(str(e))
                )
    
    async def _handle_stats_command(self, interaction: Interaction) -> Embed:
        """Handle stats command"""
        user_id = interaction.member["id"]
        skill = interaction.data.get("options", {}).get("skill")
        
        game_state = await self.game_service.get_game_state(user_id)
        if not game_state:
            return self._create_error_embed("No game state found")
        
        if skill:
            # Show specific skill
            skill_level = game_state.skills.levels.get(skill)
            skill_xp = game_state.skills.experience.get(skill)
            if skill_level is None:
                return self._create_error_embed(f"Invalid skill: {skill}")
            
            return Embed(
                title=f"{skill.capitalize()} Statistics",
                fields=[
                    EmbedField(name="Level", value=str(skill_level)),
                    EmbedField(name="Experience", value=str(skill_xp))
                ],
                color=0x00FF00
            )
        else:
            # Show all skills
            fields = []
            for skill, level in game_state.skills.levels.items():
                xp = game_state.skills.experience[skill]
                fields.append(
                    EmbedField(
                        name=skill.capitalize(),
                        value=f"Level {level} ({xp:,} xp)",
                        inline=True
                    )
                )
            
            return Embed(
                title="Skill Statistics",
                fields=fields,
                color=0x00FF00
            )
    
    async def _handle_inventory_command(self, interaction: Interaction) -> Embed:
        """Handle inventory command"""
        user_id = interaction.member["id"]
        
        game_state = await self.game_service.get_game_state(user_id)
        if not game_state:
            return self._create_error_embed("No game state found")
        
        fields = []
        for item in game_state.inventory:
            fields.append(
                EmbedField(
                    name=f"Slot {item.slot}",
                    value=f"{item.item_id} x{item.quantity}",
                    inline=True
                )
            )
        
        return Embed(
            title="Inventory",
            description=f"{len(game_state.inventory)}/28 slots used",
            fields=fields,
            color=0x00FF00
        )
    
    async def _handle_equipment_command(self, interaction: Interaction) -> Embed:
        """Handle equipment command"""
        user_id = interaction.member["id"]
        
        game_state = await self.game_service.get_game_state(user_id)
        if not game_state:
            return self._create_error_embed("No game state found")
        
        fields = []
        for slot, item in game_state.equipment.__dict__.items():
            fields.append(
                EmbedField(
                    name=slot.capitalize(),
                    value=item if item else "Empty",
                    inline=True
                )
            )
        
        return Embed(
            title="Equipment",
            fields=fields,
            color=0x00FF00
        )
    
    async def _handle_train_command(self, interaction: Interaction) -> Embed:
        """Handle train command"""
        user_id = interaction.member["id"]
        skill = interaction.data["options"]["skill"]
        method = interaction.data["options"]["method"]
        duration = interaction.data["options"].get("duration", 30)  # Default 30 minutes
        
        # Get current location and validate training method
        game_state = await self.game_service.get_game_state(user_id)
        if not game_state:
            return self._create_error_embed("No game state found")
        
        current_location = game_state.position
        available_locations = TRAINING_LOCATIONS.get(skill, [])
        
        # Find valid training methods for current location
        valid_methods = []
        for loc in available_locations:
            if loc["name"] == current_location:
                if skill == "woodcutting":
                    valid_methods = loc["trees"]
                elif skill == "mining":
                    valid_methods = loc["ores"]
                elif skill == "fishing":
                    valid_methods = loc["spots"]
                break
        
        if not valid_methods:
            return self._create_error_embed(
                f"No {skill} training methods available at your location. "
                f"Use /location to view available areas."
            )
        
        if method not in valid_methods:
            return self._create_error_embed(
                f"Invalid training method. Available methods: {', '.join(valid_methods)}"
            )
        
        # Start training
        result = await self.game_service.perform_action(
            user_id,
            f"skill_{skill}",
            {
                "method": method,
                "duration": min(duration, 60)  # Cap at 60 minutes
            }
        )
        
        if result.success:
            return Embed(
                title="Training Started",
                description=f"Started training {skill} using {method}",
                fields=[
                    EmbedField(
                        name="Location",
                        value=current_location
                    ),
                    EmbedField(
                        name="Duration",
                        value=f"{min(duration, 60)} minutes"
                    ),
                    EmbedField(
                        name="Experience Rate",
                        value=f"~{result.experience_gained['rate']}/hr"
                    )
                ],
                color=0x00FF00
            )
        else:
            return self._create_error_embed(result.message)
    
    async def _handle_combat_command(self, interaction: Interaction) -> Embed:
        """Handle combat command"""
        user_id = interaction.member["id"]
        action = interaction.data["options"]["action"]
        target = interaction.data["options"].get("target")
        style = interaction.data["options"].get("style", "accurate")
        
        game_state = await self.game_service.get_game_state(user_id)
        if not game_state:
            return self._create_error_embed("No game state found")
        
        current_location = game_state.position
        area_info = COMBAT_AREAS.get(current_location)
        
        if not area_info:
            return self._create_error_embed(
                "You must be in a combat area to engage in combat. "
                "Use /location to travel to a combat area."
            )
        
        if action == "attack_npc":
            if not target:
                return self._create_error_embed(
                    f"Available targets: {', '.join(area_info['npcs'])}"
                )
            
            if target not in area_info["npcs"]:
                return self._create_error_embed(
                    f"Target not found in this area. Available targets: {', '.join(area_info['npcs'])}"
                )
            
            result = await self.game_service.perform_action(
                user_id,
                "combat_attack",
                {
                    "target": target,
                    "style": style
                }
            )
            
            if result.success:
                return Embed(
                    title="Combat Engaged",
                    description=f"Attacking {target} using {style} style",
                    fields=[
                        EmbedField(
                            name="Location",
                            value=current_location
                        ),
                        EmbedField(
                            name="Combat Stats",
                            value=f"HP: {game_state.combat_stats.hitpoints}\n"
                                  f"Prayer: {game_state.combat_stats.prayer}"
                        )
                    ],
                    color=0x00FF00
                )
            else:
                return self._create_error_embed(result.message)
                
        elif action == "auto_combat":
            result = await self.game_service.perform_action(
                user_id,
                "combat_auto",
                {
                    "style": style,
                    "area": current_location
                }
            )
            
            if result.success:
                return Embed(
                    title="Auto Combat Enabled",
                    description=f"Auto-attacking NPCs in {current_location}",
                    fields=[
                        EmbedField(
                            name="Combat Style",
                            value=style
                        ),
                        EmbedField(
                            name="Target Range",
                            value=f"Level {area_info['level_range'][0]}-{area_info['level_range'][1]}"
                        )
                    ],
                    color=0x00FF00
                )
            else:
                return self._create_error_embed(result.message)
                
        elif action == "stop_combat":
            result = await self.game_service.perform_action(
                user_id,
                "combat_stop",
                {}
            )
            
            if result.success:
                return Embed(
                    title="Combat Stopped",
                    description="You are no longer in combat",
                    color=0x00FF00
                )
            else:
                return self._create_error_embed(result.message)
    
    async def _handle_gear_command(self, interaction: Interaction) -> Embed:
        """Handle gear command"""
        user_id = interaction.member["id"]
        action = interaction.data["options"]["action"]
        slot = interaction.data["options"].get("slot")
        item = interaction.data["options"].get("item")
        
        game_state = await self.game_service.get_game_state(user_id)
        if not game_state:
            return self._create_error_embed("No game state found")
        
        if action == "view":
            # Format equipment display
            fields = []
            for slot_name, item_id in game_state.equipment.__dict__.items():
                fields.append(
                    EmbedField(
                        name=slot_name.capitalize(),
                        value=item_id if item_id else "Empty",
                        inline=True
                    )
                )
            
            # Add combat stats
            fields.append(
                EmbedField(
                    name="Combat Stats",
                    value=f"Attack: {game_state.combat_stats.attack}\n"
                          f"Strength: {game_state.combat_stats.strength}\n"
                          f"Defence: {game_state.combat_stats.defence}\n"
                          f"Ranged: {game_state.combat_stats.ranged}\n"
                          f"Magic: {game_state.combat_stats.magic}",
                    inline=False
                )
            )
            
            return Embed(
                title="Combat Gear",
                fields=fields,
                color=0x00FF00
            )
            
        elif action in ["equip", "unequip"]:
            if not slot:
                return self._create_error_embed("Please specify an equipment slot")
            
            result = await self.game_service.perform_action(
                user_id,
                f"item_{action}",
                {
                    "slot": slot,
                    "item": item
                }
            )
            
            if result.success:
                return Embed(
                    title=f"{action.capitalize()} Successful",
                    description=f"{action.capitalize()}ped {item} in {slot} slot",
                    color=0x00FF00
                )
            else:
                return self._create_error_embed(result.message)
    
    async def _handle_location_command(self, interaction: Interaction) -> Embed:
        """Handle location command"""
        user_id = interaction.member["id"]
        action = interaction.data["options"]["action"]
        destination = interaction.data["options"].get("destination")
        
        game_state = await self.game_service.get_game_state(user_id)
        if not game_state:
            return self._create_error_embed("No game state found")
        
        if action == "view":
            current_location = game_state.position
            
            # Get available activities
            activities = []
            if current_location in COMBAT_AREAS:
                area = COMBAT_AREAS[current_location]
                activities.append(
                    f"Combat (Levels {area['level_range'][0]}-{area['level_range'][1]})"
                )
            
            for skill, locations in TRAINING_LOCATIONS.items():
                for loc in locations:
                    if loc["name"] == current_location:
                        if skill == "woodcutting":
                            activities.append(f"Woodcutting: {', '.join(loc['trees'])}")
                        elif skill == "mining":
                            activities.append(f"Mining: {', '.join(loc['ores'])}")
                        elif skill == "fishing":
                            activities.append(f"Fishing: {', '.join(loc['spots'])}")
            
            return Embed(
                title="Current Location",
                description=current_location,
                fields=[
                    EmbedField(
                        name="Available Activities",
                        value="\n".join(activities) if activities else "No activities available"
                    )
                ],
                color=0x00FF00
            )
            
        elif action == "list":
            # Combine all locations
            all_locations = set()
            
            # Add combat areas
            for area in COMBAT_AREAS:
                all_locations.add(area)
            
            # Add skilling areas
            for locations in TRAINING_LOCATIONS.values():
                for loc in locations:
                    all_locations.add(loc["name"])
            
            return Embed(
                title="Available Locations",
                description="\n".join(sorted(all_locations)),
                color=0x00FF00
            )
            
        elif action == "travel":
            if not destination:
                return self._create_error_embed("Please specify a destination")
            
            result = await self.game_service.perform_action(
                user_id,
                "move_to",
                {"destination": destination}
            )
            
            if result.success:
                return Embed(
                    title="Travel Complete",
                    description=f"You have arrived at {destination}",
                    color=0x00FF00
                )
            else:
                return self._create_error_embed(result.message)
    
    async def _handle_bank_command(self, interaction: Interaction) -> Embed:
        """Handle bank command"""
        user_id = interaction.member["id"]
        action = interaction.data["options"]["action"]
        item = interaction.data["options"].get("item")
        amount = interaction.data["options"].get("amount", 1)
        
        game_state = await self.game_service.get_game_state(user_id)
        if not game_state:
            return self._create_error_embed("No game state found")
        
        if action == "view":
            # Group items by tab
            tabs: Dict[int, List[str]] = {}
            for bank_item in game_state.bank:
                if bank_item.tab not in tabs:
                    tabs[bank_item.tab] = []
                tabs[bank_item.tab].append(
                    f"{bank_item.item_id} x{bank_item.quantity}"
                )
            
            # Create fields for each tab
            fields = []
            for tab, items in sorted(tabs.items()):
                fields.append(
                    EmbedField(
                        name=f"Tab {tab}",
                        value="\n".join(items) if items else "Empty",
                        inline=True
                    )
                )
            
            return Embed(
                title="Bank Contents",
                fields=fields,
                color=0x00FF00
            )
            
        elif action in ["deposit", "withdraw"]:
            if not item:
                return self._create_error_embed("Please specify an item")
            
            result = await self.game_service.perform_action(
                user_id,
                f"bank_{action}",
                {
                    "item": item,
                    "amount": amount
                }
            )
            
            if result.success:
                return Embed(
                    title=f"{action.capitalize()} Successful",
                    description=f"{action.capitalize()}ed {amount}x {item}",
                    color=0x00FF00
                )
            else:
                return self._create_error_embed(result.message)
    
    async def _handle_help_command(self, interaction: Interaction) -> Embed:
        """Handle help command"""
        command = interaction.data.get("options", {}).get("command")
        
        if command:
            # Show specific command help
            cmd = {**GAME_COMMANDS, **UTILITY_COMMANDS}.get(command)
            if not cmd:
                return self._create_error_embed(f"Unknown command: {command}")
            
            fields = [
                EmbedField(name="Description", value=cmd.description)
            ]
            
            if cmd.options:
                options_text = "\n".join(
                    f"• {opt.name}: {opt.description}"
                    for opt in cmd.options
                )
                fields.append(EmbedField(name="Options", value=options_text))
            
            return Embed(
                title=f"Help: /{command}",
                fields=fields,
                color=0x00FF00
            )
        else:
            # Show all commands
            game_cmds = "\n".join(
                f"• /{name}: {cmd.description}"
                for name, cmd in GAME_COMMANDS.items()
            )
            utility_cmds = "\n".join(
                f"• /{name}: {cmd.description}"
                for name, cmd in UTILITY_COMMANDS.items()
            )
            
            return Embed(
                title="Available Commands",
                fields=[
                    EmbedField(name="Game Commands", value=game_cmds),
                    EmbedField(name="Utility Commands", value=utility_cmds)
                ],
                color=0x00FF00
            )
    
    async def _handle_profile_command(self, interaction: Interaction) -> Embed:
        """Handle profile command"""
        user_id = interaction.member["id"]
        action = interaction.data["options"]["action"]
        
        user = await self.identity_service.get_user_profile(user_id)
        if not user:
            return self._create_error_embed("User profile not found")
        
        if action == "view":
            return Embed(
                title=f"Profile: {user.display_name}",
                fields=[
                    EmbedField(name="Bio", value=user.bio or "No bio set"),
                    EmbedField(name="Social Links", value="\n".join(
                        f"• {platform}: {link}"
                        for platform, link in (user.social_links or {}).items()
                    ) or "No social links")
                ],
                thumbnail={"url": user.avatar_url} if user.avatar_url else None,
                color=0x00FF00
            )
        elif action == "edit":
            # TODO: Implement profile editing
            return self._create_error_embed("Profile editing not implemented yet")
        else:
            return self._create_error_embed(f"Invalid action: {action}")
    
    def _create_error_embed(self, message: str) -> Embed:
        """Create an error embed with a message"""
        embed = ERROR_EMBED.copy()
        embed.fields = [EmbedField(name="Details", value=message)]
        return embed
    
    def _convert_embed(self, embed: Embed) -> discord.Embed:
        """Convert our Embed model to Discord.py Embed"""
        discord_embed = discord.Embed(
            title=embed.title,
            description=embed.description,
            url=embed.url,
            color=embed.color
        )
        
        if embed.fields:
            for field in embed.fields:
                discord_embed.add_field(
                    name=field.name,
                    value=field.value,
                    inline=field.inline
                )
        
        if embed.thumbnail:
            discord_embed.set_thumbnail(url=embed.thumbnail["url"])
            
        if embed.image:
            discord_embed.set_image(url=embed.image["url"])
            
        if embed.footer:
            discord_embed.set_footer(
                text=embed.footer.get("text"),
                icon_url=embed.footer.get("icon_url")
            )
            
        if embed.timestamp:
            discord_embed.timestamp = embed.timestamp
            
        return discord_embed 