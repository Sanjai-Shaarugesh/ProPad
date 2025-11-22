"""
src/settings.py
Helper module for managing application settings via GSettings
"""

from gi.repository import Gio
from src.config import APP_ID


class Settings:
    """Wrapper for GSettings to manage application preferences."""

    def __init__(self):
        """Initialize settings with the app's GSettings schema."""
        self.settings = Gio.Settings.new(APP_ID)

    # Window state
    @property
    def window_width(self) -> int:
        return self.settings.get_int("window-width")

    @window_width.setter
    def window_width(self, value: int):
        self.settings.set_int("window-width", value)

    @property
    def window_height(self) -> int:
        return self.settings.get_int("window-height")

    @window_height.setter
    def window_height(self, value: int):
        self.settings.set_int("window-height", value)

    @property
    def window_maximized(self) -> bool:
        return self.settings.get_boolean("window-maximized")

    @window_maximized.setter
    def window_maximized(self, value: bool):
        self.settings.set_boolean("window-maximized", value)

    # Application settings
    @property
    def dark_mode(self) -> bool:
        return self.settings.get_boolean("dark-mode")

    @dark_mode.setter
    def dark_mode(self, value: bool):
        self.settings.set_boolean("dark-mode", value)

    @property
    def sidebar_visible(self) -> bool:
        return self.settings.get_boolean("sidebar-visible")

    @sidebar_visible.setter
    def sidebar_visible(self, value: bool):
        self.settings.set_boolean("sidebar-visible", value)

    @property
    def last_opened_file(self) -> str:
        return self.settings.get_string("last-opened-file")

    @last_opened_file.setter
    def last_opened_file(self, value: str):
        self.settings.set_string("last-opened-file", value)

    @property
    def recent_files(self) -> list[str]:
        return self.settings.get_strv("recent-files")

    @recent_files.setter
    def recent_files(self, value: list[str]):
        self.settings.set_strv("recent-files", value)

    # Editor settings
    @property
    def font_size(self) -> int:
        return self.settings.get_int("font-size")

    @font_size.setter
    def font_size(self, value: int):
        self.settings.set_int("font-size", value)

    @property
    def show_line_numbers(self) -> bool:
        return self.settings.get_boolean("show-line-numbers")

    @show_line_numbers.setter
    def show_line_numbers(self, value: bool):
        self.settings.set_boolean("show-line-numbers", value)

    @property
    def auto_save(self) -> bool:
        return self.settings.get_boolean("auto-save")

    @auto_save.setter
    def auto_save(self, value: bool):
        self.settings.set_boolean("auto-save", value)

    @property
    def auto_save_interval(self) -> int:
        return self.settings.get_int("auto-save-interval")

    @auto_save_interval.setter
    def auto_save_interval(self, value: int):
        self.settings.set_int("auto-save-interval", value)

    def bind(self, key: str, obj, prop: str, flags=Gio.SettingsBindFlags.DEFAULT):
        """
        Bind a GSettings key to an object property.

        Args:
            key: The GSettings key name
            obj: The object to bind to
            prop: The property name on the object
            flags: Binding flags (default, get, set, etc.)
        """
        self.settings.bind(key, obj, prop, flags)

    def reset_all(self):
        """Reset all settings to their default values."""
        for key in self.settings.list_keys():
            self.settings.reset(key)


# Usage example in your application:
"""
from src.settings import Settings

class MyWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = Settings()
        
        # Restore window size
        self.set_default_size(
            self.settings.window_width,
            self.settings.window_height
        )
        
        if self.settings.window_maximized:
            self.maximize()
        
        # Bind settings to widgets
        self.settings.bind('sidebar-visible', self.sidebar, 'reveal-child')
        self.settings.bind('dark-mode', self.style_manager, 'dark')
    
    def on_close(self):
        # Save window state
        width, height = self.get_default_size()
        self.settings.window_width = width
        self.settings.window_height = height
        self.settings.window_maximized = self.is_maximized()
"""
