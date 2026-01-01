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
Notification
"""

from __future__ import annotations

from PySide2.QtCore import Slot
from PySide2.QtGui import QDesktopServices
from PySide2.QtWidgets import (
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import overlay_signal
from ..const_app import URL_RELEASE
from ..update import update_checker


class NotifyBar(QWidget):
    """Notify bar"""

    def __init__(self, parent):
        super().__init__(parent)
        self.spectate = QPushButton("Spectate Mode Enabled")
        self.spectate.setObjectName("notifySpectate")
        self.spectate.setVisible(False)
        self.spectate.clicked.connect(lambda _: parent.select_tab(3))

        self.pacenotes = QPushButton("Pace Notes Playback Enabled")
        self.pacenotes.setObjectName("notifyPacenotes")
        self.pacenotes.setVisible(False)
        self.pacenotes.clicked.connect(lambda _: parent.select_tab(4))

        self.presetlocked = QPushButton("Preset Locked")
        self.presetlocked.setObjectName("notifyPresetLocked")
        self.presetlocked.setVisible(False)
        self.presetlocked.clicked.connect(lambda _: parent.select_tab(2))

        self.updates = UpdatesNotifyButton("")
        self.updates.setObjectName("notifyUpdates")
        self.updates.setVisible(False)
        overlay_signal.updates.connect(self.updates.checking)

        layout = QVBoxLayout()
        layout.addWidget(self.spectate)
        layout.addWidget(self.pacenotes)
        layout.addWidget(self.presetlocked)
        layout.addWidget(self.updates)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)


class UpdatesNotifyButton(QPushButton):
    """Updates notify button"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        version_menu = QMenu(self)

        view_update = version_menu.addAction("View Updates On GitHub")
        view_update.triggered.connect(self.open_release)
        version_menu.addSeparator()

        dismiss_msg = version_menu.addAction("Dismiss")
        dismiss_msg.triggered.connect(self.hide)

        self.setMenu(version_menu)

    def open_release(self):
        """Open release link"""
        QDesktopServices.openUrl(URL_RELEASE)

    @Slot(bool)  # type: ignore[operator]
    def checking(self, checking: bool):
        """Checking updates"""
        if checking:
            # Show checking message only with manual checking
            self.setText("Checking For Updates...")
            self.setVisible(update_checker.is_manual())
        else:
            # Hide message if no unpdates and not manual checking
            self.setText(update_checker.message())
            self.setVisible(update_checker.is_manual() or update_checker.is_updates())
