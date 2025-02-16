# Installation Guide

This guide covers different ways to install and set up the Plex Discord selfbot.

## Prerequisites

- Python 3.8 or higher
- VLC Media Player
- Discord account
- Plex Media Server

## Automated Installation

### Windows Users
```batch
# Run the installation script
install.bat

# Include test dependencies (optional)
install.bat --test
```

### Linux/macOS Users
```bash
# Make script executable
chmod +x install.sh

# Run installation script
./install.sh

# Include test dependencies (optional)
./install.sh --test
```

### Python Script (All Platforms)
```bash
# Run Python installer
python install.py

# Include test dependencies (optional)
python install.py --test
```

## Manual Installation

If you prefer to install manually:

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

3. Install dependencies:
```bash
# Core dependencies
pip install -r requirements.txt

# Plex-specific dependencies
pip install -r requirements-plex.txt

# Test dependencies (optional)
pip install -r test-requirements.txt
```

4. Create `.env` file:
```env
# Discord selfbot token
DISCORD_TOKEN=your_token_here

# Plex server URL (e.g. http://localhost:32400)
PLEX_URL=your_plex_url_here

# Plex token
PLEX_TOKEN=your_plex_token_here
```

## Getting Required Tokens

### Discord Token
1. Open Discord in your browser
2. Press Ctrl+Shift+I to open developer tools
3. Go to Network tab
4. Type anything in any channel
5. Look for a request starting with "messages"
6. Find the "authorization" header in the request headers

### Plex Token
1. Sign in to Plex
2. Visit https://plex.tv/claim
3. Copy your token

## Verifying Installation

1. Ensure VLC is installed:
```bash
# Windows
"C:\Program Files\VideoLAN\VLC\vlc.exe" --version

# Linux/macOS
vlc --version
```

2. Check Python version:
```bash
python --version  # Should be 3.8 or higher
```

3. Test the installation:
```bash
# Activate virtual environment if not already active
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run tests (if test dependencies installed)
pytest tests/
```

## Troubleshooting

### Common Issues

1. VLC not found:
   - Install VLC from https://www.videolan.org/vlc/
   - Add VLC to system PATH

2. Python version too old:
   - Download Python 3.8+ from https://python.org
   - Ensure it's added to PATH during installation

3. Virtual environment issues:
   - Delete venv directory
   - Run installation script again

4. Dependency conflicts:
   - Delete venv directory
   - Create fresh virtual environment
   - Install dependencies in order

### Getting Help

If you encounter issues:
1. Check error messages
2. Verify all prerequisites are met
3. Try manual installation steps
4. Check system PATH settings
5. Ensure all tokens are valid

## Next Steps

After installation:
1. Edit `.env` with your credentials
2. Run the bot:
```bash
# Windows
venv\Scripts\python src\run_selfbot.py

# Linux/macOS
venv/bin/python src/run_selfbot.py
```

For development:
```bash
# Run tests
pytest tests/

# Check code style
flake8 src tests
pylint src tests

# Type checking
mypy src tests
