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

"""Widget preview panel for config dialog"""

import copy
import importlib
import logging

from PySide2.QtCore import Qt, QTimer
from PySide2.QtWidgets import QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from ...setting import cfg
from .base import BaseComponent

logger = logging.getLogger(__name__)


class WidgetPreview(BaseComponent):
    """Live preview of the widget being configured"""

    _DEBOUNCE_MS = 500

    def __init__(self, key_name, parent=None):
        super().__init__(parent)
        self._key_name = key_name
        self._active_widget = None
        self._pending_values = {}
        self._element_map = {}
        self._last_applied_values = {}
        self._module = self._load_module(key_name)
        self._available = self._module is not None
        # Debounce timer
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._rebuild)
        self._setup_ui()
        if self._available:
            self._rebuild()

    @property
    def available(self):
        return self._available

    def _load_module(self, key_name):
        try:
            return importlib.import_module(f"tinypedal.widget.{key_name}")
        except ImportError:
            logger.debug("No preview for %s (module not found)", key_name)
            return None

    def _setup_ui(self):
        title = QLabel("Preview")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "background-color: palette(dark);"
            "color: palette(bright-text);"
            "border-bottom: 2px solid palette(mid);"
            "padding: 4px;"
            "font-weight: bold;"
        )
        self._inner_widget = QWidget()
        self._inner_layout = QVBoxLayout(self._inner_widget)
        self._inner_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self._inner_layout.setContentsMargins(8, 8, 8, 8)
        scroll = QScrollArea()
        scroll.setWidget(self._inner_widget)
        scroll.setWidgetResizable(True)
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(title)
        layout.addWidget(scroll)

    def schedule_refresh(self, current_values):
        """Schedule preview refresh, fast-path for show_* changes only"""
        self._pending_values = current_values.copy()
        if not self._active_widget or not self._element_map or not self._last_applied_values:
            self._debounce_timer.start(self._DEBOUNCE_MS)
            return
        changed_keys = {
            k for k, v in current_values.items()
            if self._last_applied_values.get(k) != v
        }
        if not changed_keys:
            return
        # Fast path: only show_* keys changed
        if all(k in self._element_map for k in changed_keys):
            self._apply_show_hide(current_values)
            self._last_applied_values = current_values.copy()
        else:
            self._debounce_timer.start(self._DEBOUNCE_MS)

    def cleanup(self):
        """Stop timers and remove active widget"""
        self._debounce_timer.stop()
        self._remove_active_widget()

    def _remove_active_widget(self):
        if self._active_widget is None:
            return
        if hasattr(self._active_widget, "_update_timer"):
            self._active_widget._update_timer.stop()
        self._active_widget.hide()
        self._inner_layout.removeWidget(self._active_widget)
        self._active_widget.deleteLater()
        self._active_widget = None
        self._element_map.clear()
        self._last_applied_values.clear()

    def _create_widget_instance(self, config):
        try:
            return self._module.Realtime(cfg, self._key_name)
        except Exception:
            logger.error("Preview creation failed for %s", self._key_name, exc_info=True)
            return None

    def _prepare_widget(self, widget, config):
        """Set up widget for embedded preview display"""
        widget.setParent(self._inner_widget)
        widget.setWindowFlags(Qt.Widget)
        widget.setAttribute(Qt.WA_TranslucentBackground, False)
        widget.move(0, 0)
        if hasattr(widget, "_update_timer") and hasattr(widget, "_update_interval"):
            widget._update_timer.start(widget._update_interval, widget)
        try:
            widget.timerEvent(None)
        except Exception:
            logger.debug("timerEvent failed in preview for %s", self._key_name, exc_info=True)

    def _rebuild(self):
        """Rebuild preview with current pending values"""
        self._remove_active_widget()
        if not self._available:
            return
        original = cfg.user.setting.get(self._key_name, {})
        patched = self._patch_config(original, self._pending_values)
        forced_show, patched = self._force_show_settings(patched)
        # Temporarily replace config for widget init
        cfg.user.setting[self._key_name] = patched
        try:
            widget = self._create_widget_instance(patched)
        finally:
            cfg.user.setting[self._key_name] = original
        if widget is None:
            return
        self._prepare_widget(widget, patched)
        self._element_map = self._build_element_map(widget, patched)
        self._last_applied_values = (
            self._pending_values.copy() if self._pending_values else original.copy()
        )
        if forced_show and self._element_map:
            self._apply_show_hide(self._pending_values)
        self._inner_layout.insertWidget(0, widget)
        widget.show()
        self._active_widget = widget

    def _patch_config(self, original, pending):
        patched = copy.deepcopy(original)
        for key, value in pending.items():
            if key in patched:
                patched[key] = value
        return patched

    def _force_show_settings(self, config):
        """Force all show_* to True, return dict of originally-False ones"""
        forced = {}
        modified = config.copy()
        for key in config:
            if key.startswith("show_"):
                col_key = f"column_index_{key[5:]}"
                if col_key in config and not config[key]:
                    forced[key] = False
                    modified[key] = True
        return forced, modified

    def _build_element_map(self, widget, config):
        """Map show_* keys to (widget, column_index) for fast show/hide"""
        layout = widget.layout()
        if not isinstance(layout, QGridLayout):
            return {}
        is_vertical = config.get("layout", 0) == 0
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
        """Update element visibility without full rebuild"""
        if not self._element_map or not self._active_widget:
            return
        layout = self._active_widget.layout()
        if not isinstance(layout, QGridLayout):
            return
        is_vertical = self._active_widget.wcfg.get("layout", 0) == 0
        # Remove all mapped elements
        for _, (widget, _) in self._element_map.items():
            layout.removeWidget(widget)
        # Sort into visible and hidden
        visible = []
        hidden = []
        for show_key, (widget, col_idx) in self._element_map.items():
            if values.get(show_key, True):
                visible.append((col_idx, widget))
            else:
                hidden.append((col_idx, widget))
        visible.sort(key=lambda x: x[0])
        hidden.sort(key=lambda x: x[0])
        # Re-add in order
        idx = 0
        for _, widget in visible:
            widget.setVisible(True)
            if is_vertical:
                layout.addWidget(widget, idx, 0)
            else:
                layout.addWidget(widget, 0, idx)
            idx += 1
        for _, widget in hidden:
            widget.setVisible(False)
            if is_vertical:
                layout.addWidget(widget, idx, 0)
            else:
                layout.addWidget(widget, 0, idx)
            idx += 1
