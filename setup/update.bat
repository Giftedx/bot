@echo off
setlocal enabledelayedexpansion

:: Update script for Plex Discord selfbot

:: Check if we're in the correct directory
if not exist "requirements.txt" (
    echo [31mX Please run this script from the bot's main directory[0m
    pause
    exit /b 1
)

:: Check if virtual environment exists
if not exist "venv" (
    echo [31mX Virtual environment not found[0m
    echo.
    echo Please run the installation script first:
    echo   install.bat
    pause
    exit /b 1
)

:: Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate
    if errorlevel 1 (
        echo [31mX Failed to activate virtual environment[0m
        pause
        exit /b 1
    )
) else (
    echo [31mX Could not find virtual environment activation script[0m
    pause
    exit /b 1
)

echo Updating Plex Discord Selfbot...

:: Update pip
echo.
echo Updating pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [31mX Failed to update pip[0m
) else (
    echo [32m√ Updated pip[0m
)

:: Update main requirements
echo.
echo Updating main dependencies...
python -m pip install -r requirements.txt --upgrade
if errorlevel 1 (
    echo [31mX Failed to update main dependencies[0m
) else (
    echo [32m√ Updated main dependencies[0m
)

:: Update Plex requirements
echo.
echo Updating Plex dependencies...
python -m pip install -r requirements-plex.txt --upgrade
if errorlevel 1 (
    echo [31mX Failed to update Plex dependencies[0m
) else (
    echo [32m√ Updated Plex dependencies[0m
)

:: Update test requirements if they exist
if exist "test-requirements.txt" (
    echo.
    echo Updating test dependencies...
    python -m pip install -r test-requirements.txt --upgrade
    if errorlevel 1 (
        echo [31mX Failed to update test dependencies[0m
    ) else (
        echo [32m√ Updated test dependencies[0m
    )
)

:: Verify installation
echo.
echo Verifying installation...
if exist "verify_setup.py" (
    python verify_setup.py
    if errorlevel 1 (
        echo [31mX Verification failed[0m
    ) else (
        echo [32m√ Verification complete[0m
    )
)

:: Deactivate virtual environment
deactivate

echo.
echo Update complete!
echo.
echo You can now run the bot with:
echo   launch_plex.bat
echo.

:: If there were any errors, pause
if errorlevel 1 (
    echo Press any key to continue...
    pause >nul
)

endlocal
