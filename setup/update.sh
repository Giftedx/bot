#!/bin/bash
# Update script for Plex Discord selfbot

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
        return 1
    fi
}

# Check if we're in the correct directory
if [ ! -f "requirements.txt" ] || [ ! -f "requirements-plex.txt" ]; then
    echo -e "${RED}✗${NC} Please run this script from the bot's main directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}✗${NC} Virtual environment not found"
    echo "Please run the installation script first:"
    echo "  ./install.sh"
    exit 1
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo -e "${RED}✗${NC} Could not find virtual environment activation script"
    exit 1
fi

echo "Updating Plex Discord Selfbot..."

# Update pip
echo -e "\nUpdating pip..."
python -m pip install --upgrade pip
status "Updated pip"

# Update main requirements
echo -e "\nUpdating main dependencies..."
python -m pip install -r requirements.txt --upgrade
status "Updated main dependencies"

# Update Plex requirements
echo -e "\nUpdating Plex dependencies..."
python -m pip install -r requirements-plex.txt --upgrade
status "Updated Plex dependencies"

# Update test requirements if they exist
if [ -f "test-requirements.txt" ]; then
    echo -e "\nUpdating test dependencies..."
    python -m pip install -r test-requirements.txt --upgrade
    status "Updated test dependencies"
fi

# Verify installation
echo -e "\nVerifying installation..."
if [ -f "verify_setup.py" ]; then
    python verify_setup.py
    status "Verification complete"
fi

# Deactivate virtual environment
deactivate

echo -e "\nUpdate complete!"
echo "You can now run the bot with:"
echo "  ./launch_plex.sh"

# If there were any errors, pause
if [ $? -ne 0 ]; then
    echo -e "\nPress Enter to continue..."
    read
fi
