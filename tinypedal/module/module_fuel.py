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
Fuel module
"""

from __future__ import annotations

from math import ceil
from typing import Callable

from .. import calculation as calc
from .. import realtime_state
from ..api_control import api
from ..const_common import DELTA_DEFAULT, DELTA_ZERO, FLOAT_INF, POS_XYZ_ZERO
from ..const_file import FileExt
from ..module_info import ConsumptionDataSet, FuelInfo, minfo
from ..userfile.consumption_history import (
    load_consumption_history_file,
    save_consumption_history_file,
)
from ..userfile.fuel_delta import (
    load_fuel_delta_file,
    save_fuel_delta_file,
)
from ..validator import generator_init, valid_delta_raw
from ._base import DataModule, round6


class Realtime(DataModule):
    """Fuel usage data"""

    __slots__ = ()

    def __init__(self, config, module_name):
        super().__init__(config, module_name)

    def update_data(self):
        """Update module data"""
        _event_wait = self._event.wait
        reset = False
        update_interval = self.idle_interval

        userpath_fuel_delta = self.cfg.path.fuel_delta

        while not _event_wait(update_interval):
            if realtime_state.active:

                if not reset:
                    reset = True
                    update_interval = self.active_interval

                    combo_name = api.read.session.combo_name()
                    gen_calc_fuel = calc_consumption(
                        output=minfo.fuel,
                        telemetry_func=detect_consumption_type(),
                        filepath=userpath_fuel_delta,
                        filename=combo_name,
                        extension=FileExt.FUEL,
                        min_delta_distance=self.mcfg["minimum_delta_distance"],
                    )
                    # Reset module output
                    minfo.fuel.reset()
                    load_consumption_history(userpath_fuel_delta, combo_name)

                # Run calculation
                gen_calc_fuel.send(True)

                # Update consumption history
                update_consumption_history()

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval
                    # Trigger save check
                    gen_calc_fuel.send(False)
                    save_consumption_history(userpath_fuel_delta, combo_name)


def update_consumption_history():
    """Update consumption history"""
    if not (10 > minfo.delta.lapTimeCurrent > 2) or minfo.delta.lapTimeLast < 1:
        return

    lap_number = api.read.lap.completed_laps() - 1
    if (
        minfo.history.consumptionDataSet[0].lapTimeLast != minfo.delta.lapTimeLast
        or minfo.history.consumptionDataSet[0].lapNumber != lap_number
    ):
        minfo.history.consumptionDataSet.appendleft(
            ConsumptionDataSet(
                lapNumber=lap_number,
                isValidLap=int(minfo.delta.isValidLap),
                lapTimeLast=minfo.delta.lapTimeLast,
                lastLapUsedFuel=minfo.fuel.lastLapConsumption,
                lastLapUsedEnergy=minfo.energy.lastLapConsumption,
                batteryDrainLast=minfo.hybrid.batteryDrainLast,
                batteryRegenLast=minfo.hybrid.batteryRegenLast,
                tyreAvgWearLast=calc.mean(minfo.wheels.lastLapTreadWear),
                capacityFuel=minfo.fuel.capacity,
            )
        )
        minfo.history.consumptionDataVersion += 1


def load_consumption_history(filepath: str, combo_name: str):
    """Load consumption history"""
    if minfo.history.consumptionDataName != combo_name:
        dataset = load_consumption_history_file(
            filepath=filepath,
            filename=combo_name,
        )
        minfo.history.consumptionDataSet.clear()
        minfo.history.consumptionDataSet.extend(dataset)
        # Update combo info
        minfo.history.consumptionDataName = combo_name
        minfo.history.consumptionDataVersion = hash(combo_name)  # unique start id


def save_consumption_history(filepath: str, combo_name: str):
    """Save consumption history"""
    if minfo.history.consumptionDataVersion != hash(combo_name):
        save_consumption_history_file(
            dataset=minfo.history.consumptionDataSet,
            filepath=filepath,
            filename=combo_name,
        )
        minfo.history.consumptionDataVersion = hash(combo_name)  # reset


def detect_consumption_type() -> Callable:
    """Detect consumption type, return telemetry function"""
    # Pure electric based vehicle
    if (
        api.read.state.identifier() == "RF2"
        and api.read.vehicle.tank_capacity() == 1
        and api.read.emotor.battery_charge() > 0
    ):
        return telemetry_battery
    # Fuel based vehicle
    return telemetry_fuel


def telemetry_fuel() -> tuple[float, float]:
    """Telemetry fuel"""
    return max(api.read.vehicle.tank_capacity(), 0.01), api.read.vehicle.fuel()


def telemetry_battery() -> tuple[float, float]:
    """Telemetry battery, capacity is always 100%"""
    return 100, api.read.emotor.battery_charge() * 100


@generator_init
def calc_consumption(
    output: FuelInfo, telemetry_func: Callable, filepath: str, filename: str, extension: str,
    min_delta_distance: float):
    """Calculate consumption data"""
    recording = False
    delayed_save = False
    validating = 0
    is_pit_lap = 0  # whether pit in or pit out lap

    delta_array_last, used_last_valid, laptime_last = load_fuel_delta_file(
        filepath=filepath,
        filename=filename,
        extension=extension,
        defaults=(DELTA_DEFAULT, 0.0, 0.0)
    )
    delta_array_raw = [DELTA_ZERO]  # distance, fuel used, laptime
    delta_array_temp = DELTA_DEFAULT  # last lap temp
    delta_fuel = 0.0  # delta fuel consumption compare to last lap

    amount_start = -FLOAT_INF  # start fuel reading
    amount_last = 0.0  # last fuel reading
    amount_need_abs = 0.0  # total fuel (absolute) need to finish race
    amount_need_rel = 0.0  # total additional fuel (relative) need to finish race
    amount_end = 0.0  # amount fuel left at the end of stint before pitting
    used_curr = 0.0  # current lap fuel consumption
    used_last_raw = used_last_valid  # raw usage
    used_est = 0.0  # estimated fuel consumption, for calculation only
    est_runlaps = 0.0  # estimate laps current fuel can last
    est_runmins = 0.0  # estimate minutes current fuel can last
    est_empty = 0.0  # estimate empty capacity at end of current lap
    est_pits_late = 0.0  # estimate end-stint pit stop counts
    est_pits_early = 0.0  # estimate end-lap pit stop counts
    used_est_less = 0.0  # estimate fuel consumption for one less pit stop

    last_lap_stime = FLOAT_INF  # last lap start time
    laps_left = 0.0  # amount laps left at current lap distance
    end_timer_laps_left = 0.0  # amount laps left from start of current lap to end of race timer
    pos_recorded = 0.0  # last recorded vehicle position
    pos_last = 0.0  # last checked vehicle position
    pos_estimate = 0.0  # estimated vehicle position
    is_pos_synced = False  # vehicle position synced with API
    gps_last = POS_XYZ_ZERO  # last global position

    while True:
        updating = yield None

        # Save check
        if not updating:
            if delayed_save:
                save_fuel_delta_file(
                    filepath=filepath,
                    filename=filename,
                    extension=extension,
                    dataset=delta_array_last,
                )
            continue

        # Read telemetry
        capacity, amount_curr = telemetry_func()
        lap_stime = api.read.timing.start()
        laptime_curr = api.read.timing.current_laptime()
        time_left = api.read.session.remaining()
        in_garage = api.read.vehicle.in_garage()
        pos_curr = api.read.lap.distance()
        gps_curr = api.read.vehicle.position_xyz()
        laps_done = api.read.lap.completed_laps()
        lap_into = api.read.lap.progress()
        is_pit_lap |= api.read.vehicle.in_pits()
        laptime_last = minfo.delta.lapTimePace

        # Realtime fuel consumption
        if amount_start < amount_curr:
            amount_start = amount_last = amount_curr

        if amount_last < amount_curr:
            if api.read.vehicle.speed() > 1:  # regen check
                used_curr += amount_last - amount_curr
            else:  # pitstop refilling check
                amount_start = amount_curr
            amount_last = amount_curr
        elif amount_last > amount_curr:
            used_curr += amount_last - amount_curr
            amount_last = amount_curr

        # Lap start & finish detection
        if lap_stime > last_lap_stime:
            if not is_pit_lap and valid_delta_raw(delta_array_raw, used_curr, 1):
                delta_array_raw.append((  # set end value
                    round6(pos_last + 10),
                    round6(used_curr),
                    round6(lap_stime - last_lap_stime)
                ))
                delta_array_temp = tuple(delta_array_raw)
                validating = api.read.timing.elapsed()
            delta_array_raw[:] = DELTA_DEFAULT
            pos_last = pos_recorded = pos_curr
            used_last_raw = used_curr
            used_curr = 0
            recording = laptime_curr < 1
            is_pit_lap = 0
        last_lap_stime = lap_stime  # reset

        # Distance desync check at start of new lap, reset if higher than normal distance
        if 0 < laptime_curr < 1 and pos_curr > 300:
            pos_last = pos_recorded = pos_curr = 0

        # Update if position value is different & positive
        if 0 <= pos_curr != pos_last:
            if recording and pos_curr - pos_recorded >= min_delta_distance:
                delta_array_raw.append((round6(pos_curr), round6(used_curr)))
                pos_recorded = pos_curr
            pos_last = pos_curr  # reset last position
            is_pos_synced = True

        # Validating 1s after passing finish line
        if validating:
            timer = api.read.timing.elapsed() - validating
            if timer > 3:  # switch off after 3s
                validating = 0
            elif (timer > 0.3 and  # compare current time
                api.read.timing.last_laptime() > 0):  # is valid laptime
                used_last_valid = used_last_raw
                delta_array_last = delta_array_temp
                delta_array_temp = DELTA_DEFAULT
                delayed_save = True
                validating = 0

        # Calc delta
        if gps_last != gps_curr:
            if is_pos_synced:
                pos_estimate = pos_curr
                is_pos_synced = False
            else:
                pos_estimate += calc.distance(gps_last, gps_curr)
            gps_last = gps_curr
            # Update delta
            delta_fuel = calc.delta_telemetry(
                delta_array_last,
                pos_estimate,
                used_curr,
                laptime_curr > 0.3 and not in_garage,  # 300ms delay
            )

        # Exclude first lap & pit in/out lap
        used_est = calc.end_lap_consumption(
            used_last_valid, delta_fuel, 0 == is_pit_lap < laps_done)

        # Total refuel = laps left * last consumption - remaining fuel
        if api.read.session.lap_type():  # lap-type
            full_laps_left = calc.lap_type_full_laps_remain(
                api.read.lap.maximum(), laps_done)
            laps_left = calc.lap_type_laps_remain(
                full_laps_left, lap_into)
        elif laptime_last > 0:  # time-type race
            end_timer_laps_left = calc.end_timer_laps_remain(
                lap_into, laptime_last, time_left)
            full_laps_left = ceil(end_timer_laps_left)
            laps_left = calc.time_type_laps_remain(
                full_laps_left, lap_into)

        amount_need_abs = laps_left * used_est

        amount_need_rel = amount_need_abs - amount_curr

        amount_end = calc.end_stint_fuel(
            amount_curr, used_curr, used_est)

        est_runlaps = calc.end_stint_laps(
            amount_curr, used_est)

        est_runmins = calc.end_stint_minutes(
            est_runlaps, laptime_last)

        est_empty = calc.end_lap_empty_capacity(
            capacity, amount_curr + used_curr, used_last_valid + delta_fuel)

        est_pits_late = calc.end_stint_pit_counts(
            amount_need_rel, capacity - amount_end)

        est_pits_early = calc.end_lap_pit_counts(
            amount_need_rel, est_empty, capacity - amount_end)

        used_est_less = calc.one_less_pit_stop_consumption(
            est_pits_late, capacity, amount_curr, laps_left)

        output.capacity = capacity
        output.amountStart = amount_start
        output.amountCurrent = amount_curr
        output.amountUsedCurrent = used_curr
        output.amountEndStint = amount_end
        output.neededRelative = amount_need_rel
        output.neededAbsolute = amount_need_abs
        output.lastLapConsumption = used_last_raw
        output.estimatedConsumption = used_last_valid + delta_fuel
        output.estimatedValidConsumption = used_est
        output.estimatedLaps = est_runlaps
        output.estimatedMinutes = est_runmins
        output.estimatedNumPitStopsEnd = est_pits_late
        output.estimatedNumPitStopsEarly = est_pits_early
        output.deltaConsumption = delta_fuel
        output.oneLessPitConsumption = used_est_less
