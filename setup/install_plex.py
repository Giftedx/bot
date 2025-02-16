#!/usr/bin/env python3
"""
Installation script for Plex Discord selfbot.
This script installs additional requirements and helps set up the environment.
"""
import os
import subprocess
import sys
from pathlib import Path


def print_step(step: str) -> None:
    """Print a step in the installation process"""
    print(f"\n=== {step} ===")


def check_python_version() -> bool:
    """Check if Python version is 3.8 or higher"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✓ Python version {sys.version.split()[0]} is compatible")
        return True
    else:
        print(f"✗ Python version {sys.version.split()[0]} is not compatible")
        print("Please use Python 3.8 or higher")
        return False


def install_requirements() -> bool:
    """Install required packages"""
    try:
        # Install main requirements first
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        )

        # Install Plex-specific requirements
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements-plex.txt"]
        )

        print("✓ Successfully installed requirements")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install requirements: {e}")
        return False


def create_env_file() -> None:
    """Create .env file if it doesn't exist"""
    env_path = Path(".env")
    if not env_path.exists():
        env_content = """# Discord selfbot token (DO NOT SHARE!)
DISCORD_TOKEN=your_token_here

# Plex server URL (e.g., http://localhost:32400 or https://plex.example.com:32400)
PLEX_URL=your_plex_url_here

# Plex authentication token
PLEX_TOKEN=your_plex_token_here
"""
        env_path.write_text(env_content)
        print("✓ Created .env file template")
    else:
        print("ℹ .env file already exists")


def check_vlc() -> bool:
    """Check if VLC is installed"""
    try:
        if sys.platform == "win32":
            vlc_path = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
            if os.path.exists(vlc_path):
                print("✓ VLC is installed")
                return True
        else:
            subprocess.check_call(
                ["vlc", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print("✓ VLC is installed")
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ VLC is not installed")
        print("Please install VLC Media Player from: https://www.videolan.org/vlc/")
        return False


def main() -> None:
    """Main installation function"""
    print("Plex Discord Selfbot Installation\n")

    print_step("Checking Python version")
    if not check_python_version():
        sys.exit(1)

    print_step("Checking VLC installation")
    check_vlc()

    print_step("Installing requirements")
    if not install_requirements():
        sys.exit(1)

    print_step("Setting up environment")
    create_env_file()

    print("\nInstallation complete!")
    print("\nNext steps:")
    print("1. Edit the .env file with your Discord token and Plex credentials")
    print("2. Run the bot: python src/run_selfbot.py")
    print("\nFor help getting your tokens:")
    print(
        "Discord token: Open Discord in browser -> Ctrl+Shift+I -> Network -> Type a message -> Find 'authorization' in request headers"
    )
    print("Plex token: Sign in to Plex -> Visit https://plex.tv/claim")


if __name__ == "__main__":
    main()
