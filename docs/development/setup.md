# Development Environment Setup

## Prerequisites

### Required Software
1. **Core Development Tools**
   - Python 3.12 or higher
   - Docker/Podman
   - Git
   - VSCode (recommended)
   - WSL2 (for Windows users)

2. **Database Systems**
   - PostgreSQL 14+
   - Redis 6+

3. **Additional Tools**
   - Node.js 18+ (for frontend)
   - FFmpeg (for media features)
   - Make (for build scripts)

## Initial Setup

### 1. Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd <project-directory>

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Development Containers
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
      POSTGRES_DB: app_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 3. Configuration
```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your settings
DISCORD_TOKEN=your_token
PLEX_URL=your_plex_url
PLEX_TOKEN=your_plex_token
DATABASE_URL=postgresql://dev:dev@localhost:5432/app_dev
REDIS_URL=redis://localhost:6379
```

## Development Workflow

### 1. Code Standards
```bash
# Install development tools
pip install -r requirements-dev.txt

# Format code
black .

# Check types
mypy .

# Run linter
flake8
```

### 2. Testing
```bash
# Run all tests
pytest

# Run with coverage
coverage run -m pytest
coverage report

# Run specific tests
pytest tests/test_specific.py
```

### 3. Git Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes and commit
git add .
git commit -m "feat: your feature description"

# Push changes
git push origin feature/your-feature
```

## IDE Setup

### 1. VSCode Extensions
- Python
- Docker
- Git Lens
- Black Formatter
- Mermaid Preview
- Remote - WSL

### 2. VSCode Settings
```json
{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

## Debugging

### 1. Local Debugging
```python
# Add to your code
import debugpy

# Wait for debugger attachment
debugpy.listen(5678)
debugpy.wait_for_client()
```

### 2. VSCode Launch Configuration
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Remote Attach",
            "type": "python",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678
            }
        }
    ]
}
```

## Common Issues

### 1. Database Connection
- Check PostgreSQL service is running
- Verify connection string in .env
- Ensure database exists
- Check user permissions

### 2. Redis Connection
- Verify Redis service is running
- Check Redis URL in .env
- Test connection with redis-cli

### 3. Discord Integration
- Verify bot token is valid
- Check required intents are enabled
- Verify bot permissions

## Monitoring Development

### 1. Logging
```python
# Configure logging
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 2. Performance Profiling
```python
# Use cProfile
import cProfile

def profile_code():
    profiler = cProfile.Profile()
    profiler.enable()
    # Your code here
    profiler.disable()
    profiler.print_stats(sort='cumulative')
```

## Documentation

### 1. Code Documentation
```python
def example_function(arg1: str, arg2: int) -> bool:
    """Short description of function.

    Extended description of function.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: Description of when this error is raised
    """
    pass
```

### 2. API Documentation
```python
@app.get("/example")
async def example_endpoint():
    """Example endpoint.

    Returns:
        JSON response with example data.

    Raises:
        HTTPException: When example fails.
    """
    pass
```

## Deployment Testing

### 1. Local Deployment
```bash
# Build containers
docker-compose -f docker-compose.dev.yml build

# Start services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f
```

### 2. Testing Production Build
```bash
# Build production image
docker build -t app:latest .

# Run production container
docker run -p 8000:8000 app:latest
``` 