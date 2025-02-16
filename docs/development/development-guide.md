# Development Guide

## Table of Contents
1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Development Workflow](#development-workflow)
4. [Code Style Guide](#code-style-guide)
5. [Testing](#testing)
6. [Documentation](#documentation)
7. [Contributing](#contributing)

## Development Environment Setup

### Prerequisites
1. Python 3.8+
2. Node.js 14+
3. Redis
4. Git
5. Docker (optional)

### Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/discord-plex-player.git
   cd discord-plex-player
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   .\venv\Scripts\activate   # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

5. Create development configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your development settings
   ```

### Development Tools

1. **Code Editor Setup**
   - VSCode recommended extensions:
     - Python
     - ESLint
     - Black Formatter
     - Docker

2. **Debugging Tools**
   - VSCode launch configurations in `.vscode/launch.json`
   - Python debugger (pdb)
   - Redis CLI

## Project Structure

```
discord-plex-player/
├── src/
│   ├── bot/                 # Discord bot implementation
│   │   ├── commands/       # Bot commands
│   │   ├── events/         # Event handlers
│   │   └── cogs/          # Bot cogs
│   ├── core/               # Core functionality
│   │   ├── config.py      # Configuration management
│   │   ├── di.py          # Dependency injection
│   │   └── logging.py     # Logging setup
│   ├── services/           # Service implementations
│   │   ├── plex/          # Plex integration
│   │   └── redis/         # Redis cache
│   ├── api/                # REST API implementation
│   │   ├── routes/        # API routes
│   │   └── middleware/    # API middleware
│   └── web/                # Web interface
├── tests/                  # Test suite
├── docs/                   # Documentation
└── scripts/                # Utility scripts
```

## Development Workflow

### Feature Development

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Implement Feature**
   - Follow code style guide
   - Add tests
   - Update documentation

3. **Local Testing**
   ```bash
   # Run tests
   pytest
   
   # Run linters
   flake8
   black .
   
   # Run type checking
   mypy .
   ```

4. **Create Pull Request**
   - Fill out PR template
   - Request review
   - Address feedback

### Code Review Process

1. **Before Review**
   - Tests passing
   - Documentation updated
   - Code style compliant
   - Type checking passed

2. **Review Checklist**
   - Code quality
   - Test coverage
   - Documentation
   - Performance impact
   - Security considerations

3. **After Review**
   - Address feedback
   - Update tests if needed
   - Squash commits if requested

## Code Style Guide

### Python Code Style

1. **Follow PEP 8**
   ```python
   # Good
   def calculate_total(items: List[Item]) -> float:
       return sum(item.price for item in items)
   
   # Bad
   def calculateTotal(items):
       total = 0
       for item in items:
           total = total + item.price
       return total
   ```

2. **Type Hints**
   ```python
   from typing import List, Optional
   
   def get_user(user_id: str) -> Optional[User]:
       return User.get_by_id(user_id)
   ```

3. **Docstrings**
   ```python
   def process_media(media_id: str) -> MediaInfo:
       """
       Process media and return media information.
       
       Args:
           media_id: Unique identifier for the media
           
       Returns:
           MediaInfo object containing processed media data
           
       Raises:
           MediaNotFoundError: If media_id is invalid
       """
   ```

### JavaScript Code Style

1. **ES6+ Features**
   ```javascript
   // Use modern JavaScript features
   const { title, duration } = mediaInfo;
   const players = users.map(user => user.player);
   ```

2. **Async/Await**
   ```javascript
   async function fetchMediaInfo(mediaId) {
       try {
           const response = await api.get(`/media/${mediaId}`);
           return response.data;
       } catch (error) {
           console.error('Failed to fetch media:', error);
           throw error;
       }
   }
   ```

## Testing

### Unit Tests

1. **Test Structure**
   ```python
   def test_media_processing():
       # Arrange
       media_id = "test_123"
       expected_title = "Test Media"
       
       # Act
       result = process_media(media_id)
       
       # Assert
       assert result.title == expected_title
   ```

2. **Mocking**
   ```python
   @patch('services.plex.client.PlexClient')
   def test_media_fetch(mock_plex):
       mock_plex.return_value.get_media.return_value = {
           'title': 'Test Movie'
       }
       result = fetch_media('123')
       assert result['title'] == 'Test Movie'
   ```

### Integration Tests

1. **API Tests**
   ```python
   def test_media_api():
       client = TestClient(app)
       response = client.get('/api/media/123')
       assert response.status_code == 200
       assert 'title' in response.json()
   ```

2. **WebSocket Tests**
   ```python
   async def test_websocket():
       async with websockets.connect(WS_URL) as ws:
           await ws.send(json.dumps({'type': 'join'}))
           response = await ws.recv()
           assert json.loads(response)['type'] == 'welcome'
   ```

## Documentation

### Code Documentation

1. **Function Documentation**
   ```python
   def process_playback(
       media_id: str,
       position: int,
       volume: float
   ) -> PlaybackState:
       """
       Process media playback state change.
       
       Args:
           media_id: Media identifier
           position: Playback position in milliseconds
           volume: Playback volume (0.0 to 1.0)
           
       Returns:
           Updated PlaybackState
       """
   ```

2. **Class Documentation**
   ```python
   class MediaPlayer:
       """
       Handles media playback and synchronization.
       
       Attributes:
           current_media: Currently playing media
           volume: Current volume level
           
       Methods:
           play: Start media playback
           pause: Pause media playback
       """
   ```

### API Documentation

1. **OpenAPI/Swagger**
   ```yaml
   /media/{media_id}:
     get:
       summary: Get media information
       parameters:
         - name: media_id
           in: path
           required: true
           schema:
             type: string
   ```

2. **WebSocket Events**
   ```markdown
   ## Event: media_update
   Sent when media state changes
   
   ```json
   {
       "type": "media_update",
       "data": {
           "media_id": "123",
           "status": "playing"
       }
   }
   ```
   ```

## Contributing

### Getting Started

1. Fork the repository
2. Set up development environment
3. Create feature branch
4. Implement changes
5. Submit pull request

### Pull Request Guidelines

1. **PR Title Format**
   ```
   feat: Add new media control features
   fix: Resolve WebSocket connection issues
   docs: Update API documentation
   ```

2. **PR Description**
   - Clear description of changes
   - Related issue numbers
   - Breaking changes
   - Testing steps

### Release Process

1. **Version Bump**
   ```bash
   bump2version patch  # or minor/major
   ```

2. **Changelog Update**
   - Add new version section
   - List changes
   - Credit contributors

3. **Release Creation**
   - Tag version
   - Create GitHub release
   - Update documentation

## Best Practices

### Error Handling

1. **Custom Exceptions**
   ```python
   class MediaError(Exception):
       """Base exception for media operations."""
       pass
   
   class MediaNotFoundError(MediaError):
       """Raised when media is not found."""
       pass
   ```

2. **Error Recovery**
   ```python
   try:
       media = fetch_media(media_id)
   except MediaNotFoundError:
       logger.error(f"Media {media_id} not found")
       raise HTTPException(status_code=404)
   except MediaError as e:
       logger.error(f"Media error: {e}")
       raise HTTPException(status_code=500)
   ```

### Performance Optimization

1. **Caching**
   ```python
   @cache.memoize(timeout=300)
   def get_media_info(media_id: str) -> dict:
       return fetch_media_from_plex(media_id)
   ```

2. **Batch Operations**
   ```python
   async def update_multiple_sessions(sessions: List[Session]):
       await asyncio.gather(*[
           update_session(session)
           for session in sessions
       ])
   ```

### Security

1. **Input Validation**
   ```python
   def process_user_input(data: dict):
       if not isinstance(data.get('volume'), (int, float)):
           raise ValueError("Volume must be a number")
       if not 0 <= data['volume'] <= 1:
           raise ValueError("Volume must be between 0 and 1")
   ```

2. **Authentication**
   ```python
   def require_auth(func):
       @wraps(func)
       def wrapper(*args, **kwargs):
           if not is_authenticated():
               raise UnauthorizedError()
           return func(*args, **kwargs)
       return wrapper
   ```

## Debugging

### Logging

1. **Structured Logging**
   ```python
   logger.info("Processing media", extra={
       'media_id': media.id,
       'user_id': user.id,
       'action': 'play'
   })
   ```

2. **Error Tracking**
   ```python
   try:
       process_media(media_id)
   except Exception as e:
       logger.exception("Media processing failed")
       sentry_sdk.capture_exception(e)
   ```

### Monitoring

1. **Health Checks**
   ```python
   @app.get("/health")
   async def health_check():
       return {
           "status": "healthy",
           "redis": await check_redis(),
           "plex": await check_plex()
       }
   ```

2. **Performance Metrics**
   ```python
   @metrics.timer('media.process_time')
   def process_media(media_id: str):
       # Process media
       pass
   ```

## Support

For development support:
1. Check existing issues
2. Join developer Discord channel
3. Review documentation
4. Contact maintainers 