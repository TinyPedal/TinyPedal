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

import logging
import re
import time
from typing import Callable

from PySide2.QtCore import Qt, QTimer
from PySide2.QtGui import QKeySequence, QShortcut
from PySide2.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QScrollArea,
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
from .components.preview import WidgetPreview
from .components.drag_drop_list import DragDropOrderList
from .helpers.section_grouper import SectionGrouper
from .components.section_frame import SectionBuilder

logger = logging.getLogger(__name__)

COLUMN_LABEL = 0
EDITOR_HEIGHT = UIScaler.size(2.2)


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
        self.option_width = UIScaler.size(option_width)
        self.section_grouper = section_grouper or SectionGrouper()

        # Cache for current editor values (unsaved changes)
        self.original_keys = list(self.user_setting[self.key_name])
        self._current_values = {
            key: self.user_setting[self.key_name][key] for key in self.original_keys
        }

        # Preview widget
        self._preview: WidgetPreview | None = None

        # Row tracking for search dimming – will be populated by builder
        self._row_widgets: dict[str, QWidget] = {}
        self._row_labels: dict[str, QLabel] = {}
        self._section_title_widgets: list[tuple[QLabel, list[str]]] = []
        self._column_order_widgets: dict[str, DragDropOrderList] = {}

        # Section widgets and current column count
        self._general_frame: QFrame | None = None
        self._section_widgets: list[QFrame] = []
        self._column_index_frames: list[QFrame] = []
        self._num_columns = 0
        self._widest_section = 0

        # Voor sectie‑highlight en herordening
        self._sections: list[tuple[str | None, list[str]]] = []   # opgeslagen gegroepeerde secties
        self._highlighted_keys: set[str] = set()                  # momenteel gehighlighte keys

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type to filter options (Ctrl+F)")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_edit)

        shortcut_find = QShortcut(QKeySequence.Find, self)
        shortcut_find.activated.connect(self._focus_search)

        self.filter_timer = QTimer(self)
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self._apply_filter)

        # Buttons
        button_reset = QDialogButtonBox(QDialogButtonBox.Reset)
        button_reset.clicked.connect(self.reset_setting)

        button_apply = QDialogButtonBox(QDialogButtonBox.Apply)
        button_apply.clicked.connect(self.applying)

        button_save = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_save.accepted.connect(self.saving)
        button_save.rejected.connect(self.reject)

        # Create builder and build sections
        self.builder = SectionBuilder(
            parent_dialog=self,
            current_values=self._current_values,
            update_callback=self._update_current_value,
            option_width=self.option_width,
            highlight_callback=self.highlight_section  # nieuwe callback voor klik op sectie
        )
        option_box = self._build_sectioned_layout(self.original_keys)

        # Create scroll box
        scroll_box = QScrollArea(self)
        scroll_box.setWidget(option_box)
        scroll_box.setWidgetResizable(True)
        self._scroll_box = scroll_box

        # Preview panel (only for widget configs)
        if cfg_type == ConfigType.WIDGET:
            self._preview = WidgetPreview(key_name, parent=self)

        # Set main layout
        layout_main = QVBoxLayout()
        layout_button = QHBoxLayout()

        has_preview = self._preview is not None and self._preview.available
        if has_preview:
            layout_main.addWidget(self._preview)

        layout_main.addLayout(search_layout)

        if has_preview and (self._general_frame or self._column_index_frames):
            controls_row = QHBoxLayout()
            controls_row.setSpacing(self.MARGIN)
            if self._general_frame is not None:
                general_scroll = QScrollArea()
                general_scroll.setWidget(self._general_frame)
                general_scroll.setWidgetResizable(True)
                controls_row.addWidget(general_scroll)
            for frame in self._column_index_frames:
                col_scroll = QScrollArea()
                col_scroll.setWidget(frame)
                col_scroll.setWidgetResizable(True)
                controls_row.addWidget(col_scroll)
            layout_main.addLayout(controls_row)

        layout_main.addWidget(scroll_box, 1)
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

        # Initieel de secties sorteren volgens opgeslagen column_index_* waarden
        self.reorder_sections()

    def _update_current_value(self, key, value):
        """Update value cache"""
        self._current_values[key] = value
        if self._preview is not None:
            self._preview.schedule_refresh(self._current_values)

    def _build_sectioned_layout(self, keys: list[str]) -> QWidget:
        """Create section frames and arrange them for initial display."""
        sections = self.section_grouper.group_keys(keys)
        self._sections = sections  # bewaar voor highlight

        for title, sec_keys in sections:
            if all(k.startswith("column_index_") for k in sec_keys):
                frame = self.builder._build_column_index_frame(title, sec_keys)
                self._column_index_frames.append(frame)
            elif title == "" and self._general_frame is None:
                self._general_frame = self.builder.build_compact_frame(title, sec_keys)
            else:
                frame = self.builder._build_regular_section(title, sec_keys)
                self._section_widgets.append(frame)

        # Retrieve references from builder
        self._row_widgets = self.builder.row_widgets
        self._row_labels = self.builder.row_labels
        self._section_title_widgets = self.builder.section_title_widgets
        self._column_order_widgets = self.builder.column_order_widgets

        self._widest_section = max(
            (w.sizeHint().width() for w in self._section_widgets), default=1
        )
        return self._arrange_columns(1)

    def _arrange_columns(self, num_columns: int) -> QWidget:
        """Distribute section widgets into num_columns columns and return a container."""
        self._num_columns = num_columns
        total_rows = sum(
            (w.property("estimated_rows") or 10) for w in self._section_widgets
        )
        max_rows = max(24, -(-total_rows // num_columns))  # ceiling division

        # Detach sections from old parent before re-parenting
        for w in self._section_widgets:
            w.setParent(None)

        columns: list[list[QFrame]] = [[] for _ in range(num_columns)]
        col_rows = [0] * num_columns

        for widget in self._section_widgets:
            est = widget.property("estimated_rows") or 10
            # Place in the first column with enough room
            for col in range(num_columns):
                if col_rows[col] + est <= max_rows:
                    columns[col].append(widget)
                    col_rows[col] += est
                    break
            else:
                # All columns full: place in least-loaded column
                min_col = min(range(num_columns), key=lambda i: col_rows[i])
                columns[min_col].append(widget)
                col_rows[min_col] += est

        col_gap = UIScaler.size(1) if num_columns > 1 else 0
        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(col_gap)
        main_layout.setContentsMargins(0, 0, 0, 0)

        for col_widgets in columns:
            if not col_widgets:
                continue
            col_layout = QVBoxLayout()
            col_layout.setSpacing(0)
            col_layout.setContentsMargins(0, 0, 0, 0)
            for w in col_widgets:
                col_layout.addWidget(w)
            col_layout.addStretch(1)
            col_container = QWidget()
            col_container.setLayout(col_layout)
            main_layout.addWidget(col_container, 1)

        container = QWidget()
        container.setLayout(main_layout)
        return container

    # ------------------------------------------------------------------
    # Search / filter methods (unchanged)
    # ------------------------------------------------------------------
    def _on_search_text_changed(self):
        self.filter_timer.start(200)

    def _apply_filter(self):
        text = self.search_edit.text().strip().lower()
        if not text:
            for key in self._row_widgets:
                self._undim_row(key)
            seen: set[int] = set()
            for lw in self._column_order_widgets.values():
                if id(lw) not in seen:
                    seen.add(id(lw))
                    lw.set_dimmed_keys(set())
            for title_label, _ in self._section_title_widgets:
                title_label.setStyleSheet("""
                    background-color: palette(dark);
                    color: palette(bright-text);
                    border-bottom: 2px solid palette(mid);
                    padding: 4px;
                """)
            return

        for key in self._row_widgets:
            if text in key.lower():
                self._undim_row(key)
            else:
                self._dim_row(key)

        seen_lw: set[int] = set()
        for lw in self._column_order_widgets.values():
            if id(lw) not in seen_lw:
                seen_lw.add(id(lw))
                dimmed = set()
                for k, w in self._column_order_widgets.items():
                    if w is lw and text not in k.lower():
                        dimmed.add(k)
                lw.set_dimmed_keys(dimmed)

        for title_label, keys in self._section_title_widgets:
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
        row_widget = self._row_widgets.get(key)
        label = self._row_labels.get(key)
        if row_widget is None:
            return
        row_widget.setStyleSheet("background-color: palette(window);")
        if label is not None:
            label.setStyleSheet("color: palette(mid);")

    def _undim_row(self, key: str):
        row_widget = self._row_widgets.get(key)
        label = self._row_labels.get(key)
        if row_widget is None:
            return
        bg = row_widget.property("_base_bg") or "palette(base)"
        row_widget.setStyleSheet(f"background-color: {bg};")
        if label is not None:
            label.setStyleSheet("")

    def _focus_search(self):
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    # ------------------------------------------------------------------
    # Sectie‑highlight
    # ------------------------------------------------------------------
    def highlight_section(self, column_key):
        """Markeer alle opties van de sectie waartoe column_key behoort."""
        # Zoek de sectie die deze column_key bevat
        for title, keys in self._sections:
            if column_key in keys:
                # reset vorige highlight
                self._reset_highlight()
                # highlight de nieuwe sectie
                for k in keys:
                    row = self._row_widgets.get(k)
                    if row:
                        row.setStyleSheet("background-color: lightblue;")
                        self._highlighted_keys.add(k)
                break

    def _reset_highlight(self):
        """Zet alle gehighlighte rijen terug naar hun normale achtergrond."""
        for k in self._highlighted_keys:
            row = self._row_widgets.get(k)
            if row:
                bg = row.property("_base_bg") or "palette(base)"
                row.setStyleSheet(f"background-color: {bg};")
        self._highlighted_keys.clear()

    # ------------------------------------------------------------------
    # Herordenen van sectieframes
    # ------------------------------------------------------------------
    def reorder_sections(self):
        """Sorteer de sectieframes op basis van minimale column_index van de bijbehorende keys."""
        if not self._section_widgets:
            return

        # Bouw een lijst van (frame, min_column_index)
        frame_index = []
        for frame in self._section_widgets:
            keys = frame.property("section_keys")
            if not keys:
                continue
            min_idx = 999999
            for k in keys:
                if k.startswith("column_index_"):
                    val = self._current_values.get(k, 999999)
                    if isinstance(val, (int, float)):
                        min_idx = min(min_idx, val)
            frame_index.append((frame, min_idx))

        # Sorteer op minimale index
        frame_index.sort(key=lambda x: x[1])

        # Werk de lijst van widgets bij
        self._section_widgets = [f for f, _ in frame_index]

        # Vernieuw de layout met het huidige aantal kolommen
        new_container = self._arrange_columns(self._num_columns)
        self._scroll_box.setWidget(new_container)

    def on_column_order_changed(self):
        """Wordt aangeroepen nadat de volgorde in de lijst is gewijzigd."""
        self.reorder_sections()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def applying(self):
        self.save_setting(is_apply=True)

    def saving(self):
        self.save_setting(is_apply=False)

    def reset_setting(self):
        msg_text = (
            f"Reset all <b>{format_option_name(self.key_name)}</b> options to default?<br><br>"
            "Changes are only saved after clicking Apply or Save Button."
        )
        if self.confirm_operation(title="Reset Options", message=msg_text):
            for key, editor in self.builder.editors.items():
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

            seen_column_lists: set = set()
            for key, lw in self._column_order_widgets.items():
                if id(lw) not in seen_column_lists:
                    seen_column_lists.add(id(lw))
                    all_keys = [k for k, w in self._column_order_widgets.items() if w is lw]
                    default_vals = {
                        k: self.default_setting[self.key_name][k] for k in all_keys
                    }
                    lw.reset_to_defaults(default_vals)

    def save_setting(self, is_apply: bool):
        user_setting = self.user_setting[self.key_name]
        error_found = False

        for key in self.original_keys:
            value = self._current_values[key]

            if re.search(rxp.CFG_BOOL, key):
                user_setting[key] = value

            elif re.search(rxp.CFG_COLOR, key):
                if is_hex_color(value):
                    user_setting[key] = value
                else:
                    self.value_error_message("color", key)
                    error_found = True

            elif re.search(rxp.CFG_USER_PATH, key):
                value = set_relative_path(value)
                if set_user_data_path(value):
                    user_setting[key] = value
                    editor = self.builder.editors.get(key)
                    if editor:
                        editor.setText(value)
                        self._current_values[key] = value
                else:
                    self.value_error_message("path", key)
                    error_found = True

            elif re.search(rxp.CFG_USER_IMAGE, key):
                user_setting[key] = value

            elif re.search(rxp.CFG_FONT_NAME, key) or re.search(rxp.CFG_HEATMAP, key) or \
                 any(re.search(ref, key) for ref in rxp.CHOICE_UNITS) or \
                 any(re.search(ref, key) for ref in rxp.CHOICE_COMMON):
                user_setting[key] = value

            elif re.search(rxp.CFG_CLOCK_FORMAT, key) or re.search(rxp.CFG_STRING, key):
                if re.search(rxp.CFG_CLOCK_FORMAT, key) and not is_clock_format(value):
                    self.value_error_message("clock format", key)
                    error_found = True
                else:
                    user_setting[key] = value

            elif re.search(rxp.CFG_INTEGER, key):
                str_val = str(value)
                if is_string_number(str_val):
                    user_setting[key] = int(str_val)
                else:
                    self.value_error_message("number", key)
                    error_found = True

            else:  # float fallback
                str_val = str(value)
                if is_string_number(str_val):
                    num_val = float(str_val)
                    if num_val % 1 == 0:
                        num_val = int(num_val)
                    user_setting[key] = num_val
                else:
                    self.value_error_message("number", key)
                    error_found = True

        for key in self.original_keys:
            if key.startswith("column_index_"):
                user_setting[key] = self._current_values[key]

        if error_found:
            return

        if self.cfg_type == ConfigType.CONFIG:
            cfg.update_path()
            cfg.save(0, cfg_type=ConfigType.CONFIG)
        else:
            cfg.save(0)

        while cfg.is_saving:
            time.sleep(0.01)

        self.reloading()
        if not is_apply:
            self.accept()

    def value_error_message(self, value_type: str, option_name: str):
        msg_text = (
            f"Invalid {value_type} for <b>{format_option_name(option_name)}</b> option."
            "<br><br>Changes are not saved."
        )
        QMessageBox.warning(self, "Error", msg_text)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def _cleanup(self):
        self.filter_timer.stop()
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
        if not self._section_widgets:
            return
        usable_w = self._scroll_box.viewport().width()
        new_num = min(5, max(1, usable_w // max(self._widest_section, 1)))
        if new_num != self._num_columns:
            self._scroll_box.setWidget(self._arrange_columns(new_num))
