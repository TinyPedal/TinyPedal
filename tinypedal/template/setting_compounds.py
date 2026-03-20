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
Default compounds template
"""

from types import MappingProxyType

from .setting_heatmap import HEATMAP_DEFAULT_TYRE

COMPOUNDINFO_DEFAULT = MappingProxyType({
    "symbol": "?",
    "color": "#AAAAAA",
    "heatmap": HEATMAP_DEFAULT_TYRE,
})

COMPOUNDS_DEFAULT = {
    "Hyper - Soft": {
        "symbol": "S",
        "color": "#AAAAAA",
        "heatmap": "tyre_optimal_80",
    },
    "Hyper - Medium": {
        "symbol": "M",
        "color": "#FFCC00",
        "heatmap": "tyre_optimal_90",
    },
    "Hyper - Hard": {
        "symbol": "H",
        "color": "#EE2200",
        "heatmap": "tyre_optimal_100",
    },
    "Hyper - Wet": {
        "symbol": "W",
        "color": "#00AAFF",
        "heatmap": "tyre_optimal_50",
    },
    "LMP2 - Soft": {
        "symbol": "S",
        "color": "#AAAAAA",
        "heatmap": "tyre_optimal_80",
    },
    "LMP2 - Medium": {
        "symbol": "M",
        "color": "#FFCC00",
        "heatmap": "tyre_optimal_90",
    },
    "LMP2 - Hard": {
        "symbol": "H",
        "color": "#EE2200",
        "heatmap": "tyre_optimal_100",
    },
    "LMP2 - Wet": {
        "symbol": "W",
        "color": "#00AAFF",
        "heatmap": "tyre_optimal_50",
    },
    "LMP2_ELMS - Soft": {
        "symbol": "S",
        "color": "#AAAAAA",
        "heatmap": "tyre_optimal_80",
    },
    "LMP2_ELMS - Medium": {
        "symbol": "M",
        "color": "#FFCC00",
        "heatmap": "tyre_optimal_90",
    },
    "LMP2_ELMS - Hard": {
        "symbol": "H",
        "color": "#EE2200",
        "heatmap": "tyre_optimal_100",
    },
    "LMP2_ELMS - Wet": {
        "symbol": "W",
        "color": "#00AAFF",
        "heatmap": "tyre_optimal_50",
    },
    "LMP3 - Soft": {
        "symbol": "S",
        "color": "#AAAAAA",
        "heatmap": "tyre_optimal_80",
    },
    "LMP3 - Medium": {
        "symbol": "M",
        "color": "#FFCC00",
        "heatmap": "tyre_optimal_90",
    },
    "LMP3 - Hard": {
        "symbol": "H",
        "color": "#EE2200",
        "heatmap": "tyre_optimal_100",
    },
    "LMP3 - Wet": {
        "symbol": "W",
        "color": "#00AAFF",
        "heatmap": "tyre_optimal_50",
    },
    "GTE - Soft": {
        "symbol": "S",
        "color": "#AAAAAA",
        "heatmap": "tyre_optimal_80",
    },
    "GTE - Medium": {
        "symbol": "M",
        "color": "#FFCC00",
        "heatmap": "tyre_optimal_90",
    },
    "GTE - Hard": {
        "symbol": "H",
        "color": "#EE2200",
        "heatmap": "tyre_optimal_100",
    },
    "GTE - Wet": {
        "symbol": "W",
        "color": "#00AAFF",
        "heatmap": "tyre_optimal_50",
    },
    "GT3 - Soft": {
        "symbol": "S",
        "color": "#AAAAAA",
        "heatmap": "tyre_optimal_80",
    },
    "GT3 - Medium": {
        "symbol": "M",
        "color": "#FFCC00",
        "heatmap": "tyre_optimal_90",
    },
    "GT3 - Hard": {
        "symbol": "H",
        "color": "#EE2200",
        "heatmap": "tyre_optimal_100",
    },
    "GT3 - Wet": {
        "symbol": "W",
        "color": "#00AAFF",
        "heatmap": "tyre_optimal_50",
    },
}
