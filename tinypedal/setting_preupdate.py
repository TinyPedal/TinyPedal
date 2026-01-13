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
Setting pre update function
"""

from __future__ import annotations

from .const_api import API_LMU_CONFIG, API_RF2_CONFIG


def preupdate_specific_version_setting(preset_version: tuple[int, int, int], dict_user: dict):
    """Pre update old setting from specific version"""
    if preset_version < (2, 33, 1):
        _user_prior_2_33_1(dict_user)
    if preset_version < (2, 36, 0):
        _user_prior_2_36_0(dict_user)
    if preset_version < (2, 37, 0):
        _user_prior_2_37_0(dict_user)
    if preset_version < (2, 39, 0):
        _user_prior_2_39_0(dict_user)


def _user_prior_2_39_0(dict_user: dict):
    """Update user setting prior to 2.39.0"""
    suspension_position = dict_user.get("suspension_position")
    if isinstance(suspension_position, dict):
        if suspension_position["negative_position_color"] == "#FF2200":
            suspension_position["negative_position_color"] = "#00AAFF"


def _user_prior_2_37_0(dict_user: dict):
    """Update user setting prior to 2.37.0"""
    # Transfer wheel_alignment setting to new widgets
    wheel_alignment = dict_user.get("wheel_alignment")
    if isinstance(wheel_alignment, dict):
        wheel_alignment["bar_gap"] = 0
        dict_user["wheel_camber"] = wheel_alignment.copy()
        dict_user["wheel_toe"] = wheel_alignment.copy()
        dict_user["wheel_toe"]["position_y"] += 60


def _user_prior_2_36_0(dict_user: dict):
    """Update user setting prior to 2.36.0"""
    # Copy old telemetry_api setting
    telemetry_api = dict_user.get("telemetry_api")
    if isinstance(telemetry_api, dict):
        dict_user[API_LMU_CONFIG] = telemetry_api.copy()
        dict_user[API_RF2_CONFIG] = telemetry_api.copy()
    # Correct default update interval in module_vehicles
    module_vehicles = dict_user.get("module_vehicles")
    if isinstance(module_vehicles, dict):
        if module_vehicles["update_interval"] == 20:
            module_vehicles["update_interval"] = 10


def _user_prior_2_33_1(dict_user: dict):
    """Update user setting prior to 2.33.1"""
    # Fix option name typo "predication"
    relative_finish_order = dict_user.get("relative_finish_order")
    if isinstance(relative_finish_order, dict):
        _rename_key(relative_finish_order, "predication", "prediction")

    track_map = dict_user.get("track_map")
    if isinstance(track_map, dict):
        _rename_key(track_map, "predication", "prediction")


# Misc function
def _rename_key(data: dict, old: str, new: str):
    """Rename key name"""
    for key in tuple(data):
        if old in key:
            data[key.replace(old, new)] = data.pop(key)
