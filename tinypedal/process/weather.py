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
Weather forecast
"""

from __future__ import annotations

from ..constant import DATA

FORECAST_RF2_DEFAULT = ((
    1.0,  # fraction of forecast start time relative to session length, range 0.0 - 1.0
    -1,  # sky type index, range 0 - 10
    DATA.ABS_ZERO_CELSIUS,  # degrees in Celsius
    0.0  # fraction of rain chance, range 0.0 - 1.0
),)


def forecast_rf2(
    data: dict, default: tuple[tuple[float, int, float, float], ...]
) -> tuple[tuple[float, int, float, float], ...]:
    """Get value from weather forecast dictionary, output 5 api data"""
    try:
        forecast_nodes = (
            (0.0, "START"),
            (0.2, "NODE_25"),
            (0.4, "NODE_50"),
            (0.6, "NODE_75"),
            (0.8, "FINISH"),
        )
        output = tuple(
            (
                start_fraction,
                int(data[node]["WNV_SKY"]["currentValue"]),
                float(data[node]["WNV_TEMPERATURE"]["currentValue"]),
                min(max(float(data[node]["WNV_RAIN_CHANCE"]["currentValue"]) * 0.01, 0.0), 1.0),
            )
            for start_fraction, node in forecast_nodes
        )
    except (KeyError, TypeError, ValueError):
        output = default
    return output
