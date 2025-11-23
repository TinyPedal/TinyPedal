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
Sectors module
"""

from __future__ import annotations

from .. import realtime_state
from ..api_control import api
from ..const_common import MAX_SECONDS
from ..module_info import SectorsInfo, minfo
from ..userfile.sector_best import load_sector_best_file, save_sector_best_file
from ..validator import generator_init, valid_sectors
from ._base import DataModule, round6


class Realtime(DataModule):
    """Sectors data"""

    __slots__ = ()

    def __init__(self, config, module_name):
        super().__init__(config, module_name)

    def update_data(self):
        """Update module data"""
        _event_wait = self._event.wait
        reset = False
        update_interval = self.idle_interval

        userpath_sector_best = self.cfg.path.sector_best

        while not _event_wait(update_interval):
            if realtime_state.active:

                if not reset:
                    reset = True
                    update_interval = self.active_interval

                    combo_name = api.read.session.combo_name()
                    session_id = api.read.session.identifier()
                    (best_s_tb, best_s_pb, all_best_s_tb, all_best_s_pb
                     ) = load_sector_best_file(
                        filepath=userpath_sector_best,
                        filename=combo_name,
                        session_id=session_id,
                        defaults=[MAX_SECONDS, MAX_SECONDS, MAX_SECONDS],
                    )

                    if self.mcfg["enable_all_time_best_sectors"]:
                        gen_calc_sectors_session = calc_sectors(None, best_s_tb, best_s_pb)
                        gen_calc_sectors_alltime = calc_sectors(minfo.sectors, all_best_s_tb, all_best_s_pb)
                    else:
                        gen_calc_sectors_session = calc_sectors(minfo.sectors, best_s_tb, best_s_pb)
                        gen_calc_sectors_alltime = calc_sectors(None, all_best_s_tb, all_best_s_pb)

                # Run calculation
                tele_sectors = telemetry_sectors()
                gen_calc_sectors_session.send(tele_sectors)
                gen_calc_sectors_alltime.send(tele_sectors)

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval

                    best_s_tb, best_s_pb, new_best_session = gen_calc_sectors_session.send(tele_sectors)
                    all_best_s_tb, all_best_s_pb, new_best_all = gen_calc_sectors_alltime.send(tele_sectors)
                    if new_best_all or new_best_session:
                        save_sector_best_file(
                            filepath=userpath_sector_best,
                            filename=combo_name,
                            dataset=(
                                session_id,
                                list(map(round6, best_s_tb)),
                                list(map(round6, best_s_pb)),
                                list(map(round6, all_best_s_tb)),
                                list(map(round6, all_best_s_pb))
                            ),
                        )


def telemetry_sectors() -> tuple[int, float, float, float, float]:
    """Telemetry sectors"""
    sector_idx = api.read.lap.sector_index()
    laptime_valid = api.read.timing.last_laptime()
    curr_sector1 = api.read.timing.current_sector1()
    curr_sector2 = api.read.timing.current_sector2()
    last_sector2 = api.read.timing.last_sector2()
    return sector_idx, laptime_valid, curr_sector1, curr_sector2, last_sector2


@generator_init
def calc_sectors(output: SectorsInfo, best_s_tb: list[float], best_s_pb: list[float]):
    """Calculate sectors data"""
    no_delta_s = True
    new_best = False  # save check whether new sector best time is set
    last_sector_idx = -1  # previous recorded sector index value
    delta_s_tb = [0.0] * 3  # deltabest times against all time best sector
    delta_s_pb = [0.0] * 3  # deltabest times against best laptime sector
    prev_s = [MAX_SECONDS, MAX_SECONDS, MAX_SECONDS]  # previous sector times
    laptime_best = sum(best_s_pb)

    while True:
        (sector_idx, laptime_valid, curr_sector1, curr_sector2, last_sector2
         ) = yield best_s_tb, best_s_pb, new_best

        # Update previous & best sector time
        if last_sector_idx != sector_idx:  # keep checking until conditions met

            # While vehicle in S1, update S3 data
            if sector_idx == 0 and laptime_valid > 0 and last_sector2 > 0:
                last_sector_idx = sector_idx  # reset & stop checking

                prev_s[2] = laptime_valid - last_sector2

                # Update (time gap) deltabest bestlap sector 3
                if valid_sectors(best_s_pb[2]):
                    delta_s_pb[2] = prev_s[2] - best_s_pb[2]

                # Update deltabest sector 3
                if valid_sectors(best_s_tb[2]):
                    delta_s_tb[2] = prev_s[2] - best_s_tb[2]
                    no_delta_s = False
                else:
                    no_delta_s = True

                # Save best sector 3 time
                if prev_s[2] < best_s_tb[2]:
                    best_s_tb[2] = prev_s[2]
                    new_best = True

                # Save sector time from personal best laptime
                if laptime_valid < laptime_best and valid_sectors(prev_s):
                    laptime_best = laptime_valid
                    best_s_pb = prev_s.copy()
                    new_best = True

            # While vehicle in S2, update S1 data
            elif sector_idx == 1 and curr_sector1 > 0:
                last_sector_idx = sector_idx  # reset

                prev_s[0] = curr_sector1

                # Update (time gap) deltabest bestlap sector 1
                if valid_sectors(best_s_pb[0]):
                    delta_s_pb[0] = prev_s[0] - best_s_pb[0]

                # Update deltabest sector 1
                if valid_sectors(best_s_tb[0]):
                    delta_s_tb[0] = prev_s[0] - best_s_tb[0]
                    no_delta_s = False
                else:
                    no_delta_s = True

                # Save best sector 1 time
                if prev_s[0] < best_s_tb[0]:
                    best_s_tb[0] = prev_s[0]
                    new_best = True

            # While vehicle in S3, update S2 data
            elif sector_idx == 2 and curr_sector2 > 0 and curr_sector1 > 0:
                last_sector_idx = sector_idx  # reset

                prev_s[1] = curr_sector2 - curr_sector1

                # Update (time gap) deltabest bestlap sector 2
                if valid_sectors(best_s_pb[1]):
                    delta_s_pb[1] = prev_s[1] - best_s_pb[1]

                # Update deltabest sector 2
                if valid_sectors(best_s_tb[1]):
                    delta_s_tb[1] = prev_s[1] - best_s_tb[1]
                    no_delta_s = False
                else:
                    no_delta_s = True

                # Save best sector 2 time
                if prev_s[1] < best_s_tb[1]:
                    best_s_tb[1] = prev_s[1]
                    new_best = True

            # Output sectors data
            if output:
                output.noDeltaSector = no_delta_s
                output.sectorIndex = sector_idx
                output.sectorPrev[:] = prev_s
                output.sectorBestTB[:] = best_s_tb
                output.sectorBestPB[:] = best_s_pb
                output.deltaSectorBestPB[:] = delta_s_pb
                output.deltaSectorBestTB[:] = delta_s_tb
