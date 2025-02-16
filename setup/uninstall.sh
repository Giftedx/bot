#!/bin/bash
# Uninstall script for Plex Discord selfbot

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
    fi
}

# Check if we're in the correct directory
if [ ! -f "requirements.txt" ] || [ ! -f "requirements-plex.txt" ]; then
    echo -e "${RED}✗${NC} Please run this script from the bot's main directory"
    exit 1
fi

# Ask for confirmation
echo "This will remove all bot files and virtual environment."
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo -e "\nRemoving files...\n"

# Remove virtual environment
if [ -d "venv" ]; then
    rm -rf venv
    status "Removed virtual environment"
fi

# Remove generated files
files=(
    "plex_selfbot.log"
    ".coverage"
    "coverage.xml"
    "pytest.xml"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        status "Removed $file"
    fi
done

# Remove __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
status "Removed Python cache directories"

# Remove .pyc files
find . -type f -name "*.pyc" -delete 2>/dev/null
status "Removed compiled Python files"

echo -e "\nUninstall complete!"
echo -e "\nNote: Your .env file was preserved. Delete it manually if needed."
echo "To completely remove the bot, delete this directory."
