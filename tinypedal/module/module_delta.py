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
Delta module
"""

from functools import partial

from .. import calculation as calc
from .. import realtime_state
from ..api_control import api
from ..const_common import (
    DELTA_DEFAULT,
    DELTA_ZERO,
    FLOAT_INF,
    MAX_SECONDS,
    POS_XYZ_ZERO,
)
from ..module_info import minfo
from ..userfile.delta_best import load_delta_best_file, save_delta_best_file
from ..validator import is_same_session, valid_delta_raw, vehicle_position_sync
from ._base import DataModule, round6


class Realtime(DataModule):
    """Delta time data"""

    __slots__ = ()

    def __init__(self, config, module_name):
        super().__init__(config, module_name)

    def update_data(self):
        """Update module data"""
        _event_wait = self._event.wait
        reset = False
        update_interval = self.idle_interval

        userpath_delta_best = self.cfg.path.delta_best
        output = minfo.delta

        last_session_id = ("",-1,-1,-1)
        delta_array_session = DELTA_DEFAULT
        delta_array_stint = DELTA_DEFAULT
        laptime_session_best = MAX_SECONDS
        laptime_stint_best = MAX_SECONDS
        min_delta_distance = self.mcfg["minimum_delta_distance"]

        calc_ema_delta = partial(
            calc.exp_mov_avg,
            calc.ema_factor(min(max(self.mcfg["delta_smoothing_samples"], 1), 100))
        )
        calc_ema_laptime = partial(
            calc.exp_mov_avg,
            calc.ema_factor(min(max(self.mcfg["laptime_pace_samples"], 1), 20))
        )
        laptime_pace_margin = max(self.mcfg["laptime_pace_margin"], 0.1)
        gen_position_sync = vehicle_position_sync()

        while not _event_wait(update_interval):
            if realtime_state.active:

                if not reset:
                    reset = True
                    update_interval = self.active_interval

                    recording = False
                    validating = 0
                    is_pit_lap = 0  # whether pit in or pit out lap

                    gen_position_sync.send(None)
                    combo_name = api.read.session.combo_name()
                    session_id = api.read.session.identifier()

                    # Reset delta session best if not same session
                    if not is_same_session(combo_name, session_id, last_session_id):
                        delta_array_session = DELTA_DEFAULT
                        laptime_session_best = MAX_SECONDS
                        last_session_id = (combo_name, *session_id)

                    delta_array_best, laptime_best = load_delta_best_file(
                        filepath=userpath_delta_best,
                        filename=combo_name,
                        defaults=(DELTA_DEFAULT, MAX_SECONDS)
                    )
                    output.deltaBestData = delta_array_best
                    delta_array_raw = [DELTA_ZERO]  # distance, laptime
                    delta_array_last = DELTA_DEFAULT  # last lap

                    delta_ema_best = 0.0
                    delta_ema_last = 0.0
                    delta_ema_session = 0.0
                    delta_ema_stint = 0.0

                    laptime_curr = 0.0  # current laptime
                    laptime_last = 0.0  # last laptime
                    laptime_pace = init_laptime_pace(laptime_best)  # avearge laptime pace

                    last_lap_stime = FLOAT_INF  # last lap start time
                    pos_recorded = 0.0  # last recorded vehicle position
                    pos_last = 0.0  # last checked vehicle position
                    pos_estimate = 0.0  # estimated vehicle position
                    pos_synced = 0.0  # synced estimated vehicle position
                    pos_synced_last = 0.0  # last synced estimated vehicle position
                    is_pos_synced = False  # vehicle position synced with API
                    gps_last = POS_XYZ_ZERO  # last global position

                # Read telemetry
                lap_stime = api.read.timing.start()
                laptime_curr = max(api.read.timing.current_laptime(), 0)
                laptime_valid = api.read.timing.last_laptime()
                pos_curr = api.read.lap.distance()
                gps_curr = api.read.vehicle.position_xyz()
                in_pits = api.read.vehicle.in_pits()
                is_pit_lap |= in_pits

                # Reset delta stint best if in pit and stopped
                if in_pits and laptime_stint_best != MAX_SECONDS and api.read.vehicle.speed() < 0.1:
                    delta_array_stint = DELTA_DEFAULT
                    laptime_stint_best = MAX_SECONDS

                # Lap start & finish detection
                if lap_stime > last_lap_stime:
                    laptime_last = lap_stime - last_lap_stime
                    if valid_delta_raw(delta_array_raw, laptime_last, 1):  # set end value
                        delta_array_raw.append((round6(pos_last + 10), round6(laptime_last)))
                        delta_array_last = tuple(delta_array_raw)
                        validating = api.read.timing.elapsed()
                    delta_array_raw[:] = DELTA_DEFAULT
                    pos_last = pos_recorded = pos_curr
                    recording = laptime_curr < 1
                    is_pit_lap = 0
                last_lap_stime = lap_stime  # reset

                # 1 sec position distance check after new lap begins
                # Reset to 0 if higher than normal distance
                if 0 < laptime_curr < 1 and pos_curr > 300:
                    pos_last = pos_recorded = pos_curr = 0

                # Update if position value is different & positive
                if 0 <= pos_curr != pos_last:
                    if recording and pos_curr - pos_recorded >= min_delta_distance:
                        delta_array_raw.append((round6(pos_curr), round6(laptime_curr)))
                        pos_recorded = pos_curr
                    pos_last = pos_curr  # reset last position
                    is_pos_synced = True

                # Validating 1s after passing finish line
                if validating:
                    timer = api.read.timing.elapsed() - validating
                    if timer > 10:  # switch off after 10s
                        validating = 0
                    elif (timer > 1 and  # compare current time
                        laptime_valid > 0 and  # is valid laptime
                        abs(laptime_valid - laptime_last) < 0.001):  # is matched laptime
                        # Update laptime pace
                        if not is_pit_lap:
                            # Set initial laptime if invalid, or align to faster laptime
                            if not 0 < laptime_pace < MAX_SECONDS or laptime_valid < laptime_pace:
                                laptime_pace = laptime_valid
                            else:
                                laptime_pace = min(
                                    calc_ema_laptime(laptime_pace, laptime_valid),
                                    laptime_pace + laptime_pace_margin,
                                )
                        # Update delta best list
                        if laptime_best > laptime_last:
                            laptime_best = laptime_last
                            output.deltaBestData = delta_array_best = delta_array_last
                            save_delta_best_file(
                                filepath=userpath_delta_best,
                                filename=combo_name,
                                dataset=delta_array_best,
                            )
                        # Update delta session best list
                        if laptime_session_best > laptime_last:
                            laptime_session_best = laptime_last
                            delta_array_session = delta_array_last
                        # Update delta stint best list
                        if laptime_stint_best > laptime_last:
                            laptime_stint_best = laptime_last
                            delta_array_stint = delta_array_last
                        validating = 0

                # Calc distance
                if gps_last != gps_curr:
                    moved_distance = calc.distance(gps_last, gps_curr)
                    gps_last = gps_curr
                    # Estimate distance into lap
                    if is_pos_synced:
                        pos_estimate = pos_curr
                        is_pos_synced = False
                    else:
                        pos_estimate += moved_distance
                    pos_synced = gen_position_sync.send(pos_estimate)

                # Calc delta
                if pos_synced_last != pos_synced:
                    pos_synced_last = pos_synced
                    delay_update = laptime_curr > 0.3
                    # Smooth delta
                    delta_ema_best = calc_ema_delta(
                        delta_ema_best,
                        calc.delta_telemetry(
                            delta_array_best,
                            pos_synced,
                            laptime_curr,
                            delay_update,
                        ),
                    )
                    delta_ema_last = calc_ema_delta(
                        delta_ema_last,
                        calc.delta_telemetry(
                            delta_array_last,
                            pos_synced,
                            laptime_curr,
                            delay_update,
                        ),
                    )
                    delta_ema_session = calc_ema_delta(
                        delta_ema_session,
                        calc.delta_telemetry(
                            delta_array_session,
                            pos_synced,
                            laptime_curr,
                            delay_update,
                        ),
                    )
                    delta_ema_stint = calc_ema_delta(
                        delta_ema_stint,
                        calc.delta_telemetry(
                            delta_array_stint,
                            pos_synced,
                            laptime_curr,
                            delay_update,
                        ),
                    )

                # Estimated laptime
                laptime_est = laptime_stint_best + delta_ema_stint  # from stint
                if not 0 < laptime_est < MAX_SECONDS:
                    laptime_est = laptime_session_best + delta_ema_session  # fallback to session
                    if not 0 < laptime_est < MAX_SECONDS:
                        laptime_est = laptime_best + delta_ema_best  # fallback to best
                        if not 0 < laptime_est < MAX_SECONDS:
                            laptime_est = 0

                # Output delta time data
                output.deltaBest = delta_ema_best
                output.deltaLast = delta_ema_last
                output.deltaSession = delta_ema_session
                output.deltaStint = delta_ema_stint
                output.isValidLap = laptime_valid > 0
                output.lapTimeCurrent = laptime_curr
                output.lapTimeLast = laptime_last
                output.lapTimeBest = laptime_best
                output.lapTimeEstimated = laptime_est
                output.lapTimeSession = laptime_session_best
                output.lapTimeStint = laptime_stint_best
                output.lapTimePace = laptime_pace
                output.lapDistance = pos_synced

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval
                    last_session_id = (combo_name, *session_id)


def init_laptime_pace(laptime_best: float):
    """Initialize laptime pace value"""
    if 0 < laptime_best < MAX_SECONDS:
        return laptime_best
    return api.read.timing.reference_laptime()
