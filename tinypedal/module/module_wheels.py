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
Wheels module
"""

import logging
from collections import deque

from .. import calculation as calc
from .. import realtime_state
from ..api_control import api
from ..const_common import POS_XY_ZERO, WHEELS_DELTA_DEFAULT, WHEELS_ZERO
from ..module_info import WheelsInfo, minfo
from ..userfile.heatmap import (
    brake_failure_thickness,
    save_brake_failure_thickness,
    set_predefined_brake_name,
)
from ..validator import generator_init
from ._base import DataModule

logger = logging.getLogger(__name__)


class Realtime(DataModule):
    """Wheels data"""

    __slots__ = ()

    def __init__(self, config, module_name):
        super().__init__(config, module_name)

    def update_data(self):
        """Update module data"""
        _event_wait = self._event.wait
        reset = False
        update_interval = self.idle_interval

        gen_wheel_rotation = calc_wheel_rotation(
            output=minfo.wheels,
            max_rot_bias_f=max(self.mcfg["maximum_rotation_difference_front"], 0.00001),
            max_rot_bias_r=max(self.mcfg["maximum_rotation_difference_rear"], 0.00001),
            min_rot_axle=max(self.mcfg["minimum_axle_rotation"], 0.0),
        )
        gen_tyre_wear = calc_tyre_wear(
            output=minfo.wheels,
            min_delta_distance=self.mcfg["minimum_delta_distance"],
        )
        gen_brake_wear = calc_brake_wear(
            output=minfo.wheels,
            min_delta_distance=self.mcfg["minimum_delta_distance"],
        )
        gen_cornering_radius = calc_cornering_radius(
            output=minfo.wheels,
            sampling_interval=self.mcfg["cornering_radius_sampling_interval"],
        )

        while not _event_wait(update_interval):
            if realtime_state.active:

                if not reset:
                    reset = True
                    update_interval = self.active_interval

                # Run calculate
                is_reset = api.read.vehicle.in_garage()

                gen_wheel_rotation.send(is_reset)
                gen_tyre_wear.send(is_reset)
                gen_brake_wear.send(is_reset)
                gen_cornering_radius.send(True)

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval


@generator_init
def calc_wheel_rotation(output: WheelsInfo, max_rot_bias_f: float, max_rot_bias_r: float, min_rot_axle: float):
    """Calculate wheel rotation, radius, locking percent, slip ratio"""
    last_reset = None  # reset check

    vehicle_name = ""
    radius_front_ema = 0.0
    radius_rear_ema = 0.0
    last_accel_max = 0.0
    locking_f = 1.0
    locking_r = 1.0

    while True:
        reset = yield None

        # Reset
        if last_reset != reset:
            last_reset = reset
            last_accel_max = 0.0
            locking_f = 1.0
            locking_r = 1.0
            if vehicle_name != api.read.vehicle.vehicle_name():
                vehicle_name = api.read.vehicle.vehicle_name()
                radius_front_ema = 0.0
                radius_rear_ema = 0.0

        wheel_rot = api.read.wheel.rotation()
        speed = api.read.vehicle.speed()
        accel_max = max(
            abs(api.read.vehicle.accel_lateral()),
            abs(api.read.vehicle.accel_longitudinal()),
        )

        # Get wheel axle rotation and difference
        rot_axle_f = calc.wheel_axle_rotation(wheel_rot[0], wheel_rot[1])
        rot_axle_r = calc.wheel_axle_rotation(wheel_rot[2], wheel_rot[3])
        rot_bias_f = calc.wheel_rotation_bias(rot_axle_f, wheel_rot[0], wheel_rot[1])
        rot_bias_r = calc.wheel_rotation_bias(rot_axle_r, wheel_rot[2], wheel_rot[3])

        if rot_axle_f < -min_rot_axle:
            locking_f = calc.differential_locking_percent(rot_axle_f, wheel_rot[0])
        if rot_axle_r < -min_rot_axle:
            locking_r = calc.differential_locking_percent(rot_axle_r, wheel_rot[2])

        # Record wheel radius value within max rotation difference
        if last_accel_max != accel_max:  # check if game paused
            last_accel_max = accel_max
            d_factor = 2 / max(40 * accel_max, 20)  # scale ema factor with max accel
            # Front average wheel radius
            if rot_axle_f < -min_rot_axle and 0 < rot_bias_f < max_rot_bias_f:
                radius_front_ema = calc.exp_mov_avg(d_factor, radius_front_ema, calc.rot2radius(speed, rot_axle_f))
            # Rear average wheel radius
            if rot_axle_r < -min_rot_axle and 0 < rot_bias_r < max_rot_bias_r:
                radius_rear_ema = calc.exp_mov_avg(d_factor, radius_rear_ema, calc.rot2radius(speed, rot_axle_r))

        # Output wheels data
        output.lockingPercentFront = locking_f
        output.lockingPercentRear = locking_r
        output.slipRatio[0] = calc.slip_ratio(wheel_rot[0], radius_front_ema, speed)
        output.slipRatio[1] = calc.slip_ratio(wheel_rot[1], radius_front_ema, speed)
        output.slipRatio[2] = calc.slip_ratio(wheel_rot[2], radius_rear_ema, speed)
        output.slipRatio[3] = calc.slip_ratio(wheel_rot[3], radius_rear_ema, speed)


@generator_init
def calc_tyre_wear(output: WheelsInfo, min_delta_distance: float):
    """Calculate tyre wear & delta wear"""
    last_reset = None  # reset check

    last_lap_stime = 0.0  # last lap start time
    tread_last = list(WHEELS_ZERO)  # last moment remaining tread
    tread_wear_curr = list(WHEELS_ZERO)  # current lap tread wear
    tread_wear_valid = list(WHEELS_ZERO)  # valid last lap tread wear

    is_pit_lap = 0  # whether pit in or pit out lap
    delta_recording = False
    delta_array_raw = [WHEELS_DELTA_DEFAULT]  # distance, wear diff
    delta_array_last = (WHEELS_DELTA_DEFAULT,)
    is_valid_delta = False
    pos_last = 0.0  # last checked vehicle position

    while True:
        reset = yield None

        # Reset
        if last_reset != reset:
            last_reset = reset
            tread_last[:] = WHEELS_ZERO
            tread_wear_curr[:] = WHEELS_ZERO
            tread_wear_valid[:] = WHEELS_ZERO
            delta_array_raw[:] = (WHEELS_DELTA_DEFAULT,)
            delta_array_last = (WHEELS_DELTA_DEFAULT,)
            is_valid_delta = False
            last_lap_stime = 0.0
            output.lastLapTreadWear[:] = WHEELS_ZERO

        tread_curr_set = api.read.tyre.wear()
        lap_stime = api.read.timing.start()
        laptime_curr = api.read.timing.current_laptime()
        pos_curr = api.read.lap.distance()
        in_pits = api.read.vehicle.in_pits()
        is_pit_lap |= in_pits

        if lap_stime != last_lap_stime:
            last_lap_stime = lap_stime  # reset time stamp counter
            output.lastLapTreadWear[:] = tread_wear_curr
            # Update delta array for non-pit lap
            if len(delta_array_raw) > 1 and not is_pit_lap:
                delta_array_last = tuple(delta_array_raw)
                tread_wear_valid[:] = tread_wear_curr
            elif not is_valid_delta:  # save for first/out lap
                tread_wear_valid[:] = tread_wear_curr
            tread_wear_curr[:] = WHEELS_ZERO
            delta_array_raw[:] = (WHEELS_DELTA_DEFAULT,)
            delta_recording = laptime_curr < 1
            is_valid_delta = len(delta_array_last) > 1
            pos_last = pos_curr
            is_pit_lap = 0

        # Distance desync check at start of new lap, reset if higher than normal distance
        if 0 < laptime_curr < 1 and pos_curr > 300:
            pos_last = pos_curr = 0
        elif pos_last > pos_curr:
            pos_last = pos_curr

        # Update if position value is different & positive
        if delta_recording and pos_curr - pos_last >= min_delta_distance:
            delta_array_raw.append((pos_curr, *tread_wear_curr))
            pos_last = pos_curr

        # Find delta data index
        if is_valid_delta and laptime_curr > 0.3:
            index_higher = calc.binary_search_higher_column(
                delta_array_last, pos_curr, 0, len(delta_array_last) - 1)
        else:
            index_higher = 0

        # Calculate wear difference & accumulated wear
        for idx, tread_curr in enumerate(tread_curr_set):
            tread_curr *= 100  # fraction to percent

            # Ignore wear difference while in pit
            if in_pits:
                wear_diff = 0.0
            else:
                wear_diff = tread_last[idx] - tread_curr
            tread_last[idx] = tread_curr
            if wear_diff > 0:
                tread_wear_curr[idx] += wear_diff

            # Delta wear
            if index_higher > 0:
                delta_wear = tread_wear_curr[idx] - calc.linear_interp(
                    pos_curr,
                    delta_array_last[index_higher - 1][0],
                    delta_array_last[index_higher - 1][idx + 1],
                    delta_array_last[index_higher][0],
                    delta_array_last[index_higher][idx + 1],
                )
            else:
                delta_wear = 0.0

            # Estimate wear
            if is_valid_delta:
                est_wear = tread_wear_valid[idx] + delta_wear
                est_valid_wear = tread_wear_valid[idx] if is_pit_lap else est_wear
            else:
                est_wear = calc.wear_weighted(
                    tread_wear_curr[idx],
                    tread_wear_valid[idx],
                    api.read.lap.progress(),
                )
                est_valid_wear = est_wear

            # Output
            output.currentTreadDepth[idx] = tread_curr
            output.estimatedTreadWear[idx] = est_wear
            output.estimatedValidTreadWear[idx] = est_valid_wear


@generator_init
def calc_brake_wear(output: WheelsInfo, min_delta_distance: float):
    """Calculate brake wear"""
    last_reset = None  # reset check

    last_lap_stime = 0.0  # last lap start time
    brake_last = list(WHEELS_ZERO)  # last moment remaining brake
    brake_wear_curr = list(WHEELS_ZERO)  # current lap brake wear
    brake_wear_valid = list(WHEELS_ZERO)  # valid last lap brake wear
    brake_max_thickness = list(WHEELS_ZERO)  # brake max thickness at start of stint
    failure_record = list(WHEELS_ZERO)  # recorded failure thickness

    is_pit_lap = 0  # whether pit in or pit out lap
    delta_recording = False
    delta_array_raw = [WHEELS_DELTA_DEFAULT]  # distance, wear diff
    delta_array_last = (WHEELS_DELTA_DEFAULT,)
    is_valid_delta = False
    pos_last = 0.0  # last checked vehicle position

    while True:
        reset = yield None

        # Reset
        if last_reset != reset:
            last_reset = reset
            brake_last[:] = WHEELS_ZERO
            brake_wear_curr[:] = WHEELS_ZERO
            brake_wear_valid[:] = WHEELS_ZERO
            brake_max_thickness[:] = WHEELS_ZERO
            delta_array_raw[:] = (WHEELS_DELTA_DEFAULT,)
            delta_array_last = (WHEELS_DELTA_DEFAULT,)
            is_valid_delta = False
            last_lap_stime = 0.0
            output.lastLapBrakeWear[:] = WHEELS_ZERO
            output.failureBrakeThickness[:] = brake_failure_thickness(api.read.vehicle.class_name(), api.read.vehicle.vehicle_name())

        brake_curr_set = api.read.brake.wear()
        if -1.0 in brake_curr_set:
            continue

        lap_stime = api.read.timing.start()
        laptime_curr = api.read.timing.current_laptime()
        pos_curr = api.read.lap.distance()
        in_pits = api.read.vehicle.in_pits()
        is_pit_lap |= in_pits

        if lap_stime != last_lap_stime:
            last_lap_stime = lap_stime  # reset time stamp counter
            output.lastLapBrakeWear[:] = brake_wear_curr
            # Update delta array for non-pit lap
            if len(delta_array_raw) > 1 and not is_pit_lap:
                delta_array_last = tuple(delta_array_raw)
                brake_wear_valid[:] = brake_wear_curr
            elif not is_valid_delta:  # save for first/out lap
                brake_wear_valid[:] = brake_wear_curr
            brake_wear_curr[:] = WHEELS_ZERO
            delta_array_raw[:] = (WHEELS_DELTA_DEFAULT,)
            delta_recording = laptime_curr < 1
            is_valid_delta = len(delta_array_last) > 1
            pos_last = pos_curr
            is_pit_lap = 0

        # Distance desync check at start of new lap, reset if higher than normal distance
        if 0 < laptime_curr < 1 and pos_curr > 300:
            pos_last = pos_curr = 0
        elif pos_last > pos_curr:
            pos_last = pos_curr

        # Update if position value is different & positive
        if delta_recording and pos_curr - pos_last >= min_delta_distance:
            delta_array_raw.append((pos_curr, *brake_wear_curr))
            pos_last = pos_curr

        # Find delta data index
        if is_valid_delta and laptime_curr > 0.3:
            index_higher = calc.binary_search_higher_column(
                delta_array_last, pos_curr, 0, len(delta_array_last) - 1)
        else:
            index_higher = 0

        # Calculate wear difference & accumulated wear
        for idx, brake_curr in enumerate(brake_curr_set):
            brake_curr *= 1000  # meter to millimeter

            # Log brake failure
            if brake_curr > 0:
                failure_record[idx] = brake_curr
            elif failure_record[idx] > 0:
                logger.info(
                    "%s brake failed at %s(mm)",
                    ("Front left", "Front right", "Rear left", "Rear right")[idx],
                    failure_record[idx],
                )
                output.failureBrakeThickness[idx] = round(failure_record[idx], 2)
                save_brake_failure_thickness(
                    brake_name=set_predefined_brake_name(
                        api.read.vehicle.class_name(),
                        api.read.vehicle.vehicle_name(),
                        idx < 2,
                    ),
                    failure=output.failureBrakeThickness[idx],
                )
                failure_record[idx] = 0

            # Calibrate max thickness
            if brake_max_thickness[idx] < brake_curr:
                brake_max_thickness[idx] = brake_curr
                output.maxBrakeThickness[idx] = brake_curr

            # Ignore wear difference while in pit
            if in_pits:
                wear_diff = 0.0
            else:
                wear_diff = brake_last[idx] - brake_curr
            brake_last[idx] = brake_curr
            if wear_diff > 0:
                brake_wear_curr[idx] += wear_diff

            # Delta wear
            if index_higher > 0:
                delta_wear = brake_wear_curr[idx] - calc.linear_interp(
                    pos_curr,
                    delta_array_last[index_higher - 1][0],
                    delta_array_last[index_higher - 1][idx + 1],
                    delta_array_last[index_higher][0],
                    delta_array_last[index_higher][idx + 1],
                )
            else:
                delta_wear = 0.0

            # Estimate wear
            if is_valid_delta:
                est_wear = brake_wear_valid[idx] + delta_wear
                est_valid_wear = brake_wear_valid[idx] if is_pit_lap else est_wear
            else:
                est_wear = max(brake_wear_curr[idx], brake_wear_valid[idx])
                est_valid_wear = est_wear

            # Output
            output.currentBrakeThickness[idx] = brake_curr
            output.estimatedBrakeWear[idx] = est_wear
            output.estimatedValidBrakeWear[idx] = est_valid_wear


@generator_init
def calc_cornering_radius(output: WheelsInfo, sampling_interval: int):
    """Calculate cornering radius"""
    gps_last = POS_XY_ZERO
    min_coords = min(max(sampling_interval, 5), 100)
    coords_array = deque([POS_XY_ZERO] * min_coords * 2, min_coords * 2)

    while True:
        yield None

        gps_curr = (api.read.vehicle.position_longitudinal(), api.read.vehicle.position_lateral())

        # Calculate cornering radius based on tri-coordinates position
        if gps_last != gps_curr:
            gps_last = gps_curr
            coords_array.append(gps_curr)
            arc_center_pos = calc.tri_coords_circle_center(
                *coords_array[0], *coords_array[min_coords], *coords_array[-1])
            output.corneringRadius = calc.distance(coords_array[0], arc_center_pos)
