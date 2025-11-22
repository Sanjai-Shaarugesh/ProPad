import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk


class ShortcutsWindow(Gtk.ShortcutsWindow):
    """Keyboard shortcuts window."""

    def __init__(self, parent=None, **kwargs):
        super().__init__(**kwargs)

        if parent:
            self.set_transient_for(parent)

        self.set_modal(True)

        # Create shortcuts section
        section = Gtk.ShortcutsSection()
        section.set_visible(True)

        # File Operations Group
        file_group = Gtk.ShortcutsGroup()
        file_group.set_title("File Operations")
        file_group.set_visible(True)

        shortcuts_file = [
            ("Ctrl+N", "New File"),
            ("Ctrl+O", "Open File"),
            ("Ctrl+S", "Save"),
            ("Ctrl+Shift+S", "Save As"),
            ("Ctrl+Shift+F", "File Manager"),
            ("Ctrl+Shift+E", "Export"),
        ]

        for accel, title in shortcuts_file:
            shortcut = Gtk.ShortcutsShortcut()
            shortcut.set_accelerator(accel)
            shortcut.set_title(title)
            shortcut.set_visible(True)
            file_group.append(shortcut)

        section.append(file_group)

        # Editing Group
        edit_group = Gtk.ShortcutsGroup()
        edit_group.set_title("Editing")
        edit_group.set_visible(True)

        shortcuts_edit = [
            ("Ctrl+F", "Find"),
            ("Ctrl+H", "Find and Replace"),
            ("Ctrl+B", "Bold"),
            ("Ctrl+I", "Italic"),
            ("Ctrl+K", "Insert Link"),
        ]

        for accel, title in shortcuts_edit:
            shortcut = Gtk.ShortcutsShortcut()
            shortcut.set_accelerator(accel)
            shortcut.set_title(title)
            shortcut.set_visible(True)
            edit_group.append(shortcut)

        section.append(edit_group)

        # View Group
        view_group = Gtk.ShortcutsGroup()
        view_group.set_title("View")
        view_group.set_visible(True)

        shortcuts_view = [
            ("Ctrl+Alt+S", "Toggle Scroll Sync"),
        ]

        for accel, title in shortcuts_view:
            shortcut = Gtk.ShortcutsShortcut()
            shortcut.set_accelerator(accel)
            shortcut.set_title(title)
            shortcut.set_visible(True)
            view_group.append(shortcut)

        section.append(view_group)

        # Application Group
        app_group = Gtk.ShortcutsGroup()
        app_group.set_title("Application")
        app_group.set_visible(True)

        shortcuts_app = [
            ("F1", "About / Help"),
            ("Ctrl+Q", "Quit"),
        ]

        for accel, title in shortcuts_app:
            shortcut = Gtk.ShortcutsShortcut()
            shortcut.set_accelerator(accel)
            shortcut.set_title(title)
            shortcut.set_visible(True)
            app_group.append(shortcut)

        section.append(app_group)

        # Add section to window
        self.set_child(section)
