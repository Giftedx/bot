@echo off
setlocal enabledelayedexpansion

:: Installation script for Plex Discord selfbot
echo Installing Plex Discord Selfbot...
echo.

:: Check Python version
python -c "import sys; print('Python %s.%s' % sys.version_info[:2])" > temp.txt
set /p PYTHON_VERSION=<temp.txt
del temp.txt

echo Checking requirements...
python -c "import sys; assert sys.version_info >= (3,8)" 2>nul
if errorlevel 1 (
    echo [31mX Python 3.8+ required (found %PYTHON_VERSION%^)[0m
    exit /b 1
) else (
    echo [32m√ %PYTHON_VERSION% detected[0m
)

:: Check VLC
if exist "C:\Program Files\VideoLAN\VLC\vlc.exe" (
    echo [32m√ VLC Media Player detected[0m
) else (
    echo [31mX VLC Media Player not found[0m
    echo Please install VLC from: https://www.videolan.org/vlc/
    exit /b 1
)

:: Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [31mX Failed to create virtual environment[0m
    exit /b 1
)
echo [32m√ Created virtual environment[0m

:: Activate virtual environment
call venv\Scripts\activate
if errorlevel 1 (
    echo [31mX Failed to activate virtual environment[0m
    exit /b 1
)
echo [32m√ Activated virtual environment[0m

:: Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [31mX Failed to install main requirements[0m
    exit /b 1
)
echo [32m√ Installed main requirements[0m

pip install -r requirements-plex.txt
if errorlevel 1 (
    echo [31mX Failed to install Plex requirements[0m
    exit /b 1
)
echo [32m√ Installed Plex requirements[0m

:: Install test dependencies if --test flag is provided
echo %* | findstr /C:"--test" >nul
if not errorlevel 1 (
    echo.
    echo Installing test dependencies...
    pip install -r test-requirements.txt
    if errorlevel 1 (
        echo [31mX Failed to install test dependencies[0m
        exit /b 1
    )
    echo [32m√ Installed test dependencies[0m
)

:: Create .env if it doesn't exist
if not exist .env (
    echo.
    echo Creating .env file...
    (
        echo # Discord selfbot token
        echo DISCORD_TOKEN=your_token_here
        echo.
        echo # Plex server URL ^(e.g. http://localhost:32400^)
        echo PLEX_URL=your_plex_url_here
        echo.
        echo # Plex token
        echo PLEX_TOKEN=your_plex_token_here
    ) > .env
    echo [32m√ Created .env file[0m
) else (
    echo [32m√ .env file exists[0m
)

:: Setup complete
echo.
echo [32mSetup complete![0m
echo.
echo Next steps:
echo 1. Edit .env with your credentials
echo 2. Run the bot:
echo    venv\Scripts\python src\run_selfbot.py
echo.

:: Print test instructions if --test flag was used
echo %* | findstr /C:"--test" >nul
if not errorlevel 1 (
    echo To run tests:
    echo venv\Scripts\pytest tests\
    echo.
)

endlocal
