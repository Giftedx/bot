import os
from typing import Optional
import logging
from pathlib import Path
import uuid

class StorageService:
    def __init__(self, base_path: str = "data/storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def save_file(self, file_data: bytes, filename: str, subfolder: str = "") -> Optional[str]:
        """
        Saves a file to the storage.
        Returns the relative path to the saved file.
        """
        try:
            folder = self.base_path / subfolder
            folder.mkdir(parents=True, exist_ok=True)

            # Generate a safe filename to prevent collisions and directory traversal
            # We keep the extension
            ext = Path(filename).suffix
            unique_name = f"{uuid.uuid4()}{ext}"

            file_path = folder / unique_name

            with open(file_path, "wb") as f:
                f.write(file_data)

            # Return path relative to base_path, consistent with how we might want to serve it
            # e.g., "avatars/uuid.png"
            relative_path = Path(subfolder) / unique_name
            return str(relative_path)

        except Exception as e:
            self.logger.error(f"Error saving file: {e}")
            return None

    def get_file_path(self, relative_path: str) -> Path:
        """Returns the absolute path for a stored file."""
        return self.base_path / relative_path

    def delete_file(self, relative_path: str) -> bool:
        """Deletes a file from storage."""
        try:
            file_path = self.base_path / relative_path
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting file: {e}")
            return False
