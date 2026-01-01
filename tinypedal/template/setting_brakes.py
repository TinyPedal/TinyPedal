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
Default brakes template
"""

from types import MappingProxyType

from .setting_heatmap import HEATMAP_DEFAULT_BRAKE

BRAKEINFO_DEFAULT = MappingProxyType({
    "failure_thickness": 0.0,
    "heatmap": HEATMAP_DEFAULT_BRAKE,
})

BRAKES_DEFAULT = {
    "Hyper - Front Brake": {
        "failure_thickness": 25.0,
        "heatmap": HEATMAP_DEFAULT_BRAKE,
    },
    "Hyper - Rear Brake": {
        "failure_thickness": 25.0,
        "heatmap": HEATMAP_DEFAULT_BRAKE,
    },
    "LMP2 - Front Brake": {
        "failure_thickness": 25.0,
        "heatmap": HEATMAP_DEFAULT_BRAKE,
    },
    "LMP2 - Rear Brake": {
        "failure_thickness": 25.0,
        "heatmap": HEATMAP_DEFAULT_BRAKE,
    },
    "GTE - Front Brake": {
        "failure_thickness": 30.0,
        "heatmap": HEATMAP_DEFAULT_BRAKE,
    },
    "GTE - Rear Brake": {
        "failure_thickness": 30.0,
        "heatmap": HEATMAP_DEFAULT_BRAKE,
    },
    "GT3 - Front Brake": {
        "failure_thickness": 30.0,
        "heatmap": HEATMAP_DEFAULT_BRAKE,
    },
    "GT3 - Rear Brake": {
        "failure_thickness": 30.0,
        "heatmap": HEATMAP_DEFAULT_BRAKE,
    },
}
