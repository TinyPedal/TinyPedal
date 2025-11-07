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
Web API task
"""

from __future__ import annotations

from typing import Any, Callable, NamedTuple

from ..const_common import EMPTY_DICT, PITEST_DEFAULT
from ..module_info import minfo
from ..process.pitstop import EstimatePitTime
from ..process.vehicle import expected_usage, steerlock_to_number, stint_ve_usage
from ..process.weather import FORECAST_DEFAULT, forecast_rf2


class HttpSetup(NamedTuple):
    """Http connection setup"""

    host: str
    port: int
    timeout: float
    retry: int
    retry_delay: float


class ResRawOutput(NamedTuple):
    """URI resource raw output"""

    output: object
    name: str
    default: Any
    keys: tuple[str, ...]

    def reset(self):
        """Reset data"""
        setattr(self.output, self.name, self.default)

    def update(self, data: Any) -> bool:
        """Update data"""
        for key in self.keys:  # get data from dict
            if not isinstance(data, dict):  # not exist, set to default
                setattr(self.output, self.name, self.default)
                return False
            data = data.get(key)
        # Not exist, set to default
        if data is None:
            setattr(self.output, self.name, self.default)
            return False
        # Reset to default if value is not same type as default
        if not isinstance(data, type(self.default)):
            data = self.default
        setattr(self.output, self.name, data)
        return True


class ResParOutput(NamedTuple):
    """URI resource parsed output"""

    output: object
    name: str
    default: Any
    parser: Callable
    keys: tuple[str, ...]

    def reset(self):
        """Reset data"""
        setattr(self.output, self.name, self.default)

    def update(self, data: Any) -> bool:
        """Update data"""
        for key in self.keys:  # get data from dict
            if not isinstance(data, dict):  # not exist, set to default
                setattr(self.output, self.name, self.default)
                return False
            data = data.get(key)
        # Not exist, set to default
        if data is None:
            setattr(self.output, self.name, self.default)
            return False
        # Parse and output
        setattr(self.output, self.name, self.parser(data))
        return True


EMPTY_KEYS: tuple[str, ...] = tuple()

# Common
COMMON_WEATHERFORECAST = (
    ResParOutput(minfo.restapi, "forecastPractice", FORECAST_DEFAULT, forecast_rf2, ("PRACTICE",)),
    ResParOutput(minfo.restapi, "forecastQualify", FORECAST_DEFAULT, forecast_rf2, ("QUALIFY",)),
    ResParOutput(minfo.restapi, "forecastRace", FORECAST_DEFAULT, forecast_rf2, ("RACE",)),
)
# RF2
RF2_TIMESCALE = (
    ResRawOutput(minfo.restapi, "timeScale", 1, ("currentValue",)),
)
RF2_PRIVATEQUALIFY = (
    ResRawOutput(minfo.restapi, "privateQualifying", 0, ("currentValue",)),
)
RF2_GARAGESETUP = (
    ResParOutput(minfo.fuel, "expectedConsumption", 0.0, expected_usage, ("VM_FUEL_LEVEL", "stringValue")),
)
# LMU
LMU_CURRENTSTINT = (
    ResRawOutput(minfo.restapi, "currentVirtualEnergy", 0.0, ("fuelInfo", "currentVirtualEnergy")),
    ResRawOutput(minfo.restapi, "maxVirtualEnergy", 0.0, ("fuelInfo", "maxVirtualEnergy")),
    ResRawOutput(minfo.restapi, "aeroDamage", -1.0, ("wearables", "body", "aero")),
    ResRawOutput(minfo.restapi, "brakeWear", [], ("wearables", "brakes")),
    ResRawOutput(minfo.restapi, "suspensionDamage", [], ("wearables", "suspension")),
    ResRawOutput(minfo.restapi, "trackClockTime", -1.0, ("sessionTime", "timeOfDay")),
    ResParOutput(minfo.restapi, "pitStopEstimate", PITEST_DEFAULT, EstimatePitTime(), EMPTY_KEYS),
)
LMU_GARAGESETUP = (
    ResParOutput(minfo.restapi, "steeringWheelRange", 0.0, steerlock_to_number, ("VM_STEER_LOCK", "stringValue")),
    ResParOutput(minfo.fuel, "expectedConsumption", 0.0, expected_usage, ("VM_FUEL_CAPACITY", "stringValue")),
    ResParOutput(minfo.energy, "expectedConsumption", 0.0, expected_usage, ("VM_VIRTUAL_ENERGY", "stringValue")),
)
LMU_SESSIONSINFO = (
    ResRawOutput(minfo.restapi, "timeScale", 1, ("SESSSET_race_timescale", "currentValue")),
    ResRawOutput(minfo.restapi, "privateQualifying", 0, ("SESSSET_private_qual", "currentValue")),
)
LMU_PITSTOPTIME = (
    ResRawOutput(minfo.restapi, "penaltyTime", 0.0, ("penalties",)),
)
LMU_STINTUSAGE = (
    ResParOutput(minfo.restapi, "stintUsage", EMPTY_DICT, stint_ve_usage, EMPTY_KEYS),
)
#LMU_GAMESTATE = (
#    ResRawOutput(minfo.restapi, "trackClockTime", -1.0, ("timeOfDay",)),
#)
#("LMU", "/rest/sessions/GetGameState", LMU_GAMESTATE, None),

# Define task set
# 0 - uri path, 1 - output set, 2 - enabling condition, 3 is repeating task, 4 minimum update interval
TASKSET_RF2 = (
    ("/rest/sessions/weather", COMMON_WEATHERFORECAST, "enable_weather_info", False, 0.1),
    ("/rest/sessions/setting/SESSSET_race_timescale", RF2_TIMESCALE, "enable_session_info", False, 0.1),
    ("/rest/sessions/setting/SESSSET_private_qual", RF2_PRIVATEQUALIFY, "enable_session_info", False, 0.1),
    ("/rest/garage/fuel", RF2_GARAGESETUP, "enable_garage_setup_info", False, 0.1),
)
TASKSET_LMU = (
    ("/rest/sessions/weather", COMMON_WEATHERFORECAST, "enable_weather_info", False, 0.1),
    ("/rest/sessions", LMU_SESSIONSINFO, "enable_session_info", False, 0.1),
    ("/rest/garage/getPlayerGarageData", LMU_GARAGESETUP, "enable_garage_setup_info", False, 0.1),
    ("/rest/garage/UIScreen/RepairAndRefuel", LMU_CURRENTSTINT, "enable_vehicle_info", True, 0.2),
    ("/rest/strategy/pitstop-estimate", LMU_PITSTOPTIME, "enable_vehicle_info", True, 1.0),
    ("/rest/strategy/usage", LMU_STINTUSAGE, "enable_energy_remaining", True, 1.0),
)


def select_taskset(name: str) -> tuple:
    """Select taskset"""
    if name == "RF2":
        return TASKSET_RF2
    if name == "LMU":
        return TASKSET_LMU
    return ()
