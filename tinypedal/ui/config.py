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
from itertools import islice, zip_longest
from typing import Callable, Mapping, Sequence

from PySide2.QtCore import Qt
from PySide2.QtGui import QFontDatabase
from PySide2.QtWidgets import (
    QCompleter,
    QDialogButtonBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .. import regex_pattern as rxp
from ..const_file import ConfigType
from ..formatter import format_option_name
from ..setting import cfg
from ._common import (
    QVAL_COLOR,
    QVAL_FLOAT,
    QVAL_INTEGER,
    BaseDialog,
    CompactButton,
    UIScaler,
    singleton_dialog,
)
from ._option import (
    BooleanEdit,
    ClockFormatEdit,
    ColorEdit,
    DropDownListEdit,
    FilePathEdit,
    FloatEdit,
    ImagePathEdit,
    IntegerEdit,
    OptionGroup,
    StringEdit,
)
from .display_order import DisplayOrder

COLUMN_LABEL = 0  # grid layout column index
COLUMN_OPTION = 1


def get_font_list() -> list[str]:
    """Get all available font families list"""
    if os.getenv("PYSIDE_OVERRIDE") == "6":  # no instance in qt6
        return QFontDatabase.families()  # type: ignore[call-arg]
    return QFontDatabase().families()


@singleton_dialog(ConfigType.CONFIG)
class FontConfig(BaseDialog):
    """Config global font setting"""

    def __init__(self, parent, user_setting: dict, reload_func: Callable):
        super().__init__(parent)
        self.set_config_title("Global Font Override", cfg.filename.setting)

        self.reloading = reload_func
        self.user_setting = user_setting

        # Create options
        self.edit_fontname = DropDownListEdit(self)
        self.edit_fontname.addItem("no change")
        self.edit_fontname.addItems(get_font_list())
        self.edit_fontname.setFixedWidth(UIScaler.size(9))

        self.edit_fontsize = QSpinBox(self)
        self.edit_fontsize.setRange(-999, 999)
        self.edit_fontsize.setFixedWidth(UIScaler.size(9))

        self.edit_fontweight = DropDownListEdit(self)
        self.edit_fontweight.addItem("no change")
        self.edit_fontweight.addItems(rxp.CHOICE_COMMON[rxp.CFG_FONT_WEIGHT])
        self.edit_fontweight.setFixedWidth(UIScaler.size(9))

        self.edit_autooffset = DropDownListEdit(self)
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
        # Wait saving finish
        cfg.save(0)
        while cfg.is_saving:
            time.sleep(0.01)
        self.reloading()


@singleton_dialog(ConfigType.CONFIG)
class UserConfig(BaseDialog):
    """User configuration"""

    def __init__(
        self,
        parent,
        key_name: str,
        cfg_type: str,
        user_setting: dict,
        default_setting: dict,
        reload_func: Callable,
        option_width: int = 9,
        allow_apply: bool = True,
    ):
        """
        Args:
            key_name: config key name.
            cfg_type: config type name from "ConfigType", set to "" for none config type.
            user_setting: user setting dictionary, ex. cfg.user.setting.
            default_setting: default setting dictionary, ex. cfg.default.setting.
            reload_func: config reload (callback) function.
            option_width: option column width in pixels.
        """
        super().__init__(parent)
        self.set_config_title(format_option_name(key_name), set_preset_name(cfg_type))

        self.reloading = reload_func
        self.key_name = key_name
        self.cfg_type = cfg_type
        self.user_setting = user_setting
        self.default_setting = default_setting
        self.option_width = UIScaler.size(option_width)

        # Option dict (key: option editor)
        self.option_edit: dict = {}
        option_word_set: set[str] = set()

        # Create options
        self.layout_option = QGridLayout()
        self.layout_option.setAlignment(Qt.AlignTop)
        self.create_options(self.layout_option, option_word_set)
        option_box = QWidget(self)
        option_box.setLayout(self.layout_option)

        # Create scroll box
        scroll_box = QScrollArea(self)
        scroll_box.setWidget(option_box)
        scroll_box.setWidgetResizable(True)

        # Search box
        auto_complete_search = QCompleter(option_word_set, self)
        auto_complete_search.setCaseSensitivity(Qt.CaseInsensitive)

        edit_search = QLineEdit(self)
        edit_search.setPlaceholderText(" Type here to search options")
        edit_search.setCompleter(auto_complete_search)
        edit_search.textChanged.connect(self.search_options)

        button_clearsearch = CompactButton("Clear")
        button_clearsearch.clicked.connect(edit_search.clear)

        layout_search = QHBoxLayout()
        layout_search.addWidget(edit_search, stretch=1)
        layout_search.addWidget(button_clearsearch)

        # Button
        has_display_order = (cfg_type == ConfigType.WIDGET and self.has_display_order())
        if has_display_order:
            button_display_order = QPushButton("Configure Display Order")
            button_display_order.clicked.connect(self.open_display_order)

        button_reset = QDialogButtonBox(QDialogButtonBox.Reset)
        button_reset.clicked.connect(self.reset_setting)

        button_apply = QDialogButtonBox(QDialogButtonBox.Apply)
        button_apply.clicked.connect(self.applying)

        button_save = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_save.accepted.connect(self.saving)
        button_save.rejected.connect(self.reject)

        layout_button = QHBoxLayout()
        layout_button.addWidget(button_reset)
        layout_button.addStretch(1)
        layout_button.addWidget(button_apply)
        layout_button.addWidget(button_save)

        if not allow_apply:
            button_apply.hide()

        # Set layout
        layout_main = QVBoxLayout()
        layout_main.addLayout(layout_search)
        layout_main.addWidget(scroll_box)
        if has_display_order:
            layout_main.addWidget(button_display_order)
        layout_main.addLayout(layout_button)
        layout_main.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        self.setLayout(layout_main)
        self.setMinimumWidth(self.sizeHint().width() + UIScaler.size(2))

    def has_display_order(self) -> bool:
        """Check whether has display order option"""
        for key in reversed(self.user_setting[self.key_name].keys()):
            if "display_order" in key:
                return True
        return False

    def search_options(self, text: str):
        """Search for options"""
        text = text.strip().lower()
        layout_option = self.layout_option
        for row_index in range(layout_option.rowCount()):
            label = layout_option.itemAtPosition(row_index, 0).widget()
            option = layout_option.itemAtPosition(row_index, 1).widget()
            hidden = text not in label.text().lower()
            label.setHidden(hidden)
            option.setHidden(hidden)

    def open_display_order(self):
        """Open display order dialog"""
        # Extract column index setting
        user_orders = {k: v for k, v in self.user_setting[self.key_name].items() if k.startswith("display_order_")}
        default_orders = {k: v for k, v in self.default_setting[self.key_name].items() if k.startswith("display_order_")}
        dialog = DisplayOrder(self, user_orders=user_orders, default_orders=default_orders)
        dialog.open()

    def update_display_order(self, new_orders: dict):
        """Update display order index to user setting & editor"""
        self.user_setting[self.key_name].update(new_orders)
        for key, value in new_orders.items():
            if key in self.option_edit:
                self.option_edit[key].setText(str(value))

    def applying(self):
        """Save & apply"""
        self.save_setting(close=False)

    def saving(self):
        """Save & close"""
        self.save_setting(close=True)

    def reset_setting(self):
        """Reset setting"""
        msg_text = (
            f"Reset all <b>{format_option_name(self.key_name)}</b> options to default?<br><br>"
            "Changes are only saved after clicking Apply or Save Button."
        )
        if self.confirm_operation(title="Reset Options", message=msg_text):
            for editor in self.option_edit.values():
                editor.reset_to_default()

    def save_setting(self, close: bool):
        """Save setting"""
        user_setting = self.user_setting[self.key_name]
        for key, editor in self.option_edit.items():
            value = editor.validate()
            if value is None:  # abort if error found
                self.value_error_message(key)
                return
            user_setting[key] = value
        # Check saving type
        if self.cfg_type:
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
        # Reload
        self.reloading()
        # Close
        if close:
            self.accept()

    def value_error_message(self, option_name: str):
        """Value error message"""
        msg_text = (
            f"Invalid value for <b>{format_option_name(option_name)}</b> option."
            "<br><br>Changes are not saved."
        )
        QMessageBox.warning(self, "Error", msg_text)

    def create_options(self, layout: QGridLayout, option_word_set: set[str]):
        """Create options"""
        option_keys = self.user_setting[self.key_name].keys()
        row_index = -1
        show_group_title = cfg.application["show_option_group_title"]
        group_name = ""

        for key, next_key in zip_longest(option_keys, islice(option_keys, 1, None), fillvalue=""):
            row_index += 1
            # Group name
            if show_group_title:
                group_name = option_group_name(key, next_key, group_name)
                if group_name and group_name != "_same_group":
                    self._add_group_label(row_index, format_option_name(group_name), layout)
                    row_index += 1
            # Option name
            option_name = format_option_name(key)
            option_word_set.update(option_name.split())
            self._add_option_label(row_index, option_name, layout)
            # Bool
            if re.search(rxp.CFG_BOOL, key):
                self._add_option_bool(row_index, key, layout)
                continue
            # Units choice list string
            if self._choice_match(rxp.CHOICE_UNITS, row_index, key, layout):
                continue
            # Common choice list string
            if self._choice_match(rxp.CHOICE_COMMON, row_index, key, layout):
                continue
            # Color string
            if re.search(rxp.CFG_COLOR, key):
                self._add_option_color(row_index, key, layout)
                continue
            # User path string
            if re.search(rxp.CFG_USER_PATH, key):
                self._add_option_path(row_index, key, layout)
                continue
            # User image file path string
            if re.search(rxp.CFG_USER_IMAGE, key):
                self._add_option_image(row_index, key, layout)
                continue
            # Font name string
            if re.search(rxp.CFG_FONT_NAME, key):
                self._add_option_combolist(row_index, key, layout, get_font_list())
                continue
            # Heatmap string
            if re.search(rxp.CFG_HEATMAP, key):
                self._add_option_combolist(row_index, key, layout, cfg.user.heatmap.keys())
                continue
            # Clock format string
            if re.search(rxp.CFG_CLOCK_FORMAT, key):
                self._add_option_clock(row_index, key, layout)
                continue
            # String
            if re.search(rxp.CFG_STRING, key):
                self._add_option_string(row_index, key, layout)
                continue
            # Int
            if re.search(rxp.CFG_INTEGER, key):
                self._add_option_integer(row_index, key, layout)
                continue
            # Float or int
            self._add_option_float(row_index, key, layout)

    def _choice_match(self, choice_dict: Mapping, row_index: int, key: str, layout: QGridLayout) -> bool:
        """Choice match"""
        for ref_key, choice_list in choice_dict.items():
            if re.search(ref_key, key):
                self._add_option_combolist(row_index, key, layout, choice_list)
                return True
        return False

    def _add_group_label(self, row_index: int, option_name: str, layout: QGridLayout):
        """Option group"""
        label = OptionGroup(option_name, self)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label, row_index, COLUMN_LABEL, 1, 2)

    def _add_option_label(self, row_index: int, option_name: str, layout: QGridLayout):
        """Option label"""
        label = QLabel(option_name, self)
        label.setMinimumHeight(UIScaler.size(1.8))
        layout.addWidget(label, row_index, COLUMN_LABEL)

    def _add_option_bool(self, row_index: int, key: str, layout: QGridLayout):
        """Bool"""
        editor = BooleanEdit(self)
        editor.setFixedWidth(self.option_width)
        # Load selected option
        editor.setChecked(self.user_setting[self.key_name][key])
        editor.set_default(self.default_setting[self.key_name][key])
        # Add layout
        layout.addWidget(editor, row_index, COLUMN_OPTION)
        self.option_edit[key] = editor

    def _add_option_color(self, row_index: int, key: str, layout: QGridLayout):
        """Color string"""
        editor = ColorEdit(self, self.user_setting[self.key_name][key])
        editor.setFixedWidth(self.option_width)
        editor.setMaxLength(9)
        editor.setValidator(QVAL_COLOR)
        # Load selected option
        editor.setText(self.user_setting[self.key_name][key])
        editor.set_default(self.default_setting[self.key_name][key])
        # Add layout
        layout.addWidget(editor, row_index, COLUMN_OPTION)
        self.option_edit[key] = editor

    def _add_option_path(self, row_index: int, key: str, layout: QGridLayout):
        """Path string"""
        editor = FilePathEdit(self, self.user_setting[self.key_name][key])
        editor.setFixedWidth(self.option_width)
        # Load selected option
        editor.setText(self.user_setting[self.key_name][key])
        editor.set_default(self.default_setting[self.key_name][key])
        # Add layout
        layout.addWidget(editor, row_index, COLUMN_OPTION)
        self.option_edit[key] = editor

    def _add_option_image(self, row_index: int, key: str, layout: QGridLayout):
        """Image file path string"""
        editor = ImagePathEdit(self, self.user_setting[self.key_name][key])
        editor.setFixedWidth(self.option_width)
        # Load selected option
        editor.setText(self.user_setting[self.key_name][key])
        editor.set_default(self.default_setting[self.key_name][key])
        # Add layout
        layout.addWidget(editor, row_index, COLUMN_OPTION)
        self.option_edit[key] = editor

    def _add_option_combolist(self, row_index: int, key: str, layout: QGridLayout, items: Sequence[str]):
        """Combo droplist string"""
        editor = DropDownListEdit(self)
        editor.setFixedWidth(self.option_width)
        editor.addItems(items)
        # Load selected option
        editor.setCurrentText(str(self.user_setting[self.key_name][key]))
        editor.set_default(self.default_setting[self.key_name][key])
        # Add layout
        layout.addWidget(editor, row_index, COLUMN_OPTION)
        self.option_edit[key] = editor

    def _add_option_clock(self, row_index: int, key: str, layout: QGridLayout):
        """Clock string"""
        editor = ClockFormatEdit(self)
        editor.setFixedWidth(self.option_width)
        # Load selected option
        editor.setText(self.user_setting[self.key_name][key])
        editor.set_default(self.default_setting[self.key_name][key])
        # Add layout
        layout.addWidget(editor, row_index, COLUMN_OPTION)
        self.option_edit[key] = editor

    def _add_option_string(self, row_index: int, key: str, layout: QGridLayout):
        """String"""
        editor = StringEdit(self)
        editor.setFixedWidth(self.option_width)
        # Load selected option
        editor.setText(self.user_setting[self.key_name][key])
        editor.set_default(self.default_setting[self.key_name][key])
        # Add layout
        layout.addWidget(editor, row_index, COLUMN_OPTION)
        self.option_edit[key] = editor

    def _add_option_integer(self, row_index: int, key: str, layout: QGridLayout):
        """Integer"""
        editor = IntegerEdit(self)
        editor.setFixedWidth(self.option_width)
        editor.setValidator(QVAL_INTEGER)
        # Load selected option
        editor.setText(str(self.user_setting[self.key_name][key]))
        editor.set_default(self.default_setting[self.key_name][key])
        # Add layout
        layout.addWidget(editor, row_index, COLUMN_OPTION)
        self.option_edit[key] = editor

    def _add_option_float(self, row_index: int, key: str, layout: QGridLayout):
        """Float"""
        editor = FloatEdit(self)
        editor.setFixedWidth(self.option_width)
        editor.setValidator(QVAL_FLOAT)
        # Load selected option
        editor.setText(str(self.user_setting[self.key_name][key]))
        editor.set_default(self.default_setting[self.key_name][key])
        # Add layout
        layout.addWidget(editor, row_index, COLUMN_OPTION)
        self.option_edit[key] = editor


def set_preset_name(cfg_type: str) -> str:
    """Set preset name"""
    if not cfg_type:
        return ""
    if cfg_type == ConfigType.CONFIG:
        return f"{cfg.filename.config} (global)"
    return cfg.filename.setting


def is_different_option(key: str, next_key: str) -> bool:
    """Check if two options are different types"""
    option_refer = set(key.split("_"))
    option_refer.difference_update(
        (
            "show",
            "enable",
            "for",
            "to",
            "in",
            "on",
            "and",
            "by",
            "into",
            "if",
            "of",
            "while",
            "from",
            "as",
            "info",
            "decimal",
            "places",
            "prefix",
        )
    )
    return option_refer.isdisjoint(next_key.split("_"))


def option_group_name(key: str, next_key: str, group_name: str) -> str:
    """Create option group name"""
    # Unique group
    if key == "opacity":
        return "base_display"
    if key == "font_name":
        return "font_style"
    # Ignore font_offset
    if "font_offset" in key:
        return ""
    # Ignore none option group key name
    if not re.search(rxp.CFG_GROUP_KEY, key):
        return ""
    # Ignore all-different keywords
    if is_different_option(key, next_key):
        return ""
    # Same group already created
    if group_name:
        return "_same_group"
    # New group if current and next option are same
    if "display_order" in key:
        return "display_order"
    return re.sub(rxp.CFG_GROUP_KEY, "", key)
