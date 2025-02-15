# Media Server Bot with OSRS Integration

A multi-functional Discord bot that combines Old School RuneScape gameplay simulation, media server capabilities, and a virtual pet system.

## Core Features

- **Discord Bot Integration**
  - Command system with multiple functionality groups
  - Voice channel support
  - User management and permissions

- **OSRS Gameplay Simulation**
  - Character creation and management
  - Combat system
  - Skill progression
  - World management
  - Item system

- **Media Server Features**
  - Plex media integration
  - Music playback and queue management
  - Volume control
  - Media browsing capabilities

- **Virtual Pet System**
  - Pet management
  - Task/reward system integration
  - Pet interaction features

## Technical Stack

- Python 3.8+
- Discord.py 2.3.2+
- Redis (caching & rate limiting)
- SQLite (persistent storage)
- Docker support for containerized deployment
- Prometheus & Grafana for monitoring

## Project Structure

```
src/
├── api/          # REST API endpoints
├── application.py# Main application entry
├── bot/          # Discord bot core
├── config/       # Configuration management
├── core/         # Core utilities
├── pets/         # Pet system
├── services/     # External integrations
└── utils/        # Utility functions

deploy/           # Deployment configurations
├── docker-compose.yaml
├── kubernetes/
└── monitoring/

tests/            # Comprehensive test suite
├── integration/
├── unit/
└── playwright/   # UI tests
```

## Installation

1. Clone the repository
2. Set up virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -e ".[dev]"
```

4. Configure environment variables (see notes/environment_variables.md for full list):
```env
DISCORD_TOKEN=your_token
REDIS_URL=redis://localhost:6379/0
PLEX_SERVER_URL=your_plex_url
```

## Development

### Running Tests
```bash
pytest                    # All tests
pytest tests/unit         # Unit tests
pytest tests/integration  # Integration tests
pytest --cov=src         # Coverage report
```

### Code Quality
```bash
black src tests          # Formatting
isort src tests         # Import sorting
mypy src tests          # Type checking
flake8 src tests        # Linting
```

### Monitoring

The project includes Prometheus and Grafana dashboards for monitoring:
- Application metrics
- Discord bot performance
- Media server statistics
- System resources

## Docker Deployment

```bash
docker-compose up -d           # Development
docker-compose -f docker-compose.prod.yaml up -d  # Production
```

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines and the development process.

## Security

For security concerns and vulnerability reporting, please refer to [SECURITY.md](SECURITY.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
