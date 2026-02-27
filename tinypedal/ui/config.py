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

import os
import re
import time
from typing import Callable

from PySide2.QtCore import QPoint, Qt, QTimer
from PySide2.QtGui import QFontDatabase, QKeySequence, QShortcut
from PySide2.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .. import regex_pattern as rxp
from ..const_file import ConfigType
from ..formatter import format_option_name
from ..setting import cfg
from ..userfile import set_relative_path, set_user_data_path
from ..validator import is_clock_format, is_hex_color, is_string_number
from .config_preview import WidgetPreview
from ._common import (
    QVAL_COLOR,
    QVAL_FLOAT,
    QVAL_INTEGER,
    BaseDialog,
    DoubleClickEdit,
    UIScaler,
    singleton_dialog,
)

COLUMN_LABEL = 0  # grid layout column index


def get_font_list() -> list[str]:
    """Get all available font families list"""
    if os.getenv("PYSIDE_OVERRIDE") == "6":  # no instance in qt6
        return QFontDatabase.families()  # type: ignore[call-arg]
    return QFontDatabase().families()


class SectionGrouper:
    """Groups configuration keys into labelled sections by word overlap"""

    def __init__(self, min_match: int = 2):
        self.min_match = min_match

    @staticmethod
    def _word_set(phrase: str) -> set[str]:
        """Split underscore-delimited name into word set"""
        return set(phrase.split("_"))

    def _similar(self, topic1: str, topic2: str) -> bool:
        """Check if two topics share enough words to belong in one section"""
        # Direct match if one is a substring of the other
        if topic1 in topic2 or topic2 in topic1:
            return True
        words1 = self._word_set(topic1)
        words2 = self._word_set(topic2)
        return len(words1 & words2) >= self.min_match

    def group_keys(self, keys: list[str]) -> list[tuple[str | None, list[str]]]:
        """Group keys into labelled sections, returns list of (title, key_list) tuples"""
        # Separate column_index_* into its own group
        fixed_groups: dict[str, list[str]] = {}
        remaining: list[str] = []
        for key in keys:
            if key.startswith("column_index_"):
                fixed_groups.setdefault("Column Index", []).append(key)
            else:
                remaining.append(key)

        # Build sections from remaining keys
        sections: list[tuple[str | None, list[str]]] = []
        current_title: str | None = None
        current_keys: list[str] = []
        last_show: str | None = None

        for key in remaining:
            if key.startswith("show_"):
                topic = key[5:]  # strip 'show_' prefix
                if last_show is None:
                    current_title = topic
                    current_keys = [key]
                    last_show = topic
                elif self._similar(last_show, topic):
                    current_keys.append(key)
                    last_show = topic
                else:
                    sections.append((current_title, current_keys))
                    current_title = topic
                    current_keys = [key]
                    last_show = topic
            elif current_title is not None:
                current_keys.append(key)

        # Add last open section
        if current_keys:
            sections.append((current_title, current_keys))

        # Collect keys that appeared before the first show_* key
        all_assigned: set[str] = set()
        for _, key_list in sections:
            all_assigned.update(key_list)
        unassigned = [k for k in remaining if k not in all_assigned]
        if unassigned:
            sections.insert(0, ("", unassigned))

        # Append fixed groups
        for title, fkeys in fixed_groups.items():
            sections.append((title, fkeys))

        return sections


class ColumnIndexList(QListWidget):
    """Drag-and-drop list for setting display order of columns"""

    def __init__(self, keys: list, current_values: dict, update_callback, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setUniformItemSizes(True)
        self.setAlternatingRowColors(True)
        self.setSizeAdjustPolicy(QAbstractItemView.AdjustToContents)  # no nested scrollbar
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        h_pad = UIScaler.size(0.4)
        v_pad = UIScaler.size(0.2)
        self.setStyleSheet(f"""
            QListWidget {{
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                padding: {v_pad}px {h_pad}px;
            }}
            QListWidget::item:selected {{
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }}
        """)
        self._update_callback = update_callback

        sorted_keys = sorted(keys, key=lambda k: current_values.get(k, 999))
        for key in sorted_keys:
            label = format_option_name(key[len("column_index_"):])
            item = QListWidgetItem()
            item.setData(Qt.UserRole, key)
            item.setData(Qt.UserRole + 1, label)
            self.addItem(item)

        self.model().rowsMoved.connect(self._sync_values)
        self._sync_values()
        self._fix_height()

    def _fix_height(self):
        """Set fixed height to show all items"""
        v_pad = UIScaler.size(0.2)
        row_h = self.fontMetrics().height() + v_pad * 2
        self.setFixedHeight(row_h * self.count() + self.frameWidth() * 2)

    def _sync_values(self):
        """Update item text and value cache to reflect current order"""
        for i in range(self.count()):
            item = self.item(i)
            label = item.data(Qt.UserRole + 1)
            item.setText(f"{i + 1}. {label}")
            self._update_callback(item.data(Qt.UserRole), i + 1)

    def reset_to_defaults(self, default_values: dict):
        """Re-sort items to default order"""
        items = []
        for i in range(self.count()):
            item = self.item(i)
            items.append((item.data(Qt.UserRole), item.data(Qt.UserRole + 1)))
        items.sort(key=lambda t: default_values.get(t[0], 999))
        self.clear()
        for key, label in items:
            new_item = QListWidgetItem()
            new_item.setData(Qt.UserRole, key)
            new_item.setData(Qt.UserRole + 1, label)
            self.addItem(new_item)
        self._sync_values()


@singleton_dialog(ConfigType.CONFIG)
class FontConfig(BaseDialog):
    """Config global font setting"""

    def __init__(self, parent, user_setting: dict, reload_func: Callable):
        super().__init__(parent)
        self.set_config_title("Global Font Override", cfg.filename.setting)

        self.reloading = reload_func
        self.user_setting = user_setting

        # Combobox
        self.edit_fontname = QComboBox(self)
        self.edit_fontname.addItem("no change")
        self.edit_fontname.addItems(get_font_list())
        self.edit_fontname.setFixedWidth(UIScaler.size(9))

        self.edit_fontsize = QSpinBox(self)
        self.edit_fontsize.setRange(-999, 999)
        self.edit_fontsize.setFixedWidth(UIScaler.size(9))

        self.edit_fontweight = QComboBox(self)
        self.edit_fontweight.addItem("no change")
        self.edit_fontweight.addItems(rxp.CHOICE_COMMON[rxp.CFG_FONT_WEIGHT])
        self.edit_fontweight.setFixedWidth(UIScaler.size(9))

        self.edit_autooffset = QComboBox(self)
        self.edit_autooffset.addItems(("no change", "enable", "disable"))
        self.edit_autooffset.setFixedWidth(UIScaler.size(9))

        self.edit_fontoffset = QSpinBox(self)
        self.edit_fontoffset.setRange(-999, 999)
        self.edit_fontoffset.setFixedWidth(UIScaler.size(9))

        layout_option = QGridLayout()
        layout_option.setAlignment(Qt.AlignTop)
        layout_option.addWidget(QLabel("Font Name"), 0, 0)
        layout_option.addWidget(self.edit_fontname, 0, 1)
        layout_option.addWidget(QLabel("Font Size Addend"), 1, 0)
        layout_option.addWidget(self.edit_fontsize, 1, 1)
        layout_option.addWidget(QLabel("Font Weight"), 2, 0)
        layout_option.addWidget(self.edit_fontweight, 2, 1)
        layout_option.addWidget(QLabel("Enable Auto Font Offset"), 3, 0)
        layout_option.addWidget(self.edit_autooffset, 3, 1)
        layout_option.addWidget(QLabel("Font Offset Vertical Addend"), 4, 0)
        layout_option.addWidget(self.edit_fontoffset, 4, 1)

        # Button
        button_apply = QDialogButtonBox(QDialogButtonBox.Apply)
        button_apply.clicked.connect(self.applying)

        button_save = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_save.accepted.connect(self.saving)
        button_save.rejected.connect(self.reject)

        layout_button = QHBoxLayout()
        layout_button.addStretch(1)
        layout_button.addWidget(button_apply)
        layout_button.addWidget(button_save)

        # Set layout
        layout_main = QVBoxLayout()
        layout_main.addLayout(layout_option)
        layout_main.addLayout(layout_button)
        layout_main.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        self.setLayout(layout_main)

    def applying(self):
        """Save & apply"""
        self.save_setting(self.user_setting)

    def saving(self):
        """Save & close"""
        self.applying()
        self.accept()  # close

    def save_setting(self, dict_user: dict[str, dict]):
        """Save setting"""
        for setting in dict_user.values():
            for key in setting:
                # Font name
                if re.search(rxp.CFG_FONT_NAME, key):
                    font_name = self.edit_fontname.currentText()
                    if font_name != "no change":
                        setting[key] = font_name
                    continue
                # Font weight
                if re.search(rxp.CFG_FONT_WEIGHT, key):
                    font_weight = self.edit_fontweight.currentText()
                    if font_weight != "no change":
                        setting[key] = font_weight
                    continue
                # Font size addend
                if re.search("font_size", key):
                    font_size = self.edit_fontsize.value()
                    if font_size != 0:
                        setting[key] = max(setting[key] + font_size, 1)
                    continue
                # Auto font offset
                if key == "enable_auto_font_offset":
                    auto_offset = self.edit_autooffset.currentText()
                    if auto_offset == "disable":
                        setting[key] = False
                    elif auto_offset == "enable":
                        setting[key] = True
                    continue
                # Font offset vertical
                if key == "font_offset_vertical":
                    font_offset = self.edit_fontoffset.value()
                    if font_offset != 0:
                        setting[key] += font_offset
                    continue
        # Reset after applied
        self.edit_fontsize.setValue(0)
        self.edit_fontoffset.setValue(0)
        cfg.save(0)
        # Wait saving finish
        while cfg.is_saving:
            time.sleep(0.01)
        self.reloading()


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

        # Option dicts (key: option editor)
        self.option_bool: dict = {}
        self.option_color: dict = {}
        self.option_path: dict = {}
        self.option_image: dict = {}
        self.option_droplist: dict = {}
        self.option_string: dict = {}
        self.option_integer: dict = {}
        self.option_float: dict = {}
        self.option_column_order: dict = {}  # key -> ColumnIndexList widget
        self._preview: WidgetPreview | None = None

        # Section widgets and current column count (used for dynamic reflow)
        self._section_widgets: list[QFrame] = []
        self._num_columns = 0
        self._widest_section = 0

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type to filter options (Ctrl+F)")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_edit)

        # Ctrl+F shortcut: fires regardless of which child widget has focus
        shortcut_find = QShortcut(QKeySequence.Find, self)
        shortcut_find.activated.connect(self._focus_search)

        # Debounce timer
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

        # Create options (initial unfiltered view)
        option_box = self._build_sectioned_layout(self.original_keys)

        # Create scroll box
        scroll_box = QScrollArea(self)
        scroll_box.setWidget(option_box)
        scroll_box.setWidgetResizable(True)
        self._scroll_box = scroll_box

        # Preview panel
        self._preview = WidgetPreview(key_name, parent=self)

        # Set main layout
        layout_main = QVBoxLayout()
        layout_button = QHBoxLayout()
        layout_main.addLayout(search_layout)
        if self._preview.available:
            splitter = QSplitter(Qt.Horizontal)
            splitter.addWidget(scroll_box)
            splitter.addWidget(self._preview)
            splitter.setStretchFactor(0, 2)
            splitter.setStretchFactor(1, 1)
            layout_main.addWidget(splitter)
        else:
            layout_main.addWidget(scroll_box)
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

    def _on_search_text_changed(self):
        """Restart debounce timer"""
        self.filter_timer.start(200)  # milliseconds

    def _apply_filter(self):
        """Rebuild layout with keys that match the current filter text."""
        text = self.search_edit.text().strip().lower()
        if not text:
            filtered_keys = self.original_keys
        else:
            filtered_keys = [key for key in self.original_keys if text in key.lower()]
        self.rebuild_filtered_layout(filtered_keys)

    def rebuild_filtered_layout(self, keys: list[str]):
        """Rebuild the sectioned layout using only the given keys."""
        # Clear old option dictionaries
        self.option_bool.clear()
        self.option_color.clear()
        self.option_path.clear()
        self.option_image.clear()
        self.option_droplist.clear()
        self.option_string.clear()
        self.option_integer.clear()
        self.option_float.clear()
        self.option_column_order.clear()

        # Group the filtered keys and create new section frames
        sections = self.section_grouper.group_keys(keys)
        self._section_widgets = [
            self._create_section_frame(title, sec_keys)
            for title, sec_keys in sections
        ]

        # Recalculate widest section for column layout
        self._widest_section = max(
            (w.sizeHint().width() for w in self._section_widgets), default=1
        )

        # Rearrange columns using the current column count
        new_container = self._arrange_columns(self._num_columns)
        self._scroll_box.setWidget(new_container)

    def _update_current_value(self, key, value):
        """Update value cache"""
        self._current_values[key] = value
        if self._preview is not None:
            self._preview.schedule_refresh(self._current_values)

    def _create_editor_for_key(self, key: str) -> QWidget:
        """Create editor widget for key"""
        current_val = self._current_values[key]
        default_val = self.default_setting[self.key_name][key]

        # Bool
        if re.search(rxp.CFG_BOOL, key):
            editor = QCheckBox(self)
            editor.setFixedWidth(self.option_width)
            editor.setChecked(current_val)
            editor.defaults = default_val
            editor.stateChanged.connect(
                lambda state, k=key: self._update_current_value(k, state == Qt.Checked)
            )
            add_context_menu(editor)
            self.option_bool[key] = editor
            return editor

        # Color string
        if re.search(rxp.CFG_COLOR, key):
            editor = DoubleClickEdit(self, mode="color", init=current_val)
            editor.setFixedWidth(self.option_width)
            editor.setMaxLength(9)
            editor.setValidator(QVAL_COLOR)
            editor.textChanged.connect(editor.preview_color)
            editor.setText(current_val)
            editor.defaults = default_val
            editor.textChanged.connect(
                lambda text, k=key: self._update_current_value(k, text)
            )
            add_context_menu(editor)
            self.option_color[key] = editor
            return editor

        # User path string
        if re.search(rxp.CFG_USER_PATH, key):
            editor = DoubleClickEdit(self, mode="path", init=current_val)
            editor.setFixedWidth(self.option_width)
            editor.setText(current_val)
            editor.defaults = default_val
            editor.textChanged.connect(
                lambda text, k=key: self._update_current_value(k, text)
            )
            add_context_menu(editor)
            self.option_path[key] = editor
            return editor

        # User image file path string
        if re.search(rxp.CFG_USER_IMAGE, key):
            editor = DoubleClickEdit(self, mode="image", init=current_val)
            editor.setFixedWidth(self.option_width)
            editor.setText(current_val)
            editor.defaults = default_val
            editor.textChanged.connect(
                lambda text, k=key: self._update_current_value(k, text)
            )
            add_context_menu(editor)
            self.option_image[key] = editor
            return editor

        # Font name string
        if re.search(rxp.CFG_FONT_NAME, key):
            editor = QComboBox(self)
            editor.setFixedWidth(self.option_width)
            editor.addItems(get_font_list())
            editor.setCurrentText(str(current_val))
            editor.defaults = default_val
            editor.currentTextChanged.connect(
                lambda text, k=key: self._update_current_value(k, text)
            )
            add_context_menu(editor)
            self.option_droplist[key] = editor
            return editor

        # Heatmap string
        if re.search(rxp.CFG_HEATMAP, key):
            editor = QComboBox(self)
            editor.setFixedWidth(self.option_width)
            editor.addItems(cfg.user.heatmap.keys())
            editor.setCurrentText(str(current_val))
            editor.defaults = default_val
            editor.currentTextChanged.connect(
                lambda text, k=key: self._update_current_value(k, text)
            )
            add_context_menu(editor)
            self.option_droplist[key] = editor
            return editor

        # Units choice list string
        for ref_key, choice_list in rxp.CHOICE_UNITS.items():
            if re.search(ref_key, key):
                editor = QComboBox(self)
                editor.setFixedWidth(self.option_width)
                editor.addItems(choice_list)
                editor.setCurrentText(str(current_val))
                editor.defaults = default_val
                editor.currentTextChanged.connect(
                    lambda text, k=key: self._update_current_value(k, text)
                )
                add_context_menu(editor)
                self.option_droplist[key] = editor
                return editor
        # Common choice list string
        for ref_key, choice_list in rxp.CHOICE_COMMON.items():
            if re.search(ref_key, key):
                editor = QComboBox(self)
                editor.setFixedWidth(self.option_width)
                editor.addItems(choice_list)
                editor.setCurrentText(str(current_val))
                editor.defaults = default_val
                editor.currentTextChanged.connect(
                    lambda text, k=key: self._update_current_value(k, text)
                )
                add_context_menu(editor)
                self.option_droplist[key] = editor
                return editor

        # Clock format string
        if re.search(rxp.CFG_CLOCK_FORMAT, key) or re.search(rxp.CFG_STRING, key):
            editor = QLineEdit(self)
            editor.setFixedWidth(self.option_width)
            editor.setText(current_val)
            editor.defaults = default_val
            editor.textChanged.connect(
                lambda text, k=key: self._update_current_value(k, text)
            )
            add_context_menu(editor)
            self.option_string[key] = editor
            return editor

        # Integer
        if re.search(rxp.CFG_INTEGER, key):
            editor = QLineEdit(self)
            editor.setFixedWidth(self.option_width)
            editor.setValidator(QVAL_INTEGER)
            editor.setText(str(current_val))
            editor.defaults = default_val
            editor.textChanged.connect(
                lambda text, k=key: self._update_current_value(k, text)
            )
            add_context_menu(editor)
            self.option_integer[key] = editor
            return editor

        # Float or int (fallback)
        editor = QLineEdit(self)
        editor.setFixedWidth(self.option_width)
        editor.setValidator(QVAL_FLOAT)
        editor.setText(str(current_val))
        editor.defaults = default_val
        editor.textChanged.connect(
            lambda text, k=key: self._update_current_value(k, text)
        )
        add_context_menu(editor)
        self.option_float[key] = editor
        return editor

    def _create_column_index_frame(self, title: str | None, keys: list) -> QFrame:
        """Create drag-and-drop frame for display order settings"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        if title is not None:
            header_text = (
                format_option_name(self.key_name) if title == "" else "Display Order"
            )
            title_label = QLabel(f"<b>{header_text}</b>")
            font = title_label.font()
            font.setPointSize(font.pointSize() + 1)
            title_label.setFont(font)
            title_label.setStyleSheet("""
                background-color: palette(dark);
                color: palette(bright-text);
                border-bottom: 2px solid palette(mid);
                padding: 4px;
            """)
            layout.addWidget(title_label)

        list_widget = ColumnIndexList(
            keys, self._current_values, self._update_current_value, parent=self
        )
        for key in keys:
            self.option_column_order[key] = list_widget
        layout.addWidget(list_widget)

        frame = QFrame()
        frame.setObjectName("sectionFrame")
        frame.setLayout(layout)
        frame.setProperty("estimated_rows", len(keys) + (2 if title is not None else 1))
        return frame

    def _create_section_frame(self, title: str | None, keys: list) -> QFrame:
        """Create section frame with title bar and alternating rows"""
        # column_index_* keys get a drag-and-drop list instead of integer editors
        if keys and all(k.startswith("column_index_") for k in keys):
            return self._create_column_index_frame(title, keys)
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        row_offset = 0
        if title is not None:
            # Title bar
            header_text = (
                format_option_name(self.key_name)
                if title == ""
                else format_option_name(title)
            )
            title_label = QLabel(f"<b>{header_text}</b>")
            font = title_label.font()
            font.setPointSize(font.pointSize() + 1)
            title_label.setFont(font)
            title_label.setStyleSheet("""
                background-color: palette(dark);
                color: palette(bright-text);
                border-bottom: 2px solid palette(mid);
                padding: 4px;
            """)
            layout.addWidget(title_label, 0, COLUMN_LABEL, 1, 2)
            row_offset = 1

        # Option rows with alternating background
        for idx, key in enumerate(keys):
            row = idx + row_offset

            row_widget = QWidget()
            if idx % 2 == 0:
                row_widget.setStyleSheet("background-color: palette(alternate-base);")
            else:
                row_widget.setStyleSheet("background-color: palette(base);")

            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(
                UIScaler.size(0.4),
                UIScaler.size(0.2),
                UIScaler.size(0.4),
                UIScaler.size(0.2),
            )
            row_layout.setSpacing(UIScaler.size(0.4))

            row_layout.addWidget(QLabel(format_option_name(key)))
            row_layout.addWidget(self._create_editor_for_key(key))

            row_widget.setLayout(row_layout)
            layout.addWidget(row_widget, row, COLUMN_LABEL, 1, 2)

        frame = QFrame()
        frame.setObjectName("sectionFrame")
        frame.setLayout(layout)
        frame.setProperty("estimated_rows", len(keys) + (1 if title is not None else 0))
        return frame

    def _build_sectioned_layout(self, keys: list[str]) -> QWidget:
        """Create section frames and arrange them for initial display."""
        sections = self.section_grouper.group_keys(keys)

        self._section_widgets = [
            self._create_section_frame(title, sec_keys)
            for title, sec_keys in sections
        ]

        self._widest_section = max(
            (w.sizeHint().width() for w in self._section_widgets), default=1
        )
        try:
            avail_w = QApplication.primaryScreen().availableGeometry().width()
        except AttributeError:
            avail_w = 1920
        num_columns = min(3, max(1, int(avail_w * 0.9) // max(self._widest_section, 1)))
        return self._arrange_columns(num_columns)

    def _arrange_columns(self, num_columns: int) -> QWidget:
        """Distribute section widgets into num_columns columns and return a container."""
        self._num_columns = num_columns
        max_rows = 24

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

        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(UIScaler.size(2))

        for col_widgets in columns:
            if not col_widgets:
                continue
            col_layout = QVBoxLayout()
            col_layout.setSpacing(UIScaler.size(1))
            for w in col_widgets:
                col_layout.addWidget(w)
            col_layout.addStretch(1)
            col_container = QWidget()
            col_container.setLayout(col_layout)
            main_layout.addWidget(col_container, 1)

        container = QWidget()
        container.setLayout(main_layout)
        return container

    def closeEvent(self, event):
        """Stop all timers before Qt tears down child widgets"""
        self.filter_timer.stop()
        if self._preview is not None:
            self._preview.cleanup()
        super().closeEvent(event)

    def resizeEvent(self, event):
        """Reflow columns on window resize"""
        super().resizeEvent(event)
        if not self._section_widgets:
            return
        usable_w = event.size().width() - self.MARGIN * 2
        new_num = min(3, max(1, usable_w // max(self._widest_section, 1)))
        if new_num != self._num_columns:
            self._scroll_box.setWidget(self._arrange_columns(new_num))

    def _focus_search(self):
        """Focus and select all text in the search bar"""
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def applying(self):
        """Save & apply"""
        self.save_setting(is_apply=True)

    def saving(self):
        """Save & close"""
        self.save_setting(is_apply=False)

    def reset_setting(self):
        """Reset setting to default values (and update cache)."""
        msg_text = (
            f"Reset all <b>{format_option_name(self.key_name)}</b> options to default?<br><br>"
            "Changes are only saved after clicking Apply or Save Button."
        )
        if self.confirm_operation(title="Reset Options", message=msg_text):
            for key, editor in self.option_bool.items():
                default = editor.defaults
                editor.setChecked(default)
                self._current_values[key] = default
            for key, editor in self.option_color.items():
                default = editor.defaults
                editor.setText(default)
                self._current_values[key] = default
            for key, editor in self.option_path.items():
                default = editor.defaults
                editor.setText(default)
                self._current_values[key] = default
            for key, editor in self.option_image.items():
                default = editor.defaults
                editor.setText(default)
                self._current_values[key] = default
            for key, editor in self.option_droplist.items():
                default = str(editor.defaults)
                editor.setCurrentText(default)
                self._current_values[key] = default
            for key, editor in self.option_string.items():
                default = editor.defaults
                editor.setText(default)
                self._current_values[key] = default
            for key, editor in self.option_integer.items():
                default = str(editor.defaults)
                editor.setText(default)
                self._current_values[key] = int(default) if default.isdigit() else default
            for key, editor in self.option_float.items():
                default = str(editor.defaults)
                editor.setText(default)
                self._current_values[key] = float(default) if '.' in default else int(default)
            seen_column_lists: set = set()
            for key, lw in self.option_column_order.items():
                if id(lw) not in seen_column_lists:
                    seen_column_lists.add(id(lw))
                    all_keys = [k for k, w in self.option_column_order.items() if w is lw]
                    default_vals = {
                        k: self.default_setting[self.key_name][k] for k in all_keys
                    }
                    lw.reset_to_defaults(default_vals)

    def save_setting(self, is_apply: bool):
        """Save setting from current cache, validate, and write to config."""
        user_setting = self.user_setting[self.key_name]
        error_found = False

        # Validate and copy cached values into user_setting
        for key, editor in self.option_bool.items():
            user_setting[key] = self._current_values[key]

        for key, editor in self.option_color.items():
            value = self._current_values[key]
            if is_hex_color(value):
                user_setting[key] = value
            else:
                self.value_error_message("color", key)
                error_found = True

        for key, editor in self.option_path.items():
            value = self._current_values[key]
            # Try convert to relative path again, in case user manually sets path
            value = set_relative_path(value)
            if set_user_data_path(value):
                user_setting[key] = value
                # Update editor and cache to the reformatted path
                editor.setText(value)
                self._current_values[key] = value
            else:
                self.value_error_message("path", key)
                error_found = True

        for key, editor in self.option_image.items():
            user_setting[key] = self._current_values[key]

        for key, editor in self.option_droplist.items():
            user_setting[key] = self._current_values[key]

        for key, editor in self.option_string.items():
            value = self._current_values[key]
            if re.search(rxp.CFG_CLOCK_FORMAT, key) and not is_clock_format(value):
                self.value_error_message("clock format", key)
                error_found = True
                continue
            user_setting[key] = value

        for key, editor in self.option_integer.items():
            value = self._current_values[key]
            # Ensure it's a string for validation, then convert back
            str_val = str(value)
            if is_string_number(str_val):
                user_setting[key] = int(str_val)
            else:
                self.value_error_message("number", key)
                error_found = True

        for key, editor in self.option_float.items():
            value = self._current_values[key]
            str_val = str(value)
            if is_string_number(str_val):
                num_val = float(str_val)
                if num_val % 1 == 0:  # remove unnecessary decimal points
                    num_val = int(num_val)
                user_setting[key] = num_val
            else:
                self.value_error_message("number", key)
                error_found = True

        for key in self.option_column_order:
            user_setting[key] = self._current_values[key]

        # Abort saving if error found
        if error_found:
            return

        # Save global settings
        if self.cfg_type == ConfigType.CONFIG:
            cfg.update_path()
            cfg.save(0, cfg_type=ConfigType.CONFIG)
        # Save user preset settings
        else:
            cfg.save(0)

        # Wait saving finish
        while cfg.is_saving:
            time.sleep(0.01)

        self.reloading()
        if not is_apply:
            self.accept()

    def value_error_message(self, value_type: str, option_name: str):
        """Value error message"""
        msg_text = (
            f"Invalid {value_type} for <b>{format_option_name(option_name)}</b> option."
            "<br><br>Changes are not saved."
        )
        QMessageBox.warning(self, "Error", msg_text)


def set_preset_name(cfg_type: str):
    """Set preset name"""
    if cfg_type == ConfigType.CONFIG:
        return f"{cfg.filename.config} (global)"
    return cfg.filename.setting


def add_context_menu(parent: QWidget):
    """Add context menu"""
    parent.setContextMenuPolicy(Qt.CustomContextMenu)
    parent.customContextMenuRequested.connect(
        lambda position, parent=parent: context_menu_reset_option(position, parent)
    )


def context_menu_reset_option(position: QPoint, parent: QWidget):
    """Context menu reset option"""
    menu = QMenu()  # no parent for temp menu
    option_reset = menu.addAction("Reset to Default")
    action = menu.exec_(parent.mapToGlobal(position))
    if action == option_reset:
        if isinstance(parent, QCheckBox):
            parent.setChecked(parent.defaults)
            return
        if isinstance(parent, QLineEdit):
            parent.setText(str(parent.defaults))
            return
        if isinstance(parent, QComboBox):
            parent.setCurrentText(str(parent.defaults))
            return
