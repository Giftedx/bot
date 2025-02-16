# Error Handling Architecture

## Exception Hierarchy

### Battle System Exceptions
Base: `BattleSystemError`
- `InvalidMoveError` - Invalid move attempted
- `InvalidBattleStateError` - Battle state is invalid
- `PlayerNotInBattleError` - Player not in active battle
- `BattleAlreadyInProgressError` - Player already in battle
- `ResourceError` - Insufficient resources for move
- `StatusEffectError` - Status effect prevents action
- `DatabaseError` - Database operation failure
- `ValidationError` - Input validation failure
- `RateLimitError` - Rate limit exceeded
- `BackpressureError` - System load management
- `ConfigurationError` - Battle configuration error
- `LoggingError` - Battle logging failure

### Media System Exceptions
Base: `Exception`
- `PlexConnectionError` - Failed to connect to Plex server
- `MediaNotFoundError` - Requested media not found
- `AuthenticationError` - Authentication failure
- `StreamError` - Streaming operation failure

### Infrastructure Exceptions
Base: `Exception`
- `CacheError` - Cache operation failure
- `WebSocketError` - WebSocket communication error
- `ConfigurationError` - System configuration error

## Error Handling Strategy

1. **Battle System**
   - All battle-related errors inherit from `BattleSystemError`
   - Errors are caught and handled at the command level
   - Appropriate user feedback is provided
   - Failed operations are logged

2. **Media System**
   - Media errors are independent exceptions
   - Connection issues are retried with backoff
   - User-friendly error messages are displayed
   - Failed streams are automatically cleaned up

3. **Infrastructure**
   - System-level errors trigger monitoring alerts
   - Failed operations are logged with full context
   - Automatic recovery is attempted where possible
   - Errors are reported to monitoring systems 