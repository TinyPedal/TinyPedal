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
Config dialog
"""

from __future__ import annotations

from typing import Callable

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QDialogButtonBox,
    QHBoxLayout,
    QScrollArea,
    QVBoxLayout,
)

from ..const_file import ConfigType
from ..formatter import format_option_name
from ..setting import cfg
from ._common import BaseDialog, UIScaler, singleton_dialog
from .components.preview import WidgetPreview
from .components.search_bar import SearchBar
from .components.section_frame import SectionBuilder
from .config_layout import ConfigLayout
from .helpers import config_actions
from .helpers.section_grouper import SectionGrouper

def set_preset_name(cfg_type: str):
    """Set preset name"""
    if cfg_type == ConfigType.CONFIG:
        return f"{cfg.filename.config} (global)"
    return cfg.filename.setting


@singleton_dialog(ConfigType.CONFIG)
class UserConfig(BaseDialog):
    """User configuration dialog with sectioned layout and search bar."""

    def __init__(
        self,
        parent,
        key_name: str,
        cfg_type: str,
        user_setting: dict,
        default_setting: dict,
        reload_func: Callable,
        option_width: int = 9,
        section_grouper: SectionGrouper | None = None,
    ):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        self.set_config_title(format_option_name(key_name), set_preset_name(cfg_type))

        self.reloading = reload_func
        self.key_name = key_name
        self.cfg_type = cfg_type
        self.user_setting = user_setting
        self.default_setting = default_setting

        # Cache for current editor values (unsaved changes)
        self.original_keys = list(self.user_setting[self.key_name])
        self._current_values = {
            key: self.user_setting[self.key_name][key] for key in self.original_keys
        }

        # Row tracking for search dimming and section highlight
        self._highlighted_keys: set[str] = set()

        # Preview widget
        self._preview: WidgetPreview | None = None
        if cfg_type == ConfigType.WIDGET:
            self._preview = WidgetPreview(key_name, parent=self)
        has_preview = self._preview is not None and self._preview.available

        # Create builder
        self.builder = SectionBuilder(
            parent_dialog=self,
            current_values=self._current_values,
            update_callback=self._update_current_value,
            option_width=UIScaler.size(option_width),
            highlight_callback=self.highlight_section,
        )

        # Create layout manager and build sections
        self._layout = ConfigLayout(
            builder=self.builder,
            grouper=section_grouper or SectionGrouper(),
            keys=self.original_keys,
            key_name=key_name,
            current_values=self._current_values,
            has_preview=has_preview,
            margin=self.MARGIN,
        )
        scroll_content = self._layout.build()

        # Shortcut references from builder
        self._column_order_widgets = self.builder.column_order_widgets

        # Search bar
        self._search = SearchBar(parent=self)
        self._search.filterRequested.connect(self._on_filter)

        # Buttons
        button_reset = QDialogButtonBox(QDialogButtonBox.Reset)
        button_reset.clicked.connect(self.reset_setting)

        button_apply = QDialogButtonBox(QDialogButtonBox.Apply)
        button_apply.clicked.connect(self.applying)

        button_save = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_save.accepted.connect(self.saving)
        button_save.rejected.connect(self.reject)

        # Scroll area
        self._scroll_box = QScrollArea(self)
        self._scroll_box.setWidget(scroll_content)
        self._scroll_box.setWidgetResizable(True)

        # Assemble main layout
        layout_main = QVBoxLayout()

        if has_preview:
            layout_main.addWidget(self._preview)

        layout_main.addWidget(self._search)

        controls_row = self._layout.build_controls_row()
        if controls_row is not None:
            layout_main.addLayout(controls_row)

        layout_main.addWidget(self._scroll_box, 1)

        layout_button = QHBoxLayout()
        layout_button.addWidget(button_reset)
        layout_button.addStretch(1)
        layout_button.addWidget(button_apply)
        layout_button.addWidget(button_save)
        layout_main.addLayout(layout_button)
        layout_main.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        self.setLayout(layout_main)

        # Window sizing
        self.setMinimumWidth(self.sizeHint().width() + UIScaler.size(2))
        self.adjustSize()
        try:
            avail = self.screen().availableGeometry()
            max_w = int(avail.width() * 0.9)
            max_h = int(avail.height() * 0.9)
        except AttributeError:
            max_w = 1600
            max_h = 900
        new_w = min(self.width(), max_w)
        new_h = min(self.height(), max_h)
        if new_w != self.width() or new_h != self.height():
            self.resize(new_w, new_h)

        # Initial section reordering
        new = self._layout.reorder_sections()
        if new:
            self._scroll_box.setWidget(new)

    # ------------------------------------------------------------------
    # Value updates
    # ------------------------------------------------------------------
    def _update_current_value(self, key, value):
        """Update value cache"""
        self._current_values[key] = value
        if self._preview is not None:
            self._preview.schedule_refresh(self._current_values)

    # ------------------------------------------------------------------
    # Search / filter
    # ------------------------------------------------------------------
    def _on_filter(self, text: str):
        row_widgets = self.builder.row_widgets
        row_labels = self.builder.row_labels
        section_title_widgets = self.builder.section_title_widgets
        column_order_widgets = self._column_order_widgets

        if not text:
            for key in row_widgets:
                self._undim_row(key)
            seen: set[int] = set()
            for lw in column_order_widgets.values():
                if id(lw) not in seen:
                    seen.add(id(lw))
                    lw.set_dimmed_keys(set())
            for title_label, _ in section_title_widgets:
                title_label.setStyleSheet("""
                    background-color: palette(dark);
                    color: palette(bright-text);
                    border-bottom: 2px solid palette(mid);
                    padding: 4px;
                """)
            return

        for key in row_widgets:
            if text in key.lower():
                self._undim_row(key)
            else:
                self._dim_row(key)

        seen_lw: set[int] = set()
        for lw in column_order_widgets.values():
            if id(lw) not in seen_lw:
                seen_lw.add(id(lw))
                dimmed = set()
                for k, w in column_order_widgets.items():
                    if w is lw and text not in k.lower():
                        dimmed.add(k)
                lw.set_dimmed_keys(dimmed)

        for title_label, keys in section_title_widgets:
            all_dimmed = all(text not in k.lower() for k in keys)
            if all_dimmed:
                title_label.setStyleSheet("""
                    background-color: palette(mid);
                    color: palette(window);
                    border-bottom: 2px solid palette(mid);
                    padding: 4px;
                """)
            else:
                title_label.setStyleSheet("""
                    background-color: palette(dark);
                    color: palette(bright-text);
                    border-bottom: 2px solid palette(mid);
                    padding: 4px;
                """)

    def _dim_row(self, key: str):
        row_widget = self.builder.row_widgets.get(key)
        label = self.builder.row_labels.get(key)
        if row_widget is None:
            return
        row_widget.setStyleSheet("background-color: palette(window);")
        if label is not None:
            label.setStyleSheet("color: palette(mid);")

    def _undim_row(self, key: str):
        row_widget = self.builder.row_widgets.get(key)
        label = self.builder.row_labels.get(key)
        if row_widget is None:
            return
        bg = row_widget.property("_base_bg") or "palette(base)"
        row_widget.setStyleSheet(f"background-color: {bg};")
        if label is not None:
            label.setStyleSheet("")

    # ------------------------------------------------------------------
    # Section highlight
    # ------------------------------------------------------------------
    def highlight_section(self, column_key):
        """Highlight all options belonging to the section of column_key."""
        for title, keys in self._layout.sections:
            if column_key in keys:
                self._reset_highlight()
                for k in keys:
                    row = self.builder.row_widgets.get(k)
                    if row:
                        row.setStyleSheet("background-color: lightblue;")
                        self._highlighted_keys.add(k)
                break

    def _reset_highlight(self):
        for k in self._highlighted_keys:
            row = self.builder.row_widgets.get(k)
            if row:
                bg = row.property("_base_bg") or "palette(base)"
                row.setStyleSheet(f"background-color: {bg};")
        self._highlighted_keys.clear()

    # ------------------------------------------------------------------
    # Section reordering
    # ------------------------------------------------------------------
    def on_column_order_changed(self):
        new = self._layout.reorder_sections()
        if new:
            self._scroll_box.setWidget(new)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def applying(self):
        config_actions.save_setting(
            self.original_keys, self._current_values, self.user_setting,
            self.key_name, self.cfg_type, self.builder.editors,
            self.reloading, self,
        )

    def saving(self):
        if config_actions.save_setting(
            self.original_keys, self._current_values, self.user_setting,
            self.key_name, self.cfg_type, self.builder.editors,
            self.reloading, self,
        ):
            self.accept()

    def reset_setting(self):
        config_actions.reset_setting(
            self.builder.editors, self._current_values, self.default_setting,
            self.key_name, self._column_order_widgets, self,
        )

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def _cleanup(self):
        self._search.cleanup()
        if self._preview is not None:
            self._preview.cleanup()

    def reject(self):
        self._cleanup()
        super().reject()

    def closeEvent(self, event):
        self._cleanup()
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        new = self._layout.reflow(self._scroll_box.viewport().width())
        if new:
            self._scroll_box.setWidget(new)
