# Discord Application with OSRS, Pokemon, and Plex Integration

A modern Discord application that integrates OSRS (Old School RuneScape) data, Pokemon features, and Plex media playback using Discord's latest application features.

## Major Changes
- Migrated from bot model to Discord application model
- Implemented slash commands and modern interactions
- Added proper component handling
- Improved documentation and structure

## Documentation
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## Requirements

- Python 3.12 or higher
- Redis server (for caching)
- PostgreSQL (optional, for advanced data storage)
- FFmpeg (for media features)

## Quick Start

1. Create Discord Application:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create new application
   - Get credentials (App ID, Public Key, Token)
   - Enable required intents

2. Clone and Setup:
```bash
# Clone repository
git clone <repository-url>
cd discord-app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

3. Configure Application:
```env
# Discord Application
DISCORD_APP_ID=your_app_id
DISCORD_PUBLIC_KEY=your_public_key
DISCORD_TOKEN=your_token

# Plex Configuration (Optional)
PLEX_URL=your_plex_url
PLEX_TOKEN=your_plex_token

# Database Configuration
DATABASE_URL=your_database_url

# Redis Configuration
REDIS_URL=redis://localhost:6379
```

4. Run Application:
```bash
python -m src.app
```

## Features

### Plex Integration
- Media playback in Discord
- Library browsing
- Search functionality
- Media controls
- Quality selection

### OSRS Features
- Data collection and tracking
- Pet statistics
- Boss information
- Skill tracking
- Price monitoring

### Pokemon Features
- ROM data parsing
- PokeAPI integration
- Pokemon information
- Game data collection

## Development

1. Setup Development Environment:
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install
```

2. Run Tests:
```bash
# Run all tests
pytest

# Run with coverage
coverage run -m pytest
coverage report
```

3. Code Quality:
```bash
# Format code
black .

# Check types
mypy .

# Lint code
flake8
```

## Contributing

1. Create Feature Branch:
```bash
git checkout -b feature/your-feature-name
```

2. Development Workflow:
- Write tests first
- Implement feature
- Update documentation
- Run quality checks
- Submit pull request

3. Documentation:
- Update relevant .md files
- Add API documentation
- Update architecture docs if needed
- Add migration notes if applicable

## Deployment

See [Deployment Guide](docs/DEPLOYMENT.md) for detailed instructions on:
- Setting up production environment
- Configuring Discord application
- Setting up databases
- Monitoring and logging
- Backup procedures

## Troubleshooting

Common issues and solutions:
1. Command Registration:
   - Verify slash commands are registered
   - Check application permissions
   - Verify intents are enabled

2. Media Playback:
   - Check Plex connectivity
   - Verify media permissions
   - Check FFmpeg installation

3. Data Collection:
   - Verify API access
   - Check rate limits
   - Verify database connectivity

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Discord.py developers
- Plex API contributors
- OSRS Wiki team
- PokeAPI team 