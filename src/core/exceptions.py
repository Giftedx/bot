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
