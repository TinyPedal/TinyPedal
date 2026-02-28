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
Global font override dialog.
"""

import re
import time

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QComboBox,
    QDialogButtonBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

from .. import regex_pattern as rxp
from ..const_file import ConfigType
from ..setting import cfg
from ._common import BaseDialog, UIScaler, singleton_dialog
from .components.option_editors import get_font_list


@singleton_dialog(ConfigType.CONFIG)
class FontConfig(BaseDialog):
    """Config global font setting"""

    def __init__(self, parent, user_setting: dict, reload_func):
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
