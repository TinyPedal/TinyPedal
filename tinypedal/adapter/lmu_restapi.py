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
LMU Rest API task
"""

from __future__ import annotations

import logging

from ..constant import DATA
from ..decorator import slotclass
from ..process.garage import export_lmu_car_setup
from ..process.vehicle import absolute_refilling, export_wheels, steerlock_to_number
from ..process.weather import FORECAST_DEFAULT, WeatherNode, forecast_rf2
from ..validator import valid_value_type
from ._restapi import ResOutput, RestAPITask

logger = logging.getLogger(__name__)


@slotclass
class RestAPIData:
    """Rest API data"""

    # LMU, RF2
    timeScale: int = 1
    privateQualifying: int = 0
    forecastPractice: tuple[WeatherNode, ...] = FORECAST_DEFAULT
    forecastQualify: tuple[WeatherNode, ...] = FORECAST_DEFAULT
    forecastRace: tuple[WeatherNode, ...] = FORECAST_DEFAULT
    lastCarSetup: tuple[str, ...] = ()
    # LMU only
    steeringWheelRange: float = 0.0
    aeroDamage: float = -1.0
    repairTime: float = 0.0
    pitStopTime: float = 0.0
    absoluteRefill: float = 0.0
    maxVirtualEnergy: float = 0.0
    brakeWear: tuple[float, float, float, float] = DATA.WHEELS_NA
    suspensionDamage: tuple[float, float, float, float] = DATA.WHEELS_NA

    def __del__(self):
        logger.info("RestAPI: GC: RestAPIData")


def lmu_restapi_tasks() -> tuple[RestAPITask, ...]:
    """Define RestAPI task set - LMU"""
    # Define resources output set
    res_weatherforecast = (
        ResOutput("forecastPractice", FORECAST_DEFAULT, forecast_rf2, ("PRACTICE",)),
        ResOutput("forecastQualify", FORECAST_DEFAULT, forecast_rf2, ("QUALIFY",)),
        ResOutput("forecastRace", FORECAST_DEFAULT, forecast_rf2, ("RACE",)),
    )
    res_currentstint = (
        ResOutput("aeroDamage", -1.0, valid_value_type, ("wearables", "body", "aero")),
        ResOutput("brakeWear", DATA.WHEELS_NA, export_wheels, ("wearables", "brakes")),
        ResOutput("suspensionDamage", DATA.WHEELS_NA, export_wheels, ("wearables", "suspension")),
        ResOutput("absoluteRefill", 0.0, absolute_refilling, ("pitMenu", "pitMenu")),
        ResOutput("maxVirtualEnergy", 0.0, valid_value_type, ("fuelInfo", "maxVirtualEnergy")),
    )
    res_garagesetup = (
        ResOutput("steeringWheelRange", 0.0, steerlock_to_number, ("VM_STEER_LOCK", "stringValue")),
        ResOutput("lastCarSetup", (), export_lmu_car_setup),
    )
    res_sessionsinfo = (
        ResOutput("timeScale", 1, valid_value_type, ("SESSSET_race_timescale", "currentValue")),
        ResOutput("privateQualifying", 0, valid_value_type, ("SESSSET_private_qual", "currentValue")),
    )
    res_pitstoptime = (
        ResOutput("pitStopTime", 0.0, valid_value_type, ("total",)),
        ResOutput("repairTime", 0.0, valid_value_type, ("damage",)),
    )
    # Define task set
    return (
        RestAPITask("/rest/sessions/weather", res_weatherforecast, "enable_weather_info", False, 0.1),
        RestAPITask("/rest/sessions", res_sessionsinfo, "enable_session_info", False, 0.1),
        RestAPITask("/rest/garage/getPlayerGarageData", res_garagesetup, "enable_garage_setup_info", False, 0.1),
        RestAPITask("/rest/garage/UIScreen/RepairAndRefuel", res_currentstint, "enable_vehicle_info", True, 0.2),
        RestAPITask("/rest/strategy/pitstop-estimate", res_pitstoptime, "enable_vehicle_info", True, 1.0),
    )
