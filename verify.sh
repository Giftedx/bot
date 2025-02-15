#!/bin/bash
# Run verification script in virtual environment

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo "Please run the installation script first:"
    echo "  ./install.sh"
    exit 1
fi

# Activate virtual environment and run verification
if [ -f "venv/bin/activate" ]; then
    # Linux/macOS
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    # Windows with Git Bash
    source venv/Scripts/activate
else
    echo -e "${RED}✗ Could not find virtual environment activation script${NC}"
    exit 1
fi

# Run verification script
python verify_setup.py

# Deactivate virtual environment
deactivate
