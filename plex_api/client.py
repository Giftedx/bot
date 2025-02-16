from plexapi.server import PlexServer
from plexapi.myplex import MyPlexAccount
import logging
from typing import Dict, List, Optional, Union
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import Config

logger = logging.getLogger(__name__)

class PlexClient:
    def __init__(self, baseurl: str, token: str):
        """Initialize Plex client with server URL and authentication token."""
        try:
            self.server = PlexServer(baseurl, token)
            logger.info("Successfully connected to Plex server")
        except Exception as e:
            logger.error(f"Failed to connect to Plex server: {e}")
            raise
            
    def get_libraries(self) -> List[Dict]:
        """Get all available libraries."""
        try:
            libraries = self.server.library.sections()
            return [
                {
                    'id': library.key,
                    'title': library.title,
                    'type': library.type,
                    'count': library.totalSize
                }
                for library in libraries
            ]
        except Exception as e:
            logger.error(f"Error fetching libraries: {e}")
            return []
            
    def search(self, query: str, library_id: Optional[str] = None) -> List[Dict]:
        """Search for media items across all or specific libraries."""
        try:
            if library_id:
                library = self.server.library.sectionByID(library_id)
                results = library.search(query)
            else:
                results = self.server.library.search(query)
                
            return [
                {
                    'id': item.key,
                    'title': item.title,
                    'type': item.type,
                    'year': getattr(item, 'year', None),
                    'thumb': item.thumb if hasattr(item, 'thumb') else None,
                    'summary': item.summary if hasattr(item, 'summary') else None
                }
                for item in results
            ]
        except Exception as e:
            logger.error(f"Error searching media: {e}")
            return []
            
    def get_media_info(self, media_id: str) -> Optional[Dict]:
        """Get detailed information about a specific media item."""
        try:
            item = self.server.fetchItem(media_id)
            if not item:
                return None
                
            # Get media streams
            streams = []
            if hasattr(item, 'media'):
                for media in item.media:
                    for part in media.parts:
                        streams.append({
                            'id': part.id,
                            'file': part.file,
                            'duration': media.duration,
                            'width': media.width,
                            'height': media.height,
                            'bitrate': media.bitrate,
                            'stream_url': self._get_stream_url(item, part)
                        })
                        
            return {
                'id': item.key,
                'title': item.title,
                'type': item.type,
                'year': getattr(item, 'year', None),
                'summary': getattr(item, 'summary', None),
                'duration': getattr(item, 'duration', None),
                'streams': streams
            }
        except Exception as e:
            logger.error(f"Error fetching media info: {e}")
            return None
            
    def start_transcode(self, media_id: str, quality: str = '1080p') -> Optional[str]:
        """Start transcoding a media item and return the stream URL."""
        try:
            item = self.server.fetchItem(media_id)
            if not item:
                return None
                
            # Set transcoding parameters
            params = {
                'protocol': 'hls',
                'videoQuality': quality,
                'videoResolution': quality,
                'maxVideoBitrate': self._get_bitrate_for_quality(quality),
                'directPlay': 0,
                'directStream': 0,
                'subtitles': 'burn'
            }
            
            # Get transcoding session URL
            session = item.getStreamURL(**params)
            return session
        except Exception as e:
            logger.error(f"Error starting transcode: {e}")
            return None
            
    def _get_stream_url(self, item, part) -> str:
        """Generate direct stream URL for a media part."""
        token = self.server._token
        return f"{self.server._baseurl}{part.key}?X-Plex-Token={token}"
        
    def _get_bitrate_for_quality(self, quality: str) -> int:
        """Get recommended bitrate for quality level."""
        bitrates = {
            '4k': 40000,
            '1080p': 8000,
            '720p': 4000,
            '480p': 2000,
            '360p': 1000
        }
        return bitrates.get(quality.lower(), 8000)  # Default to 1080p bitrate 