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
About window
"""

import logging

from PySide2.QtCore import Qt
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import (
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..const_app import APP_NAME, COPYRIGHT, DESCRIPTION, LICENSE, URL_WEBSITE, VERSION
from ..const_file import ImageFile
from ._common import BaseDialog, UIScaler, singleton_dialog

logger = logging.getLogger(__name__)


@singleton_dialog("about", show_error=False)
class About(BaseDialog):
    """Create about window

    Hide window at startup.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")

        # Tab
        main_tab = self.add_tabs()

        # Button
        button_close = QDialogButtonBox(QDialogButtonBox.Close)
        button_close.rejected.connect(self.reject)

        # Layout
        layout_button = QHBoxLayout()
        layout_button.addWidget(button_close)

        layout_main = QVBoxLayout()
        layout_main.addWidget(main_tab)
        layout_main.addLayout(layout_button)
        layout_main.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        self.setLayout(layout_main)
        self.setFixedSize(self.sizeHint())

    def add_tabs(self):
        """Add tabs"""
        info_tab = self.new_about_tab()
        ctrb_tab = self.new_text_tab(self.load_text_files("docs/contributors.md"))
        lics_tab = self.new_text_tab(self.load_text_files("LICENSE.txt"))
        tpan_tab = self.new_text_tab(self.load_text_files("docs/licenses/THIRDPARTYNOTICES.txt"))
        main_tab = QTabWidget(self)
        main_tab.addTab(info_tab, "About")
        main_tab.addTab(ctrb_tab, "Contributors")
        main_tab.addTab(lics_tab, "License")
        main_tab.addTab(tpan_tab, "Third-Party Notices")
        return main_tab

    @staticmethod
    def load_text_files(filepath: str):
        """Load text file"""
        try:
            with open(filepath, "r", encoding="utf-8") as text_file:
                return text_file.read()
        except FileNotFoundError:
            logger.error("MISSING: %s file not found", filepath)
            error_text = "Error: file not found."
            link_text = f"See link: {URL_WEBSITE}/blob/master/"
            return f"{error_text} \n{link_text}{filepath}"

    def new_text_tab(self, text: str):
        """New text tab"""
        new_tab = QTextBrowser(self)
        new_tab.setText(text)
        new_tab.setMinimumSize(UIScaler.size(30), UIScaler.size(22))
        return new_tab

    def new_about_tab(self):
        """New about tab"""
        new_tab = QWidget(self)

        # Logo
        logo_image = QPixmap(ImageFile.APP_ICON)
        logo_image = logo_image.scaledToHeight(UIScaler.size(9), mode=Qt.SmoothTransformation)

        label_logo = QLabel()
        label_logo.setPixmap(logo_image)
        label_logo.setAlignment(Qt.AlignCenter)

        # Description
        label_name = QLabel(APP_NAME)
        label_name.setObjectName("labelAppName")
        label_name.setAlignment(Qt.AlignCenter)

        label_version = QLabel(f"Version {VERSION}")
        label_version.setAlignment(Qt.AlignCenter)

        label_desc = QLabel(
            f"<p>{COPYRIGHT}</p><p>{DESCRIPTION}</p><p>{LICENSE}</p>"
            f"<p><a href={URL_WEBSITE}>{URL_WEBSITE}</a></p>"
        )
        label_desc.setAlignment(Qt.AlignCenter)
        label_desc.setOpenExternalLinks(True)

        # Layout
        layout_about = QVBoxLayout()
        layout_about.addSpacing(UIScaler.size(1))
        layout_about.addWidget(label_logo)
        layout_about.addSpacing(UIScaler.size(1))
        layout_about.addWidget(label_name)
        layout_about.addWidget(label_version)
        layout_about.addSpacing(UIScaler.size(1))
        layout_about.addWidget(label_desc)
        layout_about.addSpacing(UIScaler.size(1))
        layout_about.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        new_tab.setLayout(layout_about)
        return new_tab
