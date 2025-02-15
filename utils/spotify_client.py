import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SpotifyClient:
    def __init__(self):
        try:
            client_id = os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                raise ValueError(
                    "Spotify credentials not found in environment variables"
                )
                
            auth_manager = SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
            self.spotify = spotipy.Spotify(auth_manager=auth_manager)
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client: {e}")
            raise

    async def get_track_info(self, url: str) -> Optional[Dict]:
        """Get track information from Spotify URL"""
        try:
            # Extract track ID from URL
            if 'track/' not in url:
                return None
                
            track_id = url.split('track/')[-1].split('?')[0]
            track = self.spotify.track(track_id)
            
            artist_name = track['artists'][0]['name']
            return {
                'title': f"{track['name']} - {artist_name}",
                'duration': track['duration_ms'] // 1000,
                'artist': artist_name,
                'album': track['album']['name'],
                'url': track['external_urls']['spotify']
            }
        except Exception as e:
            logger.error(f"Error getting track info: {e}")
            return None

    async def get_playlist_tracks(self, url: str) -> List[Dict]:
        """Get all tracks from a Spotify playlist"""
        try:
            if 'playlist/' not in url:
                return []
                
            playlist_id = url.split('playlist/')[-1].split('?')[0]
            results = self.spotify.playlist_tracks(playlist_id)
            tracks = []
            
            for item in results['items']:
                track = item['track']
                artist_name = track['artists'][0]['name']
                tracks.append({
                    'title': f"{track['name']} - {artist_name}",
                    'duration': track['duration_ms'] // 1000,
                    'artist': artist_name,
                    'album': track['album']['name'],
                    'url': track['external_urls']['spotify']
                })
            
            return tracks
        except Exception as e:
            logger.error(f"Error getting playlist tracks: {e}")
            return []

    async def search_track(self, query: str) -> Optional[Dict]:
        """Search for a track on Spotify"""
        try:
            results = self.spotify.search(q=query, type='track', limit=1)
            if not results['tracks']['items']:
                return None
                
            track = results['tracks']['items'][0]
            artist_name = track['artists'][0]['name']
            return {
                'title': f"{track['name']} - {artist_name}",
                'duration': track['duration_ms'] // 1000,
                'artist': artist_name,
                'album': track['album']['name'],
                'url': track['external_urls']['spotify']
            }
        except Exception as e:
            logger.error(f"Error searching track: {e}")
            return None