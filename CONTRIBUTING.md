# Contributing to OSRS Discord Bot

First off, thank you for considering contributing to OSRS Discord Bot! It's people like you that make this project such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## Getting Started

1. **Fork the Repository**
   ```bash
   git clone https://github.com/yourusername/osrs-discord-bot.git
   cd osrs-discord-bot
   ```

2. **Set Up Development Environment**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   .\venv\Scripts\activate  # Windows

   # Install dependencies
   make dev-install
   ```

3. **Set Up Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

## Development Process

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Write clean, readable code
   - Follow PEP 8 style guide
   - Add type hints
   - Write tests for new features
   - Update documentation as needed

3. **Run Local Tests**
   ```bash
   # Run all tests
   make test

   # Run specific test file
   pytest tests/test_your_feature.py

   # Run with coverage
   pytest --cov=src tests/
   ```

4. **Check Code Quality**
   ```bash
   # Format code
   make format

   # Run linting
   make lint

   # Type checking
   make type-check
   ```

## Pull Request Process

1. **Update Documentation**
   - Add docstrings to new functions/classes
   - Update README.md if needed
   - Add new environment variables to .env.example

2. **Run Tests**
   ```bash
   make test
   ```

3. **Create Pull Request**
   - Use a clear, descriptive title
   - Reference any related issues
   - Describe your changes in detail
   - Include screenshots for UI changes

4. **Code Review**
   - Address review comments
   - Keep discussions focused
   - Be patient and respectful

## Development Guidelines

### Code Style

- Use Black for formatting
- Follow PEP 8 guidelines
- Add type hints
- Write descriptive variable names
- Keep functions focused and small

### Testing

- Write unit tests for new features
- Include integration tests where needed
- Maintain high test coverage
- Use meaningful test names

### Documentation

- Use clear docstrings
- Update README.md for new features
- Document configuration options
- Include examples where helpful

### Commit Messages

Format:
```
type(scope): description

[optional body]
[optional footer]
```

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting
- refactor: Code restructuring
- test: Adding tests
- chore: Maintenance

Example:
```
feat(commands): add skill leveling command

Added new command !train for skill leveling
- Supports all OSRS skills
- Includes XP tracking
- Adds level-up notifications

Closes #123
```

## Setting Up Development Environment

### Required Software

- Python 3.8 or higher
- Docker and Docker Compose
- Redis
- Git
- VSCode (recommended)

### VSCode Extensions

Install recommended extensions from `.vscode/extensions.json`:
1. Open VSCode
2. Press Ctrl/Cmd + Shift + P
3. Type "Show Recommended Extensions"
4. Install recommended extensions

### Environment Variables

Copy `.env.example` to `.env` and fill in required values:
```bash
cp .env.example .env
```

Required variables:
- DISCORD_TOKEN
- REDIS_URL
- COMMAND_PREFIX

### Running the Bot

1. **Start Dependencies**
   ```bash
   docker-compose up -d redis
   ```

2. **Run the Bot**
   ```bash
   python -m src.main
   ```

3. **Start Monitoring** (optional)
   ```bash
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

## Getting Help

- Check existing issues
- Join our Discord server
- Read the documentation
- Ask in discussions

## Recognition

Contributors will be recognized in:
- README.md
- Release notes
- Discord server roles

Thank you for contributing!
