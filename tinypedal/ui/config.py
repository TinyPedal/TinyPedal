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

from PySide2.QtCore import QPoint, Qt
from PySide2.QtGui import QFontDatabase
from PySide2.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .. import regex_pattern as rxp
from ..const_file import ConfigType
from ..formatter import format_option_name
from ..setting import cfg
from ..userfile import set_relative_path, set_user_data_path
from ..validator import is_clock_format, is_hex_color, is_string_number
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
COLUMN_OPTION = 1


def get_font_list() -> list[str]:
    """Get all available font families list"""
    if os.getenv("PYSIDE_OVERRIDE") == "6":  # no instance in qt6
        return QFontDatabase.families()  # type: ignore[call-arg]
    return QFontDatabase().families()


class SectionGrouper:
    """Groups configuration keys based on JSON order and word overlap.

    Consecutive show_* keys that share enough common words (or one is a
    substring of the other) are merged into one section, keeping the title
    of the first show_* key.  All non-show keys are appended to the current
    section.  Fixed groups (column_index_*) are collected separately.
    """

    def __init__(self, min_match: int = 2):
        self.min_match = min_match

    @staticmethod
    def _word_set(phrase: str) -> set[str]:
        """Split an underscore-delimited name into a set of words."""
        return set(phrase.split("_"))

    def _similar(self, topic1: str, topic2: str) -> bool:
        """Check whether two topics (without 'show_') belong together."""
        # Direct match if one is a substring of the other
        if topic1 in topic2 or topic2 in topic1:
            return True
        words1 = self._word_set(topic1)
        words2 = self._word_set(topic2)
        return len(words1 & words2) >= self.min_match

    def group_keys(self, keys: list[str]) -> list[tuple[str | None, list[str]]]:
        """Group keys into labelled sections.

        Returns a list of (title, key_list) tuples.
        """
        # 1. Separate fixed groups (e.g. column_index_*)
        fixed_groups: dict[str, list[str]] = {}
        remaining: list[str] = []
        for key in keys:
            if key.startswith("column_index_"):
                fixed_groups.setdefault("Column Index", []).append(key)
            else:
                remaining.append(key)

        # 2. Iterate remaining keys and build sections
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

        # 3. Collect keys that appeared before the first show_* key
        all_assigned: set[str] = set()
        for _, key_list in sections:
            all_assigned.update(key_list)
        unassigned = [k for k in remaining if k not in all_assigned]
        if unassigned:
            sections.insert(0, ("", unassigned))

        # 4. Append fixed groups
        for title, fkeys in fixed_groups.items():
            sections.append((title, fkeys))

        return sections


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
    """User configuration dialog with sectioned layout."""

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
        """
        Args:
            key_name: config key name.
            cfg_type: config type name from "ConfigType".
            user_setting: user setting dictionary, ex. cfg.user.setting.
            default_setting: default setting dictionary, ex. cfg.default.setting.
            reload_func: config reload (callback) function.
            option_width: option column width in pixels.
            section_grouper: grouper instance that determines the section layout.
                             Defaults to SectionGrouper() if not provided.
        """
        super().__init__(parent)
        self.set_config_title(format_option_name(key_name), set_preset_name(cfg_type))

        self.reloading = reload_func
        self.key_name = key_name
        self.cfg_type = cfg_type
        self.user_setting = user_setting
        self.default_setting = default_setting
        self.option_width = UIScaler.size(option_width)
        self.section_grouper = section_grouper or SectionGrouper()

        # Option dict (key: option editor)
        self.option_bool: dict = {}
        self.option_color: dict = {}
        self.option_path: dict = {}
        self.option_image: dict = {}
        self.option_droplist: dict = {}
        self.option_string: dict = {}
        self.option_integer: dict = {}
        self.option_float: dict = {}

        # Button
        button_reset = QDialogButtonBox(QDialogButtonBox.Reset)
        button_reset.clicked.connect(self.reset_setting)

        button_apply = QDialogButtonBox(QDialogButtonBox.Apply)
        button_apply.clicked.connect(self.applying)

        button_save = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_save.accepted.connect(self.saving)
        button_save.rejected.connect(self.reject)

        # Create options
        option_box = self._build_sectioned_layout()

        # Create scroll box
        scroll_box = QScrollArea(self)
        scroll_box.setWidget(option_box)
        scroll_box.setWidgetResizable(True)

        # Set layout
        layout_main = QVBoxLayout()
        layout_button = QHBoxLayout()
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
        hint = option_box.sizeHint()
        scroll_box.setMinimumWidth(hint.width() + UIScaler.size(4))
        self.adjustSize()
        try:
            avail_h = self.screen().availableGeometry().height()
        except AttributeError:
            avail_h = 900
        max_h = int(avail_h * 0.9)
        if self.height() > max_h:
            self.resize(self.width(), max_h)

    def _create_editor_for_key(self, key: str) -> QWidget:
        """Create and register an editor widget for the given key."""
        user_val = self.user_setting[self.key_name][key]
        default_val = self.default_setting[self.key_name][key]

        # Bool
        if re.search(rxp.CFG_BOOL, key):
            editor = QCheckBox(self)
            editor.setFixedWidth(self.option_width)
            editor.setChecked(user_val)
            editor.defaults = default_val
            add_context_menu(editor)
            self.option_bool[key] = editor
            return editor

        # Color string
        if re.search(rxp.CFG_COLOR, key):
            editor = DoubleClickEdit(self, mode="color", init=user_val)
            editor.setFixedWidth(self.option_width)
            editor.setMaxLength(9)
            editor.setValidator(QVAL_COLOR)
            editor.textChanged.connect(editor.preview_color)
            editor.setText(user_val)
            editor.defaults = default_val
            add_context_menu(editor)
            self.option_color[key] = editor
            return editor

        # User path string
        if re.search(rxp.CFG_USER_PATH, key):
            editor = DoubleClickEdit(self, mode="path", init=user_val)
            editor.setFixedWidth(self.option_width)
            editor.setText(user_val)
            editor.defaults = default_val
            add_context_menu(editor)
            self.option_path[key] = editor
            return editor

        # User image file path string
        if re.search(rxp.CFG_USER_IMAGE, key):
            editor = DoubleClickEdit(self, mode="image", init=user_val)
            editor.setFixedWidth(self.option_width)
            editor.setText(user_val)
            editor.defaults = default_val
            add_context_menu(editor)
            self.option_image[key] = editor
            return editor

        # Font name string
        if re.search(rxp.CFG_FONT_NAME, key):
            editor = QComboBox(self)
            editor.setFixedWidth(self.option_width)
            editor.addItems(get_font_list())
            editor.setCurrentText(str(user_val))
            editor.defaults = default_val
            add_context_menu(editor)
            self.option_droplist[key] = editor
            return editor

        # Heatmap string
        if re.search(rxp.CFG_HEATMAP, key):
            editor = QComboBox(self)
            editor.setFixedWidth(self.option_width)
            editor.addItems(cfg.user.heatmap.keys())
            editor.setCurrentText(str(user_val))
            editor.defaults = default_val
            add_context_menu(editor)
            self.option_droplist[key] = editor
            return editor

        # Units choice list string
        for ref_key, choice_list in rxp.CHOICE_UNITS.items():
            if re.search(ref_key, key):
                editor = QComboBox(self)
                editor.setFixedWidth(self.option_width)
                editor.addItems(choice_list)
                editor.setCurrentText(str(user_val))
                editor.defaults = default_val
                add_context_menu(editor)
                self.option_droplist[key] = editor
                return editor
        # Common choice list string
        for ref_key, choice_list in rxp.CHOICE_COMMON.items():
            if re.search(ref_key, key):
                editor = QComboBox(self)
                editor.setFixedWidth(self.option_width)
                editor.addItems(choice_list)
                editor.setCurrentText(str(user_val))
                editor.defaults = default_val
                add_context_menu(editor)
                self.option_droplist[key] = editor
                return editor

        # Clock format string
        if re.search(rxp.CFG_CLOCK_FORMAT, key) or re.search(rxp.CFG_STRING, key):
            editor = QLineEdit(self)
            editor.setFixedWidth(self.option_width)
            editor.setText(user_val)
            editor.defaults = default_val
            add_context_menu(editor)
            self.option_string[key] = editor
            return editor

        # Integer
        if re.search(rxp.CFG_INTEGER, key):
            editor = QLineEdit(self)
            editor.setFixedWidth(self.option_width)
            editor.setValidator(QVAL_INTEGER)
            editor.setText(str(user_val))
            editor.defaults = default_val
            add_context_menu(editor)
            self.option_integer[key] = editor
            return editor

        # Float or int (fallback)
        editor = QLineEdit(self)
        editor.setFixedWidth(self.option_width)
        editor.setValidator(QVAL_FLOAT)
        editor.setText(str(user_val))
        editor.defaults = default_val
        add_context_menu(editor)
        self.option_float[key] = editor
        return editor

    def _create_section_frame(self, title: str | None, keys: list) -> QFrame:
        """Create a frame containing one section with title bar and alternating rows."""
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(0)
        layout.setColumnStretch(COLUMN_LABEL, 0)
        layout.setColumnStretch(COLUMN_OPTION, 1)
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

    def _build_sectioned_layout(self) -> QWidget:
        """Build the complete layout with sections distributed across columns."""
        keys = list(self.user_setting[self.key_name])
        sections = self.section_grouper.group_keys(keys)

        section_widgets = [
            self._create_section_frame(title, sec_keys)
            for title, sec_keys in sections
        ]

        # Distribute sections across columns, max 24 rows per column
        num_columns = 3
        max_rows = 24

        columns: list[list[QFrame]] = [[] for _ in range(num_columns)]
        col_rows = [0] * num_columns

        for widget in section_widgets:
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

        # Build horizontal layout
        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(UIScaler.size(2))

        for col_widgets in columns:
            if not col_widgets:
                continue
            col_layout = QVBoxLayout()
            col_layout.setAlignment(Qt.AlignTop)
            col_layout.setSpacing(UIScaler.size(1))
            for w in col_widgets:
                col_layout.addWidget(w)
            col_container = QWidget()
            col_container.setLayout(col_layout)
            main_layout.addWidget(col_container, alignment=Qt.AlignTop)

        container = QWidget()
        container.setLayout(main_layout)
        return container

    def applying(self):
        """Save & apply"""
        self.save_setting(is_apply=True)

    def saving(self):
        """Save & close"""
        self.save_setting(is_apply=False)

    def reset_setting(self):
        """Reset setting"""
        msg_text = (
            f"Reset all <b>{format_option_name(self.key_name)}</b> options to default?<br><br>"
            "Changes are only saved after clicking Apply or Save Button."
        )
        if self.confirm_operation(title="Reset Options", message=msg_text):
            for editor in self.option_bool.values():
                editor.setChecked(editor.defaults)
            for editor in self.option_color.values():
                editor.setText(editor.defaults)
            for editor in self.option_path.values():
                editor.setText(editor.defaults)
            for editor in self.option_image.values():
                editor.setText(editor.defaults)
            for editor in self.option_droplist.values():
                editor.setCurrentText(str(editor.defaults))
            for editor in self.option_string.values():
                editor.setText(editor.defaults)
            for editor in self.option_integer.values():
                editor.setText(str(editor.defaults))
            for editor in self.option_float.values():
                editor.setText(str(editor.defaults))

    def save_setting(self, is_apply: bool):
        """Save setting"""
        user_setting = self.user_setting[self.key_name]
        error_found = False

        for key, editor in self.option_bool.items():
            user_setting[key] = editor.isChecked()

        for key, editor in self.option_color.items():
            value = editor.text()
            if is_hex_color(value):
                user_setting[key] = value
            else:
                self.value_error_message("color", key)
                error_found = True

        for key, editor in self.option_path.items():
            # Try convert to relative path again, in case user manually sets path
            value = set_relative_path(editor.text())
            if set_user_data_path(value):
                user_setting[key] = value
                editor.setText(value)  # update reformatted path
            else:
                self.value_error_message("path", key)
                error_found = True

        for key, editor in self.option_image.items():
            user_setting[key] = editor.text()

        for key, editor in self.option_droplist.items():
            user_setting[key] = editor.currentText()

        for key, editor in self.option_string.items():
            value = editor.text()
            if re.search(rxp.CFG_CLOCK_FORMAT, key) and not is_clock_format(value):
                self.value_error_message("clock format", key)
                error_found = True
                continue
            user_setting[key] = value

        for key, editor in self.option_integer.items():
            value = editor.text()
            if is_string_number(value):
                user_setting[key] = int(value)
            else:
                self.value_error_message("number", key)
                error_found = True

        for key, editor in self.option_float.items():
            value = editor.text()
            if is_string_number(value):
                value = float(value)
                if value % 1 == 0:  # remove unnecessary decimal points
                    value = int(value)
                user_setting[key] = value
            else:
                self.value_error_message("number", key)
                error_found = True

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
