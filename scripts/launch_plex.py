#!/usr/bin/env python3
"""
Universal launcher script for Plex Discord selfbot.
Works on both Windows and Unix-like systems.
"""
import logging
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("plex_selfbot.log")],
)
logger = logging.getLogger(__name__)


def print_status(message: str, success: bool = True) -> None:
    """Print a status message with color if supported"""
    if platform.system() == "Windows":
        symbol = "√" if success else "X"
        color = "32" if success else "31"  # Green or Red
        print(f"[{color}m{symbol} {message}[0m")
    else:
        symbol = "✓" if success else "✗"
        print(f"{symbol} {message}")


def is_venv() -> bool:
    """Check if running in a virtual environment"""
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def activate_venv() -> bool:
    """Activate virtual environment"""
    venv_path = Path("venv")
    if not venv_path.exists():
        print_status("Virtual environment not found", False)
        print("\nPlease run the installation script first:")
        print("  Windows: install.bat")
        print("  Linux/macOS: ./install.sh")
        return False

    if platform.system() == "Windows":
        activate_script = venv_path / "Scripts" / "activate.bat"
        if not activate_script.exists():
            print_status("Activation script not found", False)
            return False

        try:
            subprocess.run([str(activate_script)], check=True, shell=True)
            return True
        except subprocess.CalledProcessError:
            print_status("Failed to activate virtual environment", False)
            return False
    else:
        activate_script = venv_path / "bin" / "activate"
        if not activate_script.exists():
            print_status("Activation script not found", False)
            return False

        os.environ["PATH"] = f"{venv_path}/bin:{os.environ.get('PATH', '')}"
        return True


def check_env() -> Optional[str]:
    """Check if required environment variables are set"""
    required_vars = {
        "DISCORD_TOKEN": "Discord user token",
        "PLEX_URL": "Plex server URL",
        "PLEX_TOKEN": "Plex authentication token",
    }

    missing = []
    for var, desc in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var} ({desc})")

    if missing:
        return "\n".join(f"- {var}" for var in missing)
    return None


def main() -> None:
    """Main entry point"""
    print("\nPlex Discord Selfbot Launcher\n")

    # Check Python version
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_status("Python 3.8+ required", False)
        sys.exit(1)
    print_status(f"Python {sys.version.split()[0]}")

    # Check virtual environment
    if not is_venv():
        if not activate_venv():
            sys.exit(1)
    print_status("Virtual environment active")

    # Check environment variables
    if missing_vars := check_env():
        print_status("Missing environment variables", False)
        print("\nPlease set the following in your .env file:")
        print(missing_vars)
        sys.exit(1)
    print_status("Environment variables configured")

    # Start the bot
    print("\nStarting Plex Discord selfbot...")
    try:
        from src.bot.plex_selfbot import run_selfbot

        run_selfbot(
            token=os.getenv("DISCORD_TOKEN", ""),
            plex_url=os.getenv("PLEX_URL", ""),
            plex_token=os.getenv("PLEX_TOKEN", ""),
        )
    except ImportError as e:
        logger.error("Failed to import selfbot: %s", e)
        print_status("Failed to import selfbot", False)
        print("\nPlease ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        print("  pip install -r requirements-plex.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nBot shutdown requested.")
        sys.exit(0)
    except Exception as e:
        logger.error("Error running selfbot: %s", e, exc_info=True)
        print_status(f"Error: {e}", False)
        print("\nCheck plex_selfbot.log for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
