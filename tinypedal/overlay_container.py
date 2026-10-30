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
Overlay container
"""

from __future__ import annotations

import logging

from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QWidget

from . import app_signal, cfg, overlay_signal, realtime_state
from .constant import APP

logger = logging.getLogger(__name__)


class OverlayContainer(QWidget):
    """Overlay container (top-level window) for holding widgets"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP.TINYPEDAL} - Overlay")
        self.__connect_signal()
        self.__set_window_attributes()  # 1
        self.__set_window_flags()  # 2

        # Set fixed size to set to screen size
        self.setFixedSize(self.screen().size())
        self.move(0, 0)  # may not work on Linux? normally should end up at 0,0
        # Show as full screen
        self.show()
        self.showFullScreen()

        # Check hide state
        self.setHidden(cfg.overlay["auto_hide"] and not realtime_state.active)

    def __set_window_attributes(self):
        """Set window attributes"""
        self.__set_opacity()
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        if cfg.compatibility["enable_translucent_background"]:
            self.setAttribute(Qt.WA_TranslucentBackground, True)

    def __set_window_flags(self):
        """Set window flags"""
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        if not cfg.overlay["vr_compatibility"]:  # hide taskbar widget
            self.setWindowFlag(Qt.Tool, True)
        if cfg.compatibility["enable_bypass_window_manager"]:
            self.setWindowFlag(Qt.X11BypassWindowManagerHint, True)
        self.__toggle_lock(locked=cfg.overlay["fixed_position"])

    def __set_opacity(self):
        """Set overlay opacity"""
        self.setWindowOpacity(cfg.compatibility["overlay_combined_mode_opacity"])

    @Slot(bool)  # type: ignore[operator]
    def __toggle_lock(self, locked: bool):
        """Toggle widget lock state"""
        self.setWindowFlag(Qt.WindowTransparentForInput, locked)
        # Need re-check after lock/unlock
        self.setHidden(cfg.overlay["auto_hide"] and not realtime_state.active)

    @Slot(bool)  # type: ignore[operator]
    def __toggle_vr_compat(self, enabled: bool):
        """Toggle widget VR compatibility"""
        self.setWindowFlag(Qt.Tool, not enabled)
        # Need re-check
        self.setHidden(cfg.overlay["auto_hide"] and not realtime_state.active)

    def __connect_signal(self):
        """Connect overlay lock and hide signal"""
        overlay_signal.locked.connect(self.__toggle_lock)
        overlay_signal.hidden.connect(self.setHidden)
        overlay_signal.iconify.connect(self.__toggle_vr_compat)
        app_signal.reload.connect(self.__set_opacity)
