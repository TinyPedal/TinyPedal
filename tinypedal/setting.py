#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022  Xiang
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
Overlay setting
"""

import os
import re
import time
import json
import shutil
import copy

from .const import PATH_SETTINGS, PATH_CLASSES


class Setting:
    """Overlay setting"""
    filepath = PATH_SETTINGS
    filename = "default.json"
    setting_default = {
        "overlay": {
            "fixed_position": False,
            "auto_hide": True,
            "delta_module": True,
            "relative_module": True,
            "fuel_module": True,
            "hover_color_1": "#FFB913",
            "hover_color_2": "#F6AD00",
            "transparent_color": "#000002",
        },
        "cruise": {
            "enable": True,
            "update_delay": 100,
            "position_x": "665",
            "position_y": "204",
            "opacity": 0.9,
            "font_name": "consolas",
            "font_size": 15,
            "font_weight": "bold",
            "bar_gap": 2,
            "font_color_track_clock": "#FFFFFF",
            "font_color_compass": "#FFFFFF",
            "font_color_elevation": "#FFFFFF",
            "font_color_odometer": "#FFFFFF",
            "bkg_color_track_clock": "#222222",
            "bkg_color_compass": "#222222",
            "bkg_color_elevation": "#222222",
            "bkg_color_odometer": "#222222",
            "show_track_clock": True,
            "track_clock_time_scale": 1,
            "track_clock_format": "%H:%M %p",
            "show_odometer": True,
            "odometer_unit": "0",
            "show_elevation": True,
            "elevation_unit": "0",
            "meters_driven": 0,
        },
        "deltabest": {
            "enable": True,
            "update_delay": 40,
            "position_x": "932",
            "position_y": "228",
            "opacity": 0.9,
            "layout": "0",
            "color_swap": "0",
            "font_name": "consolas",
            "font_size": 17,
            "font_weight": "bold",
            "bar_gap": 2,
            "font_color_deltabest": "#000000",
            "bkg_color_deltabest": "#222222",
            "bkg_color_time_gain": "#44FF00",
            "bkg_color_time_loss": "#FF4400",
            "show_delta_bar": True,
            "bar_length_scale": 2.0,
            "bar_height_scale": 1.0,
            "bar_display_range": 2,
        },
        "drs": {
            "enable": True,
            "update_delay": 50,
            "position_x": "1113",
            "position_y": "527",
            "opacity": 0.9,
            "font_name": "consolas",
            "font_size": 30,
            "font_weight": "bold",
            "font_color_activated": "#000000",
            "font_color_allowed": "#000000",
            "font_color_available": "#000000",
            "font_color_not_available": "#000000",
            "bkg_color_activated": "#44FF00",
            "bkg_color_allowed": "#FF4400",
            "bkg_color_available": "#00CCFF",
            "bkg_color_not_available": "#555555",
        },
        "engine": {
            "enable": True,
            "update_delay": 50,
            "position_x": "933",
            "position_y": "526",
            "opacity": 0.9,
            "font_name": "consolas",
            "font_size": 15,
            "font_weight": "bold",
            "bar_gap": 2,
            "font_color": "#FFFFFF",
            "bkg_color": "#222222",
            "bkg_color_overheat": "#FF2200",
            "overheat_threshold_oil": 110,
            "overheat_threshold_water": 110,
            "show_turbo": True,
            "show_rpm": True,
        },
        "force": {
            "enable": True,
            "update_delay": 50,
            "position_x": "1035",
            "position_y": "526",
            "opacity": 0.9,
            "font_name": "consolas",
            "font_size": 15,
            "font_weight": "bold",
            "bar_gap": 2,
            "font_color_g_force": "#FFCC00",
            "bkg_color_g_force": "#222222",
            "show_downforce_ratio": True,
            "font_color_downforce": "#000000",
            "bkg_color_downforce": "#DDDDDD",
        },
        "fuel": {
            "enable": True,
            "update_delay": 20,
            "position_x": "1024",
            "position_y": "362",
            "opacity": 0.9,
            "font_name": "consolas",
            "font_size": 15,
            "font_weight": "bold",
            "bar_gap": 0,
            "fuel_unit": "0",
            "font_color_fuel": "#FFFFFF",
            "font_color_consumption": "#555555",
            "font_color_estimate": "#DDDDDD",
            "font_color_pits": "#DDDDDD",
            "bkg_color_fuel": "#009900",
            "bkg_color_consumption": "#FFFFFF",
            "bkg_color_estimate": "#222222",
            "bkg_color_pits": "#555555",
            "bkg_color_low_fuel": "#FF2200",
            "show_caption": True,
            "font_color_caption": "#CCCCCC",
            "bkg_color_caption": "#777777",
        },
        "gear": {
            "enable": True,
            "update_delay": 20,
            "position_x": "933",
            "position_y": "452",
            "opacity": 0.9,
            "layout": "0",
            "speed_unit": "0",
            "font_name": "consolas",
            "font_size": 44,
            "font_weight_gear": "bold",
            "font_weight_gauge": "normal",
            "font_weight_indicator": "bold",
            "font_color_gear": "#FFFFFF",
            "font_color_gauge": "#FFFFFF",
            "bkg_color": "#222222",
            "speed_limiter_text": "LIMITER",
            "font_color_speed_limiter": "#111111",
            "bkg_color_speed_limiter": "#FF2200",
            "show_rpm_bar": True,
            "rpm_bar_gap": 2,
            "rpm_bar_height": 7,
            "rpm_bar_edge_height": 2,
            "rpm_safe_multiplier": 0.91,
            "rpm_warn_multiplier": 0.97,
            "bkg_color_rpm_bar": "#FFFFFF",
            "bkg_color_rpm_safe": "#FF2200",
            "bkg_color_rpm_warn": "#00FFFF",
            "bkg_color_rpm_over_rev": "#FF00FF",
            "show_startlights": True,
            "red_lights_text": "READY",
            "green_flag_text": "GREEN",
            "green_flag_duration": 3,
            "font_color_startlights": "#111111",
            "bkg_color_red_lights": "#FF2200",
            "bkg_color_green_flag": "#00FF00",
            "show_start_countdown": "NO_THANKS",
            "font_color_countdown": "#111111",
            "bkg_color_countdown": "#FFFFFF",
            "show_low_fuel": True,
            "low_fuel_for_race_only": True,
            "low_fuel_volume_threshold": 20,
            "low_fuel_lap_threshold": 2,
            "font_color_low_fuel": "#111111",
            "bkg_color_low_fuel": "#EE7700",
            "show_blue_flag": True,
            "blue_flag_for_race_only": True,
            "blue_flag_text": "BLUE",
            "font_color_blue_flag": "#111111",
            "bkg_color_blue_flag": "#55AAFF",
            "show_yellow_flag": True,
            "yellow_flag_for_race_only": True,
            "font_color_yellow_flag": "#111111",
            "bkg_color_yellow_flag": "#FFFF00",
        },
        "instrument": {
            "enable": True,
            "update_delay": 20,
            "position_x": "606",
            "position_y": "240",
            "opacity": 0.9,
            "icon_size": 32,
            "bar_gap": 2,
            "layout": "0",
            "column_index_headlights": 1,
            "column_index_ignition": 2,
            "column_index_clutch": 3,
            "column_index_wheel_lock": 4,
            "column_index_wheel_slip": 5,
            "bkg_color": "#222222",
            "warning_color_ignition": "#00CC00",
            "warning_color_clutch": "#00BBDD",
            "warning_color_wheel_lock": "#EE0000",
            "warning_color_wheel_slip": "#FFAA00",
            "wheel_lock_threshold": 0.2,
            "wheel_slip_threshold": 0.1,
            "wheel_radius_front": 0.320,
            "wheel_radius_rear": 0.320,
            "minimum_speed": 16.5,
            "minimum_samples": 400,
        },
        "pedal": {
            "enable": True,
            "update_delay": 20,
            "position_x": "934",
            "position_y": "321",
            "opacity": 0.9,
            "throttle_color": "#77FF00",
            "brake_color": "#FF2200",
            "clutch_color": "#00C2F2",
            "bkg_color": "#222222",
            "bar_length_scale": 1.0,
            "bar_width_scale": 1.0,
            "bar_gap": 2,
            "full_pedal_height": 5,
            "show_ffb_meter": True,
            "ffb_color": "#888888",
            "ffb_clipping_color": "#FFAA00",
        },
        "pressure": {
            "enable": True,
            "update_delay": 50,
            "position_x": "630",
            "position_y": "610",
            "opacity": 0.9,
            "layout": "0",
            "pressure_unit": "0",
            "font_name": "consolas",
            "font_size": 15,
            "font_weight": "bold",
            "bar_gap": 2,
            "font_color_pressure": "#CCCCCC",
            "bkg_color_pressure": "#222222",
            "show_tyre_load": True,
            "show_tyre_load_ratio": True,
            "font_color_load": "#CCCCCC",
            "bkg_color_load": "#222222",
        },
        "radar": {
            "enable": True,
            "update_delay": 20,
            "position_x": "378",
            "position_y": "240",
            "opacity": 0.9,
            "area_scale": 1.0,
            "vehicle_length": 4.5,
            "vehicle_width": 2.0,
            "vehicle_scale": 0.6,
            "bkg_color": "#000002",
            "player_color": "#000002",
            "player_outline_color": "#FFFFFF",
            "player_outline_width": 3,
            "opponent_color": "#FFFFFF",
            "opponent_color_laps_ahead": "#FF44CC",
            "opponent_color_laps_behind": "#00CCFF",
            "show_center_mark": True,
            "center_mark_color": "#888888",
            "additional_vehicles_front": 4,
            "additional_vehicles_behind": 4,
        },
        "relative": {
            "enable": True,
            "update_delay": 200,
            "position_x": "564",
            "position_y": "451",
            "opacity": 0.9,
            "font_name": "consolas",
            "font_size": 15,
            "font_weight": "bold",
            "font_color_player": "#000000",
            "font_color_same_lap": "#FFFFFF",
            "font_color_laps_ahead": "#FF44CC",
            "font_color_laps_behind": "#00CCFF",
            "bkg_color_place": "#333333",
            "bkg_color_player_place": "#DDDDDD",
            "bkg_color_name": "#222222",
            "bkg_color_player_name": "#CCCCCC",
            "bkg_color_gap": "#222222",
            "bkg_color_player_gap": "#CCCCCC",
            "bar_driver_name_width": 10,
            "bar_gap": 1,
            "show_laptime": True,
            "font_color_laptime": "#AAAAAA",
            "bkg_color_laptime": "#2A2A2A",
            "show_class": True,
            "bar_class_name_width": 4,
            "font_color_class": "#FFFFFF",
            "bkg_color_class": "#333333",
            "show_position_in_class": True,
            "font_color_position_in_class": "#FFFFFF",
            "bkg_color_position_in_class": "#666666",
            "bar_time_gap_width": 5,
            "show_pit_status": True,
            "pit_status_text": "P",
            "font_color_pit": "#000000",
            "bkg_color_pit": "#00CCEE",
            "show_tyre_compound": True,
            "font_color_tyre_compound": "#AAAAAA",
            "bkg_color_tyre_compound": "#2A2A2A",
            "tyre_compound_list": "ABCDEFGH",
            "column_index_place": 1,
            "column_index_driver": 2,
            "column_index_laptime": 3,
            "column_index_position_in_class": 4,
            "column_index_class": 5,
            "column_index_tyre_compound": 7,
            "column_index_time_gap": 8,
            "column_index_pit_status": 9,
            "additional_players_front": 0,
            "additional_players_behind": 0,
        },
        "sectors": {
            "enable": True,
            "update_delay": 100,
            "position_x": "933",
            "position_y": "654",
            "opacity": 0.9,
            "layout": "0",
            "target_time_mode": 0,
            "freeze_duration": 5,
            "font_name": "consolas",
            "font_size": 15,
            "font_weight": "bold",
            "bar_gap": 2,
            "font_color_target_time": "#AAAAAA",
            "bkg_color_target_time": "#222222",
            "font_color_current_time": "#FFFFFF",
            "bkg_color_current_time": "#222222",
            "show_best_sector_time": True,
            "font_color_sector": "#AAAAAA",
            "font_color_sector_highlighted": "#FFFFFF",
            "bkg_color_sector": "#222222",
            "font_color_time_gain": "#22CC22",
            "font_color_time_loss": "#BBAA00",
            "bkg_color_time_gain": "#008800",
            "bkg_color_time_loss": "#887700",
            "always_show_laptime_gap": False,
            "font_color_laptime_gap": "#AAAAAA",
            "bkg_color_laptime_gap": "#222222",
            "show_speed": True,
            "speed_unit": "0",
            "speed_highlight_duration": 5,
            "font_color_speed": "#AAAAAA",
            "font_color_speed_highlighted": "#FFFFFF",
            "bkg_color_speed": "#222222",
            "bkg_color_speed_highlighted": "#0099BB",
            "show_position_lapnumber": True,
            "font_color_position": "#FFFFFF",
            "bkg_color_position": "#222222",
            "font_color_lapnumber": "#FFFFFF",
            "bkg_color_lapnumber": "#222222",
            "last_saved_sector_data": "None",
        },
        "session": {
            "enable": True,
            "update_delay": 200,
            "position_x": "932",
            "position_y": "194",
            "opacity": 0.9,
            "font_name": "consolas",
            "font_size": 15,
            "font_weight": "bold",
            "bar_gap": 2,
            "show_clock": True,
            "show_lapnumber": True,
            "show_place": True,
            "clock_format": "%H:%M %p",
            "lapnumber_text": "Lap ",
            "font_color_clock": "#FFFFFF",
            "font_color_racelength": "#FFFFFF",
            "font_color_lapnumber": "#000000",
            "font_color_place": "#000000",
            "bkg_color_clock": "#222222",
            "bkg_color_racelength": "#880088",
            "bkg_color_lapnumber": "#FFFFFF",
            "bkg_color_place": "#00FFFF",
            "bkg_color_maxlap_warn": "#FF0000",
        },
        "steering": {
            "enable": True,
            "update_delay": 20,
            "position_x": "1023",
            "position_y": "329",
            "opacity": 0.9,
            "steering_color": "#FFAA00",
            "bkg_color": "#222222",
            "bar_length_scale": 0.5,
            "bar_height_scale": 1.0,
            "bar_edge_width": 2,
            "bar_edge_color": "#FFAA00",
            "show_scale_mark": True,
            "scale_mark_color": "#555555",
        },
        "stint": {
            "enable": True,
            "update_delay": 200,
            "position_x": "600",
            "position_y": "290",
            "opacity": 0.9,
            "font_name": "consolas",
            "font_size": 15,
            "font_weight": "bold",
            "bar_gap": 2,
            "fuel_unit": 0,
            "tyre_compound_list": "ABCDEFGH",
            "font_color_laps": "#333333",
            "font_color_wear": "#333333",
            "font_color_fuel": "#333333",
            "font_color_time": "#333333",
            "bkg_color_laps": "#FFD42A",
            "bkg_color_wear": "#FFFFFF",
            "bkg_color_fuel": "#FFD42A",
            "bkg_color_time": "#FFFFFF",
            "font_color_last_stint_laps": "#FFFFFF",
            "font_color_last_stint_wear": "#FFFFFF",
            "font_color_last_stint_fuel": "#FFFFFF",
            "font_color_last_stint_time": "#FFFFFF",
            "bkg_color_last_stint_laps": "#808080",
            "bkg_color_last_stint_wear": "#999999",
            "bkg_color_last_stint_fuel": "#808080",
            "bkg_color_last_stint_time": "#999999",
        },
        "temperature": {
            "enable": True,
            "update_delay": 50,
            "position_x": "729",
            "position_y": "611",
            "opacity": 0.9,
            "layout": "0",
            "temp_unit": "0",
            "color_swap_tyre": "0",
            "color_swap_brake": "0",
            "font_name": "consolas",
            "font_size": 15,
            "font_weight": "bold",
            "bar_gap": 2,
            "font_color_tyre": "#000000",
            "bkg_color_tyre": "#222222",
            "font_color_brake": "#000000",
            "bkg_color_brake": "#222222",
        },
        "timing": {
            "enable": True,
            "update_delay": 50,
            "position_x": "680",
            "position_y": "350",
            "opacity": 0.9,
            "layout": "0",
            "font_name": "consolas",
            "font_size": 15,
            "font_weight": "bold",
            "bar_gap": 2,
            "font_color_best": "#000000",
            "font_color_last": "#FFFFFF",
            "font_color_current": "#88FF88",
            "font_color_estimated": "#FFFF88",
            "bkg_color_best": "#FFFFFF",
            "bkg_color_last": "#222222",
            "bkg_color_current": "#222222",
            "bkg_color_estimated": "#222222",
        },
        "wear": {
            "enable": True,
            "update_delay": 50,
            "position_x": "830",
            "position_y": "610",
            "opacity": 0.9,
            "layout": "0",
            "font_name": "consolas",
            "font_size": 15,
            "font_weight": "bold",
            "font_color_remaining": "#22CC22",
            "font_color_last_wear": "#CCCCCC",
            "font_color_lifespan": "#CCCC22",
            "font_color_warning": "#FF4444",
            "bar_gap": 2,
            "bkg_color": "#222222",
            "show_realtime_wear": True,
            "seconds_before_showing_realtime_wear": 10,
            "show_lifespan": True,
            "warning_threshold_remaining": 30,
            "warning_threshold_wear": 3,
            "warning_threshold_laps": 5,
            "column_index_remaining": 0,
            "column_index_last_wear": 1,
            "column_index_lifespan": 2,
        },
        "weather": {
            "enable": True,
            "update_delay": 200,
            "position_x": "933",
            "position_y": "284",
            "opacity": 0.9,
            "temp_unit": "0",
            "font_name": "consolas",
            "font_size": 15,
            "font_weight": "bold",
            "bar_gap": 2,
            "font_color": "#FFFFFF",
            "bkg_color": "#222222",
        },
        "wheel": {
            "enable": True,
            "update_delay": 50,
            "position_x": "799",
            "position_y": "240",
            "opacity": 0.9,
            "font_name": "consolas",
            "font_size": 15,
            "font_weight": "bold",
            "font_color": "#FFFFFF",
            "bar_gap": 2,
            "bkg_color": "#222222",
            "bkg_color_bottoming": "#FF2200",
            "rideheight_offset_front": 0,
            "rideheight_offset_rear": 0,
            "wheelbase": 2800,
            "show_caption": True,
            "font_color_caption": "#CCCCCC",
            "bkg_color_caption": "#777777",
        },  
        "topspeed": {
			"enable": True,
			"update_delay": 100,	
			"position_x": "933",
			"position_y": "431",
			"opacity": 0.9,
			"font_name": "consolas",
			"font_size": 15,
			"font_weight": "bold",
			"bar_gap": 2,
			"font_color_topspeed": "#FFFFFF",
			"bkg_color_topspeed": "#222222",
			"speed_unit": "0",
    },
    }

    def __init__(self):
        self.active_widget_list = []  # create active widget list
        self.setting_user = {}
        self.overlay = {}

    def load_preset_list(self):
        """Load preset list"""
        raw_cfg_list = [(os.path.getmtime(f"{self.filepath}{data}"), data[:-5])
                        for data in os.listdir(self.filepath) if data.endswith(".json")]
        raw_cfg_list.sort(reverse=True)  # sort by file modified date

        if raw_cfg_list:
            cfg_list = [data[1] for data in raw_cfg_list
                        if re.search('backup', data[1].lower()) is None  # ignore backup file
                        and re.search('classes', data[1].lower()) is None  # ignore classes file
                        ]
        else:
            cfg_list = ["default"]
        return cfg_list

    def load(self):
        """Load & validate setting"""
        try:
            # Read JSON file
            with open(f"{self.filepath}{self.filename}", "r", encoding="utf-8") as jsonfile:
                setting_user_unsorted = json.load(jsonfile)

            # Verify setting
            verify_setting(setting_user_unsorted, self.setting_default)

            # Move overlay setting to the top of setting
            self.setting_user["overlay"] = setting_user_unsorted["overlay"]
            setting_user_unsorted.pop("overlay")

            # Sort rest of setting in alphabetical order
            for item in sorted(setting_user_unsorted):
                self.setting_user[item] = setting_user_unsorted[item]

            # Save setting to JSON file
            self.save()
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            self.backup()
            self.create()
            self.save()

        # Assign base setting
        self.overlay = self.setting_user["overlay"]

    def save(self):
        """Save setting to file"""
        with open(f"{self.filepath}{self.filename}", "w", encoding="utf-8") as jsonfile:
            json.dump(self.setting_user, jsonfile, indent=4)

    def create(self):
        """Create default setting"""
        self.setting_user = copy.deepcopy(self.setting_default)

    def backup(self):
        """Backup invalid file"""
        try:
            time_stamp = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
            shutil.copy(f"{self.filepath}{self.filename}", f"{self.filepath}{self.filename[:-5]}-backup {time_stamp}.json")
        except FileNotFoundError:
            pass


class VehicleClass:
    """Vehicle class dictionary"""
    filepath = PATH_CLASSES
    filename = "classes.json"
    classdict_default = {
            "Hypercar": {
                "HP": "#FF4400"
            },
            "LMP1": {
                "LMP1": "#FF00AA"
            },
            "LMP2": {
                "LMP2": "#0088FF"
            },
            "LMP3": {
                "LMP3": "#0044AA"
            },
            "GTE": {
                "GTE": "#00CC44"
            },
            "GT3": {
                "GT3": "#CC6600"
            },
            "DPi": {
                "DPi": "#0044AA"
            },
            "FR3.5_2014": {
                "FR35": "#4488AA"
            },
            "Formula Pro": {
                "FPro": "#FF3300"
            },
            "WriteMatchedNameHere": {
                "ReplaceClassNameHere": "#FFFFFF"
            },
        }

    def __init__(self):
        self.classdict_user = {}
        self.load()

    def load(self):
        """Load dictionary file"""
        try:
            # Load file
            with open(f"{self.filepath}{self.filename}", "r", encoding="utf-8") as jsonfile:
                self.classdict_user = json.load(jsonfile)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            # create a default copy if not found
            self.classdict_user = copy.deepcopy(self.classdict_default)
            self.save()

    def save(self):
        """Save dictionary to file"""
        with open(f"{self.filepath}{self.filename}", "w", encoding="utf-8") as jsonfile:
            json.dump(self.classdict_user, jsonfile, indent=4)


def check_invalid_key(target, origin, dict_user):
    """First step, check & remove invalid key from user list"""
    for _, key in enumerate(target):  # loop through user key list
        if key not in origin:  # check each user key in default list
            dict_user.pop(key)  # remove invalid key


def check_missing_key(target, origin, dict_user, dict_def):
    """Second step, adding missing default key to user list"""
    for _, key in enumerate(target):  # loop through default key list
        if key not in origin:  # check each default key in user list
            dict_user[key] = dict_def[key]  # add missing item to user


def check_key(dict_user, dict_def):
    """Create key-only check list, then validate key"""
    key_list_def = list(dict_def)
    key_list_user = list(dict_user)
    check_invalid_key(key_list_user, key_list_def, dict_user)
    check_missing_key(key_list_def, key_list_user, dict_user, dict_def)


def verify_setting(dict_user, dict_def):
    """Verify setting"""
    # Check top-level key
    check_key(dict_user, dict_def)
    # Check sub-level key
    for item in dict_user.keys():  # list each key lists
        check_key(dict_user[item], dict_def[item])


# Assign setting
cfg = Setting()
cfg.filename = f"{cfg.load_preset_list()[0]}.json"
cfg.load()
