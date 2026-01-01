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
Default heatmap template
"""

HEATMAP_DEFAULT_TYRE = "tyre_default"
HEATMAP_DEFAULT_BRAKE = "brake_default"

# key = temperature in Celsius
# value = HEX color code
HEATMAP_DEFAULT = {
    HEATMAP_DEFAULT_TYRE: {
        "-273": "#44F",
        "40": "#84F",
        "60": "#F4F",
        "80": "#F48",
        "100": "#F44",
        "120": "#F84",
        "140": "#FF4",
    },
    HEATMAP_DEFAULT_BRAKE: {
        "-273": "#44F",
        "100": "#48F",
        "200": "#4FF",
        "300": "#4F8",
        "400": "#4F4",
        "500": "#8F4",
        "600": "#FF4",
        "700": "#F84",
        "800": "#F44",
    },
    "tyre_optimal_70": {
        "-273": "#44F",
        "40": "#48F",
        "50": "#4FF",
        "60": "#4F8",
        "70": "#4F4",
        "80": "#8F4",
        "90": "#FF4",
        "100": "#F84",
        "110": "#F44",
    },
    "tyre_optimal_80": {
        "-273": "#44F",
        "50": "#48F",
        "60": "#4FF",
        "70": "#4F8",
        "80": "#4F4",
        "90": "#8F4",
        "100": "#FF4",
        "110": "#F84",
        "120": "#F44",
    },
    "tyre_optimal_90": {
        "-273": "#44F",
        "60": "#48F",
        "70": "#4FF",
        "80": "#4F8",
        "90": "#4F4",
        "100": "#8F4",
        "110": "#FF4",
        "120": "#F84",
        "130": "#F44",
    },
    "tyre_optimal_100": {
        "-273": "#44F",
        "70": "#48F",
        "80": "#4FF",
        "90": "#4F8",
        "100": "#4F4",
        "110": "#8F4",
        "120": "#FF4",
        "130": "#F84",
        "140": "#F44",
    },
    "brake_optimal_300": {
        "-273": "#44F",
        "75": "#48F",
        "150": "#4FF",
        "225": "#4F8",
        "300": "#4F4",
        "375": "#8F4",
        "450": "#FF4",
        "525": "#F84",
        "600": "#F44",
    },
}
