#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2026 TinyPedal developers, see contributors.md file
#
#  This file is part of TinyPedal.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Search bar widget with debounce and Ctrl+F shortcut"""

from PySide2.QtCore import Signal, QTimer
from PySide2.QtGui import QKeySequence, QShortcut
from PySide2.QtWidgets import QHBoxLayout, QLabel, QLineEdit

from .base import BaseComponent


class SearchBar(BaseComponent):
    """Search bar with debounce timer"""

    filterRequested = Signal(str)
    DEBOUNCE_MS = 200

    def __init__(self, parent=None, debounce_ms=None):
        super().__init__(parent)
        self._debounce_ms = debounce_ms or self.DEBOUNCE_MS
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Search:"))
        self._edit = QLineEdit()
        self._edit.setPlaceholderText("Type to filter options (Ctrl+F)")
        self._edit.setClearButtonEnabled(True)
        self._edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._edit)
        # Shortcut
        shortcut = QShortcut(QKeySequence.Find, self)
        shortcut.activated.connect(self.focus)
        # Debounce timer
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._emit_filter)

    def focus(self):
        """Focus and select all text"""
        self._edit.setFocus()
        self._edit.selectAll()

    def clear(self):
        self._edit.clear()

    def cleanup(self):
        """Stop timer before closing"""
        self._timer.stop()

    def _on_text_changed(self):
        self._timer.start(self._debounce_ms)

    def _emit_filter(self):
        self.filterRequested.emit(self._edit.text().strip().lower())
