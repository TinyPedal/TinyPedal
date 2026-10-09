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
Global variable, function

Important: DO NOT call those functions in non-main thread.
"""

from __future__ import annotations

import io
import logging
import os
import sys
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .api_control import APIControl
    from .configuration import Configuration
    from .hotkey_control import HotkeyControl
    from .module_control import ModuleControl
    from .module_info import ModuleInfo
    from .overlay_control import OverlayControl
    from .state import ApplicationSignal, OverlaySignal, RealtimeState
    from .update import UpdateChecker


# Create root logger
logger = logging.getLogger(__package__)

# Global state & signal
realtime_state: RealtimeState = None  # type: ignore
overlay_signal: OverlaySignal = None  # type: ignore
app_signal: ApplicationSignal = None  # type: ignore

# Global singleton (init later)
log_stream: io.StringIO = None  # type: ignore
cfg: Configuration = None  # type: ignore
api: APIControl = None  # type: ignore
minfo: ModuleInfo = None  # type: ignore
mctrl: ModuleControl = None  # type: ignore
wctrl: ModuleControl = None  # type: ignore
kctrl: HotkeyControl = None  # type: ignore
octrl: OverlayControl = None  # type: ignore
updater: UpdateChecker = None  # type: ignore


# Public function
def start(single_instance: bool, log_level: int):
    """Launch check & start app"""
    # Set log stream
    global log_stream
    if log_stream:  # one time init only
        raise RuntimeError("launch check already done")
    log_stream = io.StringIO()

    # Set global path
    from . import paths
    path_global = paths.global_config_path()

    # Config logger
    from .constant import APP, FILE
    from .log_handler import set_logging_level
    set_logging_level(logger, path_global, FILE.LOG_APP, log_stream, log_level)

    # Check single instance
    logger.info("Single instance mode: %s", "ON" if single_instance else "OFF")
    _check_single_instance(single_instance, path_global, FILE.LOG_PID)

    # Check app & library version
    from . import version_check
    logger.info("TinyPedal: %s", APP.VERSION)
    logger.info("Python: %s", version_check.python())
    logger.info("Qt: %s", version_check.qt())
    logger.info("PySide: %s", version_check.pyside())
    logger.info("psutil: %s", version_check.psutil())

    # Init global variable
    _init_globals(single_instance, path_global)

    # Init app
    _init_app()


def close():
    """Close api, modules (call before quit APP)"""
    logger.info("CLOSING............")
    # Unload modules
    _unload_modules()
    # Stop & close api
    api.stop()
    api.close()


def restart():
    """Restart APP"""
    logger.info("RESTARTING............")
    # Wait unfinished saving
    if cfg.is_saving:
        # Trigger immediate saving from queue
        cfg.save(next_task=True)
        while cfg.is_saving:
            time.sleep(0.01)
    # Close modules
    close()
    # Set restart env for skipping single instance check
    os.environ["TINYPEDAL_RESTART"] = "TRUE"
    # Restart
    if os.getenv("RUN_FROM_SOURCE"):  # run as script
        os.execl(sys.executable, sys.executable, *sys.argv)
    else:  # run as exe
        os.execl(sys.executable, *sys.argv)


def reload(reload_preset: bool = False):
    """Reload preset, api, modules

    Args:
        reload_preset:
            Whether to reload preset file.
            Should only done if changed global setting,
            or reloading from preset tab,
            or auto-loading preset.
    """
    logger.info("RELOADING............")
    # Wait unfinished saving
    if cfg.is_saving:
        # Trigger immediate saving from queue
        cfg.save(next_task=True)
        while cfg.is_saving:
            time.sleep(0.01)
    # Unload modules
    _unload_modules()
    # Reload user preset from file
    if reload_preset:
        cfg.load_user()
        cfg.save(0)  # save new changes in case preset file modified externally
    # Restart api
    api.restart()
    # Load modules
    _load_modules()


# Private function
def _init_globals(single_instance: bool, path_global: str):
    """Initialize global singleton (in order), once only after launch check done"""
    # Config
    global cfg
    if cfg:  # one time init only
        raise RuntimeError("global singleton already initialized")
    from .configuration import Configuration
    cfg = Configuration()

    # Load global config & set environment
    from .constant import CONFIG
    cfg.path.config = path_global
    cfg.load_global()
    cfg.save(config_type=CONFIG.TYPE_CONFIG)
    cfg.save(config_type=CONFIG.TYPE_SHORTCUTS)
    _clear_environment()
    _update_environment()

    # State & signal
    global realtime_state, overlay_signal, app_signal
    from .state import ApplicationSignal, OverlaySignal, RealtimeState
    realtime_state = RealtimeState()
    overlay_signal = OverlaySignal()
    app_signal = ApplicationSignal()
    realtime_state.singleton = single_instance

    # API
    global api
    from .api_control import APIControl
    api = APIControl()

    # Module data
    global minfo
    from .module_info import ModuleInfo
    minfo = ModuleInfo()

    # Module, widget control
    global mctrl, wctrl
    from . import module, widget
    from .constant import CONFIG
    from .module_control import ModuleControl
    mctrl = ModuleControl(target=module, type_id=CONFIG.TYPE_MODULE)
    wctrl = ModuleControl(target=widget, type_id=CONFIG.TYPE_WIDGET)

    # Hotkey control
    global kctrl
    from .hotkey_control import HotkeyControl
    kctrl = HotkeyControl()

    # Overlay control
    global octrl
    from .overlay_control import OverlayControl
    octrl = OverlayControl()

    # Update checker
    global updater
    from .update import UpdateChecker
    updater = UpdateChecker()


def _init_app():
    """Initialize gui, api, modules (once per launch)"""
    logger.info("STARTING............")
    # Init core GUI
    from . import ui
    if ui.QApplication.instance():
        raise RuntimeError("core GUI already initialized")
    root = ui.init(cfg.application["enable_high_dpi_scaling"])

    # Load user preset
    cfg.set_next_to_load()
    cfg.load_user()
    cfg.save()

    # Start api
    api.connect()
    api.start()

    # Start main window
    from .ui import app
    app.AppWindow()

    # Finalize loading after main GUI fully loaded
    logger.info("FINALIZING............")

    # Start modules
    _load_modules()

    # Check for updates
    if cfg.application["check_for_updates_on_startup"]:
        updater.check(False)

    # Refresh main GUI
    app_signal.refresh.emit(True)

    # Start main loop
    sys.exit(root.exec_())


def _load_modules():
    """Load modules (in order)"""
    mctrl.start()
    wctrl.start()
    kctrl.enable()
    octrl.enable()


def _unload_modules():
    """Unload modules (in order)"""
    octrl.disable()
    kctrl.disable()
    wctrl.close()
    mctrl.close()


def _save_pid_file(filepath: str, filename: str):
    """Save PID info to file"""
    import psutil
    with open(f"{filepath}{filename}", "w", encoding="utf-8") as f:
        current_pid = os.getpid()
        pid_create_time = psutil.Process(current_pid).create_time()
        pid_str = f"{current_pid},{pid_create_time}"
        f.write(pid_str)


def _is_pid_exist(filepath: str, filename: str) -> bool:
    """Check and verify PID existence"""
    import psutil
    try:
        # Load last recorded PID and creation time from pid log file
        with open(f"{filepath}{filename}", "r", encoding="utf-8") as f:
            pid_read = f.readline()
        pid = pid_read.split(",")
        pid_last = int(pid[0])
        pid_last_create_time = pid[1]
        # Verify if last PID is running and belongs to TinyPedal
        if psutil.pid_exists(pid_last) and str(psutil.Process(pid_last).create_time()) == pid_last_create_time:
            return True  # already running
    except (ProcessLookupError, psutil.NoSuchProcess, ValueError, IndexError, FileNotFoundError):
        logger.info("PID not found or invalid")
    return False  # no running


def _check_single_instance(single_mode: bool, filepath: str, filename: str):
    """Check single instance, True=passed check, False=failed check"""
    # Multi-instance mode enabled
    if not single_mode:
        return
    # Skip if restarted
    if os.getenv("TINYPEDAL_RESTART"):
        os.environ.pop("TINYPEDAL_RESTART", None)
        _save_pid_file(filepath, filename)
        return
    # Check existing PID file
    if not _is_pid_exist(filepath, filename):
        _save_pid_file(filepath, filename)
        return
    # Cancel & quit
    from . import ui

    message = (
        "TinyPedal is already running.\n\n"
        "Only one TinyPedal may be run at a time.\n"
        "Check system tray for hidden icon."
    )
    ui.cancel(message)


def _clear_environment():
    """Clear any previous environment variable (required after auto-restarted APP)"""
    os.environ.pop("QT_QPA_PLATFORM", None)
    os.environ.pop("QT_ENABLE_HIGHDPI_SCALING", None)
    os.environ.pop("QT_MEDIA_BACKEND", None)
    os.environ.pop("QT_MULTIMEDIA_PREFERRED_PLUGINS", None)


def _update_environment():
    """Update environment before starting GUI"""
    from .constant import PLATFORM
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
