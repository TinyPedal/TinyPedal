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
Vehicle
"""

from __future__ import annotations

from ..calculation import distance, oriyaw
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


class LastImpact:
    """Calculate last impact time & position based on damage

    Attributes:
        position: last impact position (x, y coordinates).
        timestamp: last impact timestamp.
    """

    __slots__ = (
        "_damage",
        "_impact_refer_x",
        "_impact_refer_y",
        "position",
        "timestamp",
    )

    def __init__(self):
        self._impact_refer_x = (0, 0, -1, 1)  # impact position reference
        self._impact_refer_y = (-1, 1, 0, 0)
        self._damage = [0.0] * 8
        self.position = (0.0, 0.0)
        self.timestamp = 0.0

    def update(self, elapsed_time: float, *damages: float) -> LastImpact:
        """Update last impact time & position

        Damage arguments order:
            0=front, 1=rear, 2=left, 3=right.

        Position order:
            front=Y-1, rear=Y+1, left=X-1, right=X+1.
        """
        impacted = False
        impact_x = impact_y = 0
        # Reset on session changed
        if self.timestamp > elapsed_time:
            self.timestamp = 0.0
            for idx in range(8):
                self._damage[idx] = 0.0
        # Record impact coordinates
        for idx, damage in enumerate(damages):
            if idx > 3:
                break
            if self._damage[idx] != damage:
                if self._damage[idx] > damage:
                    self._damage[idx] = 0.0
                else:
                    self._damage[idx] = damage
                    impacted = True
                    if 1 < idx:  # ignore front, rear
                        impact_x = self._impact_refer_x[idx]
                    if 2 > idx:  # ignore left, right
                        impact_y = self._impact_refer_y[idx]
        # Update impact time
        if impacted:
            self.timestamp = elapsed_time
            self.position = impact_x, impact_y
        return self


class VehicleOrientation:
    """Vehicle orientation

    Attributes:
        last: last x, y coordinates.
        yaw: orientation yaw in radians.
    """

    __slots__ = (
        "last",
        "yaw",
    )

    def __init__(self):
        self.last = (0.0, 0.0)
        self.yaw = 0.0

    def update(self, *pos: float) -> float:
        """Calculate high precision yaw based on coordinates displacement, inaccurate at very low speed"""
        if distance(pos, self.last) > 0.02:
            self.yaw = oriyaw(pos[0] - self.last[0], pos[1] - self.last[1])
            self.last = pos
        return self.yaw


class VehicleSpeed:
    """Vehicle speed estimate based on GPS coordinates

    Attributes:
        speed: estimated GPS speed.
    """

    __slots__ = (
        "_index",
        "_pos",
        "_time",
        "speed",
    )

    def __init__(self):
        self._index = 0
        self._pos = [(0.0, 0.0)] * 10
        self._time = [0.0] * 10
        self.speed = 0.0

    def update(self, elapsed: float, *pos: float) -> float:
        """Calculate speed estimate based on GPS coordinates"""
        if self._time[self._index] == elapsed:
            return self.speed
        # Calculate speed
        offset = self._index + 1 if self._index < 9 else 0
        delta_time = elapsed - self._time[offset]
        if delta_time > 0:
            delta_distance = distance(pos, self._pos[offset])
            self.speed = delta_distance / delta_time
        # Set next index
        if self._index < 9:
            self._index += 1
        else:
            self._index = 0
        # Store data
        self._time[self._index] = elapsed
        self._pos[self._index] = pos
        return self.speed
