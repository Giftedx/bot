class ThemeManager:
    def __init__(self):
        self.themes = {
            "default": {
                "primary_color": "#FFFFFF",
                "secondary_color": "#F0F0F0",
                # ... more default theme properties ...
            },
            "dark": {
                "primary_color": "#333333",
                "secondary_color": "#666666",
                # ... more dark theme properties ...
            },
        }

    def get_theme(self, theme_name="default"):
        return self.themes.get(theme_name, self.themes["default"])

    def list_themes(self):
        return list(self.themes.keys())