import gi


gi.require_version(namespace="Gtk", version="4.0")
gi.require_version(namespace="Adw", version="1")

from gi.repository import Adw, Gtk
from sidebar import SidebarWidget
from webview import WebViewWidget

import comrak

UI_FILE = "ui/window.ui"


@Gtk.Template(filename=UI_FILE)
class Window(Adw.ApplicationWindow):
    __gtype_name__ = "Window"

    toggle_sidebar_btn = Gtk.Template.Child()
    adw_overlay_split_view = Gtk.Template.Child()
    adw_multi_layout_view = Gtk.Template.Child()

    # Desktop containers
    sidebar_container = Gtk.Template.Child()
    webview_container = Gtk.Template.Child()

    # Mobile containers
    mobile_sidebar_container = Gtk.Template.Child()
    mobile_webview_container = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        from gi.repository import GLib

        self.is_mobile = False
        self.webview_hidden = False  # Track webview visibility state

        # Connect sidebar toggle button
        self.toggle_sidebar_btn.connect("clicked", self._on_toggle_sidebar)

        # Create widgets
        self.sidebar_widget = SidebarWidget()
        self.webview_widget = WebViewWidget()

        # Configure comrak extension options with table support
        self.extension_options = comrak.ExtensionOptions()
        self.extension_options.table = True  # Enable table support
        self.extension_options.strikethrough = True
        self.extension_options.autolink = True
        self.extension_options.tasklist = True
        self.extension_options.superscript = True
        self.extension_options.footnotes = True

        # Starting text with proper table
        initial_text = """# Welcome to ProPad

## Table Example

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |

Start editing to see the preview!"""

        # Render markdown with table support
        initial_html = comrak.render_markdown(
            initial_text, extension_options=self.extension_options
        )

        # Desktop view initially
        self.sidebar_container.append(self.sidebar_widget)
        self.webview_container.append(self.webview_widget)

        # Set initial text and render
        self.sidebar_widget.set_text(initial_text)
        self.webview_widget.load_html(initial_html, is_dark=self.is_dark_mode())

        # Connect to text buffer changes with proper theme handling
        def on_text_update(text):
            html = comrak.render_markdown(
                text, extension_options=self.extension_options
            )
            # Get dark mode status at the time of the callback
            self.webview_widget.load_html(html, is_dark=self.is_dark_mode())

        self.sidebar_widget.connect_text_changed(on_text_update)

        # Connect hide webview button
        self.sidebar_widget.connect_hide_webview(self._on_hide_webview)

        # Show sidebar by default on desktop
        self.adw_overlay_split_view.set_show_sidebar(True)

        # Listen for layout changes
        self.adw_multi_layout_view.connect(
            "notify::layout-name", self._on_layout_changed
        )

        # Set initial layout
        self._on_layout_changed(self.adw_multi_layout_view, None)

    def is_dark_mode(self) -> bool:
        """Check if the current GTK theme is dark."""
        # Use Adw.StyleManager for accurate theme detection
        style_manager = Adw.StyleManager.get_default()
        return style_manager.get_dark()

    def _on_toggle_sidebar(self, button: Gtk.Button) -> None:
        """Toggle sidebar visibility."""
        self.adw_overlay_split_view.set_show_sidebar(
            not self.adw_overlay_split_view.get_show_sidebar()
        )

    def _on_hide_webview(self) -> None:
        """Toggle webview visibility - hide/show the entire right panel."""
        self.webview_hidden = not self.webview_hidden

        if self.webview_hidden:
            # Hide the entire right side
            if not self.is_mobile:
                # On desktop, collapse the split view to show only sidebar
                self.adw_overlay_split_view.set_collapsed(True)
                self.adw_overlay_split_view.set_show_sidebar(True)
            else:
                # On mobile, just hide the webview container
                self.mobile_webview_container.set_visible(False)

            # Update button to show "Show Preview"
            self.sidebar_widget.hide_webview_btn.set_icon_name("view-reveal-symbolic")
            self.sidebar_widget.hide_webview_btn.set_tooltip_text("Show Preview")
        else:
            # Show the entire right side
            if not self.is_mobile:
                # On desktop, uncollapse the split view
                self.adw_overlay_split_view.set_collapsed(False)
                self.adw_overlay_split_view.set_show_sidebar(True)
            else:
                # On mobile, show the webview container
                self.mobile_webview_container.set_visible(True)

            # Update button to show "Hide Preview"
            self.sidebar_widget.hide_webview_btn.set_icon_name("window-close-symbolic")
            self.sidebar_widget.hide_webview_btn.set_tooltip_text("Hide Preview")

    def _on_layout_changed(self, multi_layout: Adw.MultiLayoutView, _) -> None:
        """Handle layout changes between desktop and mobile."""
        layout_name = multi_layout.get_layout_name()

        if layout_name == "mobile" and not self.is_mobile:
            self._switch_to_mobile()
        elif layout_name == "desktop" and self.is_mobile:
            self._switch_to_desktop()

    def _switch_to_mobile(self) -> None:
        """Switch to mobile layout."""
        print("Switching to mobile layout")
        self.is_mobile = True

        # Remove from desktop containers
        parent = self.sidebar_widget.get_parent()
        if parent:
            parent.remove(self.sidebar_widget)

        parent = self.webview_widget.get_parent()
        if parent:
            parent.remove(self.webview_widget)

        # Add to mobile containers
        self.mobile_sidebar_container.append(self.sidebar_widget)
        self.mobile_webview_container.append(self.webview_widget)

        # Apply current visibility state
        self.mobile_webview_container.set_visible(not self.webview_hidden)

    def _switch_to_desktop(self) -> None:
        """Switch to desktop layout."""
        print("Switching to desktop layout")
        self.is_mobile = False

        # Remove from mobile containers
        parent = self.sidebar_widget.get_parent()
        if parent:
            parent.remove(self.sidebar_widget)

        parent = self.webview_widget.get_parent()
        if parent:
            parent.remove(self.webview_widget)

        # Add back to desktop containers
        self.sidebar_container.append(self.sidebar_widget)
        self.webview_container.append(self.webview_widget)

        # Apply current visibility state
        if self.webview_hidden:
            self.adw_overlay_split_view.set_collapsed(True)
            self.adw_overlay_split_view.set_show_sidebar(True)
        else:
            self.adw_overlay_split_view.set_collapsed(False)
            self.adw_overlay_split_view.set_show_sidebar(True)

    def get_sidebar(self) -> SidebarWidget:
        """Get the sidebar widget."""
        return self.sidebar_widget

    def get_webview(self) -> WebViewWidget:
        """Get the webview widget."""
        return self.webview_widget
