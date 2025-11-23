#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2025 TinyPedal developers, see contributors.md file
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
Data module base
"""

import logging
import threading
from functools import partial

from ..setting import Setting

logger = logging.getLogger(__name__)
# Function
round4 = partial(round, ndigits=4)
round6 = partial(round, ndigits=6)


class DataModule:
    """Data module base"""

    __slots__ = (
        "module_name",
        "closed",
        "cfg",
        "mcfg",
        "active_interval",
        "idle_interval",
        "_event",
    )

    def __init__(self, config: Setting, module_name: str):
        self.module_name = module_name
        self.closed = True

        # Base config
        self.cfg = config

        # Module config
        self.mcfg: dict = self.cfg.user.setting[module_name]

        # Module update interval
        self._event = threading.Event()
        self.active_interval = max(
            self.mcfg["update_interval"],
            self.cfg.application["minimum_update_interval"]) / 1000
        self.idle_interval = max(
            self.active_interval,
            self.mcfg["idle_update_interval"],
            self.cfg.application["minimum_update_interval"]) / 1000

    def start(self):
        """Start update thread"""
        if self.closed:
            self.closed = False
            self._event.clear()
            threading.Thread(target=self.__tasks, daemon=True).start()
            logger.info("ENABLED: %s", self.module_name.replace("_", " "))

    def stop(self):
        """Stop update thread"""
        self._event.set()

    def update_data(self):
        """Update module data, rewrite in child class"""

    def __tasks(self):
        """Run tasks in separated thread"""
        self.update_data()
        # Wait update_data exit
        self.closed = True
        logger.info("DISABLED: %s", self.module_name.replace("_", " "))
