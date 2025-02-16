@echo off
setlocal enabledelayedexpansion

:: Run verification script in virtual environment

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

:: Run verification script
echo Running verification checks...
echo.
python verify_setup.py
if errorlevel 1 (
    echo.
    echo [31mX Verification failed[0m
    echo Please check the errors above and fix any issues.
    echo.
    echo For help, see:
    echo   INSTALL.md - Installation instructions
    echo   README-plex.md - Setup and configuration guide
)

:: Deactivate virtual environment
deactivate

:: Pause if there were errors
if errorlevel 1 (
    echo.
    pause
)

endlocal
