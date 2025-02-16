"""Base class for data managers with caching and validation."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

class DataManager:
    """Base class for managing game data with caching."""
    
    def __init__(self, data_dir: str = "src/osrs/data"):
        """Initialize the data manager.
        
        Args:
            data_dir: Directory containing data files.
        """
        self.data_dir = Path(data_dir)
        self._cache: Dict[str, Dict] = {}
        
    def _load_json_file(self, filename: str) -> Dict:
        """Load and cache a JSON file.
        
        Args:
            filename: Name of the JSON file to load.
            
        Returns:
            Dict containing the JSON data.
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
            json.JSONDecodeError: If the file contains invalid JSON.
        """
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
            
        if filename not in self._cache:
            try:
                with open(filepath, 'r') as f:
                    self._cache[filename] = json.load(f)
                logger.info(f"Loaded data file: {filename}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse {filename}: {e}")
                raise
                
        return self._cache[filename]
    
    @lru_cache(maxsize=1024)
    def get_data(self, filename: str, key: Optional[str] = None) -> Any:
        """Get data from a JSON file, optionally filtered by key.
        
        Args:
            filename: Name of the JSON file to load.
            key: Optional key to retrieve specific data.
            
        Returns:
            The requested data.
            
        Raises:
            KeyError: If the key doesn't exist in the data.
        """
        data = self._load_json_file(filename)
        if key is not None:
            if key not in data:
                raise KeyError(f"Key '{key}' not found in {filename}")
            return data[key]
        return data
    
    def clear_cache(self, filename: Optional[str] = None):
        """Clear the data cache.
        
        Args:
            filename: Optional specific file to clear from cache.
        """
        if filename:
            self._cache.pop(filename, None)
            self.get_data.cache_clear()
        else:
            self._cache.clear()
            self.get_data.cache_clear()
        logger.info(f"Cleared cache for: {filename if filename else 'all files'}") 