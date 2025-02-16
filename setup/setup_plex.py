#!/usr/bin/env python3
"""
Simple setup script for Plex Discord selfbot.
"""
import os
import subprocess
import sys
from pathlib import Path


def install_requirements() -> bool:
    """Install required packages"""
    try:
        # Install Plex-specific requirements
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements-plex.txt"]
        )
        print("✓ Successfully installed Plex requirements")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install requirements: {e}")
        return False


def setup_env() -> bool:
    """Set up environment file"""
    env_path = Path(".env")
    if not env_path.exists():
        env_content = """# Discord selfbot token
DISCORD_TOKEN=your_token_here

# Plex server URL (e.g. http://localhost:32400)
PLEX_URL=your_plex_url_here

# Plex token
PLEX_TOKEN=your_plex_token_here"""

        try:
            env_path.write_text(env_content)
            print("✓ Created .env file template")
            return True
        except Exception as e:
            print(f"✗ Failed to create .env file: {e}")
            return False
    else:
        print("ℹ .env file already exists")
        return True


def check_vlc() -> bool:
    """Check if VLC is installed"""
    if sys.platform == "win32":
        vlc_path = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
        if os.path.exists(vlc_path):
            print("✓ VLC is installed")
            return True
        print("✗ VLC not found. Please install VLC Media Player")
        return False

    try:
        subprocess.check_call(
            ["vlc", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print("✓ VLC is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ VLC not found. Please install VLC Media Player")
        return False


def main() -> None:
    """Main setup function"""
    print("Setting up Plex Discord Selfbot...\n")

    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        sys.exit(1)
    print("✓ Python version OK")

    # Check VLC installation
    if not check_vlc():
        print("Please install VLC from: https://www.videolan.org/vlc/")
        sys.exit(1)

    # Install requirements
    if not install_requirements():
        sys.exit(1)

    # Set up environment
    if not setup_env():
        sys.exit(1)

    print("\nSetup complete!")
    print("\nNext steps:")
    print("1. Edit .env with your credentials")
    print("2. Run: python src/run_selfbot.py")


if __name__ == "__main__":
    main()
