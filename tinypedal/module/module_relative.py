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
Relative module
"""

from __future__ import annotations

from .. import api, minfo, realtime_state
from ..constant import DATA
from ..module_info import VehicleData
from ..validator import state_timer
from ._base import DataModule


class Realtime(DataModule):
    """Relative & standings data"""

    __slots__ = ()

    def update_data(self):
        """Update module data"""
        _event_wait = self._event.wait
        reset = False
        update_interval = self.idle_interval

        gen_one_second_timer = state_timer(1.0)

        while not _event_wait(update_interval):
            if not realtime_state.paused:

                if not reset:
                    reset = True
                    update_interval = self.active_interval

                # Update vehicle relative
                update_relative_data(
                    minfo.vehicles.activeDataSet,
                    next(gen_one_second_timer),
                )

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval


def update_relative_data(
    active_dataset: tuple[VehicleData, ...],
    update_relative_delta: bool,
) -> None:
    """Update relative time"""
    plt_laptime_est = api.read.timing.estimated_laptime()
    plr_time_into = api.read.timing.estimated_time_into()

    for index, data in enumerate(active_dataset):
        data.estimatedTimeIntoLap = api.read.timing.estimated_time_into(index)

        if not data.isPlayer and data.inPit != 2:
            diff_time = plr_time_into - data.estimatedTimeIntoLap
            diff_time_ahead = diff_time_behind = diff_time - diff_time // plt_laptime_est * plt_laptime_est
            if diff_time_ahead > 0:  # negative=ahead
                diff_time_ahead -= plt_laptime_est
            if diff_time_behind < 0:  # positive=behind
                diff_time_behind += plt_laptime_est

            data.relativeGapAhead = diff_time_ahead
            data.relativeGapBehind = diff_time_behind

            if update_relative_delta:  # update at 1 sec interval
                data.relativeDeltaAhead.update(-diff_time_ahead)
                data.relativeDeltaBehind.update(diff_time_behind)
        else:
            data.relativeGapAhead = -DATA.MAX_SECONDS
            data.relativeGapBehind = DATA.MAX_SECONDS
