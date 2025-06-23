"""
This module provides a unified interface for managing sensitive configuration
values with support for both environment variables and HashiCorp Vault.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import hvac
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class Secrets:
    """Container for sensitive configuration values."""

    discord_token: str
    plex_token: Optional[str] = None
    giphy_api_key: Optional[str] = None
    redis_url: Optional[str] = None
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None


class SecretsManager:
    """Manages application secrets with Vault integration."""

    def __init__(self) -> None:
        """Initialize secrets manager."""
        self._vault_client = None
        self._init_vault()

    def _init_vault(self) -> None:
        """Initialize Vault client if credentials are available."""
        vault_addr = os.getenv("VAULT_ADDR")
        vault_token = os.getenv("VAULT_TOKEN")

        if vault_addr and vault_token:
            try:
                self._vault_client = hvac.Client(url=vault_addr, token=vault_token)
                if not self._vault_client.is_authenticated():
                    logger.warning("Vault authentication failed")
                    self._vault_client = None
            except Exception as e:
                logger.error(f"Failed to initialize Vault client: {e}")
                self._vault_client = None

    def _get_from_vault(self, path: str, key: str) -> Optional[str]:
        """Get a secret from Vault."""
        if not self._vault_client:
            return None

        try:
            secret = self._vault_client.secrets.kv.read_secret_version(path=path)
            return secret["data"]["data"].get(key)
        except Exception as e:
            logger.error(f"Error retrieving secret from Vault: {e}")
            return None

    def load_secrets(self, env_file: Optional[Path] = None) -> Secrets:
        """Load secrets from environment/Vault/env file.
        Args:
            env_file: Optional path to .env file
        Returns:
            Secrets object containing configuration
        Raises:
            ValueError: If required secrets are missing
        """
        # Load .env file if provided
        if env_file and env_file.exists():
            load_dotenv(env_file)

        # Try Vault first, then fall back to env vars
        discord_token = self._get_from_vault("discord", "token") or os.getenv("DISCORD_TOKEN")

        if not discord_token:
            raise ValueError("Discord token not found in Vault or environment")

        return Secrets(
            discord_token=discord_token,
            plex_token=self._get_from_vault("plex", "token") or os.getenv("PLEX_TOKEN"),
            giphy_api_key=self._get_from_vault("giphy", "api_key") or os.getenv("GIPHY_API_KEY"),
            redis_url=self._get_from_vault("redis", "url") or os.getenv("REDIS_URL"),
            spotify_client_id=self._get_from_vault("spotify", "client_id")
            or os.getenv("SPOTIFY_CLIENT_ID"),
            spotify_client_secret=self._get_from_vault("spotify", "client_secret")
            or os.getenv("SPOTIFY_CLIENT_SECRET"),
        )


_instance: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get or create the SecretsManager singleton instance."""
    global _instance
    if _instance is None:
        _instance = SecretsManager()
    return _instance


def load_secrets(env_file: Optional[Path] = None) -> Secrets:
    """Load secrets using the SecretsManager singleton."""
    return get_secrets_manager().load_secrets(env_file)
