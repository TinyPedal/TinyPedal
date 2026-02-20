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

import logging

logger = logging.getLogger(__name__)


def preupdate_specific_version(preset_version: tuple[int, int, int], dict_user: dict):
    """Pre update old setting from specific version"""
    # Create target version and update function list
    # Very old version may be removed later
    target_versions = (
        ((2, 41, 0), _user_prior_2_41_0),  # 2026-02-20
        ((2, 40, 0), _user_prior_2_40_0),  # 2026-01-23
        ((2, 39, 0), _user_prior_2_39_0),  # 2026-01-13
        ((2, 37, 0), _user_prior_2_37_0),  # 2025-12-24
        ((2, 36, 0), _user_prior_2_36_0),  # 2025-12-13
        ((2, 33, 1), _user_prior_2_33_1),  # 2025-08-22
    )
    for _version, _update in reversed(target_versions):
        if preset_version < _version:
            _update(dict_user)
            logger.info("USERDATA: updated old setting prior to %s.%s.%s", *_version)


def _user_prior_2_41_0(dict_user: dict):
    """Update user setting prior to 2.41.0"""
    # Rename "p2p" to "push to pass"
    p2p = dict_user.get("p2p")
    if isinstance(p2p, dict):
        dict_user["push_to_pass"] = p2p.copy()
    # Copy old track clock setting from cruise widget
    if "track_clock" not in dict_user:
        cruise = dict_user.get("cruise")
        if isinstance(cruise, dict):
            dict_user["track_clock"] = cruise.copy()
            dict_user["track_clock"]["position_y"] += 30
    # Convert font weight name to title case
    for sub_dict in dict_user.values():
        for option, value in sub_dict.items():
            if "font_weight" in option:
                sub_dict[option] = value.title()


def _user_prior_2_40_0(dict_user: dict):
    """Update user setting prior to 2.40.0"""
    track_map = dict_user.get("track_map")
    if isinstance(track_map, dict):
        if "pitstop_duration_minimum" in track_map:
            track_map["pitout_duration_minimum"] = track_map["pitstop_duration_minimum"]
        if "pitstop_duration_increment" in track_map:
            track_map["pitout_duration_increment"] = track_map["pitstop_duration_increment"]


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
        dict_user["api_lmu"] = telemetry_api.copy()
        dict_user["api_rf2"] = telemetry_api.copy()
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
