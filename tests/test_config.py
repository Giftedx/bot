"""Test configuration module."""
import os
from typing import Generator
import pytest
from src.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    """Create a Settings instance for testing."""
    return Settings()


def test_settings_load(settings: Settings) -> None:
    """Test loading settings from environment variables."""
    assert isinstance(settings, Settings)


def test_get_str(settings: Settings) -> None:
    """Test getting string values from settings."""
    # Test with default value
    assert settings.get_str("NON_EXISTENT", "default") == "default"
    
    # Test with environment variable
    os.environ["TEST_STR"] = "test_value"
    settings = Settings()  # Reload settings
    assert settings.get_str("TEST_STR") == "test_value"


def test_get_int(settings: Settings) -> None:
    """Test getting integer values from settings."""
    # Test with default value
    assert settings.get_int("NON_EXISTENT", 42) == 42
    
    # Test with environment variable
    os.environ["TEST_INT"] = "123"
    settings = Settings()  # Reload settings
    assert settings.get_int("TEST_INT") == 123


def test_get_bool(settings: Settings) -> None:
    """Test getting boolean values from settings."""
    # Test with default value
    assert settings.get_bool("NON_EXISTENT", True) is True
    
    # Test with environment variable
    os.environ["TEST_BOOL"] = "true"
    settings = Settings()  # Reload settings
    assert settings.get_bool("TEST_BOOL") is True
    
    # Test various boolean string values
    test_values = {
        "true": True,
        "1": True,
        "yes": True,
        "on": True,
        "false": False,
        "0": False,
        "no": False,
        "off": False
    }
    
    for value, expected in test_values.items():
        os.environ["TEST_BOOL"] = value
        settings = Settings()  # Reload settings
        assert settings.get_bool("TEST_BOOL") is expected


def test_get_list(settings: Settings) -> None:
    """Test getting list values from settings."""
    # Test with default value
    assert settings.get_list("NON_EXISTENT", ["default"]) == ["default"]
    
    # Test with environment variable
    os.environ["TEST_LIST"] = "item1,item2,item3"
    settings = Settings()  # Reload settings
    assert settings.get_list("TEST_LIST") == ["item1", "item2", "item3"]
    
    # Test with empty string
    os.environ["TEST_LIST"] = ""
    settings = Settings()  # Reload settings
    assert settings.get_list("TEST_LIST") == []
    
    # Test with whitespace
    os.environ["TEST_LIST"] = "  item1  ,  item2  ,  item3  "
    settings = Settings()  # Reload settings
    assert settings.get_list("TEST_LIST") == ["item1", "item2", "item3"]


def test_invalid_int(settings: Settings) -> None:
    """Test handling invalid integer values."""
    os.environ["INVALID_INT"] = "not_a_number"
    settings = Settings()  # Reload settings
    
    with pytest.raises(ValueError):
        settings.get_int("INVALID_INT")


def test_invalid_bool(settings: Settings) -> None:
    """Test handling invalid boolean values."""
    os.environ["INVALID_BOOL"] = "not_a_boolean"
    settings = Settings()  # Reload settings
    
    with pytest.raises(ValueError):
        settings.get_bool("INVALID_BOOL")


def test_invalid_list(settings: Settings) -> None:
    """Test handling invalid list values."""
    os.environ["INVALID_LIST"] = 123  # type: ignore
    settings = Settings()  # Reload settings
    
    with pytest.raises(ValueError):
        settings.get_list("INVALID_LIST")


def test_attribute_access(settings: Settings) -> None:
    """Test attribute-style access to settings."""
    os.environ["TEST_ATTR"] = "test_value"
    settings = Settings()  # Reload settings
    
    assert settings.TEST_ATTR == "test_value"
    
    with pytest.raises(AttributeError):
        settings.NON_EXISTENT_ATTR  # type: ignore


@pytest.fixture(autouse=True)
def cleanup() -> Generator[None, None, None]:
    """Clean up environment variables after each test."""
    yield
    test_vars = [
        "TEST_STR", "TEST_INT", "TEST_BOOL", "TEST_LIST",
        "INVALID_INT", "INVALID_BOOL", "INVALID_LIST",
        "TEST_ATTR"
    ]
    for var in test_vars:
        os.environ.pop(var, None)
