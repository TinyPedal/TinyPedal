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
API connector
"""

from abc import ABC, abstractmethod
from functools import partial
from typing import NamedTuple

# Import APIs
from .adapter import (
    lmu_connector,
    lmu_reader,
    restapi_connector,
    rf2_connector,
    rf2_reader,
    rf2_restapi,
)
from .const_api import API_LMU_NAME, API_LMULEGACY_NAME, API_RF2_NAME
from .const_app import PLATFORM
from .validator import bytes_to_str


class APIDataSet(NamedTuple):
    """API data set"""

    state: rf2_reader.State
    brake: rf2_reader.Brake
    emotor: rf2_reader.ElectricMotor
    engine: rf2_reader.Engine
    inputs: rf2_reader.Inputs
    lap: rf2_reader.Lap
    session: rf2_reader.Session
    switch: rf2_reader.Switch
    timing: rf2_reader.Timing
    tyre: rf2_reader.Tyre
    vehicle: rf2_reader.Vehicle
    wheel: rf2_reader.Wheel


def set_dataset_rf2(shmm: rf2_connector.RF2Info, rest: restapi_connector.RestAPIInfo) -> APIDataSet:
    """Set API data set - RF2"""
    return APIDataSet(
        rf2_reader.State(shmm, rest),
        rf2_reader.Brake(shmm, rest),
        rf2_reader.ElectricMotor(shmm, rest),
        rf2_reader.Engine(shmm, rest),
        rf2_reader.Inputs(shmm, rest),
        rf2_reader.Lap(shmm, rest),
        rf2_reader.Session(shmm, rest),
        rf2_reader.Switch(shmm, rest),
        rf2_reader.Timing(shmm, rest),
        rf2_reader.Tyre(shmm, rest),
        rf2_reader.Vehicle(shmm, rest),
        rf2_reader.Wheel(shmm, rest),
    )


def set_dataset_lmu(shmm: lmu_connector.LMUInfo, rest: restapi_connector.RestAPIInfo) -> APIDataSet:
    """Set API data set - LMU"""
    return APIDataSet(
        lmu_reader.State(shmm, rest),
        lmu_reader.Brake(shmm, rest),
        lmu_reader.ElectricMotor(shmm, rest),
        lmu_reader.Engine(shmm, rest),
        lmu_reader.Inputs(shmm, rest),
        lmu_reader.Lap(shmm, rest),
        lmu_reader.Session(shmm, rest),
        lmu_reader.Switch(shmm, rest),
        lmu_reader.Timing(shmm, rest),
        lmu_reader.Tyre(shmm, rest),
        lmu_reader.Vehicle(shmm, rest),
        lmu_reader.Wheel(shmm, rest),
    )


class Connector(ABC):
    """API Connector"""

    __slots__ = ()

    @abstractmethod
    def start(self):
        """Start API & load info access function"""

    @abstractmethod
    def stop(self):
        """Stop API"""

    @abstractmethod
    def dataset(self) -> APIDataSet:
        """Dateset"""

    @abstractmethod
    def setup(self, config: dict):
        """Setup API parameters"""


class SimRF2(Connector):
    """rFactor 2"""

    __slots__ = (
        # Primary API
        "shmmapi",
        # Secondary API
        "restapi",
    )
    NAME = API_RF2_NAME

    def __init__(self):
        self.shmmapi = rf2_connector.RF2Info()
        self.restapi = restapi_connector.RestAPIInfo(rf2_restapi.TASKSET_RF2, rf2_restapi.RestAPIData())

    def start(self):
        self.shmmapi.start()  # 1 load first
        self.restapi.start()  # 2

    def stop(self):
        self.restapi.stop()  # 1 unload first
        self.shmmapi.stop()  # 2

    def dataset(self) -> APIDataSet:
        return set_dataset_rf2(self.shmmapi, self.restapi)

    def setup(self, config: dict):
        self.shmmapi.setMode(config["access_mode"])
        self.shmmapi.setPID(config["process_id"])
        self.shmmapi.setStateOverride(config["enable_active_state_override"])
        self.shmmapi.setActiveState(config["active_state"])
        self.shmmapi.setPlayerOverride(config["enable_player_index_override"])
        self.shmmapi.setPlayerIndex(config["player_index"])
        self.restapi.setConnection(config.copy())
        rf2_reader.tostr = partial(bytes_to_str, char_encoding=config["character_encoding"].lower())


class SimLMU(Connector):
    """Le Mans Ultimate"""

    __slots__ = (
        # Primary API
        "shmmapi",
        # Secondary API
        "restapi",
    )
    NAME = API_LMU_NAME

    def __init__(self):
        self.shmmapi = lmu_connector.LMUInfo()
        self.restapi = restapi_connector.RestAPIInfo(rf2_restapi.TASKSET_LMU, rf2_restapi.RestAPIData())

    def start(self):
        self.shmmapi.start()  # 1 load first
        self.restapi.start()  # 2

    def stop(self):
        self.restapi.stop()  # 1 unload first
        self.shmmapi.stop()  # 2

    def dataset(self) -> APIDataSet:
        return set_dataset_lmu(self.shmmapi, self.restapi)

    def setup(self, config: dict):
        self.shmmapi.setMode(config["access_mode"])
        self.shmmapi.setStateOverride(config["enable_active_state_override"])
        self.shmmapi.setActiveState(config["active_state"])
        self.shmmapi.setPlayerOverride(config["enable_player_index_override"])
        self.shmmapi.setPlayerIndex(config["player_index"])
        self.restapi.setConnection(config.copy())
        lmu_reader.tostr = partial(bytes_to_str, char_encoding=config["character_encoding"].lower())


class SimLMULegacy(Connector):
    """Le Mans Ultimate (legacy)

    Use RF2 Sharedmemory Plugin if LMU native Sharedmemory API not accessible
    """

    __slots__ = (
        # Primary API
        "shmmapi",
        # Secondary API
        "restapi",
    )
    NAME = API_LMULEGACY_NAME

    def __init__(self):
        self.shmmapi = rf2_connector.RF2Info()
        self.restapi = restapi_connector.RestAPIInfo(rf2_restapi.TASKSET_LMU, rf2_restapi.RestAPIData())

    def start(self):
        self.shmmapi.start()  # 1 load first
        self.restapi.start()  # 2

    def stop(self):
        self.restapi.stop()  # 1 unload first
        self.shmmapi.stop()  # 2

    def dataset(self) -> APIDataSet:
        return set_dataset_rf2(self.shmmapi, self.restapi)

    def setup(self, config: dict):
        self.shmmapi.setMode(config["access_mode"])
        self.shmmapi.setStateOverride(config["enable_active_state_override"])
        self.shmmapi.setActiveState(config["active_state"])
        self.shmmapi.setPlayerOverride(config["enable_player_index_override"])
        self.shmmapi.setPlayerIndex(config["player_index"])
        self.restapi.setConnection(config.copy())
        rf2_reader.tostr = partial(bytes_to_str, char_encoding=config["character_encoding"].lower())


def _set_available_api():
    """Set available API for specific platform"""
    platform_all = (
        SimLMULegacy,
        SimRF2,
    )
    platform_win = (
        SimLMU,
    )
    if PLATFORM == "Windows":
        platform_all += platform_win
    # Sort API by name
    return tuple(sorted((_api for _api in platform_all), key=lambda cls:cls.NAME))


API_PACK = _set_available_api()
