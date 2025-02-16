#!/bin/bash
# Shell script wrapper for Plex Discord selfbot launcher

# Make script executable if needed
if [ ! -x "launch_plex.py" ]; then
    chmod +x launch_plex.py
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Run the launcher
if [ -f "venv/bin/python" ]; then
    venv/bin/python launch_plex.py
else
    python3 launch_plex.py
fi

# Capture exit code
exit_code=$?

# If there was an error, wait before exiting
if [ $exit_code -ne 0 ]; then
    echo
    echo "Press Enter to exit..."
    read
fi

exit $exit_code
