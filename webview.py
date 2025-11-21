import gi

gi.require_version(namespace="Gtk", version="4.0")
gi.require_version(namespace="WebKit", version="6.0")

from gi.repository import Gtk, WebKit

UI_FILE = "ui/webview.ui"


@Gtk.Template(filename=UI_FILE)
class WebViewWidget(Gtk.Box):
    __gtype_name__ = "WebViewWidget"

    webview_container = Gtk.Template.Child()

    def __init__(self, **kwargs):
        if "orientation" not in kwargs:
            kwargs["orientation"] = Gtk.Orientation.VERTICAL
        super().__init__(**kwargs)

        self.webview = WebKit.WebView.new()

        settings = self.webview.get_settings()
        settings.set_enable_javascript(True)

        self.webview_container.append(self.webview)

        self.webview.connect("load-changed", self._on_load_changed)

    def load_uri(self, uri: str):
        self.webview.load_uri(uri)

    def load_html(self, html: str):
        self.webview.load_html(html, None)

    def reload(self):
        self.webview.reload()

    def _on_load_changed(self, webview, load_event):
        print("Load changed:", load_event)
