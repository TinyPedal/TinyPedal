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
Default global (config) setting template
"""

from ..const_api import API_LMU_NAME
from ..const_app import APP_NAME, PLATFORM

GLOBAL_DEFAULT = {
    "application": {
        "show_at_startup": True,
        "check_for_updates_on_startup": True,
        "minimize_to_tray": (PLATFORM == "Windows"),
        "remember_position": True,
        "remember_size": True,
        "enable_high_dpi_scaling": True,
        "enable_auto_load_preset": False,
        "enable_global_hotkey": False,
        "show_confirmation_for_batch_toggle": True,
        'snap_distance': 10,
        "snap_gap": 0,
        "grid_move_size": 8,
        "minimum_update_interval": 10,
        "maximum_saving_attempts": 10,
        "position_x": 0,
        "position_y": 0,
        "window_width": 0,
        "window_height": 0,
        "window_color_theme": "Dark",
    },
    "compatibility": {
        "enable_bypass_window_manager": (PLATFORM != "Windows"),
        "enable_translucent_background": True,
        "enable_window_position_correction": True,
        "enable_x11_platform_plugin_override": (PLATFORM != "Windows"),
        "global_bkg_color": "#000000",
        "multimedia_plugin_on_windows": "WMF",
    },
    "telemetry": {
        "api_name": API_LMU_NAME,
        "enable_api_selection_from_preset": True,
        "enable_legacy_api_selection": (PLATFORM != "Windows"),
    },
    "user_path": {
        "settings_path": "settings/",
        "brand_logo_path": "brandlogo/",
        "delta_best_path": "deltabest/",
        "sector_best_path": "deltabest/",
        "energy_delta_path": "deltabest/",
        "fuel_delta_path": "deltabest/",
        "track_map_path": "trackmap/",
        "pace_notes_path": "pacenotes/",
        "track_notes_path": "tracknotes/",
    },
    "notification": {
        "notify_locked_preset": True,
        "font_color_locked_preset": "#FFFFFF",
        "bkg_color_locked_preset": "#777777",
        "notify_spectate_mode": True,
        "font_color_spectate_mode": "#FFFFFF",
        "bkg_color_spectate_mode": "#0088CC",
        "notify_pace_notes_playback": True,
        "font_color_pace_notes_playback": "#FFFFFF",
        "bkg_color_pace_notes_playback": "#228800",
        "notify_global_hotkey": True,
        "font_color_global_hotkey": "#FFFFFF",
        "bkg_color_global_hotkey": "#885544",
    },
    "track_map_viewer": {
        "inner_margin": 6,
        "position_increment_step": 5,
        "font_color_light": "#CCCCCC",
        "font_color_dark": "#333333",
        "bkg_color_light": "#FFFFFF",
        "bkg_color_dark": "#333333",
        "map_color": "#FFFFFF",
        "map_width": 10,
        "map_outline_color": "#111111",
        "map_outline_width": 4,
        "start_line_color": "#FF4400",
        "start_line_width": 10,
        "start_line_length": 30,
        "sector_line_color": "#00AAFF",
        "sector_line_width": 8,
        "sector_line_length": 30,
        "marked_coordinates_color": "#808080",
        "marked_coordinates_size": 15,
        "highlighted_coordinates_color": "#22DD00",
        "highlighted_coordinates_width": 5,
        "highlighted_coordinates_size": 15,
        "center_mark_color": "#808080",
        "center_mark_width": 1,
        "center_mark_radius": 1000,
        "curve_section_color": "#FF4400",
        "curve_section_width": 5,
        "osculating_circle_color": "#00AAFF",
        "osculating_circle_width": 2,
        "distance_circle_color": "#808080",
        "distance_circle_width": 1,
        "distance_circle_0_radius": 50,
        "distance_circle_1_radius": 100,
        "distance_circle_2_radius": 200,
        "distance_circle_3_radius": 300,
        "distance_circle_4_radius": 400,
        "distance_circle_5_radius": 500,
        "distance_circle_6_radius": 1000,
        "distance_circle_7_radius": 0,
        "distance_circle_8_radius": 0,
        "distance_circle_9_radius": 0,
        "curve_grade_hairpin": 5,
        "curve_grade_1": 15,
        "curve_grade_2": 25,
        "curve_grade_3": 40,
        "curve_grade_4": 65,
        "curve_grade_5": 105,
        "curve_grade_6": 275,
        "curve_grade_7": -1,
        "curve_grade_8": -1,
        "curve_grade_straight": 3050,
        "length_grade_short": 0,
        "length_grade_normal": 50,
        "length_grade_long": 150,
        "length_grade_very_long": 250,
        "length_grade_extra_long": 350,
        "length_grade_extremely_long": 450,
        "slope_grade_flat": 0,
        "slope_grade_gentle": 0.03,
        "slope_grade_moderate": 0.1,
        "slope_grade_steep": 0.25,
        "slope_grade_extreme": 0.5,
        "slope_grade_cliff": 1,
    },
}


def _set_platform_default(global_def: dict):
    """Set platform default setting"""
    if PLATFORM != "Windows":
        # Global path
        from xdg import BaseDirectory as BD

        config_paths = (
            "settings_path",
            "brand_logo_path",
            "pace_notes_path",
            "track_notes_path",
        )
        user_path = global_def["user_path"]
        for key, path in user_path.items():
            if key in config_paths:
                user_path[key] = BD.save_config_path(APP_NAME, path)
            else:
                user_path[key] = BD.save_data_path(APP_NAME, path)


_set_platform_default(GLOBAL_DEFAULT)
