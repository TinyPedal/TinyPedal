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
Default module setting template
"""


MODULE_DEFAULT = {
    "module_delta": {
        "enable": True,
        "update_interval": 10,
        "idle_update_interval": 400,
        "minimum_delta_distance": 5,
        "delta_smoothing_samples": 30,
        "laptime_pace_samples": 6,
        "laptime_pace_margin": 5,
    },
    "module_energy": {
        "enable": True,
        "update_interval": 10,
        "idle_update_interval": 400,
        "minimum_delta_distance": 5,
    },
    "module_force": {
        "enable": True,
        "update_interval": 10,
        "idle_update_interval": 400,
        "gravitational_acceleration": 9.80665,
        "max_g_force_reset_delay": 5,
        "max_average_g_force_samples": 10,
        "max_average_g_force_difference": 0.2,
        "max_average_g_force_reset_delay": 30,
        "max_braking_rate_reset_delay": 60,
    },
    "module_fuel": {
        "enable": True,
        "update_interval": 10,
        "idle_update_interval": 400,
        "minimum_delta_distance": 5,
    },
    "module_hybrid": {
        "enable": True,
        "update_interval": 10,
        "idle_update_interval": 400,
        "minimum_delta_distance": 5,
    },
    "module_mapping": {
        "enable": True,
        "update_interval": 10,
        "idle_update_interval": 400,
    },
    "module_notes": {
        "enable": True,
        "update_interval": 10,
        "idle_update_interval": 400,
    },
    "module_relative": {
        "enable": True,
        "update_interval": 100,
        "idle_update_interval": 400,
    },
    "module_sectors": {
        "enable": True,
        "update_interval": 10,
        "idle_update_interval": 400,
        "enable_all_time_best_sectors": True,
    },
    "module_stats": {
        "enable": True,
        "update_interval": 200,
        "idle_update_interval": 400,
        "vehicle_classification": "Class - Brand",
        "enable_podium_by_class": True,
    },
    "module_vehicles": {
        "enable": True,
        "update_interval": 20,
        "idle_update_interval": 400,
        "lap_difference_ahead_threshold": 0.9,
        "lap_difference_behind_threshold": 0.9,
    },
    "module_wheels": {
        "enable": True,
        "update_interval": 10,
        "idle_update_interval": 400,
        "minimum_axle_rotation": 4,
        "maximum_rotation_difference_front": 0.002,
        "maximum_rotation_difference_rear": 0.002,
        "cornering_radius_sampling_interval": 10,
        "minimum_delta_distance": 5,
    },
}
