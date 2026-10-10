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
Application UI
"""

import logging
import os
import sys

from PySide2.QtCore import QCoreApplication, QLocale, Qt
from PySide2.QtGui import QFont, QGuiApplication, QIcon, QPixmapCache
from PySide2.QtWidgets import QApplication, QMessageBox

from ..constant import APP, FILE, PLATFORM

logger = logging.getLogger(__name__)


def set_app_dpi_scale(high_dpi: bool):
    """Set APP high DPI scale"""
    if high_dpi:
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    logger.info("High DPI scaling: %s", "ON" if high_dpi else "OFF")


def set_app_locale():
    """Set APP locale"""
    loc = QLocale(QLocale.C)
    loc.setNumberOptions(QLocale.RejectGroupSeparator)
    QLocale.setDefault(loc)


def set_app_icon(root: QApplication):
    """Set APP icon"""
    root.setWindowIcon(QIcon(FILE.IMAGE_TINYPEDAL))
    # Set window icon for X11/Wayland (workaround)
    if not PLATFORM.WINDOWS:
        root.setDesktopFileName("TinyPedal-overlay")


def set_app_font(root: QApplication):
    """Set APP default font"""
    font = root.font()
    if os.getenv("PYSIDE_OVERRIDE") != "6":  # don't set family for pyside6
        font.setFamily("sans-serif")
    font.setPointSize(10)
    font.setStyleHint(QFont.SansSerif)
    root.setFont(font)


def init(high_dpi: bool) -> QApplication:
    """Initialize APP core GUI"""
    if QApplication.instance():
        raise RuntimeError("core GUI already initialized")
    # Set global locale
    set_app_locale()
    # Set DPI scale
    set_app_dpi_scale(high_dpi)
    # Set GUI
    QApplication.setStyle("Fusion")
    root = QApplication(sys.argv)
    root.setQuitOnLastWindowClosed(False)
    root.setApplicationName(APP.TINYPEDAL)
    set_app_icon(root)
    set_app_font(root)
    # Disable global pixmap cache
    QPixmapCache.setCacheLimit(0)
    logger.info("Screen pixel ratio: %s", root.devicePixelRatio())
    logger.info("Platform plugin: %s", root.platformName())
    return root


def cancel(message: str):
    """Cancel init & show message dialog & quit app"""
    logger.warning(message)
    if not QApplication.instance():
        root = QApplication(sys.argv)
        set_app_icon(root)
    QMessageBox.warning(None, f"{APP.TINYPEDAL} v{APP.VERSION}", message)
    sys.exit()
