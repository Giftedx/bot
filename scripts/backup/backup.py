#!/usr/bin/env python3
"""
Backup and restore script for Discord bot.
Handles backup of configuration, data, and logs.
"""
import datetime
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import List, Set, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class BackupManager:
    """Manages backup and restore operations."""
    
    def __init__(self, backup_dir: Optional[Path] = None):
        """Initialize backup manager."""
        self.backup_dir = backup_dir or Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
    def print_status(self, message: str, success: bool = True) -> None:
        """Print a status message with color if supported."""
        if sys.platform == "win32":
            symbol = "√" if success else "X"
            color = "32" if success else "31"  # Green or Red
            print(f"[{color}m{symbol} {message}[0m")
        else:
            symbol = "✓" if success else "✗"
            print(f"{symbol} {message}")
            
    def get_files_to_backup(self) -> Set[Path]:
        """Get list of files to backup."""
        files_to_backup = set()
        
        # Configuration files
        config_files = [
            ".env",
            "requirements/base.txt",
            "requirements/dev.txt",
            "requirements/test.txt"
        ]
        
        # Add existing config files
        for file in config_files:
            if Path(file).exists():
                files_to_backup.add(Path(file))
                
        # Add database files
        for path in Path(".").rglob("*.db"):
            files_to_backup.add(path)
            
        # Add log files
        for path in Path("logs").rglob("*.log"):
            files_to_backup.add(path)
            
        # Add data files
        for path in Path("data").rglob("*"):
            if path.is_file():
                files_to_backup.add(path)
                
        return files_to_backup
        
    def create_backup(self) -> Optional[Path]:
        """Create a new backup."""
        try:
            # Create timestamped backup directory
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}"
            backup_path.mkdir()
            
            # Get files to backup
            files = self.get_files_to_backup()
            if not files:
                self.print_status("No files to backup", False)
                return None
                
            # Copy files
            for file in files:
                # Create subdirectories if needed
                dest = backup_path / file
                dest.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(file, dest)
                self.print_status(f"Backed up {file}")
                
            # Create ZIP archive
            shutil.make_archive(str(backup_path), "zip", backup_path)
            
            # Remove uncompressed backup
            shutil.rmtree(backup_path)
            
            return backup_path.with_suffix(".zip")
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            self.print_status(f"Backup failed: {e}", False)
            return None
            
    def list_backups(self) -> List[Path]:
        """List available backups."""
        return sorted(
            self.backup_dir.glob("backup_*.zip"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
    def restore_backup(self, backup_path: Path) -> bool:
        """Restore from a backup."""
        try:
            if not backup_path.exists():
                self.print_status(f"Backup not found: {backup_path}", False)
                return False
                
            # Create temporary directory for extraction
            temp_dir = self.backup_dir / "temp_restore"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir()
            
            # Extract backup
            shutil.unpack_archive(str(backup_path), str(temp_dir))
            
            # Restore files
            for file in temp_dir.rglob("*"):
                if file.is_file():
                    # Get relative path
                    rel_path = file.relative_to(temp_dir)
                    dest = Path(rel_path)
                    
                    # Create parent directories
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(file, dest)
                    self.print_status(f"Restored {rel_path}")
                    
            # Clean up
            shutil.rmtree(temp_dir)
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            self.print_status(f"Restore failed: {e}", False)
            return False

def main() -> None:
    """Main function for backup/restore operations."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  backup.py backup              Create new backup")
        print("  backup.py list                List available backups")
        print("  backup.py restore [backup]    Restore from backup")
        sys.exit(1)
        
    manager = BackupManager()
    command = sys.argv[1]
    
    if command == "backup":
        print("\nCreating backup...")
        if backup_path := manager.create_backup():
            print(f"\nBackup saved to: {backup_path}")
            
    elif command == "list":
        backups = manager.list_backups()
        if not backups:
            print("No backups found.")
        else:
            print("\nAvailable backups:")
            for i, backup in enumerate(backups, 1):
                timestamp = datetime.datetime.fromtimestamp(
                    backup.stat().st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S")
                size = backup.stat().st_size / (1024 * 1024)  # Convert to MB
                print(f"{i}. {backup.name} ({size:.1f}MB) - {timestamp}")
                
    elif command == "restore":
        if len(sys.argv) < 3:
            backups = manager.list_backups()
            if not backups:
                print("No backups found.")
                sys.exit(1)
                
            print("\nAvailable backups:")
            for i, backup in enumerate(backups, 1):
                print(f"{i}. {backup.name}")
                
            try:
                choice = int(input("\nEnter backup number to restore: "))
                backup_path = backups[choice - 1]
            except (ValueError, IndexError):
                print("Invalid selection.")
                sys.exit(1)
        else:
            backup_path = Path(sys.argv[2])
            
        print(f"\nRestoring from {backup_path}...")
        if manager.restore_backup(backup_path):
            print("\nRestore complete!")
            
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1) 