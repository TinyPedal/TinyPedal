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
Loader function

Important: DO NOT call those functions in non-main thread.
"""

import logging
import os
import signal
import sys
import time

from .api_control import api
from .constant import CONFIG, FILE, PLATFORM
from .hotkey_control import kctrl
from .module_control import mctrl, wctrl
from .overlay_control import octrl
from .setting import cfg
from .update import update_checker

logger = logging.getLogger(__name__)


def int_signal_handler(sign, frame):
    """Quit by keyboard interrupt"""
    close()
    sys.exit()


def clear_environment():
    """Clear any previous environment variable (required after auto-restarted APP)"""
    os.environ.pop("QT_QPA_PLATFORM", None)
    os.environ.pop("QT_ENABLE_HIGHDPI_SCALING", None)
    os.environ.pop("QT_MEDIA_BACKEND", None)
    os.environ.pop("QT_MULTIMEDIA_PREFERRED_PLUGINS", None)


def update_environment():
    """Update environment before starting GUI"""
    # Windows only
    if PLATFORM.WINDOWS:
        if os.getenv("PYSIDE_OVERRIDE") == "6":
            # Use "freetype" to avoid high memory usage in pyside6
            # Match system dark-mode on windows
            os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2:fontengine=freetype"
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
    if not cfg.application["enable_high_dpi_scaling"]:
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"  # force disable (qt6 only)


def start(path_global: str):
    """Initializing (once per launch)"""
    signal.signal(signal.SIGINT, int_signal_handler)

    # Load global config
    cfg.path.config = path_global
    cfg.load_global()
    cfg.save(config_type=CONFIG.TYPE_CONFIG)
    cfg.save(config_type=CONFIG.TYPE_SHORTCUTS)

    # Config environment
    clear_environment()
    update_environment()

    # Load core GUI
    from . import ui
    root = ui.init(cfg.application["enable_high_dpi_scaling"])

    # Start api, modules, widgets, main window in order
    logger.info("STARTING............")
    # 1 load user preset
    cfg.set_next_to_load(f"{cfg.preset_files()[0]}{FILE.EXT_JSON}")
    cfg.load_user()
    cfg.save()
    # 2 start api
    api.connect()
    api.start()
    # 3 start modules
    mctrl.start()
    # 4 start widgets
    wctrl.start()
    # 5 start main window
    from .ui import app
    app.AppWindow()

    # Finalize loading after main GUI fully loaded
    logger.info("FINALIZING............")
    # 1 Enable overlay control
    octrl.enable()
    # 2 Enable hotkey control
    kctrl.enable()
    # 3 Check for updates
    if cfg.application["check_for_updates_on_startup"]:
        update_checker.check(False)

    # Start main loop
    sys.exit(root.exec_())


def close():
    """Close api, modules, widgets. Call before quit APP."""
    logger.info("CLOSING............")
    # 1 unload modules
    unload_modules()
    # 2 stop & close api
    api.stop()
    api.close()
    logger.info("API: closed")


def restart():
    """Restart APP"""
    logger.info("RESTARTING............")
    # 0 must close first
    close()
    # 1 wait unfinished saving
    if cfg.is_saving:
        # Trigger immediate saving from queue
        cfg.save(next_task=True)
        while cfg.is_saving:
            time.sleep(0.01)
    # 2 set restart env for skipping single instance check
    os.environ["TINYPEDAL_RESTART"] = "TRUE"
    # 3 restart
    if os.getenv("RUN_FROM_SOURCE"):  # run as script
        os.execl(sys.executable, sys.executable, *sys.argv)
    else:  # run as exe
        os.execl(sys.executable, *sys.argv)


def reload(reload_preset: bool = False):
    """Reload preset, api, modules, widgets

    Args:
        reload_preset:
            Whether to reload preset file.
            Should only done if changed global setting,
            or reloading from preset tab,
            or auto-loading preset.
    """
    logger.info("RELOADING............")
    # 0 wait unfinished saving
    if cfg.is_saving:
        # Trigger immediate saving from queue
        cfg.save(next_task=True)
        while cfg.is_saving:
            time.sleep(0.01)
    # 1 unload modules
    unload_modules()
    # 2 reload user preset from file
    if reload_preset:
        cfg.load_user()
        cfg.save(0)  # save new changes in case preset was edited externally
    # 3 restart api
    api.restart()
    # 4 load modules
    load_modules()


def load_modules():
    """Load modules, widgets"""
    octrl.enable()  # 1 overlay control
    mctrl.start()  # 2 module
    wctrl.start()  # 3 widget
    kctrl.enable()  # 4 hotkey


def unload_modules():
    """Unload modules, widgets"""
    kctrl.disable()  # 1 hotkey
    wctrl.close()  # 2 widget
    mctrl.close()  # 3 module
    octrl.disable()  # 4 overlay control
