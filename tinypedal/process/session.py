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
Session statistics
"""

from __future__ import annotations

from types import MappingProxyType


class LMUResults:
    """LMU results data (extracted from results stream)

    Attributes:
        data: results dict, accessing via driver name.
        timestamp: last updated session timestamp.
        stream: last data stream.
    """

    DEFAULT = MappingProxyType({
        "contact_vehicle": 0,
        "contact_immovable": 0,
        "track_cut": 0,
        "penalty": "",
    })

    __slots__ = (
        "data",
        "stream",
        "timestamp",
    )

    def __init__(self):
        self.stream = b""
        self.data = {}
        self.timestamp = 0

    def _get_driver(self, driver: bytes) -> dict:
        """Get driver data, add new if missing"""
        if driver not in self.data:
            self.data[driver] = self.DEFAULT.copy()
        return self.data[driver]

    def _incidents(self, line: str):
        """Log incidents"""
        pos_beg = line.find(b">")
        if pos_beg > 8:
            pos_beg += 1
            pos_end = line.find(b"(", pos_beg)
            if pos_end > pos_beg:
                driver_data = self._get_driver(line[pos_beg:pos_end])
                if b"with another vehicle" in line:
                    driver_data["contact_vehicle"] += 1
                else:
                    driver_data["contact_immovable"] += 1

    def _track_limits(self, line: str):
        """Log track limits"""
        if b"No Further Action" not in line:
            pos_beg = line.find(b"Driver=")
            if pos_beg > 11:
                pos_beg += 8
                pos_end = line.find(b'"', pos_beg)
                if pos_end > pos_beg:
                    driver_data = self._get_driver(line[pos_beg:pos_end])
                    driver_data["track_cut"] += 1

    def _penalty_scored(self, line: str):
        """Log penalty - scored"""
        pos_beg = line.find(b"Driver=")
        if pos_beg > 8:
            pos_beg += 8
            pos_end = line.find(b'"', pos_beg)
            if pos_end > pos_beg:
                driver_data = self._get_driver(line[pos_beg:pos_end])
                if b"Stop/Go" in line:  # stop go
                    penalty_symbol = "S"
                else:  # driver through
                    penalty_symbol = "D"
                driver_data["penalty"] += penalty_symbol

    def _penalty_served(self, line: str):
        """Log penalty - served"""
        pos_beg = line.find(b">")
        if pos_beg > 8:
            pos_beg += 1
            pos_end = line.find(b" served", pos_beg)
            if pos_end > pos_beg:
                driver_data = self._get_driver(line[pos_beg:pos_end])
                if b"Stop/Go" in line:  # stop go
                    penalty_symbol = "S"
                else:  # driver through
                    penalty_symbol = "D"
                driver_data["penalty"] = driver_data["penalty"].replace(penalty_symbol, "", 1)

    def update(self, stream: bytes):
        """Update results data"""
        # Check stream
        if self.stream == stream:
            return
        self.stream = stream
        if not stream:
            return
        # Parse stream
        for line in stream.split(b"\n"):
            if not line:
                continue
            # Log incidents
            if line.startswith(b"<Incident"):
                self._incidents(line)
                continue
            # Log track limits
            if line.startswith(b"<TrackLimits"):
                self._track_limits(line)
                continue
            # Log penalty
            if line.startswith(b"<Penalty"):
                if b"Penalty=" in line:
                    self._penalty_scored(line)
                else:
                    self._penalty_served(line)
                continue
