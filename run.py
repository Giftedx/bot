#!/usr/bin/env python3
"""
Run script for Plex Discord selfbot.
Handles environment setup and provides a clean startup process.
"""
import logging
import os
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
        return f"Missing environment variables:\n" + "\n".join(
            f"- {var}" for var in missing
        )
    return None


def is_venv() -> bool:
    """Check if running in a virtual environment"""
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def main() -> None:
    """Main entry point"""
    print("Starting Plex Discord Selfbot...")

    # Check virtual environment
    if not is_venv():
        print("Not running in a virtual environment!")
        print("Please activate the virtual environment first:")
        if sys.platform == "win32":
            print("  venv\\Scripts\\activate")
        else:
            print("  source venv/bin/activate")
        sys.exit(1)

    # Check environment variables
    if error := check_env():
        print(error)
        print("\nPlease set these in your .env file.")
        sys.exit(1)

    try:
        # Import and run the selfbot
        from src.bot.plex_selfbot import run_selfbot

        run_selfbot(
            token=os.getenv("DISCORD_TOKEN", ""),
            plex_url=os.getenv("PLEX_URL", ""),
            plex_token=os.getenv("PLEX_TOKEN", ""),
        )
    except ImportError as e:
        logger.error(f"Failed to import selfbot: {e}")
        print("\nError: Could not import the selfbot.")
        print("Please ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        print("  pip install -r requirements-plex.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running selfbot: {e}")
        print(f"\nError starting the bot: {e}")
        print("\nCheck plex_selfbot.log for details.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot shutdown requested.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\nUnexpected error: {e}")
        print("Check plex_selfbot.log for details.")
        sys.exit(1)
