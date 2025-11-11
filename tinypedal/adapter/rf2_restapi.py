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
Rest API task
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, NamedTuple

from ..const_common import EMPTY_DICT, PITEST_DEFAULT, WHEELS_NA
from ..process.pitstop import EstimatePitTime
from ..process.vehicle import (
    expected_usage,
    export_wheels,
    steerlock_to_number,
    stint_ve_usage,
)
from ..process.weather import FORECAST_DEFAULT, WeatherNode, forecast_rf2


class RestAPIData:
    """Rest API data"""

    __slots__ = (
        "timeScale",
        "trackClockTime",
        "privateQualifying",
        "steeringWheelRange",
        "currentVirtualEnergy",
        "maxVirtualEnergy",
        "expectedFuelConsumption",
        "expectedVirtualEnergyConsumption",
        "aeroDamage",
        "penaltyTime",
        "forecastPractice",
        "forecastQualify",
        "forecastRace",
        "brakeWear",
        "suspensionDamage",
        "stintUsage",
        "pitStopEstimate",
    )

    def __init__(self):
        self.timeScale: int = 1
        self.trackClockTime: float = -1.0
        self.privateQualifying: int = 0
        self.steeringWheelRange: float = 0.0
        self.currentVirtualEnergy: float = 0.0
        self.maxVirtualEnergy: float = 0.0
        self.expectedFuelConsumption: float = 0.0
        self.expectedVirtualEnergyConsumption: float = 0.0
        self.aeroDamage: float = -1.0
        self.penaltyTime: float = 0.0
        self.forecastPractice: tuple[WeatherNode, ...] = FORECAST_DEFAULT
        self.forecastQualify: tuple[WeatherNode, ...] = FORECAST_DEFAULT
        self.forecastRace: tuple[WeatherNode, ...] = FORECAST_DEFAULT
        self.brakeWear: tuple[float, float, float, float] = WHEELS_NA
        self.suspensionDamage: tuple[float, float, float, float] = WHEELS_NA
        self.stintUsage: Mapping[str, tuple[float, float, float, float, int]] = EMPTY_DICT
        self.pitStopEstimate: tuple[float, float, float, float, int] = PITEST_DEFAULT


class HttpSetup(NamedTuple):
    """Http connection setup"""

    host: str
    port: int
    timeout: float
    retry: int
    retry_delay: float


class ResRawOutput(NamedTuple):
    """URI resource raw output"""

    name: str
    default: Any
    keys: tuple[str, ...]

    def reset(self, output: RestAPIData):
        """Reset data"""
        setattr(output, self.name, self.default)

    def update(self, output: RestAPIData, data: Any) -> bool:
        """Update data"""
        for key in self.keys:  # get data from dict
            if not isinstance(data, dict):  # not exist, set to default
                setattr(output, self.name, self.default)
                return False
            data = data.get(key)
        # Not exist, set to default
        if data is None:
            setattr(output, self.name, self.default)
            return False
        # Reset to default if value is not same type as default
        if not isinstance(data, type(self.default)):
            data = self.default
        setattr(output, self.name, data)
        return True


class ResParOutput(NamedTuple):
    """URI resource parsed output"""

    name: str
    default: Any
    parser: Callable
    keys: tuple[str, ...]

    def reset(self, output: RestAPIData):
        """Reset data"""
        setattr(output, self.name, self.default)

    def update(self, output: RestAPIData, data: Any) -> bool:
        """Update data"""
        for key in self.keys:  # get data from dict
            if not isinstance(data, dict):  # not exist, set to default
                setattr(output, self.name, self.default)
                return False
            data = data.get(key)
        # Not exist, set to default
        if data is None:
            setattr(output, self.name, self.default)
            return False
        # Parse and output
        setattr(output, self.name, self.parser(data))
        return True


EMPTY_KEYS: tuple[str, ...] = tuple()

# Common
COMMON_WEATHERFORECAST = (
    ResParOutput("forecastPractice", FORECAST_DEFAULT, forecast_rf2, ("PRACTICE",)),
    ResParOutput("forecastQualify", FORECAST_DEFAULT, forecast_rf2, ("QUALIFY",)),
    ResParOutput("forecastRace", FORECAST_DEFAULT, forecast_rf2, ("RACE",)),
)
# RF2
RF2_TIMESCALE = (
    ResRawOutput("timeScale", 1, ("currentValue",)),
)
RF2_PRIVATEQUALIFY = (
    ResRawOutput("privateQualifying", 0, ("currentValue",)),
)
RF2_GARAGESETUP = (
    ResParOutput("expectedFuelConsumption", 0.0, expected_usage, ("VM_FUEL_LEVEL", "stringValue")),
)
# LMU
LMU_CURRENTSTINT = (
    ResRawOutput("currentVirtualEnergy", 0.0, ("fuelInfo", "currentVirtualEnergy")),
    ResRawOutput("maxVirtualEnergy", 0.0, ("fuelInfo", "maxVirtualEnergy")),
    ResRawOutput("aeroDamage", -1.0, ("wearables", "body", "aero")),
    ResParOutput("brakeWear", WHEELS_NA, export_wheels, ("wearables", "brakes")),
    ResParOutput("suspensionDamage", WHEELS_NA, export_wheels, ("wearables", "suspension")),
    ResRawOutput("trackClockTime", -1.0, ("sessionTime", "timeOfDay")),
    ResParOutput("pitStopEstimate", PITEST_DEFAULT, EstimatePitTime(), EMPTY_KEYS),
)
LMU_GARAGESETUP = (
    ResParOutput("steeringWheelRange", 0.0, steerlock_to_number, ("VM_STEER_LOCK", "stringValue")),
    ResParOutput("expectedFuelConsumption", 0.0, expected_usage, ("VM_FUEL_CAPACITY", "stringValue")),
    ResParOutput("expectedVirtualEnergyConsumption", 0.0, expected_usage, ("VM_VIRTUAL_ENERGY", "stringValue")),
)
LMU_SESSIONSINFO = (
    ResRawOutput("timeScale", 1, ("SESSSET_race_timescale", "currentValue")),
    ResRawOutput("privateQualifying", 0, ("SESSSET_private_qual", "currentValue")),
)
LMU_PITSTOPTIME = (
    ResRawOutput("penaltyTime", 0.0, ("penalties",)),
)
LMU_STINTUSAGE = (
    ResParOutput("stintUsage", EMPTY_DICT, stint_ve_usage, EMPTY_KEYS),
)

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
