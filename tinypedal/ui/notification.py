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

from ..const_app import URL_RELEASE
from ..setting import cfg
from ..update import update_checker


class NotifyBar(QWidget):
    """Notify bar"""

    def __init__(self, parent):
        super().__init__(parent)
        self.presetlocked = QPushButton("Preset Locked")
        self.presetlocked.setVisible(False)

        self.spectate = QPushButton("Spectate Mode Enabled")
        self.spectate.setVisible(False)

        self.pacenotes = QPushButton("Pace Notes Playback Enabled")
        self.pacenotes.setVisible(False)

        self.hotkey = QPushButton("Global Hotkey Enabled")
        self.hotkey.setVisible(False)

        self.updates = UpdatesNotifyButton("")
        self.updates.setVisible(False)

        layout = QVBoxLayout()
        layout.addWidget(self.presetlocked)
        layout.addWidget(self.spectate)
        layout.addWidget(self.pacenotes)
        layout.addWidget(self.hotkey)
        layout.addWidget(self.updates)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    @Slot(bool)  # type: ignore[operator]
    def refresh(self):
        """Refresh & update style"""
        # Locked preset
        self.presetlocked.setVisible(
            cfg.notification["notify_locked_preset"]
            and cfg.filename.setting in cfg.user.filelock
        )
        if self.presetlocked.isVisible():
            self.presetlocked.setStyleSheet(
                f"color: {cfg.notification['font_color_locked_preset']};"
                f"background: {cfg.notification['bkg_color_locked_preset']};"
            )
        # Spectate mode
        self.spectate.setVisible(
            cfg.notification["notify_spectate_mode"]
            and cfg.api["enable_player_index_override"]
        )
        if self.spectate.isVisible():
            self.spectate.setStyleSheet(
                f"color: {cfg.notification['font_color_spectate_mode']};"
                f"background: {cfg.notification['bkg_color_spectate_mode']};"
            )
        # Pace notes playback
        self.pacenotes.setVisible(
            cfg.notification["notify_pace_notes_playback"]
            and cfg.user.setting["pace_notes_playback"]["enable"]
        )
        if self.pacenotes.isVisible():
            self.pacenotes.setStyleSheet(
                f"color: {cfg.notification['font_color_pace_notes_playback']};"
                f"background: {cfg.notification['bkg_color_pace_notes_playback']};"
            )
        # Global hotkey
        self.hotkey.setVisible(
            cfg.notification["notify_global_hotkey"]
            and cfg.application["enable_global_hotkey"]
        )
        if self.hotkey.isVisible():
            self.hotkey.setStyleSheet(
                f"color: {cfg.notification['font_color_global_hotkey']};"
                f"background: {cfg.notification['bkg_color_global_hotkey']};"
            )


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
