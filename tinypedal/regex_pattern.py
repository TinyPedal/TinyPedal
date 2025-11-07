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
Regular expression, pattern, string constants
"""

import re

# Compiled regex function
rex_hex_color = re.compile(r"^#[0-9A-F]{3}$|^#[0-9A-F]{6}$|^#[0-9A-F]{8}$", flags=re.IGNORECASE)
rex_invalid_char = re.compile(r'[\\/:*?"<>|]')
rex_number_extract = re.compile(r"\d*\.?\d+")

# Bool
CFG_BOOL = (
    # Exact match
    "^active_state$|"
    "^auto_hide$|"
    "^auto_hide_if_not_available$|"
    "^auto_hide_in_private_qualifying$|"
    "^check_for_updates_on_startup$|"
    "^fixed_position$|"
    "^minimize_to_tray$|"
    "^remember_position$|"
    "^remember_size$|"
    "^vr_compatibility$|"
    # Partial match
    "align_center|"
    "enable|"
    "shorten|"
    "show|"
    "swap_upper_caption|"
    "swap_lower_caption|"
    "swap_style|"
    "uppercase"
)

# String with unique validator
CFG_COLOR = "color"
CFG_CLOCK_FORMAT = "clock_format"

# String choice
CFG_API_NAME = "api_name"
CFG_CHARACTER_ENCODING = "character_encoding"
CFG_DELTABEST_SOURCE = "deltabest_source"
CFG_FONT_WEIGHT = "font_weight"
CFG_TARGET_LAPTIME = "target_laptime"
CFG_TEXT_ALIGNMENT = "text_alignment"
CFG_MULTIMEDIA_PLUGIN = "multimedia_plugin"
CFG_STATS_CLASSIFICATION = "vehicle_classification"
CFG_WINDOW_COLOR_THEME = "window_color_theme"

# String common
CFG_FONT_NAME = "font_name"
CFG_HEATMAP = "heatmap"
CFG_USER_PATH = "_path"
CFG_USER_IMAGE = "_image_file"
CFG_STRING = (
    # Exact match
    "^process_id$|"
    "^url_host$|"
    "^LMU$|"
    "^RF2$|"
    # Partial match
    "file_name|"
    "prefix|"
    "sound_format|"
    "suffix|"
    "text|"
    "unit"
)

# Integer
CFG_INTEGER = (
    # Exact match
    "^access_mode$|"
    "^electric_braking_allocation$|"
    "^grid_move_size$|"
    "^lap_time_history_count$|"
    "^leading_zero$|"
    "^manual_steering_range$|"
    "^maximum_saving_attempts$|"
    "^player_index$|"
    "^parts_width$|"
    "^parts_max_height$|"
    "^parts_max_width$|"
    "^position_x$|"
    "^position_y$|"
    "^snap_distance$|"
    "^snap_gap$|"
    "^stint_history_count$|"
    "^window_width$|"
    "^window_height$|"
    # Partial match
    "area_margin|"
    "area_size|"
    "bar_edge_width|"
    "bar_gap|"
    "bar_height|"
    "bar_length|"
    "bar_width|"
    "column_index|"
    "decimal_places|"
    "display_detail_level|"
    "display_height|"
    "display_margin|"
    "display_size|"
    "display_width|"
    "draw_order_index|"
    "font_size|"
    "horizontal_gap|"
    "icon_size|"
    "inner_gap|"
    "layout|"
    "max_queue|"
    "number_of|"
    "samples|"
    "sampling_interval|"
    "sound_volume|"
    "split_gap|"
    "update_interval|"
    "url_port|"
    "vehicles|"
    "vertical_gap"
)

# Filename
CFG_INVALID_FILENAME = (
    # Exact match
    "^$|"
    "^brakes$|"
    "^brands$|"
    "^classes$|"
    "^compounds$|"
    "^config$|"
    "^heatmap$|"
    "^tracks$|"
    # Partial match
    "backup"
)

# API name
API_NAME_RF2 = "rFactor 2"
API_NAME_LMU = "Le Mans Ultimate"
API_NAME_ALIAS = {
    API_NAME_RF2: "RF2",
    API_NAME_LMU: "LMU",
}

# Abbreviation
ABBR_PATTERN = (
    "^id | id$| id |"
    "^ui | ui$| ui |"
    "api|"
    "dpi|"
    "drs|"
    "ffb|"
    "lmu|"
    "p2p|"
    "rpm|"
    "rf2|"
    "url"
)

# Choice dictionary
CHOICE_COMMON = {
    CFG_API_NAME: [API_NAME_RF2, API_NAME_LMU],
    CFG_CHARACTER_ENCODING: ["UTF-8", "ISO-8859-1"],
    CFG_DELTABEST_SOURCE: ["Best", "Session", "Stint", "Last"],
    CFG_FONT_WEIGHT: ["normal", "bold"],
    CFG_TARGET_LAPTIME: ["Theoretical", "Personal"],
    CFG_TEXT_ALIGNMENT: ["Left", "Center", "Right"],
    CFG_MULTIMEDIA_PLUGIN: ["WMF", "DirectShow"],
    CFG_STATS_CLASSIFICATION: ["Class - Brand", "Class", "Vehicle"],
    CFG_WINDOW_COLOR_THEME: ["Light", "Dark"],
}
CHOICE_UNITS = {
    "distance_unit": ["Meter", "Feet"],
    "fuel_unit": ["Liter", "Gallon"],
    "odometer_unit": ["Kilometer", "Mile", "Meter"],
    "power_unit": ["Kilowatt", "Horsepower", "Metric Horsepower"],
    "speed_unit": ["KPH", "MPH", "m/s"],
    "temperature_unit": ["Celsius", "Fahrenheit"],
    "turbo_pressure_unit": ["bar", "psi", "kPa"],
    "tyre_pressure_unit": ["kPa", "psi", "bar"],
}

# Misc
COMMON_TYRE_COMPOUNDS = (
    ("super", "Q"),  # super soft
    ("inter", "I"),  # intermediate
    ("soft", "S"),
    ("med", "M"),  # medium
    ("hard", "H"),
    ("rain|wet", "W"),
    ("slick|dry", "S"),
    ("road|radial|tread", "R"),
    ("bias", "B"),  # bias ply
)
