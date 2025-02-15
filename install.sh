#!/bin/bash
# Installation script for Plex Discord selfbot

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print status message
status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        exit 1
    fi
}

# Check Python version
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if (( $(echo "$python_version >= 3.8" | bc -l) )); then
    status "Python $python_version"
else
    status "Python 3.8+ required (found $python_version)" && exit 1
fi

# Check VLC
if command -v vlc >/dev/null 2>&1; then
    status "VLC Media Player"
else
    status "VLC Media Player not found. Please install it first." && exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
status "Created virtual environment"

# Activate virtual environment
source venv/bin/activate
status "Activated virtual environment"

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt
status "Installed main requirements"

pip install -r requirements-plex.txt
status "Installed Plex requirements"

# Install test dependencies if --test flag is provided
if [[ "$*" == *"--test"* ]]; then
    echo "Installing test dependencies..."
    pip install -r test-requirements.txt
    status "Installed test dependencies"
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# Discord selfbot token
DISCORD_TOKEN=your_token_here

# Plex server URL (e.g. http://localhost:32400)
PLEX_URL=your_plex_url_here

# Plex token
PLEX_TOKEN=your_plex_token_here
EOL
    status "Created .env file"
else
    status ".env file already exists"
fi

echo -e "\nSetup complete!"
echo -e "\nNext steps:"
echo "1. Edit .env with your credentials"
echo "2. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo "3. Run the bot:"
echo "   python src/run_selfbot.py"

if [[ "$*" == *"--test"* ]]; then
    echo -e "\nTo run tests:"
    echo "pytest tests/"
fi
