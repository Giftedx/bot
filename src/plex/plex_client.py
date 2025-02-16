"""Plex client for handling Plex server connections and media playback."""

import os
from typing import Dict, List, Optional
from plexapi.server import PlexServer
from plexapi.video import Movie, Episode
from plexapi.audio import Track
from dotenv import load_dotenv

load_dotenv()

class PlexClient:
    """Client for interacting with Plex Media Server."""
    
    def __init__(self):
        """Initialize the Plex client using environment variables."""
        self.base_url = os.getenv('PLEX_URL')
        self.token = os.getenv('PLEX_TOKEN')
        
        if not self.base_url or not self.token:
            raise ValueError("PLEX_URL and PLEX_TOKEN must be set in environment variables")
            
        self.server = PlexServer(self.base_url, self.token)
        
    def search_media(self, query: str, media_type: Optional[str] = None) -> List[Dict]:
        """Search for media on the Plex server.
        
        Args:
            query: Search query string.
            media_type: Optional type filter (movie, show, music).
            
        Returns:
            List of matching media items.
        """
        results = []
        
        if media_type == 'movie' or media_type is None:
            movies = self.server.library.search(query, libtype='movie')
            for movie in movies:
                results.append({
                    'type': 'movie',
                    'title': movie.title,
                    'year': movie.year,
                    'duration': movie.duration,
                    'key': movie.key,
                    'thumb': movie.thumb,
                    'summary': movie.summary
                })
                
        if media_type == 'show' or media_type is None:
            shows = self.server.library.search(query, libtype='show')
            for show in shows:
                results.append({
                    'type': 'show',
                    'title': show.title,
                    'year': show.year,
                    'seasons': len(show.seasons()),
                    'key': show.key,
                    'thumb': show.thumb,
                    'summary': show.summary
                })
                
        if media_type == 'music' or media_type is None:
            tracks = self.server.library.search(query, libtype='track')
            for track in tracks:
                results.append({
                    'type': 'track',
                    'title': track.title,
                    'artist': track.grandparentTitle,
                    'album': track.parentTitle,
                    'duration': track.duration,
                    'key': track.key,
                    'thumb': track.thumb
                })
                
        return results
        
    def get_stream_url(self, media_key: str) -> str:
        """Get the direct stream URL for a media item.
        
        Args:
            media_key: The Plex key for the media item.
            
        Returns:
            Direct stream URL for the media.
            
        Raises:
            ValueError: If media item not found.
        """
        try:
            media = self.server.fetchItem(media_key)
            
            # Get the best quality stream
            part = media.media[0].parts[0]
            
            # Construct direct stream URL
            stream_url = f"{self.base_url}{part.key}?X-Plex-Token={self.token}"
            return stream_url
            
        except Exception as e:
            raise ValueError(f"Failed to get stream URL: {str(e)}")
            
    def get_media_info(self, media_key: str) -> Dict:
        """Get detailed information about a media item.
        
        Args:
            media_key: The Plex key for the media item.
            
        Returns:
            Dict containing media details.
            
        Raises:
            ValueError: If media item not found.
        """
        try:
            media = self.server.fetchItem(media_key)
            
            info = {
                'title': media.title,
                'type': media.type,
                'duration': getattr(media, 'duration', None),
                'summary': getattr(media, 'summary', None),
                'year': getattr(media, 'year', None),
                'thumb': getattr(media, 'thumb', None),
                'art': getattr(media, 'art', None),
                'rating': getattr(media, 'rating', None),
                'stream_url': self.get_stream_url(media_key)
            }
            
            # Add type-specific information
            if isinstance(media, Movie):
                info.update({
                    'studio': media.studio,
                    'director': [d.tag for d in media.directors],
                    'genre': [g.tag for g in media.genres]
                })
            elif isinstance(media, Episode):
                info.update({
                    'show_title': media.grandparentTitle,
                    'season': media.seasonNumber,
                    'episode': media.index
                })
            elif isinstance(media, Track):
                info.update({
                    'artist': media.grandparentTitle,
                    'album': media.parentTitle,
                    'track_number': media.index
                })
                
            return info
            
        except Exception as e:
            raise ValueError(f"Failed to get media info: {str(e)}")
            
    def get_recently_added(self, limit: int = 10, media_type: Optional[str] = None) -> List[Dict]:
        """Get recently added media items.
        
        Args:
            limit: Maximum number of items to return.
            media_type: Optional type filter (movie, show, music).
            
        Returns:
            List of recently added media items.
        """
        results = []
        
        if media_type:
            items = self.server.library.recentlyAdded(maxresults=limit, libtype=media_type)
        else:
            items = self.server.library.recentlyAdded(maxresults=limit)
            
        for item in items:
            results.append(self.get_media_info(item.key))
            
        return results 