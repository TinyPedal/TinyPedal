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
    "heatmap": HEATMAP_DEFAULT_TYRE,
})

COMPOUNDS_DEFAULT = {
    "Hyper - Soft": {
        "symbol": "S",
        "heatmap": "tyre_optimal_70",
    },
    "Hyper - Medium": {
        "symbol": "M",
        "heatmap": "tyre_optimal_80",
    },
    "Hyper - Hard": {
        "symbol": "H",
        "heatmap": "tyre_optimal_90",
    },
    "Hyper - Wet": {
        "symbol": "W",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "LMP2 - Soft": {
        "symbol": "S",
        "heatmap": "tyre_optimal_70",
    },
    "LMP2 - Medium": {
        "symbol": "M",
        "heatmap": "tyre_optimal_80",
    },
    "LMP2 - Hard": {
        "symbol": "H",
        "heatmap": "tyre_optimal_90",
    },
    "LMP2 - Wet": {
        "symbol": "W",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "GTE - Soft": {
        "symbol": "S",
        "heatmap": "tyre_optimal_80",
    },
    "GTE - Medium": {
        "symbol": "M",
        "heatmap": "tyre_optimal_90",
    },
    "GTE - Hard": {
        "symbol": "H",
        "heatmap": "tyre_optimal_100",
    },
    "GTE - Wet": {
        "symbol": "W",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "GTE - P2M (Rain)": {
        "symbol": "W",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "GT3 - Soft": {
        "symbol": "S",
        "heatmap": "tyre_optimal_80",
    },
    "GT3 - Medium": {
        "symbol": "M",
        "heatmap": "tyre_optimal_90",
    },
    "GT3 - Hard": {
        "symbol": "H",
        "heatmap": "tyre_optimal_100",
    },
    "GT3 - Wet": {
        "symbol": "W",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "GT3 - P2M (Rain)": {
        "symbol": "W",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "BTCC - Soft": {
        "symbol": "S",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "BTCC - Medium": {
        "symbol": "M",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "BTCC - Hard": {
        "symbol": "H",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "BTCC - Wet": {
        "symbol": "W",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "Hypercar - Soft": {
        "symbol": "S",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "Hypercar - Medium": {
        "symbol": "M",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "Hypercar - Hard": {
        "symbol": "H",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "Hypercar - Wet": {
        "symbol": "W",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "LMP2 - S7M (Soft)": {
        "symbol": "S",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "LMP2 - S8M (Medium)": {
        "symbol": "M",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "LMP2 - S9M (Hard)": {
        "symbol": "H",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "LMP2 - H5M (Inter)": {
        "symbol": "I",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "LMP2 - P2M (Rain)": {
        "symbol": "W",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "LMP3 - S8M (Medium)": {
        "symbol": "M",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
    "LMP3 - P2M (Rain)": {
        "symbol": "W",
        "heatmap": HEATMAP_DEFAULT_TYRE,
    },
}
