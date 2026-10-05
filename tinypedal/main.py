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

import argparse
import io
import logging
import os

import psutil

from . import realtime_state, version_check
from .constant import APP, FILE
from .log_handler import set_logging_level
from .userpath import set_global_config_path

logger = logging.getLogger(__package__)
log_stream = io.StringIO()


def save_pid_file(filepath: str, filename: str):
    """Save PID info to file"""
    with open(f"{filepath}{filename}", "w", encoding="utf-8") as f:
        current_pid = os.getpid()
        pid_create_time = psutil.Process(current_pid).create_time()
        pid_str = f"{current_pid},{pid_create_time}"
        f.write(pid_str)


def is_pid_exist(filepath: str, filename: str) -> bool:
    """Check and verify PID existence"""
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


def check_single_instance(single_mode: bool, filepath: str, filename: str):
    """Check single instance, True=passed check, False=failed check"""
    # Multi-instance mode enabled
    if not single_mode:
        return
    # Skip if restarted
    if os.getenv("TINYPEDAL_RESTART"):
        os.environ.pop("TINYPEDAL_RESTART", None)
        save_pid_file(filepath, filename)
        return
    # Check existing PID file
    if not is_pid_exist(filepath, filename):
        save_pid_file(filepath, filename)
        return
    # Cancel & quit
    from . import ui

    message = (
        "TinyPedal is already running.\n\n"
        "Only one TinyPedal may be run at a time.\n"
        "Check system tray for hidden icon."
    )
    ui.cancel(message)


def check_version_info():
    """Check app & library version info"""
    logger.info("TinyPedal: %s", APP.VERSION)
    logger.info("Python: %s", version_check.python())
    logger.info("Qt: %s", version_check.qt())
    logger.info("PySide: %s", version_check.pyside())
    logger.info("psutil: %s", version_check.psutil())


def start_app(cli_args: argparse.Namespace):
    """Init main window"""
    # Set global path
    path_global = set_global_config_path()

    # Initialize logger
    set_logging_level(logger, path_global, FILE.LOG_APP, log_stream, cli_args.log_level)

    # Check single instance
    realtime_state.singleton = bool(cli_args.single_instance)
    logger.info("Single instance mode: %s", "ON" if realtime_state.singleton else "OFF")
    check_single_instance(realtime_state.singleton, path_global, FILE.LOG_PID)

    # Check versions
    check_version_info()

    # Start app
    from . import loader

    loader.start(path_global)
