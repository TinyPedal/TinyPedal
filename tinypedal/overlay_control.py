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
Overlay Control
"""

import logging
import threading
from time import sleep

from . import overlay_signal, realtime_state
from .api_control import api
from .setting import cfg

logger = logging.getLogger(__name__)


class OverlayToggle:
    """Overlay state toggle"""

    __slots__ = ()

    def vr(self):
        """Toggle VR state"""
        self.__toggle_option("vr_compatibility")
        overlay_signal.iconify.emit(cfg.overlay["vr_compatibility"])

    def lock(self):
        """Toggle lock state"""
        self.__toggle_option("fixed_position")
        overlay_signal.locked.emit(cfg.overlay["fixed_position"])

    def hide(self):
        """Toggle hide state"""
        self.__toggle_option("auto_hide")

    def grid(self):
        """Toggle grid move state"""
        self.__toggle_option("enable_grid_move")

    @staticmethod
    def __toggle_option(option_name: str):
        """Toggle option"""
        cfg.overlay[option_name] = not cfg.overlay[option_name]
        cfg.save()


class OverlayControl:
    """Overlay control"""

    __slots__ = (
        "toggle",
        "_stopped",
        "_event",
        "_last_detected_sim",
        "_last_active_state",
        "_last_hide_state",
    )

    def __init__(self):
        self.toggle = OverlayToggle()
        self._stopped = True
        self._event = threading.Event()

        self._last_detected_sim = None
        self._last_active_state = None
        self._last_hide_state = None

    def enable(self):
        """Enable overlay control"""
        if self._stopped:
            self._stopped = False
            self._event.clear()
            threading.Thread(target=self.__updating, daemon=True).start()
            logger.info("ENABLED: overlay control")

    def disable(self):
        """Disable overlay control"""
        self._event.set()
        while not self._stopped:
            sleep(0.01)

    def __updating(self):
        """Update global state"""
        _event_wait = self._event.wait
        while not _event_wait(0.2):
            # Read state
            active = api.read.state.active()
            paused = api.read.state.paused()
            # Update state
            realtime_state.active = active
            realtime_state.paused = paused
            # Auto hide state check
            hide_state = cfg.overlay["auto_hide"] and not active
            if self._last_hide_state != hide_state:
                self._last_hide_state = hide_state
                overlay_signal.hidden.emit(hide_state)
            # Active state check
            if self._last_active_state != active:
                self._last_active_state = active
                # Update auto load state only once when player enters track
                if active and cfg.application["enable_auto_load_preset"]:
                    if not self.__check_preset_class():
                        self.__check_preset_sim()
                # Set overlay timer state
                overlay_signal.paused.emit(not active)

        self._stopped = True
        logger.info("DISABLED: overlay control")

    def __check_preset_class(self) -> bool:
        """Check primary preset from class"""
        class_name = api.read.vehicle.class_name()
        class_data = cfg.user.classes.get(class_name)
        if class_data is None:
            return False
        class_preset_name = class_data["preset"]
        if class_preset_name == "":
            return False
        preset_name = cfg.get_primary_preset_name(class_preset_name)
        self.__auto_load_preset(class_name, preset_name)
        return True

    def __check_preset_sim(self) -> bool:
        """Check primary preset from sim"""
        # Get sim_name, returns "" if no game running
        sim_name = api.read.state.identifier()
        # Abort if game not found
        if not sim_name:
            self._last_detected_sim = None
            return False
        # Abort if same as last found game
        if sim_name == self._last_detected_sim:
            return True
        # Assign sim name to last detected, set preset name
        self._last_detected_sim = sim_name
        preset_name = cfg.get_primary_preset_name(cfg.primary_preset.get(sim_name, ""))
        self.__auto_load_preset(sim_name, preset_name)
        return True

    def __auto_load_preset(self, target_name, preset_name):
        """Auto load primary preset"""
        logger.info("AUTOLOADING: %s detected, attempt loading %s (primary preset)", target_name, preset_name)
        # Abort if preset file does not exist
        if preset_name == "":
            logger.info("AUTOLOADING: %s (primary preset) not found, abort auto loading", preset_name)
            return
        # Check if already loaded
        if cfg.is_loaded(preset_name):
            logger.info("AUTOLOADING: %s (primary preset) already loaded", preset_name)
            return
        # Update preset name & signal reload
        cfg.set_next_to_load(preset_name)
        overlay_signal.reload.emit(True)


octrl = OverlayControl()
