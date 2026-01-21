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
Hotkey Control
"""

from __future__ import annotations

import logging
import threading
from time import sleep

from .hotkey.command import COMMANDS_HOTKEY
from .hotkey.common import get_key_state_function, load_hotkey, refresh_keystate
from .setting import cfg

logger = logging.getLogger(__name__)


class HotkeyControl:
    """Hotkey control"""

    __slots__ = (
        "_stopped",
        "_event",
    )

    def __init__(self):
        self._stopped = True
        self._event = threading.Event()

    def enable(self):
        """Enable hotkey control"""
        if self._stopped and cfg.application["enable_global_hotkey"]:
            self._stopped = False
            self._event.clear()
            threading.Thread(target=self.__updating, daemon=True).start()
            logger.info("ENABLED: hotkey control")

    def disable(self):
        """Disable hotkey control"""
        self._event.set()
        while not self._stopped:
            sleep(0.01)

    def reload(self):
        """Reload"""
        self.disable()
        self.enable()

    def __gather_command(self):
        """Gather & validate hotkey commands"""
        for hotkey_name, hotkey_func in COMMANDS_HOTKEY:
            key_string = cfg.user.shortcuts[hotkey_name]["bind"]
            key_codes = load_hotkey(key_string)
            if key_codes:
                yield key_codes, hotkey_name, hotkey_func

    def __updating(self):
        """Update hotkey state"""
        _event_wait = self._event.wait
        commands = tuple(self.__gather_command())
        get_key_state = get_key_state_function()
        refresh_keystate(get_key_state)

        while not _event_wait(0.2):
            # Close & disable if no commands
            if not commands:
                break
            # Run command
            for key_codes, hotkey_name, hotkey_func in commands:
                if min(get_key_state(code) != 0 for code in key_codes):
                    hotkey_func()
                    logger.info(
                        "HOTKEY: %s (command: %s)",
                        cfg.user.shortcuts[hotkey_name]["bind"],
                        hotkey_name,
                    )

        self._stopped = True
        logger.info("DISABLED: hotkey control")


kctrl = HotkeyControl()
