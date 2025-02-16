@echo off
setlocal enabledelayedexpansion

:: Batch script wrapper for Plex Discord selfbot launcher

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [31mX Python not found[0m
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: Check Python version
python -c "import sys; assert sys.version_info >= (3,8)" >nul 2>&1
if errorlevel 1 (
    echo [31mX Python 3.8 or higher required[0m
    echo.
    echo Please upgrade Python from:
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check if VLC is installed
if not exist "C:\Program Files\VideoLAN\VLC\vlc.exe" (
    if not exist "C:\Program Files (x86)\VideoLAN\VLC\vlc.exe" (
        echo [31mX VLC Media Player not found[0m
        echo.
        echo Please install VLC Media Player from:
        echo https://www.videolan.org/vlc/
        echo.
        echo Make sure to install the 64-bit version.
        pause
        exit /b 1
    )
)

:: Run the launcher
echo Starting Plex Discord selfbot...
echo.

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python launch_plex.py
) else (
    python launch_plex.py
)

:: Capture exit code
set EXIT_CODE=%errorlevel%

:: If there was an error, show troubleshooting info
if %EXIT_CODE% neq 0 (
    echo.
    echo [31mX Bot exited with an error[0m
    echo.
    echo Troubleshooting steps:
    echo 1. Check plex_selfbot.log for detailed error messages
    echo 2. Verify your .env file contains valid credentials
    echo 3. Ensure Plex server is running and accessible
    echo 4. Try running verify_setup.py to check your installation
    echo.
    echo For more help, see:
    echo - INSTALL.md: Installation instructions
    echo - README-plex.md: Configuration guide
    echo.
    pause
)

exit /b %EXIT_CODE%
