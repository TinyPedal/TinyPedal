"""Reusable button bar component for dialog footers"""

from PySide2.QtWidgets import QHBoxLayout

from .base import BaseComponent
from .._common import CompactButton


class ButtonBar(BaseComponent):
    """Standard button bar matching the app's CompactButton style.

    Usage:
        bar = ButtonBar()
        bar.add_left("Reset", on_reset)
        bar.add_right("Apply", on_apply)
        bar.add_right("Save", on_save)
        bar.add_right("Cancel", on_cancel)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._stretch_added = False

    def _ensure_stretch(self):
        if not self._stretch_added:
            self._layout.addStretch(1)
            self._stretch_added = True

    def add_left(self, text, callback):
        """Add a button to the left group"""
        button = CompactButton(text)
        button.clicked.connect(callback)
        # Insert before stretch if it exists, otherwise just append
        if self._stretch_added:
            idx = self._layout.count() - 1  # before stretch
            # Find stretch index
            for i in range(self._layout.count()):
                item = self._layout.itemAt(i)
                if item.spacerItem():
                    idx = i
                    break
            self._layout.insertWidget(idx, button)
        else:
            self._layout.addWidget(button)
        return button

    def add_right(self, text, callback):
        """Add a button to the right group"""
        self._ensure_stretch()
        button = CompactButton(text)
        button.clicked.connect(callback)
        self._layout.addWidget(button)
        return button
