"""
Plex command cog for the unified bot.
"""
import logging
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands
from discord import FFmpegPCMAudio, VoiceClient
from src.core.plex_manager import PlexManager
from src.core.exceptions import MediaNotFoundError, PlexConnectionError, PlexAPIError, StreamingError # Updated import path
from src.core.virtual_display import VirtualDisplayManager  # type: ignore

# These imports will need to be verified and potentially adjusted
from src.integrations.plex_discord import PlexDiscordPlayer
from src.app.interactions.components import MediaControlView

logger = logging.getLogger(__name__)

class PlexCog(commands.Cog, name="Plex"):
    """Plex media commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        plex_url = self.bot.config_manager.get_secret("plex.url")
        plex_token = self.bot.config_manager.get_secret("plex.token")
        
        if not all([plex_url, plex_token]):
            raise ValueError("Plex URL or Token is not configured.")
            
        self.player = PlexDiscordPlayer(bot, plex_url, plex_token)
        self.tree = self.bot.tree
        self.plex_manager = PlexManager() # Changed instantiation
        self.display_manager = VirtualDisplayManager()
        self.voice_client: Optional[VoiceClient] = None

    async def cog_load(self):
        """Initialize Plex commands and player."""
        await self.player.initialize()
        self._register_commands()
        
    async def cog_unload(self):
        """Cleanup resources."""
        await self.player.cleanup()
        
    def _register_commands(self):
        """Register all Plex-related commands."""
        
        @self.tree.command(name="plex-play", description="Play media from Plex")
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
            interaction: discord.Interaction, 
            media_id: str, 
            quality: Optional[app_commands.Choice[str]] = None
        ):
            await interaction.response.defer()
            
            try:
                embed = await self.player.create_embed_player(
                    interaction,
                    media_id,
                    quality=quality.value if quality else "original"
                )
                if not embed:
                    await interaction.followup.send("Failed to create media player.")
                    return
                    
                view = MediaControlView(self.player)
                await interaction.followup.send(embed=embed, view=view)
                await self.player.start_playback(interaction)
                
            except Exception as e:
                logger.error(f"Error playing media: {e}")
                await interaction.followup.send(f"Error playing media: {str(e)}")
                
        @self.tree.command(name="plex-search", description="Search for media in Plex")
        @app_commands.describe(
            query="Search term",
            library="Library to search in (optional)",
        )
        async def search_media(
            interaction: discord.Interaction,
            query: str,
            library: Optional[str] = None
        ):
            await interaction.response.defer()
            
            try:
                results = await self.player.search_media(query, library)
                if not results:
                    await interaction.followup.send("No results found.")
                    return
                    
                options = [
                    discord.SelectOption(
                        label=item.title[:100],
                        description=f"{item.type.capitalize()} - {item.year}" if hasattr(item, 'year') else item.type.capitalize(),
                        value=str(item.ratingKey),
                        emoji="🎬" if item.type == "movie" else "📺" if item.type == "episode" else "🎵"
                    )
                    for item in results[:25]
                ]
                
                select = discord.ui.Select(
                    placeholder="Select media to play...",
                    options=options,
                    custom_id="media_select"
                )
                
                async def select_callback(select_interaction: discord.Interaction):
                    # This is a simplification. The original play_media needs the full interaction context.
                    # A more robust solution might involve a custom View that stores context.
                    await select_interaction.response.send_message(f"Initiating playback for item...")
                    # The `play_media` function needs to be callable here with the right context
                    # For now, this callback is a placeholder for the interaction flow.
                    
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
                
        @self.tree.command(name="plex-status", description="Show current media playback status")
        async def media_status(interaction: discord.Interaction):
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
                
                progress = int((state.position / state.duration) * 20)
                bar = "▓" * progress + "░" * (20 - progress)
                embed.add_field(name="Progress", value=bar, inline=False)
                
                view = MediaControlView(self.player)
                await interaction.response.send_message(embed=embed, view=view)
                
            except Exception as e:
                logger.error(f"Error getting media status: {e}")
                await interaction.response.send_message(f"Error getting media status: {str(e)}")
                
        @self.tree.command(name="plex-libraries", description="List available Plex libraries")
        async def list_libraries(interaction: discord.Interaction):
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
    """Set up the Plex cog."""
    try:
        await bot.add_cog(PlexCog(bot))
    except ValueError as e:
        logger.warning(f"Skipping Plex cog setup: {e}")
    except Exception as e:
        logger.error(f"Failed to load Plex cog: {e}")
