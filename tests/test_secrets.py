"""Tests for enhanced secrets management functionality."""
import os
from unittest.mock import Mock, patch

import hvac
import pytest

from src.core.secrets import Secrets, SecretsManager, get_secrets_manager, load_secrets


@pytest.fixture
def mock_vault_client():
    """Create a mock Vault client."""
    client = Mock(spec=hvac.Client)
    client.is_authenticated.return_value = True
    return client


@pytest.fixture
def secrets_manager(mock_vault_client):
    """Create a SecretsManager with mocked Vault client."""
    with patch("hvac.Client", return_value=mock_vault_client):
        os.environ["VAULT_ADDR"] = "http://vault:8200"
        os.environ["VAULT_TOKEN"] = "test-token"
        manager = SecretsManager()
        yield manager


def test_secrets_manager_init_without_vault():
    """Test SecretsManager initialization without Vault credentials."""
    if "VAULT_ADDR" in os.environ:
        del os.environ["VAULT_ADDR"]
    if "VAULT_TOKEN" in os.environ:
        del os.environ["VAULT_TOKEN"]

    manager = SecretsManager()
    assert manager._vault_client is None


def test_secrets_manager_vault_auth_failure(mock_vault_client):
    """Test handling of Vault authentication failure."""
    mock_vault_client.is_authenticated.return_value = False

    with patch("hvac.Client", return_value=mock_vault_client):
        os.environ["VAULT_ADDR"] = "http://vault:8200"
        os.environ["VAULT_TOKEN"] = "invalid-token"

        manager = SecretsManager()
        assert manager._vault_client is None


def test_load_secrets_from_vault(secrets_manager, mock_vault_client):
    """Test loading secrets from Vault."""
    mock_vault_client.secrets.kv.read_secret_version.return_value = {
        "data": {"data": {"token": "vault-discord-token", "api_key": "vault-giphy-key"}}
    }

    secrets = secrets_manager.load_secrets()
    assert secrets.discord_token == "vault-discord-token"
    mock_vault_client.secrets.kv.read_secret_version.assert_called()


def test_load_secrets_fallback_to_env(secrets_manager, mock_vault_client):
    """Test fallback to environment variables when Vault fails."""
    mock_vault_client.secrets.kv.read_secret_version.side_effect = Exception(
        "Vault error"
    )

    os.environ["DISCORD_TOKEN"] = "env-discord-token"
    os.environ["GIPHY_API_KEY"] = "env-giphy-key"

    secrets = secrets_manager.load_secrets()
    assert secrets.discord_token == "env-discord-token"
    assert secrets.giphy_api_key == "env-giphy-key"


def test_load_secrets_from_env_file(tmp_path):
    """Test loading secrets from .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DISCORD_TOKEN=file-discord-token\n"
        "PLEX_TOKEN=file-plex-token\n"
        "GIPHY_API_KEY=file-giphy-key\n"
    )

    if "VAULT_ADDR" in os.environ:
        del os.environ["VAULT_ADDR"]

    secrets = load_secrets(env_file)
    assert secrets.discord_token == "file-discord-token"
    assert secrets.plex_token == "file-plex-token"
    assert secrets.giphy_api_key == "file-giphy-key"


def test_secrets_manager_singleton():
    """Test that get_secrets_manager returns singleton instance."""
    s1 = get_secrets_manager()
    s2 = get_secrets_manager()
    assert s1 is s2


def test_load_secrets_missing_required():
    """Test error when required secrets are missing."""
    if "DISCORD_TOKEN" in os.environ:
        del os.environ["DISCORD_TOKEN"]
    if "VAULT_ADDR" in os.environ:
        del os.environ["VAULT_ADDR"]

    with pytest.raises(ValueError, match="Discord token not found"):
        load_secrets()
