#!/usr/bin/env python3
"""
Installation script for Discord bot.
Handles installation of all components and dependencies.
"""
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def print_status(message: str, success: bool = True) -> None:
    """Print a status message with color if supported."""
    if sys.platform == "win32":
        symbol = "√" if success else "X"
        color = "32" if success else "31"  # Green or Red
        print(f"[{color}m{symbol} {message}[0m")
    else:
        symbol = "✓" if success else "✗"
        print(f"{symbol} {message}")

def check_python_version() -> bool:
    """Check if Python version is 3.8 or higher."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print_status(f"Python {sys.version.split()[0]}")
        return True
    print_status("Python 3.8+ required", False)
    return False

def check_dependencies() -> List[str]:
    """Check for required system dependencies."""
    missing = []
    
    # Check for VLC (required for media playback)
    if sys.platform == "win32":
        vlc_path = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
        if not os.path.exists(vlc_path):
            missing.append("VLC Media Player")
    else:
        try:
            subprocess.check_call(
                ["vlc", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append("VLC Media Player")
    
    return missing

def create_virtual_env() -> bool:
    """Create and activate virtual environment."""
    try:
        # Create venv if it doesn't exist
        if not Path("venv").exists():
            subprocess.check_call([sys.executable, "-m", "venv", "venv"])
            print_status("Created virtual environment")
        
        # Get venv Python path
        if sys.platform == "win32":
            python_path = "venv\\Scripts\\python.exe"
        else:
            python_path = "venv/bin/python"
            
        if not Path(python_path).exists():
            print_status("Virtual environment Python not found", False)
            return False
            
        print_status("Virtual environment ready")
        return True
        
    except Exception as e:
        print_status(f"Failed to create virtual environment: {e}", False)
        return False

def install_requirements(python_path: str) -> bool:
    """Install Python package requirements."""
    requirements_files = [
        "requirements/base.txt",
        "requirements/dev.txt"
    ]
    
    for req_file in requirements_files:
        if not Path(req_file).exists():
            print_status(f"Requirements file not found: {req_file}", False)
            continue
            
        try:
            subprocess.check_call(
                [python_path, "-m", "pip", "install", "-r", req_file]
            )
            print_status(f"Installed {req_file}")
        except subprocess.CalledProcessError as e:
            print_status(f"Failed to install {req_file}: {e}", False)
            return False
            
    return True

def create_env_file() -> bool:
    """Create .env file if it doesn't exist."""
    env_path = Path(".env")
    if env_path.exists():
        print_status(".env file exists")
        return True

    try:
        env_content = """# Discord bot token
DISCORD_TOKEN=your_token_here

# Bot settings
COMMAND_PREFIX=!
BOT_DESCRIPTION="Discord Bot"

# Plex settings (optional)
PLEX_URL=your_plex_url_here
PLEX_TOKEN=your_plex_token_here

# Logging
LOG_LEVEL=INFO
LOG_FILE=bot.log

# Performance
COMMAND_RATE_LIMIT=5
COMMAND_COOLDOWN=3.0
MAX_CONCURRENT_STREAMS=3

# Features
ENABLE_METRICS=true
METRICS_PORT=9090"""

        env_path.write_text(env_content)
        print_status("Created .env file")
        return True
    except Exception as e:
        print_status(f"Failed to create .env file: {e}", False)
        return False

def create_directory_structure() -> bool:
    """Create required directory structure."""
    try:
        directories = [
            "logs",
            "data",
            "src/bot",
            "src/cogs",
            "src/core",
            "src/services",
            "src/utils",
            "tests",
            "docs"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            
        print_status("Created directory structure")
        return True
    except Exception as e:
        print_status(f"Failed to create directories: {e}", False)
        return False

def main() -> None:
    """Main installation function."""
    print("\nInstalling Discord Bot\n")

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Check system dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        print("\nMissing required dependencies:")
        for dep in missing_deps:
            print(f"- {dep}")
        print("\nPlease install missing dependencies and try again.")
        sys.exit(1)

    # Create virtual environment
    if not create_virtual_env():
        sys.exit(1)

    # Get venv Python path
    python_path = "venv\\Scripts\\python.exe" if sys.platform == "win32" else "venv/bin/python"

    # Install requirements
    print("\nInstalling requirements...")
    if not install_requirements(python_path):
        sys.exit(1)

    # Create directory structure
    print("\nCreating directory structure...")
    if not create_directory_structure():
        sys.exit(1)

    # Create .env file
    print("\nSetting up environment...")
    if not create_env_file():
        sys.exit(1)

    print("\nInstallation complete!")
    print("\nNext steps:")
    print("1. Edit .env with your credentials")
    print("2. Activate the virtual environment:")
    if sys.platform == "win32":
        print("   .\\venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("3. Run the bot: python -m src.main")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInstallation cancelled.")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error during installation", exc_info=True)
        print_status(f"Installation failed: {e}", False)
        sys.exit(1) 