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
API connector
"""

from abc import ABC, abstractmethod
from functools import partial
from typing import NamedTuple

# Import APIs
from .adapter import restapi_connector, rf2_connector, rf2_data
from .regex_pattern import API_NAME_LMU, API_NAME_RF2
from .validator import bytes_to_str


class APIDataSet(NamedTuple):
    """API data set"""

    state: rf2_data.State
    brake: rf2_data.Brake
    emotor: rf2_data.ElectricMotor
    engine: rf2_data.Engine
    inputs: rf2_data.Inputs
    lap: rf2_data.Lap
    session: rf2_data.Session
    switch: rf2_data.Switch
    timing: rf2_data.Timing
    tyre: rf2_data.Tyre
    vehicle: rf2_data.Vehicle
    wheel: rf2_data.Wheel


def set_dataset_rf2(shmm: rf2_connector.RF2Info, rest: restapi_connector.RestAPIInfo) -> APIDataSet:
    """Set API data set - RF2"""
    return APIDataSet(
        rf2_data.State(shmm, rest),
        rf2_data.Brake(shmm, rest),
        rf2_data.ElectricMotor(shmm, rest),
        rf2_data.Engine(shmm, rest),
        rf2_data.Inputs(shmm, rest),
        rf2_data.Lap(shmm, rest),
        rf2_data.Session(shmm, rest),
        rf2_data.Switch(shmm, rest),
        rf2_data.Timing(shmm, rest),
        rf2_data.Tyre(shmm, rest),
        rf2_data.Vehicle(shmm, rest),
        rf2_data.Wheel(shmm, rest),
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
        "shmmapi",  # shared memory API
        "restapi",  # Rest API
    )
    NAME = API_NAME_RF2

    def __init__(self):
        self.shmmapi = rf2_connector.RF2Info()  # primary
        self.restapi = restapi_connector.RestAPIInfo(self.shmmapi)  # secondary

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
        rf2_data.tostr = partial(bytes_to_str, char_encoding=config["character_encoding"].lower())


class SimLMU(Connector):
    """Le Mans Ultimate"""

    __slots__ = (
        "shmmapi",  # shared memory API
        "restapi",  # Rest API
    )
    NAME = API_NAME_LMU

    def __init__(self):
        self.shmmapi = rf2_connector.RF2Info()  # primary
        self.restapi = restapi_connector.RestAPIInfo(self.shmmapi)  # secondary

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
        rf2_data.tostr = partial(bytes_to_str, char_encoding=config["character_encoding"].lower())


# Add new API to API_PACK
API_PACK = (
    SimRF2,
    SimLMU,
)
