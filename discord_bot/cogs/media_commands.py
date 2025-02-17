"""Media commands for Plex integration."""

from discord.ext import commands
import discord
from plexapi.server import PlexServer
from plexapi.exceptions import NotFound, Unauthorized
import asyncio
from typing import Optional, List
import datetime

class MediaCommands(commands.Cog, name="Media"):
    """Media server integration and playback commands.
    
    This category includes commands for:
    - Searching Plex media library
    - Playing media on Plex clients
    - Viewing media information
    - Managing playlists
    - Viewing recently added content
    
    Requires:
    - Configured Plex server
    - Valid Plex authentication token
    - At least one Plex client
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.plex = None
        self.setup_plex()
    
    def setup_plex(self):
        """Set up connection to Plex server."""
        try:
            baseurl = self.bot.config.PLEX_URL
            token = self.bot.config.PLEX_TOKEN
            
            if baseurl and token:
                self.plex = PlexServer(baseurl, token)
        except Exception as e:
            print(f"Error connecting to Plex: {e}")
    
    @commands.group(name="plex", invoke_without_command=True)
    async def plex_group(self, ctx):
        """Plex media commands. Use subcommands search/play/info.
        
        This is a command group for Plex media server integration.
        Use one of the subcommands to interact with your Plex server.
        
        Subcommands:
        ------------
        search - Search for media
        play - Play media on a Plex client
        info - Get detailed media information
        recent - Show recently added media
        
        Examples:
        ---------
        !plex search Avengers
        !plex play "The Matrix"
        !plex info "Star Wars"
        !plex recent
        
        Notes:
        ------
        - Requires configured Plex server
        - Some commands require active Plex client
        """
        await ctx.send_help(ctx.command)
    
    @plex_group.command(name="search")
    async def search_media(self, ctx, *, query: str):
        """Search for media on the Plex server.
        
        Searches across all libraries (movies, TV shows, music)
        and returns the top 5 matches.
        
        Parameters:
        -----------
        query: The search term(s)
        
        Examples:
        ---------
        !plex search Avengers
        !plex search "Breaking Bad"
        !plex search "The Office"
        
        Notes:
        ------
        - Searches all media types
        - Shows up to 5 results
        - Includes basic media info
        """
        if not self.plex:
            await ctx.send("Plex integration is not configured!")
            return
            
        try:
            # Search all libraries
            results = self.plex.library.search(query, limit=5)
            
            if not results:
                await ctx.send(f"No results found for '{query}'")
                return
                
            # Create embed
            embed = discord.Embed(
                title=f"Search Results: {query}",
                color=discord.Color.blue()
            )
            
            for item in results:
                # Format details based on media type
                if hasattr(item, 'type'):
                    if item.type == 'movie':
                        details = f"Year: {item.year}\nRating: {getattr(item, 'rating', 'N/A')}\nDuration: {item.duration}"
                    elif item.type == 'show':
                        details = f"Years: {item.year}-{getattr(item, 'year', 'Present')}\nRating: {getattr(item, 'rating', 'N/A')}\nSeasons: {len(item.seasons())}"
                    elif item.type == 'episode':
                        details = f"Show: {item.grandparentTitle}\nSeason {item.parentIndex} Episode {item.index}\nAir Date: {item.originallyAvailableAt}"
                    else:
                        details = "No details available"
                else:
                    details = "No details available"
                
                embed.add_field(
                    name=f"{item.title} ({getattr(item, 'type', 'Unknown').capitalize()})",
                    value=details,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"Error searching Plex: {e}")
    
    @plex_group.command(name="play")
    async def play_media(self, ctx, *, title: str):
        """Start playing media on the Plex server.
        
        Searches for and plays the specified media on the first
        available Plex client.
        
        Parameters:
        -----------
        title: The title of the media to play
        
        Examples:
        ---------
        !plex play "The Matrix"
        !plex play "Friends S01E01"
        !plex play "Inception"
        
        Notes:
        ------
        - Requires active Plex client
        - Plays first search result
        - Can play movies or TV episodes
        """
        if not self.plex:
            await ctx.send("Plex integration is not configured!")
            return
            
        try:
            # Search for the media
            results = self.plex.library.search(title, limit=1)
            
            if not results:
                await ctx.send(f"No results found for '{title}'")
                return
                
            media = results[0]
            
            # Start playback (note: this requires a Plex client to be configured)
            try:
                clients = self.plex.clients()
                if not clients:
                    await ctx.send("No available Plex clients found!")
                    return
                    
                client = clients[0]  # Use first available client
                client.playMedia(media)
                
                embed = discord.Embed(
                    title="Now Playing",
                    description=f"Started playing {media.title}",
                    color=discord.Color.green()
                )
                
                if hasattr(media, 'type'):
                    if media.type == 'movie':
                        embed.add_field(name="Year", value=media.year)
                        embed.add_field(name="Duration", value=str(datetime.timedelta(milliseconds=media.duration)))
                    elif media.type == 'episode':
                        embed.add_field(name="Show", value=media.grandparentTitle)
                        embed.add_field(name="Season", value=media.parentIndex)
                        embed.add_field(name="Episode", value=media.index)
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"Error starting playback: {e}")
                
        except Exception as e:
            await ctx.send(f"Error accessing Plex: {e}")
    
    @plex_group.command(name="info")
    async def media_info(self, ctx, *, title: str):
        """Get detailed information about media.
        
        Shows comprehensive information about the specified media,
        including metadata, ratings, and availability.
        
        Parameters:
        -----------
        title: The title to get information about
        
        Examples:
        ---------
        !plex info "The Dark Knight"
        !plex info "Stranger Things"
        !plex info "The Office S03E01"
        
        Notes:
        ------
        - Shows detailed metadata
        - Includes artwork if available
        - Works with movies and TV shows
        """
        if not self.plex:
            await ctx.send("Plex integration is not configured!")
            return
            
        try:
            # Search for the media
            results = self.plex.library.search(title, limit=1)
            
            if not results:
                await ctx.send(f"No results found for '{title}'")
                return
                
            media = results[0]
            
            # Create embed with detailed information
            embed = discord.Embed(
                title=media.title,
                description=getattr(media, 'summary', 'No summary available'),
                color=discord.Color.blue()
            )
            
            if hasattr(media, 'type'):
                embed.add_field(name="Type", value=media.type.capitalize())
                
                if media.type == 'movie':
                    embed.add_field(name="Year", value=media.year)
                    embed.add_field(name="Rating", value=getattr(media, 'rating', 'N/A'))
                    embed.add_field(name="Duration", value=str(datetime.timedelta(milliseconds=media.duration)))
                    embed.add_field(name="Studio", value=getattr(media, 'studio', 'N/A'))
                    
                    if hasattr(media, 'genres'):
                        genres = ", ".join(genre.tag for genre in media.genres)
                        embed.add_field(name="Genres", value=genres or "N/A")
                        
                elif media.type == 'show':
                    embed.add_field(name="Years", value=f"{media.year}-{getattr(media, 'year', 'Present')}")
                    embed.add_field(name="Rating", value=getattr(media, 'rating', 'N/A'))
                    embed.add_field(name="Seasons", value=len(media.seasons()))
                    
                    if hasattr(media, 'genres'):
                        genres = ", ".join(genre.tag for genre in media.genres)
                        embed.add_field(name="Genres", value=genres or "N/A")
                        
                elif media.type == 'episode':
                    embed.add_field(name="Show", value=media.grandparentTitle)
                    embed.add_field(name="Season", value=media.parentIndex)
                    embed.add_field(name="Episode", value=media.index)
                    embed.add_field(name="Air Date", value=media.originallyAvailableAt)
                    embed.add_field(name="Duration", value=str(datetime.timedelta(milliseconds=media.duration)))
            
            # Add thumbnail if available
            if hasattr(media, 'thumb'):
                embed.set_thumbnail(url=media.thumb)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"Error getting media info: {e}")
    
    @plex_group.command(name="recent")
    async def recent_media(self, ctx, limit: int = 5):
        """Show recently added media.
        
        Displays the most recently added content to your Plex server.
        
        Parameters:
        -----------
        limit: Number of items to show (default: 5, max: 10)
        
        Examples:
        ---------
        !plex recent
        !plex recent 10
        
        Notes:
        ------
        - Shows newest items first
        - Includes all media types
        - Shows add date
        """
        if not self.plex:
            await ctx.send("Plex integration is not configured!")
            return
            
        try:
            # Get recently added items
            recent = self.plex.library.recentlyAdded()[:limit]
            
            if not recent:
                await ctx.send("No recent media found!")
                return
                
            embed = discord.Embed(
                title="Recently Added Media",
                color=discord.Color.blue()
            )
            
            for item in recent:
                if hasattr(item, 'type'):
                    if item.type == 'movie':
                        details = f"Year: {item.year}\nAdded: {item.addedAt.strftime('%Y-%m-%d')}"
                    elif item.type == 'episode':
                        details = f"Show: {item.grandparentTitle}\nSeason {item.parentIndex} Episode {item.index}\nAdded: {item.addedAt.strftime('%Y-%m-%d')}"
                    else:
                        details = f"Added: {item.addedAt.strftime('%Y-%m-%d')}"
                else:
                    details = f"Added: {item.addedAt.strftime('%Y-%m-%d')}"
                
                embed.add_field(
                    name=f"{item.title} ({getattr(item, 'type', 'Unknown').capitalize()})",
                    value=details,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"Error getting recent media: {e}")
    
    @plex_group.command(name="ondeck")
    async def on_deck(self, ctx):
        """Show on deck items (recently watched, in progress)."""
        if not self.plex:
            await ctx.send("Plex integration is not configured!")
            return
            
        try:
            # Get on deck items
            deck = self.plex.library.onDeck()
            
            if not deck:
                await ctx.send("No items on deck!")
                return
                
            embed = discord.Embed(
                title="On Deck",
                description="Continue watching these items:",
                color=discord.Color.blue()
            )
            
            for item in deck:
                if hasattr(item, 'type') and item.type == 'episode':
                    details = (f"Show: {item.grandparentTitle}\n"
                             f"Season {item.parentIndex} Episode {item.index}\n"
                             f"Progress: {item.viewOffset // 1000 // 60}/"
                             f"{item.duration // 1000 // 60} minutes")
                else:
                    details = (f"Progress: {item.viewOffset // 1000 // 60}/"
                             f"{item.duration // 1000 // 60} minutes")
                
                embed.add_field(
                    name=item.title,
                    value=details,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"Error getting on deck items: {e}")

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(MediaCommands(bot)) 