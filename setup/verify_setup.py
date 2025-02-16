#!/usr/bin/env python3
"""
Verify the Plex Discord selfbot installation and configuration.
"""
import os
import platform
import subprocess
import sys
from typing import List, Tuple


def print_status(message: str, success: bool = True) -> None:
    """Print a status message with color"""
    GREEN = "\033[92m"
    RED = "\033[91m"
    RESET = "\033[0m"

    symbol = "✓" if success else "✗"
    color = GREEN if success else RED
    print(f"{color}{symbol} {message}{RESET}")


def check_python_version() -> bool:
    """Check if Python version is 3.8 or higher"""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    if version.major == 3 and version.minor >= 8:
        print_status(f"Python version {version_str}")
        return True
    print_status(f"Python version {version_str} (3.8+ required)", False)
    return False


def check_vlc() -> bool:
    """Check if VLC is installed"""
    if platform.system() == "Windows":
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
    return False


def check_dependencies() -> List[Tuple[str, bool]]:
    """Check if required Python packages are installed"""
    required_packages = ["discord.py-self", "plexapi", "python-dotenv", "python-vlc"]

    results = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_").split(".")[0])
            results.append((package, True))
        except ImportError:
            results.append((package, False))

    return results


def check_env_vars() -> List[Tuple[str, bool]]:
    """Check if required environment variables are set"""
    required_vars = ["DISCORD_TOKEN", "PLEX_URL", "PLEX_TOKEN"]

    return [(var, bool(os.getenv(var))) for var in required_vars]


def check_virtual_env() -> bool:
    """Check if running in a virtual environment"""
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def main() -> None:
    """Run all verification checks"""
    print("Verifying Plex Discord Selfbot Setup\n")

    # Check Python version
    python_ok = check_python_version()
    print()

    # Check VLC
    vlc_ok = check_vlc()
    print()

    # Check virtual environment
    venv_ok = check_virtual_env()
    print_status(
        "Virtual environment active" if venv_ok else "Not in virtual environment",
        venv_ok,
    )
    print()

    # Check dependencies
    print("Checking dependencies:")
    dep_results = check_dependencies()
    dep_ok = all(result[1] for result in dep_results)
    for package, installed in dep_results:
        print_status(f"Package: {package}", installed)
    print()

    # Check environment variables
    print("Checking environment variables:")
    env_results = check_env_vars()
    env_ok = all(result[1] for result in env_results)
    for var, exists in env_results:
        print_status(f"Environment variable: {var}", exists)

    # Overall status
    print("\nVerification Results:")
    all_ok = all([python_ok, vlc_ok, venv_ok, dep_ok, env_ok])
    if all_ok:
        print_status("All checks passed! The bot should work correctly.")
        print("\nYou can now run the bot:")
        if platform.system() == "Windows":
            print("venv\\Scripts\\python src\\run_selfbot.py")
        else:
            print("venv/bin/python src/run_selfbot.py")
    else:
        print_status("Some checks failed. Please fix the issues marked with ✗", False)
        if not python_ok:
            print("- Install Python 3.8 or higher")
        if not vlc_ok:
            print("- Install VLC Media Player")
        if not venv_ok:
            print("- Run installation script to set up virtual environment")
        if not dep_ok:
            print("- Install missing packages with: pip install -r requirements.txt")
        if not env_ok:
            print("- Set up missing environment variables in .env file")


if __name__ == "__main__":
    main()
