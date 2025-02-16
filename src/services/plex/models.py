"""Data models for Plex media and streaming."""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class MediaInfo:
    """Information about a media item."""
    id: str
    title: str
    type: str
    duration: int
    thumb: Optional[str] = None
    year: Optional[int] = None
    summary: Optional[str] = None
    rating: Optional[float] = None
    studio: Optional[str] = None
    added_at: Optional[datetime] = None
    
    @classmethod
    def from_plex(cls, plex_media: Any) -> "MediaInfo":
        """Create MediaInfo from Plex media object."""
        return cls(
            id=str(plex_media.ratingKey),
            title=plex_media.title,
            type=plex_media.type,
            duration=plex_media.duration,
            thumb=plex_media.thumb,
            year=getattr(plex_media, "year", None),
            summary=getattr(plex_media, "summary", None),
            rating=getattr(plex_media, "rating", None),
            studio=getattr(plex_media, "studio", None),
            added_at=getattr(plex_media, "addedAt", None)
        )

@dataclass
class StreamInfo:
    """Information about a media stream."""
    stream_url: str
    duration: int
    media_type: str
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None
    resolution: Optional[str] = None
    bitrate: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stream_url": self.stream_url,
            "duration": self.duration,
            "media_type": self.media_type,
            "video_codec": self.video_codec,
            "audio_codec": self.audio_codec,
            "resolution": self.resolution,
            "bitrate": self.bitrate
        }

@dataclass
class PlaybackState:
    """Current state of media playback."""
    media_id: str
    media: Optional[MediaInfo] = None
    position: float = 0
    duration: float = 0
    is_playing: bool = False
    is_paused: bool = False
    volume: int = 100
    start_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "media_id": self.media_id,
            "media": self.media.to_dict() if self.media else None,
            "position": self.position,
            "duration": self.duration,
            "is_playing": self.is_playing,
            "is_paused": self.is_paused,
            "volume": self.volume,
            "start_time": self.start_time
        }

@dataclass
class PlexSession:
    """Information about a Plex playback session."""
    session_id: str
    media: MediaInfo
    stream_info: StreamInfo
    state: PlaybackState
    user_id: Optional[str] = None
    device_id: Optional[str] = None
    started_at: datetime = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "media": self.media.to_dict(),
            "stream_info": self.stream_info.to_dict(),
            "state": self.state.to_dict(),
            "user_id": self.user_id,
            "device_id": self.device_id,
            "started_at": self.started_at.isoformat()
        } 