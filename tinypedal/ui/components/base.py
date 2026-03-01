"""Base component for config dialog widgets"""

from PySide2.QtWidgets import QWidget


class BaseComponent(QWidget):
    """Base class providing a uniform interface for config dialog components"""

    def cleanup(self):
        """Stop timers, release resources. No-op by default."""
