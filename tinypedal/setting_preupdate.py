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
        ((2, 42, 8), _user_prior_2_42_8),  # 2026-03-06
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


def _user_prior_2_42_8(dict_user: dict):
    """Update user setting prior to 2.42.8"""
    # Copy options from sectors module to sectors widget
    module_sectors = dict_user.get("module_sectors")
    sectors = dict_user.get("sectors")
    if isinstance(module_sectors, dict) and isinstance(sectors, dict):
        if "enable_all_time_best_sectors" in module_sectors:
            sectors["enable_all_time_best_sectors"] = module_sectors["enable_all_time_best_sectors"]
    # Copy options in instrument widget
    instrument = dict_user.get("instrument")
    if isinstance(instrument, dict):
        if "bkg_color" in instrument:
            instrument["bkg_color_headlights"] = instrument["bkg_color"]
            instrument["bkg_color_ignition"] = instrument["bkg_color"]
            instrument["bkg_color_clutch"] = instrument["bkg_color"]
            instrument["bkg_color_wheel_lock"] = instrument["bkg_color"]
            instrument["bkg_color_wheel_slip"] = instrument["bkg_color"]
    # Rename options in fuel widget
    fuel = dict_user.get("fuel")
    if isinstance(fuel, dict):
        _rename_key(fuel, "_laps", "_estimated_laps")
        _rename_key(fuel, "_minutes", "_estimated_minutes")
        _rename_key(fuel, "_used", "_estimated_consumption")
        _rename_key(fuel, "_save", "_saving_target")
        _rename_key(fuel, "_pits", "_pitstop_count")
        _rename_key(fuel, "_early", "_early_pitstop_count")
        _rename_key(fuel, "_delta", "_delta_consumption")
        _rename_key(fuel, "_end", "_end_remaining")
        _rename_key(fuel, "_refuel", "_refueling")
        _rename_key(fuel, "_remain", "_remaining")
    # Rename options in virtual energy widget
    virtual_energy = dict_user.get("virtual_energy")
    if isinstance(virtual_energy, dict):
        _rename_key(virtual_energy, "_laps", "_estimated_laps")
        _rename_key(virtual_energy, "_minutes", "_estimated_minutes")
        _rename_key(virtual_energy, "_used", "_estimated_consumption")
        _rename_key(virtual_energy, "_save", "_saving_target")
        _rename_key(virtual_energy, "_pits", "_pitstop_count")
        _rename_key(virtual_energy, "_early", "_early_pitstop_count")
        _rename_key(virtual_energy, "_delta", "_delta_consumption")
        _rename_key(virtual_energy, "_end", "_end_remaining")
        _rename_key(virtual_energy, "_ratio", "_fuel_ratio")
        _rename_key(virtual_energy, "_bias", "_fuel_bias")
        _rename_key(virtual_energy, "_refill", "_refilling")
        _rename_key(virtual_energy, "_remain", "_remaining")
    # Rename options in steering widget
    steering = dict_user.get("steering")
    if isinstance(steering, dict):
        if "font_color" in steering:
            steering["font_color_steering_angle"] = steering["font_color"]
    # Rename options in track map widget
    track_map = dict_user.get("track_map")
    if isinstance(track_map, dict):
        if "enabled_fixed_pitout_prediction" in track_map:
            track_map["enable_fixed_pitout_prediction"] = track_map["enabled_fixed_pitout_prediction"]
        if "show_vehicle_standings" in track_map:
            track_map["show_vehicle_class_standings"] = track_map["show_vehicle_standings"]
    # Rename options in navigation widget
    navigation = dict_user.get("navigation")
    if isinstance(navigation, dict):
        if "show_vehicle_standings" in navigation:
            navigation["show_vehicle_class_standings"] = navigation["show_vehicle_standings"]
    # Rename options in friction_circle widget
    friction_circle = dict_user.get("friction_circle")
    if isinstance(friction_circle, dict):
        if "font_color" in friction_circle:
            friction_circle["font_color_readings"] = friction_circle["font_color"]
    # Rename options in deltabest widget
    deltabest = dict_user.get("deltabest")
    if isinstance(deltabest, dict):
        if "bkg_color_deltabar" in deltabest:
            deltabest["bkg_color_delta_bar"] = deltabest["bkg_color_deltabar"]
        if "bar_length" in deltabest:
            deltabest["delta_bar_length"] = deltabest["bar_length"]
        if "bar_height" in deltabest:
            deltabest["delta_bar_height"] = deltabest["bar_height"]
        if "bar_display_range" in deltabest:
            deltabest["delta_bar_display_range"] = deltabest["bar_display_range"]
        if "show_animated_deltabest" in deltabest:
            deltabest["enable_animated_deltabest"] = deltabest["show_animated_deltabest"]
    # Rename options in radar widget
    radar = dict_user.get("radar")
    if isinstance(radar, dict):
        if "auto_hide" in radar:
            radar["enable_auto_hide"] = radar["auto_hide"]
        if "auto_hide_in_private_qualifying" in radar:
            radar["enable_auto_hide_in_private_qualifying"] = radar["auto_hide_in_private_qualifying"]
    # Rename options in pace notes widget
    pace_notes = dict_user.get("pace_notes")
    if isinstance(pace_notes, dict):
        if "auto_hide_if_not_available" in pace_notes:
            pace_notes["enable_auto_hide_if_not_available"] = pace_notes["auto_hide_if_not_available"]
    # Rename options in track notes widget
    track_notes = dict_user.get("track_notes")
    if isinstance(track_notes, dict):
        if "auto_hide_if_not_available" in track_notes:
            track_notes["enable_auto_hide_if_not_available"] = track_notes["auto_hide_if_not_available"]
    # Rename options in trailing widget
    trailing = dict_user.get("trailing")
    if isinstance(trailing, dict):
        _rename_key(trailing, "draw_order_index", "display_order")
    # Rename all "column_index" to "display_order"
    for option in dict_user.values():
        if isinstance(option, dict):
            _rename_key(option, "column_index", "display_order")
    # Swap all suffix "_decimal_places" with prefix "decimal_places_"
    for option in dict_user.values():
        if isinstance(option, dict):
            _swap_suffix_with_prefix(option, "_decimal_places", "decimal_places_")


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
            data[key.replace(old, new)] = data[key]


def _swap_suffix_with_prefix(data: dict, suffix: str, prefix: str):
    """Rename key name by swap suffix with prefix"""
    for key in tuple(data):
        if suffix in key:
            data[f"{prefix}{key.split(suffix)[0]}"] = data[key]
