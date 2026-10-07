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
Global variable
"""

from __future__ import annotations

import io
import logging
import os
from typing import TYPE_CHECKING

from . import state

if TYPE_CHECKING:
    from .api_control import APIControl
    from .hotkey_control import HotkeyControl
    from .module_control import ModuleControl
    from .module_info import ModuleInfo
    from .overlay_control import OverlayControl
    from .setting import Setting
    from .update import UpdateChecker


# Create root logger
logger = logging.getLogger(__package__)

# Global state & signal
realtime_state = state.RealtimeState()
overlay_signal = state.OverlaySignal()
app_signal = state.ApplicationSignal()

# Global singleton (init later)
log_stream: io.StringIO = None  # type: ignore
cfg: Setting = None  # type: ignore
api: APIControl = None  # type: ignore
minfo: ModuleInfo = None  # type: ignore
mctrl: ModuleControl = None  # type: ignore
wctrl: ModuleControl = None  # type: ignore
kctrl: HotkeyControl = None  # type: ignore
octrl: OverlayControl = None  # type: ignore
updater: UpdateChecker = None  # type: ignore


def start(single_instance: bool, log_level: int):
    """Launch check & start app"""
    # Set log stream
    global log_stream
    if log_stream is not None:  # one time init only
        return
    log_stream = io.StringIO()

    # Set global path
    from . import paths
    path_global = paths.global_config_path()

    # Config logger
    from .constant import APP, FILE
    from .log_handler import set_logging_level
    set_logging_level(logger, path_global, FILE.LOG_APP, log_stream, log_level)

    # Check single instance
    from . import realtime_state
    realtime_state.singleton = single_instance
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
    _init_globals()

    # Start app
    from . import loader
    loader.start(path_global)


def _init_globals():
    """Initialize global singleton (in order), once only after launch check done"""
    # 1 config
    global cfg
    if cfg is not None:  # one time init only
        return
    from .setting import Setting
    cfg = Setting()

    # 2 api
    global api
    from .api_control import APIControl
    api = APIControl()

    # 3 module data
    global minfo
    from .module_info import ModuleInfo
    minfo = ModuleInfo()

    # 4 module, widget control
    global mctrl, wctrl
    from . import module, widget
    from .constant import CONFIG
    from .module_control import ModuleControl
    mctrl = ModuleControl(target=module, type_id=CONFIG.TYPE_MODULE)
    wctrl = ModuleControl(target=widget, type_id=CONFIG.TYPE_WIDGET)

    # 5 hotkey control
    global kctrl
    from .hotkey_control import HotkeyControl
    kctrl = HotkeyControl()

    # 6 overlay control
    global octrl
    from .overlay_control import OverlayControl
    octrl = OverlayControl()

    # 7 update checker
    global updater
    from .update import UpdateChecker
    updater = UpdateChecker()


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
