"""Custom exceptions for the application."""


# --- Battle System Exceptions ---
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


class DatabaseError(
    BattleSystemError
):  # Note: Was BattleSystemError, could be a more general DB error too.
    """Raised when database operation fails."""

    pass


class ValidationError(
    BattleSystemError
):  # Note: Was BattleSystemError, could be a more general Validation error.
    """Raised when input validation fails."""

    pass


class RateLimitError(BattleSystemError):
    """Raised when action rate limit is exceeded."""

    pass


class BackpressureError(BattleSystemError):
    """Raised when system is under too much load."""

    pass


# class ConfigurationError(BattleSystemError): # This was specific to BattleSystem
#     """Raised when configuration is invalid."""
#     pass


class LoggingError(BattleSystemError):
    """Raised when logging operation fails."""

    pass


# --- General Application Exceptions ---


class ConfigurationError(Exception):  # More general ConfigurationError
    """Raised when there's an error with configuration."""

    pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class CacheError(Exception):
    """Raised when there's an error with caching operations."""

    pass


class WebSocketError(Exception):
    """Raised when there's an error with WebSocket operations."""

    pass


# --- Plex Specific Exceptions (as refactored) ---
class StreamingError(Exception):  # Base for Plex streaming/API issues
    """Base exception for streaming-related errors."""

    pass


class MediaNotFoundError(StreamingError):
    """Raised when requested media is not found."""

    pass


class PlexConnectionError(StreamingError):
    """Raised when connection to Plex server fails."""

    pass


class PlexAPIError(StreamingError):
    """Raised for general Plex API errors."""

    pass


# --- Other specific exceptions can be added below ---
