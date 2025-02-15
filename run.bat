@echo off
setlocal enabledelayedexpansion

:: Run script for Plex Discord selfbot

:: Check if virtual environment exists
if not exist "venv" (
    echo [31mX Virtual environment not found[0m
    echo.
    echo Please run the installation script first:
    echo   install.bat
    echo.
    echo Or create a virtual environment manually:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo   pip install -r requirements-plex.txt
    exit /b 1
)

:: Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate
    if errorlevel 1 (
        echo [31mX Failed to activate virtual environment[0m
        exit /b 1
    )
) else (
    echo [31mX Could not find virtual environment activation script[0m
    echo Please ensure the virtual environment was created correctly.
    exit /b 1
)

:: Check if .env file exists
if not exist ".env" (
    echo [31mX .env file not found[0m
    echo.
    echo Please create a .env file with your credentials:
    echo   DISCORD_TOKEN=your_token_here
    echo   PLEX_URL=your_plex_url_here
    echo   PLEX_TOKEN=your_plex_token_here
    exit /b 1
)

:: Run the bot
echo Starting Plex Discord selfbot...
echo.
echo Press Ctrl+C to stop the bot
echo.

python src/bot/plex_selfbot.py

:: Check for errors
if errorlevel 1 (
    echo.
    echo [31mX Bot exited with an error[0m
    echo Please check the error message above.
    echo.
    echo Common issues:
    echo - Invalid Discord token
    echo - Plex server not accessible
    echo - Missing dependencies
    echo.
    echo For help, see:
    echo   README-plex.md - Setup and configuration guide
    echo   INSTALL.md - Installation instructions
)

:: Deactivate virtual environment
deactivate

:: Pause if there were errors
if errorlevel 1 (
    echo.
    pause
)

endlocal
