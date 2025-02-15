@echo off
setlocal enabledelayedexpansion

:: Uninstall script for Plex Discord selfbot

:: Check if we're in the correct directory
if not exist "requirements.txt" (
    echo [31mX Please run this script from the bot's main directory[0m
    pause
    exit /b 1
)

:: Ask for confirmation
echo This will remove all bot files and virtual environment.
set /p CONFIRM="Continue? (y/N) "
if /i "%CONFIRM%" neq "y" (
    echo.
    echo Uninstall cancelled.
    exit /b 0
)

echo.
echo Removing files...
echo.

:: Remove virtual environment
if exist "venv" (
    rmdir /s /q "venv"
    if errorlevel 1 (
        echo [31mX Failed to remove virtual environment[0m
    ) else (
        echo [32m√ Removed virtual environment[0m
    )
)

:: Remove generated files
set "FILES_TO_REMOVE=plex_selfbot.log .coverage coverage.xml pytest.xml"
for %%f in (%FILES_TO_REMOVE%) do (
    if exist "%%f" (
        del /f /q "%%f"
        if errorlevel 1 (
            echo [31mX Failed to remove %%f[0m
        ) else (
            echo [32m√ Removed %%f[0m
        )
    )
)

:: Remove __pycache__ directories
for /d /r %%d in (*) do (
    if "%%~nxd"=="__pycache__" (
        rmdir /s /q "%%d"
        if errorlevel 1 (
            echo [31mX Failed to remove %%d[0m
        ) else (
            echo [32m√ Removed %%d[0m
        )
    )
)

:: Remove .pyc files
for /r %%f in (*.pyc) do (
    del /f /q "%%f"
    if errorlevel 1 (
        echo [31mX Failed to remove %%f[0m
    ) else (
        echo [32m√ Removed %%f[0m
    )
)

echo.
echo Uninstall complete!
echo.
echo Note: Your .env file was preserved. Delete it manually if needed.
echo To completely remove the bot, delete this directory.
echo.

pause
endlocal
