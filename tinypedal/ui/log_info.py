#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2025 TinyPedal developers, see contributors.md file
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
Log window
"""

from PySide2.QtGui import QTextCursor
from PySide2.QtWidgets import (
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from ..const_file import FileFilter
from ..main import log_stream
from ._common import QSS_EDITOR_BUTTON, BaseDialog


class LogInfo(BaseDialog):
    """Create log info dialog"""

    def __init__(self, parent):
        super().__init__(parent)
        self.set_utility_title("Log")

        # Text view
        self.log_view = QTextBrowser(self)
        self.log_view.setStyleSheet("font-size: 12px;")
        self.log_view.setMinimumSize(550, 300)
        self.refresh_log()

        # Button
        button_refresh = QPushButton("Refresh")
        button_refresh.clicked.connect(self.refresh_log)
        button_refresh.setStyleSheet(QSS_EDITOR_BUTTON)

        button_save = QPushButton("Save")
        button_save.clicked.connect(self.save_log)
        button_save.setStyleSheet(QSS_EDITOR_BUTTON)

        button_copy = QPushButton("Copy")
        button_copy.clicked.connect(self.copy_log)
        button_copy.setStyleSheet(QSS_EDITOR_BUTTON)

        button_clear = QPushButton("Clear")
        button_clear.clicked.connect(self.clear_log)
        button_clear.setStyleSheet(QSS_EDITOR_BUTTON)

        button_close = QDialogButtonBox(QDialogButtonBox.Close)
        button_close.rejected.connect(self.reject)
        button_close.setStyleSheet(QSS_EDITOR_BUTTON)

        # Layout
        layout_button = QHBoxLayout()
        layout_button.addWidget(button_refresh)
        layout_button.addWidget(button_save)
        layout_button.addWidget(button_copy)
        layout_button.addWidget(button_clear)
        layout_button.addWidget(button_close)
        layout_button.setContentsMargins(5,5,5,5)

        layout_main = QVBoxLayout()
        layout_main.addWidget(self.log_view)
        layout_main.addLayout(layout_button)
        layout_main.setContentsMargins(3,3,3,7)
        self.setLayout(layout_main)

    def refresh_log(self):
        """Refresh log"""
        self.log_view.setText(log_stream.getvalue())
        self.log_view.moveCursor(QTextCursor.End)

    def clear_log(self):
        """Clear log"""
        if self.confirm_operation(message="Clear all log?"):
            log_stream.truncate(0)
            log_stream.seek(0)
            self.refresh_log()

    def copy_log(self):
        """Copy log"""
        self.log_view.selectAll()
        self.log_view.copy()
        QMessageBox.information(self, "Copy", "Copied all log to Clipboard.")

    def save_log(self):
        """Save log"""
        filename_full = QFileDialog.getSaveFileName(
            self,
            dir="log",
            filter=";;".join((FileFilter.TXT, FileFilter.LOG, FileFilter.ALL)),
        )[0]
        if not filename_full:
            return
        with open(filename_full, "w", newline="", encoding="utf-8") as log_file:
            log_stream.seek(0)
            log_file.writelines(log_stream)
        # Set back to end
        log_stream.seek(2)
