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
import sys
import time

from . import api, app_signal, cfg, kctrl, mctrl, octrl, updater, wctrl
from .constant import FILE

logger = logging.getLogger(__name__)


def init():
    """Initialize gui, api, modules (once per launch)"""
    logger.info("STARTING............")
    # 1 init core GUI
    from . import ui
    if ui.QApplication.instance():
        raise RuntimeError("core GUI already initialized")
    root = ui.init(cfg.application["enable_high_dpi_scaling"])
    # 2 load user preset
    cfg.set_next_to_load(f"{cfg.preset_files()[0]}{FILE.EXT_JSON}")
    cfg.load_user()
    cfg.save()
    # 3 start api
    api.connect()
    api.start()
    # 4 start main window
    from .ui import app
    app.AppWindow()

    # Finalize loading after main GUI fully loaded
    logger.info("FINALIZING............")
    # 1 start modules
    load_modules()
    # 2 Check for updates
    if cfg.application["check_for_updates_on_startup"]:
        updater.check(False)
    # 3 Refresh GUI
    app_signal.refresh.emit(True)

    # Start main loop
    sys.exit(root.exec_())


def close():
    """Close api, modules (call before quit APP)"""
    logger.info("CLOSING............")
    # 1 unload modules
    unload_modules()
    # 2 stop & close api
    api.stop()
    api.close()


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
    """Reload preset, api, modules

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
    """Load modules (in order)"""
    mctrl.start()
    wctrl.start()
    kctrl.enable()
    octrl.enable()


def unload_modules():
    """Unload modules (in order)"""
    octrl.disable()
    kctrl.disable()
    wctrl.close()
    mctrl.close()
