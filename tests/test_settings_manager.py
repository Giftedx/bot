import pytest
from src.core.settings_manager import SettingsManager
from pathlib import Path


@pytest.fixture
def env_with_discord_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISCORD_TOKEN", "test_discord_token")


def test_settings_manager_environment_variables(
    env_with_discord_token: pytest.fixture,
) -> None:
    settings_manager = SettingsManager()
    assert settings_manager.get_setting_str("DISCORD_TOKEN") == "test_discord_token"


@pytest.fixture
def create_dotenv_file(tmp_path: Path) -> Path:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("PLEX_URL=test_plex_url\n")
    return dotenv_path


def test_settings_manager_dotenv_file(
    create_dotenv_file: Path,
) -> None:
    settings_manager = SettingsManager(dotenv_path=str(create_dotenv_file))
    assert settings_manager.get_setting_str("PLEX_URL") == "test_plex_url"


def test_settings_manager_command_line_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FFMPEG_PATH", "env_ffmpeg_path")
    settings_manager = SettingsManager()
    settings_manager._settings["FFMPEG_PATH"] = "command_line_ffmpeg_path"
    assert settings_manager.get_setting_str("FFMPEG_PATH") == "command_line_ffmpeg_path"


def test_settings_manager_default_value() -> None:
    settings_manager = SettingsManager()
    assert (
        settings_manager.get_setting_str("NON_EXISTENT_SETTING", "default_value") == "default_value"
    )


def test_settings_manager_missing_environment_variable() -> None:
    settings_manager = SettingsManager()
    assert settings_manager.get_setting_str("NON_EXISTENT_SETTING") is None


def test_settings_manager_type_conversions() -> None:
    settings_manager = SettingsManager()
    settings_manager._settings["REDIS_PORT"] = "6379"
    settings_manager._settings["DEBUG_MODE"] = "True"

    assert settings_manager.get_setting_int("REDIS_PORT") == 6379
    assert settings_manager.get_setting_bool("DEBUG_MODE") is True


def test_settings_manager_no_hardcoded_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Simulate a hardcoded secret
    monkeypatch.setattr(
        SettingsManager,
        "_settings",
        {"DISCORD_TOKEN": "hardcoded_token"},
    )
    settings_manager = SettingsManager()
    # Assert that the hardcoded token is NOT used
    assert settings_manager.get_setting_str("DISCORD_TOKEN") != "hardcoded_token"
    # Assert that the env var is used or None (if not set)
    monkeypatch.delenv("DISCORD_TOKEN", raising=False)
    assert settings_manager.get_setting_str("DISCORD_TOKEN") is None
