"""Media player service using VLC."""
import logging
import os
from typing import Optional, Dict, Any
import vlc

from ...core.config import Config

logger = logging.getLogger(__name__)

class MediaPlayer:
    """VLC-based media player."""
    
    def __init__(self):
        """Initialize the media player."""
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.current_media: Optional[vlc.Media] = None
        self._setup_player()
        
    def _setup_player(self) -> None:
        """Configure VLC media player."""
        try:
            # Set up event manager
            self.event_manager = self.player.event_manager()
            
            # Configure player settings
            self.player.audio_set_volume(100)
            
            logger.info("Media player initialized")
        except Exception as e:
            logger.error(f"Failed to set up media player: {e}")
            raise
            
    def start(self, url: str) -> bool:
        """Start playing media from URL."""
        try:
            # Create media
            self.current_media = self.instance.media_new(url)
            
            # Set player media
            self.player.set_media(self.current_media)
            
            # Start playback
            return bool(self.player.play())
            
        except Exception as e:
            logger.error(f"Failed to start playback: {e}")
            return False
            
    def stop(self) -> None:
        """Stop playback."""
        try:
            self.player.stop()
            self.current_media = None
        except Exception as e:
            logger.error(f"Failed to stop playback: {e}")
            
    def pause(self) -> None:
        """Pause playback."""
        try:
            self.player.pause()
        except Exception as e:
            logger.error(f"Failed to pause playback: {e}")
            
    def resume(self) -> None:
        """Resume playback."""
        try:
            self.player.play()
        except Exception as e:
            logger.error(f"Failed to resume playback: {e}")
            
    def set_volume(self, volume: int) -> None:
        """Set player volume (0-100)."""
        try:
            self.player.audio_set_volume(max(0, min(100, volume)))
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            
    def seek(self, position: float) -> None:
        """Seek to position (0.0-1.0)."""
        try:
            self.player.set_position(max(0.0, min(1.0, position)))
        except Exception as e:
            logger.error(f"Failed to seek: {e}")
            
    def get_state(self) -> Dict[str, Any]:
        """Get current player state."""
        try:
            return {
                "is_playing": self.player.is_playing(),
                "position": self.player.get_position(),
                "time": self.player.get_time(),
                "length": self.player.get_length(),
                "volume": self.player.audio_get_volume(),
                "state": str(self.player.get_state())
            }
        except Exception as e:
            logger.error(f"Failed to get player state: {e}")
            return {}
            
    def cleanup(self) -> None:
        """Clean up player resources."""
        try:
            self.stop()
            self.player.release()
            self.instance.release()
        except Exception as e:
            logger.error(f"Failed to clean up player: {e}")
            
    def __del__(self):
        """Ensure resources are cleaned up."""
        self.cleanup() 