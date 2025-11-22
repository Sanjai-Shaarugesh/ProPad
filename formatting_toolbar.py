import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

UI_FILE = "ui/formatting_toolbar.ui"


@Gtk.Template(filename=UI_FILE)
class FormattingToolbar(Gtk.Popover):
    __gtype_name__ = "FormattingToolbar"

    # Text formatting buttons
    btn_bold = Gtk.Template.Child()
    btn_italic = Gtk.Template.Child()
    btn_strikethrough = Gtk.Template.Child()
    btn_code = Gtk.Template.Child()

    # Heading buttons
    btn_h1 = Gtk.Template.Child()
    btn_h2 = Gtk.Template.Child()
    btn_h3 = Gtk.Template.Child()
    btn_h4 = Gtk.Template.Child()

    # List and block buttons
    btn_bullet_list = Gtk.Template.Child()
    btn_numbered_list = Gtk.Template.Child()
    btn_quote = Gtk.Template.Child()
    btn_code_block = Gtk.Template.Child()

    # Insert buttons
    btn_link = Gtk.Template.Child()
    btn_image = Gtk.Template.Child()
    btn_table = Gtk.Template.Child()
    btn_mermaid = Gtk.Template.Child()
    btn_latex = Gtk.Template.Child()

    def __init__(self, textview, parent_window=None, **kwargs):
        super().__init__(**kwargs)
        self.textview = textview
        self.parent_window = parent_window
        self.buffer = textview.get_buffer()

        # Connect all buttons
        self.btn_bold.connect("clicked", lambda b: self._wrap_selection("**", "**"))
        self.btn_italic.connect("clicked", lambda b: self._wrap_selection("*", "*"))
        self.btn_strikethrough.connect(
            "clicked", lambda b: self._wrap_selection("~~", "~~")
        )
        self.btn_code.connect("clicked", lambda b: self._wrap_selection("`", "`"))

        self.btn_h1.connect("clicked", lambda b: self._insert_heading(1))
        self.btn_h2.connect("clicked", lambda b: self._insert_heading(2))
        self.btn_h3.connect("clicked", lambda b: self._insert_heading(3))
        self.btn_h4.connect("clicked", lambda b: self._insert_heading(4))

        self.btn_bullet_list.connect("clicked", lambda b: self._insert_bullet_list())
        self.btn_numbered_list.connect(
            "clicked", lambda b: self._insert_numbered_list()
        )
        self.btn_quote.connect("clicked", lambda b: self._insert_block_quote())
        self.btn_code_block.connect("clicked", lambda b: self._insert_code_block())

        self.btn_link.connect("clicked", self._on_insert_link)
        self.btn_image.connect("clicked", self._on_insert_image)
        self.btn_table.connect("clicked", self._on_insert_table)
        self.btn_mermaid.connect("clicked", self._on_insert_mermaid)
        self.btn_latex.connect("clicked", self._on_insert_latex)

    def _wrap_selection(self, prefix, suffix):
        """Wrap selected text with prefix and suffix."""
        bounds = self.buffer.get_selection_bounds()
        if bounds:
            start, end = bounds
            text = self.buffer.get_text(start, end, True)
            self.buffer.delete(start, end)
            self.buffer.insert(start, f"{prefix}{text}{suffix}")
        else:
            cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            self.buffer.insert(cursor, f"{prefix}text{suffix}")
        self.popdown()

    def _insert_heading(self, level):
        """Insert a heading at the current line."""
        cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        line_num = cursor.get_line()
        line_start = self.buffer.get_iter_at_line(line_num)
        line_end = self.buffer.get_iter_at_line(line_num)
        line_end.forward_to_line_end()

        # Get current line text
        line_text = self.buffer.get_text(line_start, line_end, True)

        # Remove existing heading markers
        stripped_text = line_text.lstrip("#").lstrip()

        # Insert new heading
        heading_prefix = "#" * level + " "
        self.buffer.delete(line_start, line_end)
        self.buffer.insert(line_start, heading_prefix + stripped_text)
        self.popdown()

    def _insert_bullet_list(self):
        """Insert a bullet list with proper markdown formatting."""
        try:
            bounds = self.buffer.get_selection_bounds()

            if bounds:
                # Multiple lines selected - add bullet to each line
                start, end = bounds
                text = self.buffer.get_text(start, end, True)
                lines = text.split("\n")

                # Add bullet to each non-empty line
                bulleted_lines = []
                for line in lines:
                    stripped = line.lstrip()
                    if stripped:
                        # Remove existing bullets if any
                        if stripped.startswith("- "):
                            stripped = stripped[2:]
                        elif stripped.startswith("* "):
                            stripped = stripped[2:]
                        bulleted_lines.append(f"- {stripped}")
                    else:
                        bulleted_lines.append("")

                result = "\n".join(bulleted_lines)
                self.buffer.delete(start, end)
                self.buffer.insert(start, result)
            else:
                # Single line - insert bullet
                cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
                line_num = cursor.get_line()
                line_start = self.buffer.get_iter_at_line(line_num)
                line_end = self.buffer.get_iter_at_line(line_num)
                if not line_end.is_end():
                    line_end.forward_to_line_end()

                line_text = self.buffer.get_text(line_start, line_end, True)
                stripped = line_text.lstrip()

                # Check if line is empty or at start
                if not stripped or cursor.get_offset() == line_start.get_offset():
                    # Insert at start of line
                    self.buffer.insert(line_start, "- ")
                else:
                    # Insert new line with bullet
                    self.buffer.insert(cursor, "\n- ")

            self.popdown()
        except Exception as e:
            print(f"Error inserting bullet list: {e}")
            import traceback

            traceback.print_exc()

    def _insert_numbered_list(self):
        """Insert a numbered list with proper markdown formatting."""
        try:
            bounds = self.buffer.get_selection_bounds()

            if bounds:
                # Multiple lines selected - number each line
                start, end = bounds
                text = self.buffer.get_text(start, end, True)
                lines = text.split("\n")

                # Add number to each non-empty line
                numbered_lines = []
                counter = 1
                for line in lines:
                    stripped = line.lstrip()
                    if stripped:
                        # Remove existing numbering if any
                        import re

                        stripped = re.sub(r"^\d+\.\s+", "", stripped)
                        # Remove bullets if any
                        if stripped.startswith("- "):
                            stripped = stripped[2:]
                        elif stripped.startswith("* "):
                            stripped = stripped[2:]
                        numbered_lines.append(f"{counter}. {stripped}")
                        counter += 1
                    else:
                        numbered_lines.append("")

                result = "\n".join(numbered_lines)
                self.buffer.delete(start, end)
                self.buffer.insert(start, result)
            else:
                # Single line - insert number
                cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
                line_num = cursor.get_line()
                line_start = self.buffer.get_iter_at_line(line_num)
                line_end, _ = self.buffer.get_iter_at_offset(self.offset)

                # You intended to check if we are at end of buffer before adding newline
                if not line_end.is_end():
                    self.buffer.insert(line_end, "\n")

                line_text = self.buffer.get_text(line_start, line_end, True)
                stripped = line_text.lstrip()

                # Check if line is empty or at start
                if not stripped or cursor.get_offset() == line_start.get_offset():
                    # Insert at start of line
                    self.buffer.insert(line_start, "1. ")
                else:
                    # Insert new line with number (auto-increment if possible)
                    # Try to detect previous number
                    if line_num > 0:
                        prev_line_start = self.buffer.get_iter_at_line(line_num - 1)
                        prev_line_end = self.buffer.get_iter_at_line(line_num - 1)
                        if not prev_line_end.is_end():
                            prev_line_end.forward_to_line_end()
                        prev_text = self.buffer.get_text(
                            prev_line_start, prev_line_end, True
                        )

                        import re

                        match = re.match(r"^(\d+)\.", prev_text.lstrip())
                        if match:
                            next_num = int(match.group(1)) + 1
                            self.buffer.insert(cursor, f"\n{next_num}. ")
                        else:
                            self.buffer.insert(cursor, "\n1. ")
                    else:
                        self.buffer.insert(cursor, "\n1. ")

            self.popdown()
        except Exception as e:
            print(f"Error inserting numbered list: {e}")
            import traceback

            traceback.print_exc()

    def _insert_block_quote(self):
        """Insert a block quote."""
        bounds = self.buffer.get_selection_bounds()
        if bounds:
            start, end = bounds
            text = self.buffer.get_text(start, end, True)
            quoted = "\n".join(f"> {line}" for line in text.split("\n"))
            self.buffer.delete(start, end)
            self.buffer.insert(start, quoted)
        else:
            cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            self.buffer.insert(cursor, "\n> Quote text here\n")
        self.popdown()

    def _insert_code_block(self):
        """Insert a code block."""
        cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        bounds = self.buffer.get_selection_bounds()

        if bounds:
            start, end = bounds
            text = self.buffer.get_text(start, end, True)
            self.buffer.delete(start, end)
            self.buffer.insert(start, f"\n```\n{text}\n```\n")
        else:
            self.buffer.insert(cursor, "\n```\ncode here\n```\n")
        self.popdown()

    def _on_insert_link(self, button):
        """Insert a markdown link."""
        bounds = self.buffer.get_selection_bounds()
        if bounds:
            start, end = bounds
            text = self.buffer.get_text(start, end, True)
            self.buffer.delete(start, end)
            self.buffer.insert(start, f"[{text}](url)")
        else:
            cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            self.buffer.insert(cursor, "[link text](url)")
        self.popdown()

    def _on_insert_image(self, button):
        """Insert a markdown image."""
        cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        self.buffer.insert(cursor, "![alt text](image-url)")
        self.popdown()

    def _on_insert_table(self, button):
        """Insert a markdown table."""
        cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        table = """\n| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
"""
        self.buffer.insert(cursor, table)
        self.popdown()

    def _on_insert_mermaid(self, button):
        """Insert a Mermaid diagram block."""
        cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        mermaid = """\n```mermaid
graph TD
    A[Start] --> B[Process]
    B --> C[End]
```
"""
        self.buffer.insert(cursor, mermaid)
        self.popdown()

    def _on_insert_latex(self, button):
        """Insert a LaTeX math block."""
        cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        latex = "\n$$\nx = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}\n$$\n"
        self.buffer.insert(cursor, latex)
        self.popdown()
