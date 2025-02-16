# Development Guide

## Overview

This guide covers development practices, standards, and workflows for the Discord application.

## Development Environment

### Prerequisites
1. Python 3.12+
2. Redis
3. PostgreSQL (optional)
4. FFmpeg
5. Git
6. Discord Developer Account

### Setup
1. Install Python dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Set up pre-commit hooks:
```bash
pre-commit install
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with development credentials
```

## Code Structure

### Application Core (`src/app/`)
- `client.py`: Discord application client
- `commands/`: Command handlers
- `interactions/`: UI components
- `state.py`: Application state management

### Integrations (`src/integrations/`)
- `plex_discord.py`: Plex media integration
- `osrs/`: OSRS data integration
- `pokemon/`: Pokemon data integration

### Data Layer (`src/data/`)
- Data models
- Database interactions
- Cache management
- API integrations

## Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/your-feature

# Run tests
pytest

# Format code
black .

# Check types
mypy .

# Lint code
flake8
```

### 2. Command Development
1. Create command file in `src/app/commands/`
2. Implement using Discord's application commands:
```python
@tree.command(name="command-name", description="Command description")
@app_commands.describe(
    param1="Parameter description",
    param2="Parameter description"
)
async def your_command(interaction: discord.Interaction, param1: str, param2: int):
    # Command implementation
    pass
```

### 3. Component Development
1. Create component in `src/app/interactions/`
2. Implement proper lifecycle:
```python
class YourComponent(discord.ui.View):
    def __init__(self):
        super().__init__()
        # Setup
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Validate interaction
        pass
        
    async def on_timeout(self):
        # Handle timeout
        pass
```

### 4. Integration Development
1. Create integration in `src/integrations/`
2. Implement proper cleanup:
```python
class YourIntegration:
    async def __aenter__(self):
        # Setup
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup
        pass
```

## Testing

### 1. Unit Tests
```python
# test_your_feature.py
import pytest

@pytest.mark.asyncio
async def test_feature():
    # Test implementation
    pass
```

### 2. Integration Tests
```python
# test_integration.py
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration():
    # Test implementation
    pass
```

### 3. Component Tests
```python
# test_component.py
import pytest
from discord.ui import View

@pytest.mark.asyncio
async def test_component():
    # Test implementation
    pass
```

## Documentation

### 1. Code Documentation
- Use docstrings for all public interfaces
- Include type hints
- Document exceptions
- Add usage examples

### 2. API Documentation
- Document all commands
- Include parameter descriptions
- Add response examples
- Note permissions required

### 3. Architecture Documentation
- Update for new features
- Document design decisions
- Include diagrams if needed
- Note dependencies

## Best Practices

### 1. Error Handling
```python
try:
    # Operation
    pass
except SpecificException as e:
    logger.error(f"Specific error: {e}")
    # Handle specific case
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Handle general case
```

### 2. Logging
```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
```

### 3. State Management
```python
class YourFeature:
    def __init__(self):
        self._state = {}
        
    async def update_state(self, key: str, value: Any):
        self._state[key] = value
        await self._persist_state()
```

### 4. Resource Management
```python
async def cleanup_resources(self):
    try:
        # Cleanup
        pass
    finally:
        # Ensure resources are released
        pass
```

## Deployment

### 1. Testing Deployment
```bash
# Run deployment checks
python scripts/check_deployment.py

# Test in staging
python scripts/deploy_staging.py
```

### 2. Production Deployment
```bash
# Deploy to production
python scripts/deploy_production.py

# Monitor deployment
python scripts/monitor_deployment.py
```

## Troubleshooting

### 1. Development Issues
- Check Discord Developer Portal
- Verify application settings
- Check command registration
- Verify permissions

### 2. Integration Issues
- Check API access
- Verify credentials
- Check rate limits
- Monitor resource usage

### 3. Performance Issues
- Profile code
- Check database queries
- Monitor memory usage
- Check API latency
``` 