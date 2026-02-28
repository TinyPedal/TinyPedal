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

import re
import time
from typing import Callable

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from .. import regex_pattern as rxp
from ..const_file import ConfigType
from ..formatter import format_option_name
from ..setting import cfg
from ..userfile import set_relative_path, set_user_data_path
from ..validator import is_clock_format, is_hex_color, is_string_number
from ._common import BaseDialog, UIScaler, singleton_dialog
from .components.drag_drop_list import DragDropOrderList
from .components.option_editors import create_editor
from .components.preview import WidgetPreview
from .components.search_bar import SearchBar
from .components.table import OptionTable
from .helpers.config_grouper import ConfigGrouper
from .helpers.layout_builder import LayoutBuilder


ROW_HEIGHT = UIScaler.size(1.8)


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
        config_grouper: ConfigGrouper | None = None,
    ):
        super().__init__(parent)
        try:
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
            self._option_width = UIScaler.size(option_width)

            # Widget tracking
            self._all_tables: list[OptionTable] = []
            self._order_lists: list[DragDropOrderList] = []
            self._editors = {}
            self._column_order_widgets = {}
            self._highlighted_keys: set[str] = set()

            # Preview widget
            self._preview: WidgetPreview | None = None
            if cfg_type == ConfigType.WIDGET:
                self._preview = WidgetPreview(key_name, parent=self)
            has_preview = self._preview is not None and self._preview.available

            # Build sections using the grouper
            self.grouper = config_grouper or ConfigGrouper()
            sections = self.grouper.group_keys(self.original_keys)

            general_table = None
            column_index_widgets = []
            self.section_widgets = []
            sections_to_merge = []

            for title, sec_keys in sections:
                if all(k.startswith("column_index_") for k in sec_keys):
                    widget = self._build_column_order(title, sec_keys)
                    column_index_widgets.append(widget)
                elif title == "" and general_table is None:
                    general_table = self._build_table(title, sec_keys, columns=2)
                else:
                    sections_to_merge.append((title, sec_keys))

            # Bin-pack sections into merged tables (max 24 rows each)
            self._pack_sections(sections_to_merge)

            self._sort_section_widgets()

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

            # ---- Layout via LayoutBuilder ----
            builder = LayoutBuilder(
                spacing=2,
                margins=(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN),
            )

            # Row 1: preview (fixed)
            if has_preview:
                builder.add_zone(self._preview, name='preview')

            # Row 2: general + sections (fixed, horizontal)
            info_widgets = []
            if general_table is not None:
                info_widgets.append(general_table)
            for widget in column_index_widgets:
                info_widgets.append(widget)
            if info_widgets:
                builder.add_horizontal_zone(info_widgets, name='info')

            # Row 3: search bar (fixed)
            builder.add_zone(self._search, name='search')

            # Row 4: option tables (scrollable, columns or compact stack)
            builder.add_columns_zone(
                self.section_widgets, max_columns=5,
                compact_threshold=1, scrollable=True, name='content',
            )
            self._columns_zone = builder.named_zones.get('content')

            # Build layout and add buttons
            main_widget = builder.build()

            layout_button = QHBoxLayout()
            layout_button.addWidget(button_reset)
            layout_button.addStretch(1)
            layout_button.addWidget(button_apply)
            layout_button.addWidget(button_save)
            main_widget.layout().addLayout(layout_button, 0)

            outer = QVBoxLayout()
            outer.setContentsMargins(0, 0, 0, 0)
            outer.setAlignment(Qt.AlignHCenter)
            outer.addWidget(main_widget)
            self.setLayout(outer)

            # Window sizing: max 85% of screen width for content
            try:
                avail = self.screen().availableGeometry()
                max_w = int(avail.width() * 0.85)
                max_h = int(avail.height() * 0.85)
            except AttributeError:
                max_w = 1400
                max_h = 800
            main_widget.setMaximumWidth(max_w)
            self.setMinimumWidth(min(self.sizeHint().width() + UIScaler.size(2), max_w))
            self.adjustSize()
            new_w = min(self.width(), max_w)
            new_h = min(self.height(), max_h)
            if new_w != self.width() or new_h != self.height():
                self.resize(new_w, new_h)
        except Exception:
            import traceback
            traceback.print_exc()
            raise

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------
    def _build_table(self, title, keys, columns=1):
        """Build an OptionTable from config keys."""
        table = OptionTable(parent=self, columns=columns, row_height=ROW_HEIGHT)
        if title is not None:
            display = format_option_name(self.key_name) if title == "" else format_option_name(title)
            table.set_title(display)

        for key in keys:
            editor = create_editor(
                self, key, self._current_values[key],
                self.default_setting[self.key_name][key],
                self._update_current_value,
            )
            editor.setFixedHeight(ROW_HEIGHT)
            editor.setFixedWidth(self._option_width)
            table.add_row(key, format_option_name(key), editor)
            self._editors[key] = editor

        self._all_tables.append(table)
        return table

    def _build_column_order(self, title, keys):
        """Build a drag-and-drop list for column_index keys."""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        col_title_label = None
        if title is not None:
            header_text = (
                format_option_name(self.key_name) if title == ""
                else "Sections"
            )
            col_title_label = QLabel(f"<b>{header_text}</b>")
            font = col_title_label.font()
            font.setPointSize(font.pointSize() + 1)
            col_title_label.setFont(font)
            col_title_label.setStyleSheet("""
                background-color: palette(dark);
                color: palette(bright-text);
                border-bottom: 2px solid palette(mid);
                padding: 4px;
            """)
            layout.addWidget(col_title_label)

        sorted_keys = sorted(keys, key=lambda k: self._current_values.get(k, 999))
        items = [
            (key, format_option_name(key[len("column_index_"):]))
            for key in sorted_keys
        ]

        def on_reorder(new_order):
            for index, key in enumerate(new_order, start=1):
                self._update_current_value(key, index)
            self.on_column_order_changed()

        list_widget = DragDropOrderList(
            items=items,
            on_reorder_callback=on_reorder,
            row_height=ROW_HEIGHT,
            parent=self,
        )
        list_widget.sectionClicked.connect(self.highlight_section)

        for key in keys:
            self._column_order_widgets[key] = list_widget

        layout.addWidget(list_widget)
        self._order_lists.append(list_widget)

        container = QWidget()
        container.setLayout(layout)
        return container

    # ------------------------------------------------------------------
    # Section packing
    # ------------------------------------------------------------------
    MAX_TABLE_ROWS = 12
    MIN_REMAINING = 4

    def _pack_sections(self, sections_data):
        """Bin-pack sections into merged tables."""
        current_rows = 0
        current_sections = []

        for title, sec_keys in sections_data:
            section_size = len(sec_keys) + 1  # keys + header
            remaining = self.MAX_TABLE_ROWS - current_rows

            if current_sections and (
                remaining < self.MIN_REMAINING
                or current_rows + section_size > self.MAX_TABLE_ROWS
            ):
                self.section_widgets.append(
                    self._build_merged_table(current_sections)
                )
                current_sections = []
                current_rows = 0

            current_sections.append((title, sec_keys))
            current_rows += section_size

        if current_sections:
            self.section_widgets.append(
                self._build_merged_table(current_sections)
            )

    def _build_merged_table(self, sections_data):
        """Build an OptionTable containing one or more sections."""
        table = OptionTable(parent=self, columns=1, row_height=ROW_HEIGHT)
        all_keys = []

        for title, sec_keys in sections_data:
            table.add_section_header(format_option_name(title))
            for key in sec_keys:
                editor = create_editor(
                    self, key, self._current_values[key],
                    self.default_setting[self.key_name][key],
                    self._update_current_value,
                )
                editor.setFixedHeight(ROW_HEIGHT)
                editor.setFixedWidth(self._option_width)
                table.add_row(key, format_option_name(key), editor)
                self._editors[key] = editor
            all_keys.extend(sec_keys)

        table.setProperty("section_keys", all_keys)
        self._all_tables.append(table)
        return table

    # ------------------------------------------------------------------
    # Section sorting by column_index
    # ------------------------------------------------------------------
    def _get_min_index(self, widget):
        """Return the smallest column_index value belonging to a section."""
        keys = widget.property("section_keys") or []
        min_idx = 999999
        for k in keys:
            if k.startswith("column_index_"):
                val = self._current_values.get(k, 999999)
                if isinstance(val, (int, float)):
                    min_idx = min(min_idx, val)
        return min_idx

    def _sort_section_widgets(self):
        """Sort self.section_widgets by column_index."""
        self.section_widgets.sort(key=self._get_min_index)

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
        for table in self._all_tables:
            table.apply_filter(text)
        for order_list in self._order_lists:
            order_list.apply_filter(text)

    # ------------------------------------------------------------------
    # Section highlight
    # ------------------------------------------------------------------
    def highlight_section(self, column_key):
        """Highlight all options belonging to the section of column_key."""
        for title, keys in self.grouper.group_keys(self.original_keys):
            if column_key in keys:
                self._clear_highlight()
                self._highlighted_keys = set(keys)
                for table in self._all_tables:
                    table.highlight_keys(self._highlighted_keys)
                break

    def _clear_highlight(self):
        if self._highlighted_keys:
            for table in self._all_tables:
                table.clear_highlight(self._highlighted_keys)
            self._highlighted_keys.clear()

    # ------------------------------------------------------------------
    # Section reordering
    # ------------------------------------------------------------------
    def on_column_order_changed(self):
        """Called when the order in a column_index list changes."""
        self._sort_section_widgets()
        from .helpers.layout_builder import ColumnsZone
        if isinstance(self._columns_zone, ColumnsZone):
            self._columns_zone.widgets = self.section_widgets[:]

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def applying(self):
        self._save_setting()

    def saving(self):
        if self._save_setting():
            self.accept()

    def _save_setting(self) -> bool:
        """Validate and save all values. Returns True on success."""
        target = self.user_setting[self.key_name]
        error_found = False

        for key in self.original_keys:
            value = self._current_values[key]

            if re.search(rxp.CFG_BOOL, key):
                target[key] = value

            elif re.search(rxp.CFG_COLOR, key):
                if is_hex_color(value):
                    target[key] = value
                else:
                    self._value_error("color", key)
                    error_found = True

            elif re.search(rxp.CFG_USER_PATH, key):
                value = set_relative_path(value)
                if set_user_data_path(value):
                    target[key] = value
                    editor = self._editors.get(key)
                    if editor:
                        editor.setText(value)
                        self._current_values[key] = value
                else:
                    self._value_error("path", key)
                    error_found = True

            elif re.search(rxp.CFG_USER_IMAGE, key):
                target[key] = value

            elif re.search(rxp.CFG_FONT_NAME, key) or re.search(rxp.CFG_HEATMAP, key) or \
                 any(re.search(ref, key) for ref in rxp.CHOICE_UNITS) or \
                 any(re.search(ref, key) for ref in rxp.CHOICE_COMMON):
                target[key] = value

            elif re.search(rxp.CFG_CLOCK_FORMAT, key) or re.search(rxp.CFG_STRING, key):
                if re.search(rxp.CFG_CLOCK_FORMAT, key) and not is_clock_format(value):
                    self._value_error("clock format", key)
                    error_found = True
                else:
                    target[key] = value

            elif re.search(rxp.CFG_INTEGER, key):
                str_val = str(value)
                if is_string_number(str_val):
                    target[key] = int(str_val)
                else:
                    self._value_error("number", key)
                    error_found = True

            else:  # float fallback
                str_val = str(value)
                if is_string_number(str_val):
                    num_val = float(str_val)
                    if num_val % 1 == 0:
                        num_val = int(num_val)
                    target[key] = num_val
                else:
                    self._value_error("number", key)
                    error_found = True

        for key in self.original_keys:
            if key.startswith("column_index_"):
                target[key] = self._current_values[key]

        if error_found:
            return False

        if self.cfg_type == ConfigType.CONFIG:
            cfg.update_path()
            cfg.save(0, cfg_type=ConfigType.CONFIG)
        else:
            cfg.save(0)

        while cfg.is_saving:
            time.sleep(0.01)

        self.reloading()
        return True

    def reset_setting(self):
        """Reset all editors to defaults."""
        msg_text = (
            f"Reset all <b>{format_option_name(self.key_name)}</b> options to default?<br><br>"
            "Changes are only saved after clicking Apply or Save Button."
        )
        if not self.confirm_operation(title="Reset Options", message=msg_text):
            return

        for key, editor in self._editors.items():
            default = editor.defaults
            if isinstance(editor, QCheckBox):
                editor.setChecked(default)
                self._current_values[key] = default
            elif isinstance(editor, QLineEdit):
                editor.setText(str(default))
                self._current_values[key] = default
            elif isinstance(editor, QComboBox):
                editor.setCurrentText(str(default))
                self._current_values[key] = default

        seen: set = set()
        for key, lw in self._column_order_widgets.items():
            if id(lw) not in seen:
                seen.add(id(lw))
                all_keys = [k for k, w in self._column_order_widgets.items() if w is lw]
                default_vals = {
                    k: self.default_setting[self.key_name][k] for k in all_keys
                }
                lw.reset_to_defaults(default_vals)

    def _value_error(self, value_type: str, option_name: str):
        msg_text = (
            f"Invalid {value_type} for <b>{format_option_name(option_name)}</b> option."
            "<br><br>Changes are not saved."
        )
        QMessageBox.warning(self, "Error", msg_text)

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
