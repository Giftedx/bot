#!/usr/bin/env python3
"""
Update script for Plex Discord selfbot.
Updates dependencies and checks for new versions.
"""
import logging
import platform
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
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


def run_pip_upgrade(requirements_file: str) -> Tuple[bool, List[str]]:
    """Upgrade packages from a requirements file"""
    try:
        # Get list of outdated packages
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Install/upgrade packages
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                requirements_file,
                "--upgrade",
            ],
            check=True,
        )
        return True, []
    except subprocess.CalledProcessError as e:
        logger.error("Failed to upgrade packages: %s", e)
        return False, [str(e)]


def is_venv() -> bool:
    """Check if running in a virtual environment"""
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def main() -> None:
    """Main update function"""
    print("\nUpdating Plex Discord Selfbot\n")

    # Check virtual environment
    if not is_venv():
        print_status("Not running in virtual environment", False)
        print("\nPlease activate the virtual environment first:")
        if platform.system() == "Windows":
            print("  venv\\Scripts\\activate")
        else:
            print("  source venv/bin/activate")
        sys.exit(1)

    # Check for requirements files
    requirements_files = ["requirements.txt", "requirements-plex.txt"]
    missing_files = [f for f in requirements_files if not Path(f).exists()]
    if missing_files:
        print_status("Missing requirements files", False)
        for file in missing_files:
            print(f"- {file} not found")
        sys.exit(1)

    # Update pip itself
    print("Updating pip...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True
        )
        print_status("Updated pip")
    except subprocess.CalledProcessError as e:
        print_status(f"Failed to update pip: {e}", False)

    # Update packages from each requirements file
    for req_file in requirements_files:
        print(f"\nUpdating packages from {req_file}...")
        success, errors = run_pip_upgrade(req_file)
        if success:
            print_status(f"Updated packages from {req_file}")
        else:
            print_status(f"Failed to update some packages from {req_file}", False)
            for error in errors:
                print(f"- {error}")

    print("\nUpdate complete!")
    print("\nTo verify the installation:")
    print("1. Run verify_setup.py to check dependencies")
    print("2. Test the bot with launch_plex.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nUpdate cancelled.")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error during update: %s", e, exc_info=True)
        print_status(f"Error: {e}", False)
        sys.exit(1)
