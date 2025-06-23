"""Theme management system for UI customization.

This module handles interface theming including:
- Theme definition and validation
- Color scheme management
- Theme switching and persistence
- Dark/light mode support
"""

from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum


class ThemeMode(Enum):
    """Available theme modes."""

    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


@dataclass
class ColorScheme:
    """Color scheme definition for a theme."""

    primary: str
    secondary: str
    background: str
    surface: str
    error: str
    text_primary: str
    text_secondary: str


class ThemeManager:
    """Manages UI themes and color schemes."""

    def __init__(self, default_mode: ThemeMode = ThemeMode.LIGHT):
        """Initialize theme manager.

        Args:
            default_mode: Default theme mode to use
        """
        self._current_mode = default_mode
        self._themes: Dict[str, ColorScheme] = {}
        self._active_theme: Optional[str] = None

    def register_theme(self, name: str, scheme: ColorScheme) -> None:
        """Register a new theme.

        Args:
            name: Unique theme identifier
            scheme: Color scheme for the theme
        """
        self._themes[name] = scheme

    def set_theme(self, name: str) -> None:
        """Activate a specific theme.

        Args:
            name: Name of theme to activate

        Raises:
            ThemeNotFound: If theme name is not registered
        """
        if name not in self._themes:
            raise ThemeNotFound(f"Theme '{name}' not found.")
        self._active_theme = name

    def set_mode(self, mode: ThemeMode) -> None:
        """Set the theme mode.

        Args:
            mode: Theme mode to activate
        """
        self._current_mode = mode

    def get_theme(self, theme_name: str = "default") -> Optional[ColorScheme]:
        """Retrieve a theme by name.

        Args:
            theme_name: Name of the theme to retrieve

        Returns:
            The color scheme of the theme or None if not found
        """
        return self._themes.get(theme_name)

    def list_themes(self) -> list:
        """List all registered themes.

        Returns:
            A list of theme names
        """
        return list(self._themes.keys())


class ThemeNotFound(Exception):
    """Exception raised when a theme is not found."""

    pass
