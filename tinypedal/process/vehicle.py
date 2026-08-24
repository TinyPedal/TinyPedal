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
Vehicle function
"""

from __future__ import annotations

from ..regex_pattern import rex_number_extract


def export_wheels(data: list, default: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    """Export wheel data"""
    try:
        return data[0], data[1], data[2], data[3]
    except (IndexError, TypeError, ValueError):
        return default


def expected_usage(value: str, default: float) -> float:
    """Extract expected fuel or energy usage from car setup"""
    try:
        match_obj = rex_number_extract.findall(value)
        assert match_obj is not None
        return float(match_obj[0]) / float(match_obj[1])
    except (AssertionError, ZeroDivisionError, AttributeError, IndexError, TypeError, ValueError):
        return default


def steerlock_to_number(value: str, default: float) -> float:
    """Convert steerlock (degree) string to float value from car setup"""
    try:
        match_obj = rex_number_extract.search(value)
        assert match_obj is not None
        return float(match_obj.group())
    except (AssertionError, AttributeError, TypeError, ValueError):
        return default


def absolute_refilling(dataset: list[dict], default: float) -> float:
    """Get absolute refilling of fuel or virtual energy from next pit"""
    abs_refill = default
    try:
        for data in dataset:
            # Get absolute refilling energy (percent) from raw value
            if data.get("name") == "VIRTUAL ENERGY:":
                abs_refill = float(data["currentSetting"])
                break
            # Get absolute refilling fuel (liter) from raw string
            if data.get("name") == "FUEL:":
                raw_value = data["settings"][data["currentSetting"]]["text"]
                abs_refill = float(rex_number_extract.search(raw_value).group())
                if "gal" in raw_value.lower():  # convert to liter
                    abs_refill *= 3.7854118
                break
    except (AttributeError, TypeError, IndexError, ValueError):
        abs_refill = default
    return abs_refill
