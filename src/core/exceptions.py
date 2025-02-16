"""Custom exceptions for battle system."""


class BattleSystemError(Exception):
    """Base exception for battle system errors."""

    pass


class InvalidMoveError(BattleSystemError):
    """Raised when an invalid move is attempted."""

    pass


class InvalidBattleStateError(BattleSystemError):
    """Raised when battle state is invalid."""

    pass


class PlayerNotInBattleError(BattleSystemError):
    """Raised when player is not in an active battle."""

    pass


class BattleAlreadyInProgressError(BattleSystemError):
    """Raised when player is already in a battle."""

    pass


class ResourceError(BattleSystemError):
    """Raised when insufficient resources for move."""

    pass


class StatusEffectError(BattleSystemError):
    """Raised when status effect prevents action."""

    pass


class DatabaseError(BattleSystemError):
    """Raised when database operation fails."""

    pass


class ValidationError(BattleSystemError):
    """Raised when input validation fails."""

    pass


class RateLimitError(BattleSystemError):
    """Raised when action rate limit is exceeded."""

    pass


class BackpressureError(BattleSystemError):
    """Raised when system is under too much load."""

    pass


class ConfigurationError(BattleSystemError):
    """Raised when configuration is invalid."""

    pass


class LoggingError(BattleSystemError):
    """Raised when logging operation fails."""

    pass


"""Custom exceptions for the application."""

class PlexConnectionError(Exception):
    """Raised when unable to connect to Plex server."""
    pass

class MediaNotFoundError(Exception):
    """Raised when requested media is not found."""
    pass

class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass

class StreamError(Exception):
    """Raised when there's an error with media streaming."""
    pass

class CacheError(Exception):
    """Raised when there's an error with caching operations."""
    pass

class WebSocketError(Exception):
    """Raised when there's an error with WebSocket operations."""
    pass

class ConfigurationError(Exception):
    """Raised when there's an error with configuration."""
    pass
