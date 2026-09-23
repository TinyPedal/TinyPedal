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

    def check_missing(self, driver: bytes):
        """Check & add missing driver"""
        if driver not in self.data:
            self.data[driver] = self.DEFAULT.copy()

    def update(self, stream: bytes):
        """Update results data"""
        # Check stream
        if self.stream == stream:
            return
        self.stream = stream
        if not stream:
            return
        # Parse stream
        results_data = self.data
        for line in stream.split(b"\n"):
            if not line:
                continue
            # Log incidents
            if line.startswith(b"<Incident"):
                pos_beg = line.find(b">")
                if pos_beg > 8:
                    pos_beg += 1
                    pos_end = line.find(b"(", pos_beg)
                    driver = line[pos_beg:pos_end]
                    self.check_missing(driver)
                    if b"with another vehicle" in line:
                        results_data[driver]["contact_vehicle"] += 1
                    else:
                        results_data[driver]["contact_immovable"] += 1
                continue
            # Log track cuts
            if line.startswith(b"<TrackLimits"):
                if b"No Further Action" not in line:
                    pos_beg = line.find(b"Driver=")
                    if pos_beg > 11:
                        pos_beg += 8
                        pos_end = line.find(b'"', pos_beg)
                        driver = line[pos_beg:pos_end]
                        self.check_missing(driver)
                        results_data[driver]["track_cut"] += 1
