"""Data models for Plex integration."""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class StreamInfo:
    """Information about a media stream."""

    url: str
    quality: str
    direct_play: bool
    expires_at: datetime

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "quality": self.quality,
            "direct_play": self.direct_play,
            "expires_at": self.expires_at.isoformat(),
        }


@dataclass
class MediaInfo:
    """Information about a media item."""

    id: str
    title: str
    type: str
    duration: int
    thumb: Optional[str] = None
    summary: Optional[str] = None
    year: Optional[int] = None
    rating: Optional[float] = None

    @classmethod
    def from_plex(cls, plex_item: Any) -> "MediaInfo":
        """Create MediaInfo from Plex media item."""
        return cls(
            id=str(plex_item.ratingKey),
            title=plex_item.title,
            type=plex_item.type,
            duration=plex_item.duration,
            thumb=plex_item.thumb,
            summary=plex_item.summary,
            year=getattr(plex_item, "year", None),
            rating=getattr(plex_item, "rating", None),
        )

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "duration": self.duration,
            "thumb": self.thumb,
            "summary": self.summary,
            "year": self.year,
            "rating": self.rating,
        }


@dataclass
class PlaybackState:
    """Current playback state."""

    media_id: str
    position: int
    duration: int
    is_playing: bool
    volume: float
    timestamp: datetime

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "media_id": self.media_id,
            "position": self.position,
            "duration": self.duration,
            "is_playing": self.is_playing,
            "volume": self.volume,
            "timestamp": self.timestamp.isoformat(),
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
            "media": self.media.dict(),
            "stream_info": self.stream_info.dict(),
            "state": self.state.dict(),
            "user_id": self.user_id,
            "device_id": self.device_id,
            "started_at": self.started_at.isoformat(),
        }
