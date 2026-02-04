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
Log window
"""

from PySide2.QtCore import QBasicTimer
from PySide2.QtGui import QTextCursor, QTextOption
from PySide2.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QTextBrowser,
    QVBoxLayout,
)

from ..const_file import FileFilter
from ..main import log_stream
from ._common import BaseDialog, CompactButton, UIScaler, singleton_dialog


@singleton_dialog("log", show_error=False)
class LogInfo(BaseDialog):
    """Create log info dialog"""

    def __init__(self, parent):
        super().__init__(parent)
        self.set_utility_title("Log")

        self._update_timer = QBasicTimer()
        self.last_position = -1

        # Text view
        self.log_view = QTextBrowser(self)
        self.log_view.setMinimumSize(UIScaler.size(42), UIScaler.size(22))
        self.log_view.setWordWrapMode(QTextOption.NoWrap)
        self.refresh_log()

        # Check box
        checkbox_autorefresh = QCheckBox("Auto Refresh")
        checkbox_autorefresh.setChecked(False)
        checkbox_autorefresh.toggled.connect(self.toggle_auto_refresh)

        # Button
        button_save = CompactButton("Save")
        button_save.clicked.connect(self.save_log)

        button_copy = CompactButton("Copy")
        button_copy.clicked.connect(self.copy_log)

        button_clear = CompactButton("Clear")
        button_clear.clicked.connect(self.clear_log)

        self.button_refresh = CompactButton("Refresh")
        self.button_refresh.clicked.connect(self.refresh_log)

        button_close = CompactButton("Close")
        button_close.clicked.connect(self.reject)

        # Layout
        layout_button = QHBoxLayout()
        layout_button.addWidget(button_save)
        layout_button.addWidget(button_copy)
        layout_button.addWidget(button_clear)
        layout_button.addWidget(self.button_refresh)
        layout_button.addWidget(checkbox_autorefresh)
        layout_button.addStretch(1)
        layout_button.addWidget(button_close)

        layout_main = QVBoxLayout()
        layout_main.addWidget(self.log_view)
        layout_main.addLayout(layout_button)
        layout_main.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        self.setLayout(layout_main)

    def timerEvent(self, event):
        """Refresh log"""
        position = log_stream.tell()
        if self.last_position != position:
            self.last_position = position
            self.refresh_log()

    def toggle_auto_refresh(self, checked: bool):
        """Toggle auto refresh"""
        if checked:
            self._update_timer.start(200, self)
            self.button_refresh.setDisabled(True)
        else:
            self._update_timer.stop()
            self.button_refresh.setDisabled(False)

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
