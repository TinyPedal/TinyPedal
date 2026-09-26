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
Timing
"""

from __future__ import annotations


class TimeScale:
    """Time scale estimate

    Attributes:
        scale: session time scale.
    """

    __slots__ = (
        "last_elapsed_time",
        "last_track_time",
        "scale",
    )

    def __init__(self):
        self.last_elapsed_time = 0.0
        self.last_track_time = 0.0
        self.scale = 0

    def update(self, elapsed_time: float, track_time: float) -> TimeScale:
        """Update time scale estimate"""
        delta_elapsed_time = elapsed_time - self.last_elapsed_time
        delta_track_time = track_time - self.last_track_time
        if delta_elapsed_time > 5 and delta_track_time >= 0:
            self.scale = round(delta_track_time / delta_elapsed_time)
            self.last_elapsed_time = elapsed_time
            self.last_track_time = track_time
        elif delta_elapsed_time < 0:
            self.last_elapsed_time = elapsed_time
            self.last_track_time = track_time
        return self


class ValidLapStatus:
    """Valid lap status

    Attributes:
        current: is current lap valid.
        last: is last lap valid.
        timestamp: last recorded lap elapsed time.
    """

    __slots__ = (
        "_resets",
        "current",
        "last",
        "timestamp",
    )

    def __init__(self):
        self._resets = 0
        self.current = True
        self.last = True
        self.timestamp = 0.0

    def update(self, timestamp: float, is_current_valid: bool, resets: int) -> ValidLapStatus:
        """Update current and last lap validation status"""
        if self._resets != resets:
            self._resets = resets
            self.last = self.current = True
        if 10 < timestamp:  # record during current lap
            self.current = is_current_valid
        if self.timestamp > timestamp:  # new lap, store last
            self.last = self.current
        self.timestamp = timestamp
        return self


class LastLapTime:
    """Last lap time (unverified)

    Attributes:
        last: last lap time (unverified).
        timestamp: last recorded lap start time.
    """

    __slots__ = (
        "last",
        "timestamp",
    )

    def __init__(self):
        self.last = 0.0
        self.timestamp = 0.0

    def update(self, timestamp: float) -> float:
        """Update unverified lap time based on lap start time"""
        if self.timestamp != timestamp:
            if 0 < self.timestamp < timestamp:
                self.last = timestamp - self.timestamp
            else:
                self.last = 0.0
            self.timestamp = timestamp
        return self.last


class LastSectorTime:
    """Last sector time

    Attributes:
        index: sector index.
        accumulated: accumulated sector time (seconds) from start of lap to last sector.
        last: last sector time (seconds).
    """

    __slots__ = (
        "accumulated",
        "index",
        "last",
    )

    def __init__(self):
        self.accumulated = 0
        self.index = -1
        self.last = 0

    def update(self, sector_index: int, accumulated: float, last_lap_time: float, is_valid: bool) -> LastSectorTime:
        """Update last sector time (milliseconds)"""
        if self.index != sector_index and self.accumulated != accumulated:
            if not is_valid:
                self.last = 0
            elif sector_index == 0:  # new lap
                self.last = max(last_lap_time - self.accumulated, 0)
            else:
                self.last = max(accumulated - self.accumulated, 0)

            self.accumulated = accumulated
            self.index = sector_index
        return self
