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
rF2 Rest API task
"""

from __future__ import annotations

import logging

from ..process.garage import export_rf2_car_setup
from ..process.weather import FORECAST_DEFAULT, forecast_rf2
from ..validator import valid_value_type
from .lmu_restapi import RestAPIData as RestAPIData
from .restapi_connector import ResOutput, RestAPITask

logger = logging.getLogger(__name__)


def rf2_restapi_tasks() -> tuple[RestAPITask, ...]:
    """Define RestAPI task set - RF2"""
    # Define resources output set
    res_weatherforecast = (
        ResOutput("forecastPractice", FORECAST_DEFAULT, forecast_rf2, ("PRACTICE",)),
        ResOutput("forecastQualify", FORECAST_DEFAULT, forecast_rf2, ("QUALIFY",)),
        ResOutput("forecastRace", FORECAST_DEFAULT, forecast_rf2, ("RACE",)),
    )
    res_timescale = (
        ResOutput("timeScale", 1, valid_value_type, ("currentValue",)),
    )
    res_privatequalify = (
        ResOutput("privateQualifying", 0, valid_value_type, ("currentValue",)),
    )
    res_garagesetup = (
        ResOutput("lastCarSetup", (), export_rf2_car_setup),
    )
    # Define task set
    return (
        RestAPITask("/rest/sessions/weather", res_weatherforecast, "enable_weather_info", False, 0.1),
        RestAPITask("/rest/sessions/setting/SESSSET_race_timescale", res_timescale, "enable_session_info", False, 0.1),
        RestAPITask("/rest/sessions/setting/SESSSET_private_qual", res_privatequalify, "enable_session_info", False, 0.1),
        RestAPITask("/rest/garage/aerodynamics", res_garagesetup, "enable_garage_setup_info", False, 0.1),
        RestAPITask("/rest/garage/brakes", res_garagesetup, "enable_garage_setup_info", False, 0.1),
        RestAPITask("/rest/garage/chassis", res_garagesetup, "enable_garage_setup_info", False, 0.1),
        RestAPITask("/rest/garage/drivetrain", res_garagesetup, "enable_garage_setup_info", False, 0.1),
        RestAPITask("/rest/garage/electronics", res_garagesetup, "enable_garage_setup_info", False, 0.1),
        RestAPITask("/rest/garage/fuel", res_garagesetup, "enable_garage_setup_info", False, 0.1),
        RestAPITask("/rest/garage/gears", res_garagesetup, "enable_garage_setup_info", False, 0.1),
        RestAPITask("/rest/garage/suspension", res_garagesetup, "enable_garage_setup_info", False, 0.1),
        RestAPITask("/rest/garage/tires", res_garagesetup, "enable_garage_setup_info", False, 0.1),
    )
