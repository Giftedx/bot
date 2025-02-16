"""
Discord commands for Plex media playback using slash commands and components.
"""

import logging
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

from ...integrations.plex_discord import PlexDiscordPlayer

logger = logging.getLogger(__name__)

class MediaControlView(View):
    """Media control buttons view."""
    
    def __init__(self, player: PlexDiscordPlayer, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.player = player
        
        # Add control buttons
        self.add_item(Button(label="⏯️", custom_id="toggle_play", style=discord.ButtonStyle.primary))
        self.add_item(Button(label="⏹️", custom_id="stop", style=discord.ButtonStyle.danger))
        self.add_item(Button(label="⏪", custom_id="rewind", style=discord.ButtonStyle.secondary))
        self.add_item(Button(label="⏩", custom_id="forward", style=discord.ButtonStyle.secondary))
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Handle button interactions."""
        if not interaction.data:
            return False
            
        custom_id = interaction.data.get("custom_id", "")
        
        try:
            if custom_id == "toggle_play":
                state = self.player.get_current_state(str(interaction.guild_id))
                if state and state.is_playing:
                    await self.player.pause_playback(interaction)
                    await interaction.response.send_message("Media paused", ephemeral=True)
                else:
                    await self.player.resume_playback(interaction)
                    await interaction.response.send_message("Media resumed", ephemeral=True)
                    
            elif custom_id == "stop":
                await self.player.stop_playback(interaction)
                await interaction.response.send_message("Media stopped", ephemeral=True)
                self.stop()
                
            elif custom_id == "rewind":
                state = self.player.get_current_state(str(interaction.guild_id))
                if state:
                    new_pos = max(0, state.position - 10)
                    await self.player.seek(interaction, new_pos)
                    await interaction.response.send_message(f"Rewound to {new_pos}s", ephemeral=True)
                    
            elif custom_id == "forward":
                state = self.player.get_current_state(str(interaction.guild_id))
                if state:
                    new_pos = min(state.duration, state.position + 10)
                    await self.player.seek(interaction, new_pos)
                    await interaction.response.send_message(f"Forwarded to {new_pos}s", ephemeral=True)
                    
            return True
            
        except Exception as e:
            logger.error(f"Error handling button interaction: {e}")
            await interaction.response.send_message(
                "Error processing media control", ephemeral=True
            )
            return False

class PlexCommands(commands.GroupCog, group_name="plex"):
    """Plex media commands using slash commands."""
    
    def __init__(self, bot: commands.Bot, plex_url: str, plex_token: str):
        self.bot = bot
        self.player = PlexDiscordPlayer(bot, plex_url, plex_token)
        super().__init__()
        
    async def cog_load(self):
        """Initialize the Plex player when the cog loads."""
        await self.player.initialize()
        
    async def cog_unload(self):
        """Cleanup resources when the cog unloads."""
        await self.player.cleanup()
        
    @app_commands.command(name="play")
    @app_commands.describe(
        media_id="The Plex media ID to play",
        quality="Video quality (optional)",
    )
    @app_commands.choices(quality=[
        app_commands.Choice(name="Original", value="original"),
        app_commands.Choice(name="1080p", value="1080"),
        app_commands.Choice(name="720p", value="720"),
        app_commands.Choice(name="480p", value="480"),
    ])
    async def play_media(
        self, 
        interaction: discord.Interaction, 
        media_id: str, 
        quality: app_commands.Choice[str] = None
    ):
        """Play Plex media in the current channel."""
        await interaction.response.defer()
        
        try:
            # Create embedded player
            embed = await self.player.create_embed_player(
                interaction, 
                media_id,
                quality=quality.value if quality else "original"
            )
            if not embed:
                await interaction.followup.send("Failed to create media player.")
                return
                
            # Create media controls
            view = MediaControlView(self.player)
            
            # Send embed with controls and start playback
            await interaction.followup.send(embed=embed, view=view)
            await self.player.start_playback(interaction)
            
        except Exception as e:
            logger.error(f"Error playing media: {e}")
            await interaction.followup.send(f"Error playing media: {str(e)}")
            
    @app_commands.command(name="search")
    @app_commands.describe(
        query="Search term",
        library="Library to search in (optional)",
    )
    async def search_media(
        self, 
        interaction: discord.Interaction, 
        query: str, 
        library: Optional[str] = None
    ):
        """Search for media in your Plex libraries."""
        await interaction.response.defer()
        
        try:
            results = await self.player.search_media(query, library)
            if not results:
                await interaction.followup.send("No results found.")
                return
                
            # Create select menu for results
            options = [
                discord.SelectOption(
                    label=item.title[:100],  # Discord has a 100-char limit
                    description=f"{item.type.capitalize()} - {item.year}" if hasattr(item, 'year') else item.type.capitalize(),
                    value=item.ratingKey,
                    emoji="🎬" if item.type == "movie" else "📺" if item.type == "episode" else "🎵"
                )
                for item in results[:25]  # Discord has a 25-option limit
            ]
            
            select = discord.ui.Select(
                placeholder="Select media to play...",
                options=options,
                custom_id="media_select"
            )
            
            async def select_callback(select_interaction: discord.Interaction):
                media_id = select_interaction.data["values"][0]
                await self.play_media(select_interaction, media_id)
                
            select.callback = select_callback
            view = discord.ui.View()
            view.add_item(select)
            
            await interaction.followup.send(
                f"Found {len(results)} results for '{query}':", 
                view=view
            )
            
        except Exception as e:
            logger.error(f"Error searching media: {e}")
            await interaction.followup.send(f"Error searching media: {str(e)}")
            
    @app_commands.command(name="status")
    async def media_status(self, interaction: discord.Interaction):
        """Show current media playback status."""
        try:
            state = self.player.get_current_state(str(interaction.guild_id))
            if not state:
                await interaction.response.send_message("No media currently playing.")
                return
                
            embed = discord.Embed(title="Media Status", color=discord.Color.blue())
            embed.add_field(name="Title", value=state.title)
            embed.add_field(
                name="Position", 
                value=f"{state.position//60}:{state.position%60:02d} / {state.duration//60}:{state.duration%60:02d}"
            )
            embed.add_field(name="Status", value="Playing" if state.is_playing else "Paused")
            embed.set_thumbnail(url=state.thumbnail_url)
            
            # Add progress bar
            progress = int((state.position / state.duration) * 20)
            bar = "▓" * progress + "░" * (20 - progress)
            embed.add_field(name="Progress", value=bar, inline=False)
            
            view = MediaControlView(self.player)
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error getting media status: {e}")
            await interaction.response.send_message(f"Error getting media status: {str(e)}")
            
    @app_commands.command(name="libraries")
    async def list_libraries(self, interaction: discord.Interaction):
        """List available Plex libraries."""
        await interaction.response.defer()
        
        try:
            libraries = await self.player.get_libraries()
            
            embed = discord.Embed(
                title="Plex Libraries",
                color=discord.Color.blue(),
                description="Available media libraries:"
            )
            
            for lib in libraries:
                count = await self.player.get_library_count(lib.key)
                embed.add_field(
                    name=lib.title,
                    value=f"Type: {lib.type}\nItems: {count:,}",
                    inline=True
                )
                
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error listing libraries: {e}")
            await interaction.followup.send(f"Error listing libraries: {str(e)}")

async def setup(bot: commands.Bot):
    """Set up the Plex commands cog."""
    # Get Plex configuration from bot
    plex_url = bot.config.get("PLEX_URL")
    plex_token = bot.config.get("PLEX_TOKEN")
    
    if not all([plex_url, plex_token]):
        logger.warning("Plex configuration missing. Plex commands will not be available.")
        return
        
    await bot.add_cog(PlexCommands(bot, plex_url, plex_token)) 