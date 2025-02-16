#!/usr/bin/env python3
"""
Backup script for Plex Discord selfbot.
Creates a backup of configuration files and user data.
"""
import datetime
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import List, Set

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


def create_backup_dir() -> Path:
    """Create backup directory with timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"backup_{timestamp}")
    backup_dir.mkdir(exist_ok=True)
    return backup_dir


def get_files_to_backup() -> Set[Path]:
    """Get list of files to backup"""
    files_to_backup = set()

    # Configuration files
    config_files = [
        ".env",
        "requirements.txt",
        "requirements-plex.txt",
        "test-requirements.txt",
    ]

    # Add existing config files
    for file in config_files:
        if Path(file).exists():
            files_to_backup.add(Path(file))

    # Add database files
    for path in Path(".").rglob("*.db"):
        files_to_backup.add(path)

    # Add log files
    for path in Path(".").rglob("*.log"):
        files_to_backup.add(path)

    return files_to_backup


def backup_files(files: Set[Path], backup_dir: Path) -> List[str]:
    """Backup files to backup directory"""
    errors = []
    for file in files:
        try:
            # Create subdirectories if needed
            dest = backup_dir / file
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(file, dest)
            print_status(f"Backed up {file}")
        except Exception as e:
            errors.append(f"Failed to backup {file}: {e}")
            logger.error("Backup error: %s", e)

    return errors


def create_zip_archive(backup_dir: Path) -> bool:
    """Create ZIP archive of backup directory"""
    try:
        shutil.make_archive(str(backup_dir), "zip", backup_dir)
        print_status(f"Created archive {backup_dir}.zip")
        return True
    except Exception as e:
        logger.error("Failed to create ZIP archive: %s", e)
        return False


def main() -> None:
    """Main backup function"""
    print("\nCreating backup of Plex Discord Selfbot\n")

    # Create backup directory
    backup_dir = create_backup_dir()
    print_status(f"Created backup directory: {backup_dir}")

    # Get files to backup
    files = get_files_to_backup()
    if not files:
        print_status("No files to backup", False)
        sys.exit(1)

    # Backup files
    print("\nBacking up files...")
    errors = backup_files(files, backup_dir)

    # Create ZIP archive
    print("\nCreating archive...")
    if create_zip_archive(backup_dir):
        # Remove backup directory after successful ZIP creation
        shutil.rmtree(backup_dir)

    # Print results
    print("\nBackup complete!")
    print(f"Total files backed up: {len(files) - len(errors)}")
    if errors:
        print("\nErrors occurred:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)

    print(f"\nBackup saved to: {backup_dir}.zip")
    print("Keep this file in a safe place.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBackup cancelled.")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error during backup: %s", e, exc_info=True)
        print_status(f"Error: {e}", False)
        sys.exit(1)
