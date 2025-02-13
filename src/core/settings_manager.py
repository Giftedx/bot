"""Settings management module."""
import os
import argparse
from typing import Dict, Optional, Any
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class SettingsManager:
    """Manages application settings, loading them hierarchically.

    Priority Order:
    1. Command-line arguments (highest priority, intended for one-off overrides)
    2.  .env file (if present)
    3. Environment variables (lowest priority, can serve as a baseline)
    """

    def __init__(self, dotenv_path: Optional[str] = None) -> None:
        """Initializes the SettingsManager. Loads settings from various sources."""
        self._settings: Dict[str, Optional[str]] = {}
        # settings loaded:
        self._arg_parser = self._create_arg_parser()
        # Initial load from environment (lowest priority, gets system OS
        # if set up as necessary, already)
        self._settings.update(os.environ)

        # Load from .env file, if provided: it MUST also be supported (2nd layer!)
        if dotenv_path:
            load_dotenv(dotenv_path=dotenv_path, override=True)
            # use override always here so values don't get "skipped"
            # from earlier setting values
            self._settings.update(dict(os.environ))
            # and load AFTER any existing variable

    def _create_arg_parser(self) -> argparse.ArgumentParser:
        """Creates and configures the command-line argument parser."""
        parser = argparse.ArgumentParser(
            description="Media Server Configuration")
        # MUST support those keys referenced within previous configuration and
        # context... starting with "redis":
        parser.add_argument("--REDIS_HOST", type=str,
                            help="Redis hostname")
        parser.add_argument("--REDIS_PORT", type=int, help="Redis port")
        parser.add_argument("--REDIS_DB", type=int, help="Redis DB number")
        parser.add_argument("--PLEX_URL", type=str, help="Plex URL")
        parser.add_argument("--PLEX_TOKEN", type=str, help="Plex token")
        parser.add_argument("--DISCORD_TOKEN", type=str,
                            help="Discord token")
        parser.add_argument("--TAUTULLI_URL", type=str, help="Tautulli URL")
        parser.add_argument("--TAUTULLI_API_KEY", type=str,
                            help="Tautulli key")
        parser.add_argument("--FFMPEG_PATH", type=str, help="FFmpeg path")
        parser.add_argument("--BOT_TYPE", type=str, default="regular",
                            help="Bot type (regular or selfbot)")
        parser.add_argument("--COMMAND_PREFIX", type=str, default="!",
                            help="Bot type (regular or selfbot)")
        return parser

    def load_settings(self) -> None:
        """Loads settings from the command line, overriding existing values."""
        # First load command line given highest level to prioritize
        args, _ = self._arg_parser.parse_known_args()
        # if provided those arguments, override config settings with a filter
        # vars must ALWAYS contain default type "str" but this gets properly
        # cast/typed, simplifying
        for key, value in vars(args).items():
            if value is not None:  # Only override if explicitly set via command line
                self._settings[key] = value
                # type is maintained through parser, mypy should not complain
                logging.info(f"Setting '{key}' overridden via command line.")

    # Generic property retrieval.
    def get_setting(self, key: str, default: Optional[Any] = None) -> Any:
        """Retrieves a setting.

        Args:
            key: The setting key.

        Returns:
            The setting value.
        """
        value = self._settings.get(key)

        if value is None:
            if default is not None:
                return default
            return None

        return value

    # Enforce type safety with explicit helper methods.
    def get_setting_str(self, key: str, default: Optional[str] = None) -> Optional[str]:
        val = self.get_setting(key)
        if val is None:
            if default is not None:
                return default
            else:
                return None
        return str(val)

    def get_setting_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        val = self.get_setting(key)
        if val is None: return default

        try:
            return int(
                str(val))  # explicit cast to str to ensure type safety
        except ValueError:
            logging.warning(f"Setting '{key}' has invalid int, using default")
            return default

    def get_setting_bool(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        val = self.get_setting(key)
        if val is None:
            if default is not None:
                return default
            return None
        val_str = str(val).lower()
        if val_str in ('true', '1', 't', 'y', 'yes'):
            return True
        if val_str in ('false', '0', 'f', 'n', 'no'):
            return False
        else:
            logging.warning(f"'{key}' has invalid boolean value")
            return default

    def get_settings(self) -> Dict[str, Optional[str]]:
        """Returns a copy of settings."""
        return self._settings.copy()