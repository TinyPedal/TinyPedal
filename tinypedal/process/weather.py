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
Weather forecast function
"""

from __future__ import annotations

from functools import lru_cache
from typing import NamedTuple

from ..const_common import ABS_ZERO_CELSIUS, MAX_SECONDS


class WeatherNode(NamedTuple):
    """Weather forecast node info"""

    start_percent: float = MAX_SECONDS
    sky_type: int = -1
    temperature: float = ABS_ZERO_CELSIUS
    rain_chance: float = -1.0


FORECAST_DEFAULT = (WeatherNode(),)
FORECAST_NODES_RF2 = ("START", "NODE_25", "NODE_50", "NODE_75", "FINISH")


def forecast_rf2(data: dict) -> tuple[WeatherNode, ...]:
    """Get value from weather forecast dictionary, output 5 api data"""
    try:
        output = tuple(
            WeatherNode(
                start_percent=round(index * 0.2, 1),
                sky_type=data[node]["WNV_SKY"]["currentValue"],
                temperature=round(data[node]["WNV_TEMPERATURE"]["currentValue"]),
                rain_chance=round(data[node]["WNV_RAIN_CHANCE"]["currentValue"]),
            )
            for index, node in enumerate(FORECAST_NODES_RF2)
        )
    except (KeyError, TypeError):
        output = FORECAST_DEFAULT
    return output


@lru_cache(maxsize=2)
def forecast_sky_type(sky_type: int, raininess: float) -> int:
    """Correct current sky type index based on current raininess

    Rain percent:
        1-10 drizzle, 11-20 light rain, 21-40 rain, 41-60 heavy rain, 61-100 storm

    Sky type:
        0 Clear
        1 Light Clouds
        2 Partially Cloudy
        3 Mostly Cloudy
        4 Overcast
        5 Cloudy & Drizzle
        6 Cloudy & Light Rain
        7 Overcast & Light Rain
        8 Overcast & Rain
        9 Overcast & Heavy Rain
        10 Overcast & Storm
    """
    if raininess <= 0:
        if sky_type > 4:
            return 4
        return 0
    if 0 < raininess <= 10:
        return 5
    if 10 < raininess <= 15:
        return 6
    if 15 < raininess <= 20:
        return 7
    if 20 < raininess <= 40:
        return 8
    if 40 < raininess <= 60:
        return 9
    if 60 < raininess:
        return 10
    return sky_type
