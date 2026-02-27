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

"""
Widget preview panel for config dialog
"""

import copy
import importlib

from PySide2.QtCore import Qt, QTimer
from PySide2.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..setting import cfg


class WidgetPreview(QFrame):
    """Embedded live preview of the widget being configured"""

    _DEBOUNCE_MS = 500

    def __init__(self, key_name: str, parent=None):
        super().__init__(parent)
        self._key_name = key_name
        self._active_widget = None
        self._pending_values: dict = {}

        try:
            self._module = importlib.import_module(f"tinypedal.widget.{key_name}")
            self._available = True
        except ImportError:
            self._module = None
            self._available = False

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self._rebuild)

        title = QLabel("Preview")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            background-color: palette(dark);
            color: palette(bright-text);
            border-bottom: 2px solid palette(mid);
            padding: 4px;
            font-weight: bold;
        """)

        self._inner = QWidget()
        inner_layout = QVBoxLayout()
        inner_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        inner_layout.setContentsMargins(8, 8, 8, 8)
        self._inner.setLayout(inner_layout)
        self._inner_layout = inner_layout

        scroll = QScrollArea()
        scroll.setWidget(self._inner)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(title)
        layout.addWidget(scroll)
        self.setLayout(layout)

        if self._available:
            self._rebuild()

    @property
    def available(self) -> bool:
        """True if a widget module exists for this key"""
        return self._available

    def schedule_refresh(self, current_values: dict):
        """Schedule a preview rebuild after debounce delay"""
        self._pending_values = current_values.copy()
        self._debounce.start(self._DEBOUNCE_MS)

    def _remove_active(self):
        """Stop and remove the currently active preview widget"""
        if self._active_widget is None:
            return
        self._active_widget._update_timer.stop()
        self._inner_layout.removeWidget(self._active_widget)
        self._active_widget.deleteLater()
        self._active_widget = None

    def _rebuild(self):
        """Rebuild preview widget with current pending values"""
        self._remove_active()
        if not self._available:
            return

        # Apply pending (unsaved) values to a deep copy of the settings
        original = cfg.user.setting[self._key_name]
        patched = copy.deepcopy(original)
        for key, value in self._pending_values.items():
            if key in patched:
                patched[key] = value

        # Temporarily swap in patched settings so the widget reads them at init
        cfg.user.setting[self._key_name] = patched
        try:
            widget = self._module.Realtime(cfg, self._key_name)
        except Exception:
            cfg.user.setting[self._key_name] = original
            return
        cfg.user.setting[self._key_name] = original

        # Embed as plain child widget, strip overlay window flags
        widget.setParent(self._inner)
        widget.setWindowFlags(Qt.Widget)
        widget.setAttribute(Qt.WA_TranslucentBackground, False)

        # Start timer directly - bypassing start() which would connect global
        # overlay signals and briefly show the widget as a floating overlay
        widget._update_timer.start(widget._update_interval, widget)

        self._inner_layout.insertWidget(0, widget)
        self._active_widget = widget
        widget.show()

    def closeEvent(self, event):
        """Clean up on close"""
        self._remove_active()
        super().closeEvent(event)
