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
)

COLUMN_LABEL = 0  # grid layout column index
COLUMN_OPTION = 1


def get_font_list() -> list[str]:
    """Get all available font families list"""
    if os.getenv("PYSIDE_OVERRIDE") == "6":  # no instance in qt6
        return QFontDatabase.families()  # type: ignore[call-arg]
    return QFontDatabase().families()


class FontConfig(BaseDialog):
    """Config global font setting"""

    def __init__(self, parent, user_setting: dict, reload_func: Callable):
        super().__init__(parent)
        self.set_config_title("Global Font Override", cfg.filename.setting)

        self.reloading = reload_func
        self.user_setting = user_setting

        # Combobox
        self.edit_fontname = QComboBox(self)
        self.edit_fontname.addItems(["no change"] + get_font_list())
        self.edit_fontname.setFixedWidth(UIScaler.size(9))

        self.edit_fontsize = QSpinBox(self)
        self.edit_fontsize.setRange(-999,999)
        self.edit_fontsize.setFixedWidth(UIScaler.size(9))

        self.edit_fontweight = QComboBox(self)
        self.edit_fontweight.addItems(["no change"] + rxp.CHOICE_COMMON[rxp.CFG_FONT_WEIGHT])
        self.edit_fontweight.setFixedWidth(UIScaler.size(9))

        layout_option = QGridLayout()
        layout_option.setAlignment(Qt.AlignTop)
        layout_option.addWidget(QLabel("Font Name"), 0, 0)
        layout_option.addWidget(self.edit_fontname, 0, 1)
        layout_option.addWidget(QLabel("Font Size Addend"), 1, 0)
        layout_option.addWidget(self.edit_fontsize, 1, 1)
        layout_option.addWidget(QLabel("Font Weight"), 2, 0)
        layout_option.addWidget(self.edit_fontweight, 2, 1)

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

    def save_setting(self, dict_user: dict):
        """Save setting"""
        for item in dict_user.keys():
            key_list_user = tuple(dict_user[item])
            for key in key_list_user:
                if (re.search(rxp.CFG_FONT_NAME, key) and
                    self.edit_fontname.currentText() != "no change"):
                    dict_user[item][key] = self.edit_fontname.currentText()
                    continue
                if (re.search(rxp.CFG_FONT_WEIGHT, key) and
                    self.edit_fontweight.currentText() != "no change"):
                    dict_user[item][key] = self.edit_fontweight.currentText()
                    continue
                if (re.search("font_size", key) and
                    self.edit_fontsize.value() != 0):
                    dict_user[item][key] = max(
                        dict_user[item][key] + self.edit_fontsize.value(), 1)
                    continue
        self.edit_fontsize.setValue(0)
        cfg.save(0)
        while cfg.is_saving:  # wait saving finish
            time.sleep(0.01)
        self.reloading()


class UserConfig(BaseDialog):
    """User configuration"""

    def __init__(
        self, parent, key_name: str, cfg_type: str, user_setting: dict,
        default_setting: dict, reload_func: Callable, option_width: int = 9):
        """
        Args:
            key_name: config key name.
            cfg_type: config type name from "ConfigType".
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
        self.option_bool: dict = {}
        self.option_color: dict = {}
        self.option_path: dict = {}
        self.option_image: dict = {}
        #self.option_fontname: dict = {}
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
        layout_option = QGridLayout()
        layout_option.setAlignment(Qt.AlignTop)
        self.create_options(layout_option)
        option_box = QWidget(self)
        option_box.setLayout(layout_option)

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
        self.setMinimumWidth(self.sizeHint().width() + UIScaler.size(2))

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

            #for editor in self.option_fontname.values():
            #    editor.setCurrentFont(editor.defaults)

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

        #for key, editor in self.option_fontname.items():
        #    user_setting[key] = editor.currentFont().family()

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
        # Reload
        self.reloading()
        # Close
        if not is_apply:
            self.accept()

    def value_error_message(self, value_type: str, option_name: str):
        """Value error message"""
        msg_text = (
            f"Invalid {value_type} for <b>{format_option_name(option_name)}</b> option."
            "<br><br>Changes are not saved."
        )
        QMessageBox.warning(self, "Error", msg_text)

    def create_options(self, layout):
        """Create options"""
        key_list_user = tuple(self.user_setting[self.key_name])  # create user key list

        for idx, key in enumerate(key_list_user):
            self.__add_option_label(idx, key, layout)
            # Bool
            if re.search(rxp.CFG_BOOL, key):
                self.__add_option_bool(idx, key, layout)
                continue
            # Units choice list string
            if self.__choice_match(rxp.CHOICE_UNITS, idx, key, layout):
                continue
            # Common choice list string
            if self.__choice_match(rxp.CHOICE_COMMON, idx, key, layout):
                continue
            # Color string
            if re.search(rxp.CFG_COLOR, key):
                self.__add_option_color(idx, key, layout)
                continue
            # User path string
            if re.search(rxp.CFG_USER_PATH, key):
                self.__add_option_path(idx, key, layout)
                continue
            # User image file path string
            if re.search(rxp.CFG_USER_IMAGE, key):
                self.__add_option_image(idx, key, layout)
                continue
            # Font name string
            if re.search(rxp.CFG_FONT_NAME, key):
                self.__add_option_combolist(idx, key, layout, get_font_list())
                continue
            # Heatmap string
            if re.search(rxp.CFG_HEATMAP, key):
                self.__add_option_combolist(idx, key, layout, tuple(cfg.user.heatmap))
                continue
            # Clock format string
            if re.search(rxp.CFG_CLOCK_FORMAT, key):
                self.__add_option_string(idx, key, layout)
                continue
            # String
            if re.search(rxp.CFG_STRING, key):
                self.__add_option_string(idx, key, layout)
                continue
            # Int
            if re.search(rxp.CFG_INTEGER, key):
                self.__add_option_integer(idx, key, layout)
                continue
            # Float or int
            self.__add_option_float(idx, key, layout)

    def __choice_match(self, choice_dict, idx, key, layout):
        """Choice match"""
        for ref_key, choice_list in choice_dict.items():
            if re.search(ref_key, key):
                self.__add_option_combolist(
                    idx, key, layout, choice_list)
                return True
        return False

    def __add_option_label(self, idx, key, layout):
        """Option label"""
        label = QLabel(format_option_name(key))
        layout.addWidget(label, idx, COLUMN_LABEL)

    def __add_option_bool(self, idx, key, layout):
        """Bool"""
        editor = QCheckBox(self)
        editor.setFixedWidth(self.option_width)
        editor.setChecked(self.user_setting[self.key_name][key])
        # Context menu
        editor.defaults = self.default_setting[self.key_name][key]
        add_context_menu(editor)
        # Add layout
        layout.addWidget(editor, idx, COLUMN_OPTION)
        self.option_bool[key] = editor

    def __add_option_color(self, idx, key, layout):
        """Color string"""
        editor = DoubleClickEdit(
            self, mode="color", init=self.user_setting[self.key_name][key])
        editor.setFixedWidth(self.option_width)
        editor.setMaxLength(9)
        editor.setValidator(QVAL_COLOR)
        editor.textChanged.connect(editor.preview_color)
        # Load selected option
        editor.setText(self.user_setting[self.key_name][key])
        # Context menu
        editor.defaults = self.default_setting[self.key_name][key]
        add_context_menu(editor)
        # Add layout
        layout.addWidget(editor, idx, COLUMN_OPTION)
        self.option_color[key] = editor

    def __add_option_path(self, idx, key, layout):
        """Path string"""
        editor = DoubleClickEdit(
            self, mode="path", init=self.user_setting[self.key_name][key])
        editor.setFixedWidth(self.option_width)
        # Load selected option
        editor.setText(self.user_setting[self.key_name][key])
        # Context menu
        editor.defaults = self.default_setting[self.key_name][key]
        add_context_menu(editor)
        # Add layout
        layout.addWidget(editor, idx, COLUMN_OPTION)
        self.option_path[key] = editor

    def __add_option_image(self, idx, key, layout):
        """Image file path string"""
        editor = DoubleClickEdit(
            self, mode="image", init=self.user_setting[self.key_name][key])
        editor.setFixedWidth(self.option_width)
        # Load selected option
        editor.setText(self.user_setting[self.key_name][key])
        # Context menu
        editor.defaults = self.default_setting[self.key_name][key]
        add_context_menu(editor)
        # Add layout
        layout.addWidget(editor, idx, COLUMN_OPTION)
        self.option_image[key] = editor

    #def __add_option_fontname(self, idx, key, layout):
    #    """Font name string"""
    #    editor = QFontComboBox(self)
    #    editor.setFixedWidth(self.option_width)
    #    # Load selected option
    #    editor.setCurrentFont(self.user_setting[self.key_name][key])
    #    # Context menu
    #    editor.defaults = self.default_setting[self.key_name][key]
    #    add_context_menu(editor)
    #    # Add layout
    #    layout.addWidget(editor, idx, COLUMN_OPTION)
    #    self.option_fontname[key] = editor

    def __add_option_combolist(self, idx, key, layout, item_list):
        """Combo droplist string"""
        editor = QComboBox(self)
        editor.setFixedWidth(self.option_width)
        editor.addItems(item_list)
        # Load selected option
        editor.setCurrentText(str(self.user_setting[self.key_name][key]))
        # Context menu
        editor.defaults = self.default_setting[self.key_name][key]
        add_context_menu(editor)
        # Add layout
        layout.addWidget(editor, idx, COLUMN_OPTION)
        self.option_droplist[key] = editor

    def __add_option_string(self, idx, key, layout):
        """String"""
        editor = QLineEdit(self)
        editor.setFixedWidth(self.option_width)
        # Load selected option
        editor.setText(self.user_setting[self.key_name][key])
        # Context menu
        editor.defaults = self.default_setting[self.key_name][key]
        add_context_menu(editor)
        # Add layout
        layout.addWidget(editor, idx, COLUMN_OPTION)
        self.option_string[key] = editor

    def __add_option_integer(self, idx, key, layout):
        """Integer"""
        editor = QLineEdit(self)
        editor.setFixedWidth(self.option_width)
        editor.setValidator(QVAL_INTEGER)
        # Load selected option
        editor.setText(str(self.user_setting[self.key_name][key]))
        # Context menu
        editor.defaults = self.default_setting[self.key_name][key]
        add_context_menu(editor)
        # Add layout
        layout.addWidget(editor, idx, COLUMN_OPTION)
        self.option_integer[key] = editor

    def __add_option_float(self, idx, key, layout):
        """Float"""
        editor = QLineEdit(self)
        editor.setFixedWidth(self.option_width)
        editor.setValidator(QVAL_FLOAT)
        # Load selected option
        editor.setText(str(self.user_setting[self.key_name][key]))
        # Context menu
        editor.defaults = self.default_setting[self.key_name][key]
        add_context_menu(editor)
        # Add layout
        layout.addWidget(editor, idx, COLUMN_OPTION)
        self.option_float[key] = editor


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