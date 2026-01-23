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
API control
"""

import logging

from . import api_connector, realtime_state
from .const_app import PLATFORM
from .setting import cfg

logger = logging.getLogger(__name__)


def _set_available_api():
    """Set available API for specific platform"""
    enable_legacy = cfg.telemetry["enable_legacy_api_selection"]
    if PLATFORM == "Windows":
        available_api = (
            (api_connector.SimLMU, False),  # API, is legacy
            (api_connector.SimLMULegacy, not enable_legacy),
            (api_connector.SimRF2, False),
        )
    else:
        available_api = (
            (api_connector.SimLMULegacy, not enable_legacy),
            (api_connector.SimRF2, False),
        )
    # Sort API by name
    api_gen = (_api for _api, _legacy in available_api if not _legacy)
    return tuple(sorted(api_gen, key=lambda cls:cls.NAME))


class APIControl:
    """API Control"""

    __slots__ = (
        "_api",
        "_available_api",
        "_same_api_loaded",
        "read",
    )

    def __init__(self):
        self._api = None
        self._available_api = _set_available_api()
        self._same_api_loaded = False
        self.read = None

    def connect(self, name: str = ""):
        """Connect to API

        Args:
            name: API full name
        """
        if not name:
            name = cfg.api_name

        # Do not create new instance if same API already loaded
        self._same_api_loaded = bool(self._api is not None and self._api.NAME == name)
        if self._same_api_loaded:
            logger.info("CONNECTING: same API detected, fast restarting")
            return

        for _api in self._available_api:
            if _api.NAME == name:
                self._api = _api()
                return

        logger.warning("CONNECTING: Invalid API name, fall back to default")
        self._api = self._available_api[0]()
        cfg.api_name = self._api.NAME

    def start(self):
        """Start API"""
        logger.info("CONNECTING: %s API", self._api.NAME)
        self.setup()
        self._api.start()

        # Reload dataset if API changed
        if self.read is None or not self._same_api_loaded:
            init_read = self._api.reader()
            self.read = init_read
            self._same_api_loaded = True

        logger.info("ENCODING: %s", cfg.api["character_encoding"])
        logger.info("CONNECTED: %s API (%s)", self._api.NAME, self.read.state.version())

    def stop(self):
        """Stop API"""
        logger.info("DISCONNECTING: %s API (%s)", self._api.NAME, self.read.state.version())
        self._api.stop()
        logger.info("DISCONNECTED: %s API", self._api.NAME)

    def restart(self):
        """Restart API"""
        self.stop()
        self.connect()
        self.start()

    def setup(self):
        """Setup & apply API changes"""
        setting_api = cfg.api
        realtime_state.overriding = setting_api["enable_active_state_override"]
        realtime_state.spectating = setting_api["enable_player_index_override"]
        self._api.setup(setting_api)

    @property
    def available(self):
        """Available API"""
        return self._available_api

    @property
    def name(self) -> str:
        """API full name output"""
        return self._api.NAME


api = APIControl()
