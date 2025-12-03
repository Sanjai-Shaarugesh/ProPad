"""
Enhanced Scroll Synchronization System
Prevents jumping and provides smooth bidirectional sync between TextView and WebView
"""

import gi
import threading
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable

gi.require_version("Gtk", "4.0")
gi.require_version("WebKit", "6.0")

from gi.repository import Gtk, GLib, WebKit


class ScrollSource(Enum):
    """Track which widget initiated the scroll"""

    NONE = 0
    TEXTVIEW = 1
    WEBVIEW = 2
    PROGRAMMATIC = 3


@dataclass
class ScrollState:
    """Maintains current scroll state"""

    percentage: float = 0.0
    source: ScrollSource = ScrollSource.NONE
    timestamp: int = 0

    def is_recent(self, current_time: int, threshold_ms: int = 150) -> bool:
        """Check if this scroll event is recent"""
        return (current_time - self.timestamp) < threshold_ms


class SmoothScrollSyncManager:
    """
    Manages smooth bidirectional scroll synchronization without jumping.

    Key features:
    - Prevents feedback loops using source tracking
    - Debounces scroll events to reduce CPU usage
    - Uses scroll restoration to prevent jumping during typing
    - Supports both manual and programmatic scrolling
    """

    def __init__(self):
        self.enabled = True
        self._lock = threading.Lock()

        # Track scroll states
        self._textview_state = ScrollState()
        self._webview_state = ScrollState()

        # Current active scroll source
        self._active_source = ScrollSource.NONE
        self._scroll_timeout_id = None

        # Debounce settings
        self.debounce_ms = 50  # Wait 50ms before syncing
        self.threshold = 0.003  # Minimum change to trigger sync

        # Widget references
        self.textview: Optional[Gtk.TextView] = None
        self.webview: Optional[WebKit.WebView] = None
        self.textview_adjustment: Optional[Gtk.Adjustment] = None

        print("🔄 SmoothScrollSyncManager initialized")

    def setup_textview(
        self, textview: Gtk.TextView, scrolled_window: Gtk.ScrolledWindow
    ):
        """Setup TextView scroll monitoring"""
        self.textview = textview
        self.textview_adjustment = scrolled_window.get_vadjustment()

        if not self.textview_adjustment:
            print("⚠️ Warning: Could not get vadjustment from scrolled window")
            return False

        # Connect to value-changed signal
        self.textview_adjustment.connect("value-changed", self._on_textview_scroll)

        print("✅ TextView scroll monitoring setup complete")
        return True

    def setup_webview(self, webview: WebKit.WebView):
        """Setup WebView scroll monitoring"""
        self.webview = webview

        # Inject scroll monitoring JavaScript
        js_code = """
        (function() {
            if (window.scrollSyncInitialized) return;
            window.scrollSyncInitialized = true;
            
            let lastPercentage = 0;
            let scrolling = false;
            
            function getScrollPercentage() {
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
                return scrollHeight > 0 ? scrollTop / scrollHeight : 0;
            }
            
            function notifyScroll() {
                const percentage = getScrollPercentage();
                if (Math.abs(percentage - lastPercentage) > 0.003) {
                    lastPercentage = percentage;
                    document.title = 'scroll:' + percentage.toFixed(6);
                }
            }
            
            // Throttled scroll handler
            let scrollTimeout;
            window.addEventListener('scroll', function() {
                scrolling = true;
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(function() {
                    notifyScroll();
                    scrolling = false;
                }, 16); // ~60fps
            }, { passive: true });
            
            // Polling as backup
            setInterval(function() {
                if (!scrolling) {
                    notifyScroll();
                }
            }, 100);
        })();
        """

        try:
            self.webview.evaluate_javascript(js_code, -1, None, None, None)
            # Start polling for title changes
            GLib.timeout_add(100, self._poll_webview_scroll)
            print("✅ WebView scroll monitoring setup complete")
            return True
        except Exception as e:
            print(f"❌ Error setting up WebView scroll monitoring: {e}")
            return False

    def _on_textview_scroll(self, adjustment: Gtk.Adjustment):
        """Handle TextView scroll events"""
        if not self.enabled:
            return

        with self._lock:
            # Skip if WebView is currently scrolling
            if self._active_source == ScrollSource.WEBVIEW:
                return

            # Calculate percentage
            value = adjustment.get_value()
            upper = adjustment.get_upper()
            page_size = adjustment.get_page_size()
            max_scroll = upper - page_size

            if max_scroll <= 0:
                percentage = 0.0
            else:
                percentage = value / max_scroll

            current_time = GLib.get_monotonic_time() // 1000  # Convert to ms

            # Check if change is significant
            if abs(percentage - self._textview_state.percentage) < self.threshold:
                return

            # Update state
            self._textview_state.percentage = percentage
            self._textview_state.source = ScrollSource.TEXTVIEW
            self._textview_state.timestamp = current_time

            # Set active source
            self._active_source = ScrollSource.TEXTVIEW

            # Debounce the sync
            if self._scroll_timeout_id:
                GLib.source_remove(self._scroll_timeout_id)

            self._scroll_timeout_id = GLib.timeout_add(
                self.debounce_ms, self._sync_to_webview, percentage
            )

    def _poll_webview_scroll(self) -> bool:
        """Poll WebView scroll position from document title"""
        if not self.enabled or not self.webview:
            return True

        with self._lock:
            # Skip if TextView is currently scrolling
            if self._active_source == ScrollSource.TEXTVIEW:
                return True

            try:
                title = self.webview.get_title()
                if title and title.startswith("scroll:"):
                    percentage = float(title.split(":")[1])
                    current_time = GLib.get_monotonic_time() // 1000

                    # Check if change is significant
                    if (
                        abs(percentage - self._webview_state.percentage)
                        < self.threshold
                    ):
                        return True

                    # Update state
                    self._webview_state.percentage = percentage
                    self._webview_state.source = ScrollSource.WEBVIEW
                    self._webview_state.timestamp = current_time

                    # Set active source
                    self._active_source = ScrollSource.WEBVIEW

                    # Debounce the sync
                    if self._scroll_timeout_id:
                        GLib.source_remove(self._scroll_timeout_id)

                    self._scroll_timeout_id = GLib.timeout_add(
                        self.debounce_ms, self._sync_to_textview, percentage
                    )
            except Exception as e:
                print(f"Error polling WebView scroll: {e}")

        return True

    def _sync_to_webview(self, percentage: float) -> bool:
        """Sync TextView scroll to WebView"""
        if not self.enabled or not self.webview:
            self._active_source = ScrollSource.NONE
            self._scroll_timeout_id = None
            return False

        with self._lock:
            js_code = f"""
            (function() {{
                const targetPercentage = {percentage};
                const maxScroll = Math.max(
                    document.documentElement.scrollHeight - window.innerHeight,
                    0
                );
                const targetScroll = maxScroll * targetPercentage;
                
                // Use smooth scrolling
                window.scrollTo({{
                    top: targetScroll,
                    behavior: 'auto'  // Instant for better sync
                }});
            }})();
            """

            try:
                self.webview.evaluate_javascript(js_code, -1, None, None, None)
            except Exception as e:
                print(f"Error syncing to WebView: {e}")

            # Release lock after delay
            GLib.timeout_add(100, self._release_lock)
            self._scroll_timeout_id = None
            return False

    def _sync_to_textview(self, percentage: float) -> bool:
        """Sync WebView scroll to TextView"""
        if not self.enabled or not self.textview_adjustment:
            self._active_source = ScrollSource.NONE
            self._scroll_timeout_id = None
            return False

        with self._lock:
            upper = self.textview_adjustment.get_upper()
            page_size = self.textview_adjustment.get_page_size()
            max_scroll = upper - page_size

            if max_scroll > 0:
                target_value = max_scroll * percentage
                self.textview_adjustment.set_value(target_value)

            # Release lock after delay
            GLib.timeout_add(100, self._release_lock)
            self._scroll_timeout_id = None
            return False

    def _release_lock(self) -> bool:
        """Release the active scroll source lock"""
        with self._lock:
            self._active_source = ScrollSource.NONE
        return False

    def scroll_textview_to_percentage(self, percentage: float):
        """Programmatically scroll TextView (e.g., for restoration)"""
        if not self.textview_adjustment:
            return

        with self._lock:
            self._active_source = ScrollSource.PROGRAMMATIC

            upper = self.textview_adjustment.get_upper()
            page_size = self.textview_adjustment.get_page_size()
            max_scroll = upper - page_size

            if max_scroll > 0:
                target_value = max_scroll * percentage
                self.textview_adjustment.set_value(target_value)

            # Update state
            self._textview_state.percentage = percentage
            self._textview_state.source = ScrollSource.PROGRAMMATIC

            # Release after short delay
            GLib.timeout_add(150, self._release_lock)

    def scroll_webview_to_percentage(self, percentage: float):
        """Programmatically scroll WebView (e.g., for restoration)"""
        if not self.webview:
            return

        with self._lock:
            self._active_source = ScrollSource.PROGRAMMATIC

            js_code = f"""
            (function() {{
                const targetPercentage = {percentage};
                const maxScroll = Math.max(
                    document.documentElement.scrollHeight - window.innerHeight,
                    0
                );
                const targetScroll = maxScroll * targetPercentage;
                
                window.scrollTo({{
                    top: targetScroll,
                    behavior: 'auto'
                }});
            }})();
            """

            try:
                self.webview.evaluate_javascript(js_code, -1, None, None, None)
            except Exception as e:
                print(f"Error scrolling WebView: {e}")

            # Update state
            self._webview_state.percentage = percentage
            self._webview_state.source = ScrollSource.PROGRAMMATIC

            # Release after short delay
            GLib.timeout_add(150, self._release_lock)

    def get_textview_percentage(self) -> float:
        """Get current TextView scroll percentage"""
        if not self.textview_adjustment:
            return 0.0

        value = self.textview_adjustment.get_value()
        upper = self.textview_adjustment.get_upper()
        page_size = self.textview_adjustment.get_page_size()
        max_scroll = upper - page_size

        return 0.0 if max_scroll <= 0 else value / max_scroll

    def get_webview_percentage(self, callback: Callable[[float], None]):
        """Get current WebView scroll percentage (async)"""
        if not self.webview:
            callback(0.0)
            return

        js_code = """
        (function() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
            const percentage = scrollHeight > 0 ? scrollTop / scrollHeight : 0;
            document.title = 'getscroll:' + percentage.toFixed(6);
            return percentage;
        })();
        """

        try:
            self.webview.evaluate_javascript(js_code, -1, None, None, None)
            GLib.timeout_add(50, lambda: self._read_webview_percentage(callback))
        except Exception as e:
            print(f"Error getting WebView percentage: {e}")
            callback(0.0)

    def _read_webview_percentage(self, callback: Callable[[float], None]) -> bool:
        """Read percentage from document title"""
        try:
            title = self.webview.get_title()
            if title and title.startswith("getscroll:"):
                percentage = float(title.split(":")[1])
                callback(percentage)
            else:
                callback(0.0)
        except Exception:
            callback(0.0)
        return False

    def set_enabled(self, enabled: bool):
        """Enable or disable scroll synchronization"""
        self.enabled = enabled
        print(f"🔄 Scroll sync {'enabled' if enabled else 'disabled'}")

    def save_scroll_positions(self, callback: Callable[[float, float], None]):
        """Save both scroll positions (async)"""
        textview_pos = self.get_textview_percentage()

        def on_webview_pos(webview_pos: float):
            callback(textview_pos, webview_pos)

        self.get_webview_percentage(on_webview_pos)

    def restore_scroll_positions(self, textview_pos: float, webview_pos: float):
        """Restore both scroll positions without triggering sync"""
        print(
            f"🔄 Restoring scroll positions - TextView: {textview_pos:.3f}, WebView: {webview_pos:.3f}"
        )

        # Temporarily disable sync
        was_enabled = self.enabled
        self.enabled = False

        # Restore TextView immediately
        self.scroll_textview_to_percentage(textview_pos)

        # Restore WebView after HTML loads (with delay)
        def restore_webview():
            self.scroll_webview_to_percentage(webview_pos)
            # Re-enable sync after restoration
            GLib.timeout_add(
                300, lambda: setattr(self, "enabled", was_enabled) or False
            )
            return False

        GLib.timeout_add(200, restore_webview)


# Example integration code
"""
# In window.py __init__:
self.scroll_sync_manager = SmoothScrollSyncManager()

# After creating widgets:
self.scroll_sync_manager.setup_textview(
    self.sidebar_widget.textview,
    self.sidebar_widget.textview.get_parent()  # ScrolledWindow
)

# After webview loads HTML:
self.scroll_sync_manager.setup_webview(self.webview_widget.webview)

# For toggling sync:
def _on_toggle_sync_scroll(self, button):
    self.sync_scroll_enabled = not self.sync_scroll_enabled
    self.scroll_sync_manager.set_enabled(self.sync_scroll_enabled)
    self._update_sync_scroll_button()

# For saving state on close:
def _on_close_request(self, window):
    def on_positions_saved(tv_pos, wv_pos):
        self.state_manager.save_scroll_positions(tv_pos, wv_pos)
    
    self.scroll_sync_manager.save_scroll_positions(on_positions_saved)
    return False

# For restoring state:
def _restore_state(self):
    # ... restore other state ...
    
    scroll_positions = self.state_manager.get_scroll_positions()
    
    def restore_after_layout():
        self.scroll_sync_manager.restore_scroll_positions(
            scroll_positions.get("sidebar", 0.0),
            scroll_positions.get("webview", 0.0)
        )
        return False
    
    # Delay until widgets are ready
    GLib.timeout_add(500, restore_after_layout)
"""
