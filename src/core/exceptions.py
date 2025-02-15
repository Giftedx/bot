"""Core exceptions for the application."""


class ApplicationError(Exception):
    """Base class for all application exceptions."""
    pass


class ConfigurationError(ApplicationError):
    """Raised when there is a configuration error."""
    pass


class PlexError(ApplicationError):
    """Base class for Plex-related exceptions."""
    pass


class PlexConnectionError(PlexError):
    """Raised when connection to Plex server fails."""
    pass


class PlexAuthError(PlexError):
    """Raised when Plex authentication fails."""
    pass


class MediaNotFoundError(PlexError):
    """Raised when requested media is not found."""
    pass


class StreamingError(PlexError):
    """Raised when streaming operations fail."""
    pass


class ClientNotFoundError(PlexError):
    """Raised when specified Plex client is not found."""
    pass


class PlaybackError(PlexError):
    """Raised when media playback fails."""
    pass