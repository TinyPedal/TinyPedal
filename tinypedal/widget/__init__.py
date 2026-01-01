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
Widget modules

Add new widget to import list below in ascending order,
file name must match corresponding key name
in template/setting_widget.py dictionary.
"""

__all__ = [
    "battery",
    "brake_bias",
    "brake_performance",
    "brake_pressure",
    "brake_temperature",
    "brake_wear",
    "cruise",
    "damage",
    "deltabest",
    "deltabest_extended",
    "differential",
    "drs",
    "electric_motor",
    "elevation",
    "engine",
    "flag",
    "force",
    "friction_circle",
    "fuel",
    "fuel_energy_saver",
    "gear",
    "heading",
    "instrument",
    "lap_time_history",
    "laps_and_position",
    "navigation",
    "p2p",
    "pace_notes",
    "pedal",
    "pit_stop_estimate",
    "radar",
    "rake_angle",
    "relative",
    "relative_finish_order",
    "ride_height",
    "rivals",
    "roll_angle",
    "rpm_led",
    "sectors",
    "session",
    "slip_ratio",
    "speedometer",
    "standings",
    "steering",
    "steering_wheel",
    "stint_history",
    "suspension_force",
    "suspension_position",
    "system_performance",
    "timing",
    "track_map",
    "track_notes",
    "trailing",
    "tyre_carcass",
    "tyre_inner_layer",
    "tyre_load",
    "tyre_pressure",
    "tyre_temperature",
    "tyre_wear",
    "virtual_energy",
    "weather",
    "weather_forecast",
    "weight_distribution",
    "wheel_camber",
    "wheel_toe",
]

from . import *
