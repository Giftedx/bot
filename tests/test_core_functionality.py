"""
Comprehensive test suite for core bot functionality.

This module tests the essential components of the Discord bot to ensure
everything works correctly after setup and configuration.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import ConfigManager
from src.core.unified_database import UnifiedDatabaseManager, DatabaseConfig
from src.bot.base_bot import BaseBot


class TestConfiguration:
    """Test configuration management."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
        
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_config_manager_creation(self):
        """Test ConfigManager can be created."""
        config_manager = ConfigManager(str(self.config_dir))
        assert config_manager is not None
        assert config_manager.config_dir == self.config_dir
    
    def test_default_config_loading(self):
        """Test default configuration is loaded."""
        config_manager = ConfigManager(str(self.config_dir))
        config = config_manager.config
        
        # Check essential config sections exist
        assert "bot" in config
        assert "database" in config
        assert "events" in config
        
        # Check specific values
        assert config["bot"]["command_prefix"] == "!"
        assert config["database"]["path"] == "data/bot.db"
    
    def test_config_get_method(self):
        """Test config get method with nested keys."""
        config_manager = ConfigManager(str(self.config_dir))
        
        # Test simple key
        prefix = config_manager.get_config("bot.command_prefix")
        assert prefix == "!"
        
        # Test nested key
        db_path = config_manager.get_config("database.path")
        assert db_path == "data/bot.db"
        
        # Test default value
        unknown = config_manager.get_config("unknown.key", "default")
        assert unknown == "default"
    
    def test_secrets_loading(self):
        """Test secrets loading."""
        config_manager = ConfigManager(str(self.config_dir))
        secrets = config_manager.secrets
        
        # Check secrets structure
        assert "discord" in secrets
        assert "plex" in secrets
        assert "api_keys" in secrets


class TestDatabase:
    """Test database functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_database_manager_creation(self):
        """Test UnifiedDatabaseManager can be created."""
        config = DatabaseConfig(db_path=str(self.db_path))
        db_manager = UnifiedDatabaseManager(config)
        assert db_manager is not None
    
    def test_database_initialization(self):
        """Test database initialization."""
        config = DatabaseConfig(db_path=str(self.db_path))
        db_manager = UnifiedDatabaseManager(config)
        
        # Database should be initialized
        assert self.db_path.exists()
        
        # Check tables exist
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Essential tables should exist
            assert "players" in tables
            assert "pets" in tables
            assert "effects" in tables
    
    def test_database_operations(self):
        """Test basic database operations."""
        config = DatabaseConfig(db_path=str(self.db_path))
        db_manager = UnifiedDatabaseManager(config)
        
        # Test player operations
        player_data = {
            "discord_id": 123456789,
            "username": "testuser",
            "data": '{"level": 1, "xp": 0}'
        }
        
        with db_manager.transaction() as cursor:
            cursor.execute(
                "INSERT INTO players (discord_id, username, data) VALUES (?, ?, ?)",
                (player_data["discord_id"], player_data["username"], player_data["data"])
            )
        
        # Verify player was created
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT * FROM players WHERE discord_id = ?", (123456789,))
            result = cursor.fetchone()
            assert result is not None
            assert result[1] == 123456789  # discord_id
            assert result[2] == "testuser"  # username


class TestBot:
    """Test bot functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
        
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    @patch('discord.ext.commands.Bot.__init__')
    def test_bot_creation(self, mock_bot_init):
        """Test BaseBot can be created."""
        mock_bot_init.return_value = None
        
        config_manager = ConfigManager(str(self.config_dir))
        bot = BaseBot(config_manager=config_manager)
        
        assert bot is not None
        assert bot.config_manager == config_manager
    
    @patch('discord.ext.commands.Bot.__init__')
    def test_bot_database_integration(self, mock_bot_init):
        """Test bot database integration."""
        mock_bot_init.return_value = None
        
        config_manager = ConfigManager(str(self.config_dir))
        bot = BaseBot(config_manager=config_manager)
        
        # Bot should have database manager
        assert hasattr(bot, 'db_manager')
        assert bot.db_manager is not None
    
    @patch('discord.ext.commands.Bot.__init__')
    def test_bot_metrics_integration(self, mock_bot_init):
        """Test bot metrics integration."""
        mock_bot_init.return_value = None
        
        config_manager = ConfigManager(str(self.config_dir))
        bot = BaseBot(config_manager=config_manager)
        
        # Bot should have metrics
        assert hasattr(bot, 'metrics')
        assert bot.metrics is not None


class TestIntegration:
    """Test integration between components."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
        
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_config_database_integration(self):
        """Test configuration and database work together."""
        config_manager = ConfigManager(str(self.config_dir))
        
        # Get database path from config
        db_path = config_manager.get_config("database.path")
        assert db_path == "data/bot.db"
        
        # Create database with config
        db_config = DatabaseConfig(db_path=db_path)
        db_manager = UnifiedDatabaseManager(db_config)
        
        assert db_manager is not None
    
    def test_full_system_initialization(self):
        """Test full system initialization."""
        config_manager = ConfigManager(str(self.config_dir))
        
        # This should not raise any exceptions
        assert config_manager is not None
        
        # Test database initialization
        db_path = config_manager.get_config("database.path")
        db_config = DatabaseConfig(db_path=db_path)
        db_manager = UnifiedDatabaseManager(db_config)
        
        assert db_manager is not None


class TestErrorHandling:
    """Test error handling."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
        
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_invalid_config_key(self):
        """Test handling of invalid config keys."""
        config_manager = ConfigManager(str(self.config_dir))
        
        # Should return default value for invalid key
        value = config_manager.get_config("invalid.key", "default_value")
        assert value == "default_value"
    
    def test_database_connection_error(self):
        """Test database connection error handling."""
        # Try to create database with invalid path
        invalid_path = "/invalid/path/database.db"
        db_config = DatabaseConfig(db_path=invalid_path)
        
        # This should handle the error gracefully
        try:
            db_manager = UnifiedDatabaseManager(db_config)
            # If it doesn't raise an exception, that's fine too
            # as long as it handles the error internally
        except Exception as e:
            # Should be a specific database error
            assert "database" in str(e).lower() or "path" in str(e).lower()


class TestPerformance:
    """Test performance characteristics."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
        
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_config_loading_performance(self):
        """Test configuration loading performance."""
        import time
        
        start_time = time.time()
        config_manager = ConfigManager(str(self.config_dir))
        end_time = time.time()
        
        # Should load quickly (less than 1 second)
        load_time = end_time - start_time
        assert load_time < 1.0
    
    def test_database_initialization_performance(self):
        """Test database initialization performance."""
        import time
        
        db_path = Path(self.temp_dir) / "perf_test.db"
        db_config = DatabaseConfig(db_path=str(db_path))
        
        start_time = time.time()
        db_manager = UnifiedDatabaseManager(db_config)
        end_time = time.time()
        
        # Should initialize quickly (less than 2 seconds)
        init_time = end_time - start_time
        assert init_time < 2.0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])