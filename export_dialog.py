import gi
import os
import tempfile
import re

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")

from gi.repository import Gtk, Adw, Gio, WebKit, GLib
import comrak


UI_FILE = "ui/export_dialog.ui"


@Gtk.Template(filename=UI_FILE)
class ExportDialog(Adw.Window):
    __gtype_name__ = "ExportDialog"

    btn_export_html = Gtk.Template.Child()
    btn_export_pdf = Gtk.Template.Child()
    btn_export_image = Gtk.Template.Child()
    btn_close = Gtk.Template.Child()
    check_include_css = Gtk.Template.Child()
    check_standalone = Gtk.Template.Child()
    dropdown_image_format = Gtk.Template.Child()

    def __init__(self, parent_window, **kwargs):
        super().__init__(**kwargs)
        self.set_transient_for(parent_window)
        self.parent_window = parent_window

        # Configure comrak with same settings as main window
        self.extension_options = comrak.ExtensionOptions()
        self.extension_options.table = True
        self.extension_options.strikethrough = True
        self.extension_options.autolink = True
        self.extension_options.tasklist = True
        self.extension_options.superscript = True
        self.extension_options.footnotes = True

        # Connect signals
        self.btn_export_html.connect("clicked", self._on_export_html)
        self.btn_export_pdf.connect("clicked", self._on_export_pdf)
        self.btn_export_image.connect("clicked", self._on_export_image)
        self.btn_close.connect("clicked", lambda b: self.close())

    def get_markdown_content(self):
        """Get markdown content from parent window."""
        if self.parent_window:
            sidebar = self.parent_window.get_sidebar()
            return sidebar.get_text()
        return ""

    def get_html_content(self):
        """Convert markdown to HTML."""
        markdown = self.get_markdown_content()
        html = comrak.render_markdown(
            markdown, extension_options=self.extension_options
        )
        return html

    def get_full_html_document_from_webview(self, for_pdf=False):
        """Get complete HTML document using the same rendering as WebView."""
        if not self.parent_window:
            return ""

        # Get the processed HTML
        markdown = self.get_markdown_content()
        html = comrak.render_markdown(
            markdown, extension_options=self.extension_options
        )

        # Process Mermaid blocks (same as webview.py)
        def process_mermaid_blocks(html_content):
            patterns = [
                re.compile(
                    r'<pre><code class="language-mermaid">(.*?)</code></pre>', re.DOTALL
                ),
                re.compile(r'<pre lang="mermaid"><code>(.*?)</code></pre>', re.DOTALL),
                re.compile(r'<code class="language-mermaid">(.*?)</code>', re.DOTALL),
                re.compile(r"```mermaid\s*(.*?)\s*```", re.DOTALL),
            ]

            def replace_mermaid(match):
                mermaid_code = match.group(1).strip()
                mermaid_code = (
                    mermaid_code.replace("&lt;", "<")
                    .replace("&gt;", ">")
                    .replace("&amp;", "&")
                    .replace("&quot;", '"')
                )
                return f'<div class="mermaid">\n{mermaid_code}\n</div>'

            result = html_content
            for pattern in patterns:
                result = pattern.sub(replace_mermaid, result)
            return result

        # Process GitHub alerts (same as webview.py)
        def process_github_alerts(html_content):
            alert_pattern = re.compile(
                r"<blockquote>\s*<p>\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(.*?)</p>(.*?)</blockquote>",
                re.DOTALL | re.IGNORECASE,
            )

            def replace_alert(match):
                alert_type = match.group(1).upper()
                first_line = match.group(2).strip()
                rest_content = match.group(3).strip()
                full_content = first_line
                if rest_content:
                    full_content += rest_content
                return f'<div class="alert alert-{alert_type.lower()}" data-alert-type="{alert_type}">{full_content}</div>'

            return alert_pattern.sub(replace_alert, html_content)

        # Process HTML the same way as WebView
        processed_html = process_mermaid_blocks(html)
        processed_html = process_github_alerts(processed_html)

        # Determine theme
        is_dark = (
            False
            if for_pdf
            else (self.parent_window.is_dark_mode() if self.parent_window else False)
        )

        # Load external files
        def load_external_file(filename):
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(script_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                return ""

        css_content = load_external_file("assets/styles.css")
        js_mermaid = load_external_file("assets/mermaid-loader.js")
        js_mathjax_config = load_external_file("assets/mathjax-config.js")
        js_mathjax_render = load_external_file("assets/mathjax-render.js")

        # Theme colors
        bg_color = "#1e1e1e" if is_dark else "#ffffff"
        text_color = "#d4d4d4" if is_dark else "#1e1e1e"
        link_color = "#4fc3f7" if is_dark else "#0066cc"
        code_bg = "#2d2d2d" if is_dark else "#f5f5f5"
        pre_bg = "#2d2d2d" if is_dark else "#f5f5f5"
        border_color = "#333333" if is_dark else "#e1e4e8"
        mermaid_theme = "dark" if is_dark else "default"

        # Alert colors
        if is_dark:
            note_bg, note_border, note_icon = "#1f2937", "#3b82f6", "#3b82f6"
            tip_bg, tip_border, tip_icon = "#1e3a2e", "#10b981", "#10b981"
            important_bg, important_border, important_icon = (
                "#3a2e42",
                "#a855f7",
                "#a855f7",
            )
            warning_bg, warning_border, warning_icon = "#3a2e1e", "#f59e0b", "#f59e0b"
            caution_bg, caution_border, caution_icon = "#3a1e1e", "#ef4444", "#ef4444"
        else:
            note_bg, note_border, note_icon = "#dbeafe", "#3b82f6", "#1e40af"
            tip_bg, tip_border, tip_icon = "#d1fae5", "#10b981", "#065f46"
            important_bg, important_border, important_icon = (
                "#f3e8ff",
                "#a855f7",
                "#6b21a8",
            )
            warning_bg, warning_border, warning_icon = "#fef3c7", "#f59e0b", "#92400e"
            caution_bg, caution_border, caution_icon = "#fee2e2", "#ef4444", "#991b1b"

        # Replace CSS variables
        css_with_theme = (
            css_content.replace("{bg_color}", bg_color)
            .replace("{text_color}", text_color)
            .replace("{link_color}", link_color)
            .replace("{code_bg}", code_bg)
            .replace("{pre_bg}", pre_bg)
            .replace("{border_color}", border_color)
            .replace("{note_bg}", note_bg)
            .replace("{note_border}", note_border)
            .replace("{note_icon}", note_icon)
            .replace("{tip_bg}", tip_bg)
            .replace("{tip_border}", tip_border)
            .replace("{tip_icon}", tip_icon)
            .replace("{important_bg}", important_bg)
            .replace("{important_border}", important_border)
            .replace("{important_icon}", important_icon)
            .replace("{warning_bg}", warning_bg)
            .replace("{warning_border}", warning_border)
            .replace("{warning_icon}", warning_icon)
            .replace("{caution_bg}", caution_bg)
            .replace("{caution_border}", caution_border)
            .replace("{caution_icon}", caution_icon)
        )

        # Replace JS variables
        js_mermaid_with_theme = js_mermaid.replace("{mermaid_theme}", mermaid_theme)

        # Build complete HTML document
        html_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Exported Document</title>
<style id="theme-style">
{css_with_theme}
</style>

<!-- Mermaid for diagrams (Latest Version v11) -->
<script type="module">
{js_mermaid_with_theme}
</script>

<!-- MathJax for LaTeX -->
<script>
{js_mathjax_config}
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

<!-- Ensure MathJax renders after page load -->
<script>
{js_mathjax_render}
</script>
</head>
<body>
{processed_html}
</body>
</html>"""

        return html_doc

    def _on_export_html(self, button):
        """Export as HTML."""
        dialog = Gtk.FileDialog()
        dialog.set_title("Export as HTML")

        if self.parent_window and self.parent_window.current_file:
            base_name = os.path.splitext(
                os.path.basename(self.parent_window.current_file)
            )[0]
            dialog.set_initial_name(f"{base_name}.html")
        else:
            dialog.set_initial_name("document.html")

        filter_html = Gtk.FileFilter()
        filter_html.set_name("HTML Files")
        filter_html.add_pattern("*.html")
        filter_html.add_pattern("*.htm")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_html)
        dialog.set_filters(filters)

        dialog.save(self, None, self._on_export_html_response)

    def _on_export_html_response(self, dialog, result):
        """Handle HTML export response."""
        try:
            file = dialog.save_finish(result)
            if file:
                filepath = file.get_path()
                html_content = self.get_full_html_document_from_webview(for_pdf=False)

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(html_content)

                print(f"Exported to HTML: {filepath}")
                self._show_success_message(
                    "HTML Export Successful", f"Document exported to:\n{filepath}"
                )
        except Exception as e:
            if "dismissed" not in str(e).lower():
                print(f"Error exporting to HTML: {e}")
                self._show_error_message(
                    "Export Failed", f"Could not export to HTML: {str(e)}"
                )

    def _on_export_pdf(self, button):
        """Export as PDF using WebKit print operation."""
        html_content = self.get_full_html_document_from_webview(for_pdf=True)

        if self.parent_window and self.parent_window.current_file:
            base_name = os.path.splitext(
                os.path.basename(self.parent_window.current_file)
            )[0]
            export_filename = f"{base_name}.pdf"
        else:
            export_filename = "document.pdf"

        dialog = Gtk.FileDialog()
        dialog.set_title("Export as PDF")
        dialog.set_initial_name(export_filename)

        filter_pdf = Gtk.FileFilter()
        filter_pdf.set_name("PDF Files")
        filter_pdf.add_pattern("*.pdf")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_pdf)
        dialog.set_filters(filters)

        self._pdf_html_content = html_content
        dialog.save(self, None, self._on_export_pdf_response)

    def _on_export_pdf_response(self, dialog, result):
        """Handle PDF export response."""
        try:
            file = dialog.save_finish(result)
            if file:
                filepath = file.get_path()
                self._generate_pdf_with_webkit(filepath, self._pdf_html_content)
        except Exception as e:
            if "dismissed" not in str(e).lower():
                print(f"Error exporting to PDF: {e}")
                self._show_error_message(
                    "Export Failed", f"Could not export to PDF: {str(e)}"
                )

    def _generate_pdf_with_webkit(self, filepath, html_content):
        """Generate PDF from HTML using WebKit print operation."""
        webview = WebKit.WebView()
        webview.set_size_request(800, 600)

        def on_load_finished(web_view, event):
            if event == WebKit.LoadEvent.FINISHED:
                GLib.timeout_add(3000, lambda: start_print_operation())

        def start_print_operation():
            try:
                print_op = WebKit.PrintOperation.new(webview)

                page_setup = Gtk.PageSetup()
                paper_size = Gtk.PaperSize.new(Gtk.PAPER_NAME_A4)
                page_setup.set_paper_size(paper_size)
                page_setup.set_top_margin(15, Gtk.Unit.MM)
                page_setup.set_bottom_margin(15, Gtk.Unit.MM)
                page_setup.set_left_margin(15, Gtk.Unit.MM)
                page_setup.set_right_margin(15, Gtk.Unit.MM)

                print_settings = Gtk.PrintSettings()
                print_settings.set_printer("Print to File")
                print_settings.set(Gtk.PRINT_SETTINGS_OUTPUT_URI, f"file://{filepath}")

                print_op.set_page_setup(page_setup)
                print_op.set_print_settings(print_settings)
                print_op.print_()

                print(f"Exported to PDF: {filepath}")
                self._show_success_message(
                    "PDF Export Successful", f"Document exported to:\n{filepath}"
                )
            except Exception as e:
                print(f"Error during PDF generation: {e}")
                self._show_error_message(
                    "Export Failed", f"Could not generate PDF: {str(e)}"
                )

        webview.connect("load-changed", on_load_finished)
        webview.load_html(html_content, "file:///")

    def _on_export_image(self, button):
        """Export as image (PNG/JPEG/WebP)."""
        formats = ["png", "jpg", "webp"]
        selected_index = self.dropdown_image_format.get_selected()
        format_ext = formats[selected_index]

        dialog = Gtk.FileDialog()
        dialog.set_title("Export as Image")

        if self.parent_window and self.parent_window.current_file:
            base_name = os.path.splitext(
                os.path.basename(self.parent_window.current_file)
            )[0]
            dialog.set_initial_name(f"{base_name}.{format_ext}")
        else:
            dialog.set_initial_name(f"document.{format_ext}")

        filter_img = Gtk.FileFilter()
        filter_img.set_name(f"{format_ext.upper()} Files")
        filter_img.add_pattern(f"*.{format_ext}")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_img)
        dialog.set_filters(filters)

        dialog.save(
            self, None, lambda d, r: self._on_export_image_response(d, r, format_ext)
        )

    def _on_export_image_response(self, dialog, result, format_ext):
        """Handle image export response."""
        try:
            file = dialog.save_finish(result)
            if file:
                filepath = file.get_path()
                self._generate_image(filepath, format_ext)
        except Exception as e:
            if "dismissed" not in str(e).lower():
                print(f"Error exporting to image: {e}")
                self._show_error_message(
                    "Export Failed", f"Could not export to image: {str(e)}"
                )

    def _generate_image(self, filepath, format_ext):
        """Generate image from HTML content using WebKit snapshot."""
        webview = WebKit.WebView()
        webview.set_size_request(1200, 800)
        html_content = self.get_full_html_document_from_webview(for_pdf=False)

        def on_snapshot_ready(source, result, user_data):
            try:
                texture = webview.get_snapshot_finish(result)
                texture.save_to_png(filepath)
                print(f"Exported to {format_ext.upper()}: {filepath}")
                self._show_success_message(
                    f"{format_ext.upper()} Export Successful",
                    f"Document exported to:\n{filepath}",
                )
            except Exception as e:
                print(f"Error saving snapshot: {e}")
                self._show_error_message(
                    "Export Failed", f"Could not save image: {str(e)}"
                )

        def on_load_finished(web_view, event):
            if event == WebKit.LoadEvent.FINISHED:
                GLib.timeout_add(2000, lambda: take_snapshot())

        def take_snapshot():
            webview.get_snapshot(
                WebKit.SnapshotRegion.FULL_DOCUMENT,
                WebKit.SnapshotOptions.NONE,
                None,
                on_snapshot_ready,
                None,
            )

        webview.connect("load-changed", on_load_finished)
        webview.load_html(html_content, "file:///")

    def _show_success_message(self, heading, body):
        """Show success message dialog."""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(heading)
        dialog.set_body(body)
        dialog.add_response("ok", "OK")
        dialog.present()

    def _show_error_message(self, heading, body):
        """Show error message dialog."""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(heading)
        dialog.set_body(body)
        dialog.add_response("ok", "OK")
        dialog.present()
