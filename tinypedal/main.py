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
Launcher
"""

import io
import logging
import os
import sys

import psutil
from PySide2.QtCore import QCoreApplication, QLocale, Qt
from PySide2.QtGui import QFont, QGuiApplication, QIcon, QPixmapCache
from PySide2.QtWidgets import QApplication, QMessageBox

from . import version_check
from .const_app import (
    APP_NAME,
    PATH_GLOBAL,
    PLATFORM,
    VERSION,
)
from .const_file import ConfigType, ImageFile, LogFile
from .log_handler import set_logging_level
from .setting import cfg

logger = logging.getLogger(__package__)
log_stream = io.StringIO()


def save_pid_file():
    """Save PID info to file"""
    with open(f"{PATH_GLOBAL}{LogFile.PID}", "w", encoding="utf-8") as f:
        current_pid = os.getpid()
        pid_create_time = psutil.Process(current_pid).create_time()
        pid_str = f"{current_pid},{pid_create_time}"
        f.write(pid_str)


def is_pid_exist() -> bool:
    """Check and verify PID existence"""
    try:
        # Load last recorded PID and creation time from pid log file
        with open(f"{PATH_GLOBAL}{LogFile.PID}", "r", encoding="utf-8") as f:
            pid_read = f.readline()
        pid = pid_read.split(",")
        pid_last = int(pid[0])
        pid_last_create_time = pid[1]
        # Verify if last PID is running and belongs to TinyPedal
        if psutil.pid_exists(pid_last):
            if str(psutil.Process(pid_last).create_time()) == pid_last_create_time:
                return True  # already running
    except (ProcessLookupError, psutil.NoSuchProcess, ValueError, IndexError, FileNotFoundError):
        logger.info("PID not found or invalid")
    return False  # no running


def single_instance_check(is_single_instance: bool):
    """Single instance check"""
    # Check if single instance mode enabled
    if not is_single_instance:
        logger.info("Single instance mode: OFF")
        return
    logger.info("Single instance mode: ON")
    # Skip if restarted
    if os.getenv("TINYPEDAL_RESTART") == "TRUE":
        os.environ.pop("TINYPEDAL_RESTART", None)
        save_pid_file()
        return
    # Check existing PID file first, then exe PID
    if not is_pid_exist():  # (is_pid_exist() or is_exe_running())
        save_pid_file()
        return
    # Show warning to console and popup dialog
    warning_text = (
        "TinyPedal is already running.\n\n"
        "Only one TinyPedal may be run at a time.\n"
        "Check system tray for hidden icon."
    )
    logger.warning(warning_text)
    QMessageBox.warning(None, f"{APP_NAME} v{VERSION}", warning_text)
    sys.exit()


def get_version():
    """Get version info"""
    logger.info("TinyPedal: %s", VERSION)
    logger.info("Python: %s", version_check.python())
    logger.info("Qt: %s", version_check.qt())
    logger.info("PySide: %s", version_check.pyside())
    logger.info("psutil: %s", version_check.psutil())


def init_gui() -> QApplication:
    """Initialize Qt Gui"""
    # Set global locale
    loc = QLocale(QLocale.C)
    loc.setNumberOptions(QLocale.RejectGroupSeparator)
    QLocale.setDefault(loc)
    # Set DPI scale
    if cfg.application["enable_high_dpi_scaling"]:
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    # Set GUI
    QApplication.setStyle("Fusion")
    root = QApplication(sys.argv)
    root.setQuitOnLastWindowClosed(False)
    root.setApplicationName(APP_NAME)
    root.setWindowIcon(QIcon(ImageFile.APP_ICON))
    # Set window icon for X11/Wayland (workaround)
    if PLATFORM != "Windows":
        root.setDesktopFileName("TinyPedal-overlay")
    # Set default font
    font = root.font()
    if os.getenv("PYSIDE_OVERRIDE") != "6":  # don't set family for pyside6
        font.setFamily("sans-serif")
    font.setPointSize(10)
    font.setStyleHint(QFont.SansSerif)
    root.setFont(font)
    # Disable global pixmap cache
    QPixmapCache.setCacheLimit(0)
    logger.info("Screen pixel ratio: %s", root.devicePixelRatio())
    logger.info("Platform plugin: %s", root.platformName())
    return root


def unset_environment():
    """Clear any previous environment variable (required after auto-restarted APP)"""
    os.environ.pop("QT_QPA_PLATFORM", None)
    os.environ.pop("QT_ENABLE_HIGHDPI_SCALING", None)
    os.environ.pop("QT_MEDIA_BACKEND", None)
    os.environ.pop("QT_MULTIMEDIA_PREFERRED_PLUGINS", None)


def set_environment():
    """Set environment before starting GUI"""
    # Windows only
    if PLATFORM == "Windows":
        if os.getenv("PYSIDE_OVERRIDE") == "6":
            # Use "freetype" to avoid high memory usage in pyside6
            os.environ["QT_QPA_PLATFORM"] = "windows:fontengine=freetype"
            os.environ["QT_MEDIA_BACKEND"] = "windows"
        else:
            if cfg.compatibility["multimedia_plugin_on_windows"] == "WMF":
                multimedia_plugin = "windowsmediafoundation"
            else:
                multimedia_plugin = "directshow"
            os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = multimedia_plugin

    # Linux only
    else:
        if cfg.compatibility["enable_x11_platform_plugin_override"]:
            os.environ["QT_QPA_PLATFORM"] = "xcb"

    # Common
    if cfg.application["enable_high_dpi_scaling"]:
        logger.info("High DPI scaling: ON")
    else:
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"  # force disable (qt6 only)
        logger.info("High DPI scaling: OFF")


def start_app(cli_args):
    """Init main window"""
    unset_environment()
    set_logging_level(logger, log_stream, cli_args.log_level)
    get_version()
    # load global config
    cfg.load_global()
    cfg.save(cfg_type=ConfigType.CONFIG)
    cfg.save(cfg_type=ConfigType.SHORTCUTS)
    set_environment()
    # Main GUI
    root = init_gui()
    single_instance_check(cli_args.single_instance)
    # Load core modules
    from . import loader
    loader.start()
    # Start mainloop
    sys.exit(root.exec_())
