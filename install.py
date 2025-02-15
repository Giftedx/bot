#!/usr/bin/env python3
"""
Installation script for Plex Discord selfbot.
"""
import os
import subprocess
import sys
from pathlib import Path


def print_status(message: str, success: bool = True) -> None:
    """Print a status message"""
    print(f"{'✓' if success else '✗'} {message}")


def check_python() -> bool:
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print_status(f"Python {sys.version.split()[0]}")
        return True
    print_status("Python 3.8+ required", False)
    return False


def check_vlc() -> bool:
    """Check VLC installation"""
    if sys.platform == "win32":
        vlc_path = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
        if os.path.exists(vlc_path):
            print_status("VLC Media Player")
            return True
    else:
        try:
            subprocess.check_call(
                ["vlc", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print_status("VLC Media Player")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    print_status("VLC Media Player not found", False)
    print("Please install from: https://www.videolan.org/vlc/")
    return False


def install_requirements(test_mode: bool = False) -> bool:
    """Install Python packages"""
    requirements = ["requirements.txt", "requirements-plex.txt"]
    if test_mode:
        requirements.append("test-requirements.txt")

    for req in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req])
            print_status(f"Installed {req}")
        except subprocess.CalledProcessError as e:
            print_status(f"Failed to install {req}: {e}", False)
            return False
    return True


def create_env() -> bool:
    """Create .env file if it doesn't exist"""
    env_path = Path(".env")
    if env_path.exists():
        print_status(".env file exists")
        return True

    try:
        env_content = """# Discord selfbot token
DISCORD_TOKEN=your_token_here

# Plex server URL (e.g. http://localhost:32400)
PLEX_URL=your_plex_url_here

# Plex token
PLEX_TOKEN=your_plex_token_here"""

        env_path.write_text(env_content)
        print_status("Created .env file")
        return True
    except Exception as e:
        print_status(f"Failed to create .env file: {e}", False)
        return False


def main() -> None:
    """Main installation function"""
    print("Installing Plex Discord Selfbot\n")

    # Check requirements
    if not check_python():
        sys.exit(1)

    if not check_vlc():
        sys.exit(1)

    # Install packages
    print("\nInstalling packages...")
    test_mode = "--test" in sys.argv
    if not install_requirements(test_mode):
        sys.exit(1)

    # Create .env
    print("\nSetting up environment...")
    if not create_env():
        sys.exit(1)

    # Print next steps
    print("\nNext steps:")
    print("1. Edit .env with your credentials")
    print("2. Run the bot: python src/run_selfbot.py")

    if test_mode:
        print("\nTo run tests:")
        print("pytest tests/")


if __name__ == "__main__":
    main()
