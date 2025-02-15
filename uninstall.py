#!/usr/bin/env python3
"""
Uninstall script for Plex Discord selfbot.
Removes virtual environment and generated files.
"""
import logging
import os
import shutil
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def print_status(message: str, success: bool = True) -> None:
    """Print a status message with color if supported"""
    if sys.platform == "win32":
        symbol = "√" if success else "X"
        color = "32" if success else "31"  # Green or Red
        print(f"[{color}m{symbol} {message}[0m")
    else:
        symbol = "✓" if success else "✗"
        print(f"{symbol} {message}")


def remove_directory(path: Path) -> bool:
    """Safely remove a directory and its contents"""
    try:
        if path.exists():
            shutil.rmtree(path)
            return True
        return False
    except Exception as e:
        logger.error("Failed to remove directory %s: %s", path, e)
        return False


def remove_file(path: Path) -> bool:
    """Safely remove a file"""
    try:
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception as e:
        logger.error("Failed to remove file %s: %s", path, e)
        return False


def main() -> None:
    """Main uninstall function"""
    print("\nUninstalling Plex Discord Selfbot\n")

    # Ask for confirmation
    response = input(
        "This will remove all bot files and virtual environment. Continue? (y/N) "
    ).lower()
    if response != "y":
        print("\nUninstall cancelled.")
        sys.exit(0)

    print("\nRemoving files...")

    # Remove virtual environment
    venv_removed = remove_directory(Path("venv"))
    print_status("Virtual environment", venv_removed)

    # Remove generated files
    files_to_remove = [
        Path("plex_selfbot.log"),
        Path(".coverage"),
        Path("coverage.xml"),
        Path("pytest.xml"),
    ]

    for file_path in files_to_remove:
        removed = remove_file(file_path)
        if removed:
            print_status(f"Removed {file_path}")

    # Remove __pycache__ directories
    for path in Path(".").rglob("__pycache__"):
        if remove_directory(path):
            print_status(f"Removed {path}")

    # Remove .pyc files
    for path in Path(".").rglob("*.pyc"):
        if remove_file(path):
            print_status(f"Removed {path}")

    print("\nUninstall complete!")
    print("\nNote: Your .env file was preserved. Delete it manually if needed.")
    print("To completely remove the bot, delete this directory.")


def confirm_in_correct_directory() -> bool:
    """Confirm we're in the bot's directory"""
    required_files = [
        "requirements.txt",
        "requirements-plex.txt",
        "src/bot/plex_selfbot.py",
    ]

    for file in required_files:
        if not Path(file).exists():
            print_status(f"Could not find {file}", False)
            print("\nPlease run this script from the bot's main directory.")
            return False
    return True


if __name__ == "__main__":
    try:
        if confirm_in_correct_directory():
            main()
    except KeyboardInterrupt:
        print("\nUninstall cancelled.")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error during uninstall: %s", e, exc_info=True)
        print_status(f"Error: {e}", False)
        sys.exit(1)
