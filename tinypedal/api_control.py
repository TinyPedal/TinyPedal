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

from __future__ import annotations

import logging

from . import adapter, cfg, realtime_state
from .constant import API

logger = logging.getLogger(__name__)


def _get_available_api(enable_legacy: bool):
    """Get available API"""
    return {
        _api.NAME: _api
        for _api in (
            adapter.SimACC,
            adapter.SimLMU,
            adapter.SimLMULegacy,
            adapter.SimRF2,
        )
        if not _api.LEGACY or enable_legacy
    }


class APIControl:
    """API Control"""

    __slots__ = (
        "_api",
        "_available_api",
        "_enable_legacy",
        "_same_api_loaded",
        "read",
    )

    def __init__(self):
        self._api: adapter.Connector = None  # type: ignore
        self._available_api = {}
        self._enable_legacy = False
        self._same_api_loaded = False
        self.read: adapter.APIDataReader = None  # type: ignore

    def connect(self, name: str = ""):
        """Connect to API

        Args:
            name: API full name
        """
        if not name:
            name = cfg.selected_api

        enable_legacy = cfg.telemetry["enable_legacy_api_selection"]
        if not self._available_api or self._enable_legacy != enable_legacy:
            self._enable_legacy = enable_legacy
            self._available_api = _get_available_api(enable_legacy)
            self._same_api_loaded = False
        else:
            # Do not create new instance if same API already loaded
            self._same_api_loaded = bool(self._api is not None and self._api.NAME == name)

        if self._same_api_loaded:
            logger.info("CONNECTING: same API detected, fast restarting")
            return

        _api = self._available_api.get(name)
        if _api is not None:
            self._api = _api()
            return

        logger.warning("CONNECTING: Invalid API name, fall back to default")
        self._api = self._available_api[API.NAME_LMU]
        cfg.selected_api = self._api.NAME

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

    def close(self):
        """Close & dereference API"""
        if self._api:
            self._api.close()
        for var in self.__slots__:
            setattr(self, var, None)

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
    def available(self) -> tuple[str, ...]:
        """Available API name list"""
        return tuple(self._available_api)

    @property
    def name(self) -> str:
        """API full name"""
        return self._api.NAME

    @property
    def alias(self) -> str:
        """API alias name"""
        return API.MAP_ALIAS[self._api.NAME]
