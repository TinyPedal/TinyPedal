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
import logging

logger = logging.getLogger(__name__)

from PySide2.QtCore import Qt, QTimer
from PySide2.QtWidgets import (
    QFrame,
    QGridLayout,
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
        self._element_map: dict = {}
        self._last_applied_values: dict = {}

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
        """Schedule a preview rebuild, or fast-toggle visibility for show_* changes"""
        self._pending_values = current_values.copy()

        if self._active_widget and self._element_map and self._last_applied_values:
            changed = {
                k: v for k, v in current_values.items()
                if self._last_applied_values.get(k) != v
            }
            if not changed:
                return
            if all(k in self._element_map for k in changed):
                self._apply_show_hide(current_values)
                self._last_applied_values = current_values.copy()
                return

        self._debounce.start(self._DEBOUNCE_MS)

    def _remove_active(self):
        """Stop and remove the currently active preview widget"""
        if self._active_widget is None:
            return
        self._active_widget._update_timer.stop()
        self._active_widget.hide()
        self._inner_layout.removeWidget(self._active_widget)
        self._active_widget.deleteLater()
        self._active_widget = None
        self._element_map = {}
        self._last_applied_values = {}

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

        # Force all show_* settings to True (where they have a matching
        # column_index_*) so every element is created.  We hide the ones
        # the user toggled off *after* widget construction.
        forced_show = {}
        for key in patched:
            if key.startswith("show_"):
                col_key = f"column_index_{key[5:]}"
                if col_key in patched and not patched[key]:
                    forced_show[key] = False
                    patched[key] = True

        # Temporarily swap in patched settings so the widget reads them at init
        cfg.user.setting[self._key_name] = patched
        try:
            widget = self._module.Realtime(cfg, self._key_name)
        except Exception:
            logger.error("Preview rebuild failed for %s", self._key_name, exc_info=True)
            cfg.user.setting[self._key_name] = original
            return
        cfg.user.setting[self._key_name] = original

        # Embed as plain child widget, strip overlay window flags.
        # move(0, 0) resets the screen-coordinate position stored by Base.__init__
        # so the widget starts at a visible location before the layout repositions it.
        widget.setParent(self._inner)
        widget.setWindowFlags(Qt.Widget)
        widget.setAttribute(Qt.WA_TranslucentBackground, False)
        widget.move(0, 0)

        # Start timer directly - bypassing start() which would connect global
        # overlay signals and briefly show the widget as a floating overlay
        widget._update_timer.start(widget._update_interval, widget)

        # Populate elements with real data before showing so placeholders
        # like "BATTERY" are replaced immediately.
        try:
            widget.timerEvent(None)
        except Exception:
            pass

        # Build the element map and apply visibility BEFORE showing
        # to prevent a flash of hidden elements.
        self._active_widget = widget
        self._element_map = self._build_element_map(widget, patched)
        # Use pending_values if available, otherwise fall back to the original
        # config so the very first schedule_refresh can detect real changes.
        if self._pending_values:
            self._last_applied_values = self._pending_values.copy()
        else:
            self._last_applied_values = dict(original)
        if self._element_map and forced_show:
            self._apply_show_hide(self._pending_values)

        self._inner_layout.insertWidget(0, widget)
        widget.show()

    def _build_element_map(self, widget, config):
        """Map show_* keys to their QWidget elements in the grid layout.

        Returns a dict of {show_key: (QWidget, original_column_index)}.
        Returns empty dict if the widget doesn't use a simple QGridLayout.
        """
        layout = widget.layout()
        if not isinstance(layout, QGridLayout):
            return {}

        is_vertical = config.get("layout", 0) == 0

        # Map grid positions to widgets
        pos_to_widget = {}
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget():
                row, col, _, _ = layout.getItemPosition(i)
                pos_to_widget[(row, col)] = item.widget()

        element_map = {}
        for key in config:
            if not key.startswith("show_"):
                continue
            col_key = f"column_index_{key[5:]}"
            if col_key not in config:
                continue
            col_idx = config[col_key]
            pos = (col_idx, 0) if is_vertical else (0, col_idx)
            w = pos_to_widget.get(pos)
            if w:
                element_map[key] = (w, col_idx)

        return element_map

    def _apply_show_hide(self, values):
        """Toggle visibility of mapped elements and relayout to avoid gaps"""
        if not self._element_map or not self._active_widget:
            return

        layout = self._active_widget.layout()
        if not isinstance(layout, QGridLayout):
            return

        is_vertical = self._active_widget.wcfg.get("layout", 0) == 0

        # Remove all mapped elements from the grid
        for _show_key, (widget, _col_idx) in self._element_map.items():
            layout.removeWidget(widget)

        # Separate into visible / hidden, each sorted by column_index
        visible = []
        hidden = []
        for show_key, (widget, col_idx) in self._element_map.items():
            if values.get(show_key, True):
                visible.append((col_idx, widget))
            else:
                hidden.append((col_idx, widget))

        visible.sort(key=lambda x: x[0])
        hidden.sort(key=lambda x: x[0])

        # Re-add: visible elements first (in order), hidden elements at the end
        idx = 0
        for _col_idx, widget in visible:
            widget.setVisible(True)
            if is_vertical:
                layout.addWidget(widget, idx, 0)
            else:
                layout.addWidget(widget, 0, idx)
            idx += 1

        for _col_idx, widget in hidden:
            widget.setVisible(False)
            if is_vertical:
                layout.addWidget(widget, idx, 0)
            else:
                layout.addWidget(widget, 0, idx)
            idx += 1

    def cleanup(self):
        """Stop all timers and remove active widget; call before parent dialog closes"""
        self._debounce.stop()
        self._remove_active()

    def closeEvent(self, event):
        """Clean up on close (only fires when used as a top-level window)"""
        self.cleanup()
        super().closeEvent(event)
