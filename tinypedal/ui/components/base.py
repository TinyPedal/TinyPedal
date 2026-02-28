"""Base component for config dialog widgets"""

from PySide2.QtWidgets import QWidget


class BaseComponent(QWidget):
    """Base class providing a uniform interface for config dialog components"""

    def apply_filter(self, text):
        """Filter/dim items matching text. No-op by default."""

    def highlight_keys(self, keys):
        """Highlight items matching keys. No-op by default."""

    def clear_highlight(self, keys):
        """Clear highlight on items. No-op by default."""

    def cleanup(self):
        """Stop timers, release resources. No-op by default."""
