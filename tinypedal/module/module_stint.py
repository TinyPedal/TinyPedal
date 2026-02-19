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
Stint module
"""

from __future__ import annotations

from collections import deque

from .. import calculation as calc
from .. import realtime_state
from ..api_control import api
from ..const_common import FLOAT_INF, MAX_SECONDS
from ..module_info import ConsumptionDataSet, StintData, StintDataSet, minfo
from ..userfile.consumption_history import (
    load_consumption_history_file,
    save_consumption_history_file,
)
from ..userfile.heatmap import select_compound_symbol
from ..validator import generator_init
from ._base import DataModule


class Realtime(DataModule):
    """Stint data"""

    __slots__ = ()

    def __init__(self, config, module_name):
        super().__init__(config, module_name)

    def update_data(self):
        """Update module data"""
        _event_wait = self._event.wait
        reset = False
        update_interval = self.idle_interval

        userpath_fuel_delta = self.cfg.path.fuel_delta

        gen_stint_history = calc_stint_history(
            minfo.history.stintData,
            minfo.history.stintDataSet,
            self.mcfg["minimum_stint_threshold_minutes"] * 60,
            max(self.mcfg["minimum_pitstop_threshold_seconds"], 0.0),
            max(self.mcfg["minimum_tyre_temperature_threshold"], 0.0),
        )

        while not _event_wait(update_interval):
            if realtime_state.active:

                if not reset:
                    reset = True
                    update_interval = self.active_interval

                    combo_name = api.read.session.combo_name()
                    load_consumption_history(userpath_fuel_delta, combo_name)

                # Update consumption history
                if (minfo.delta.lapTimeCurrent < 10
                    and minfo.delta.lapTimeCurrent > 2
                    and minfo.delta.lapTimeLast > 0):
                    update_consumption_history()

                # Update stint history
                next(gen_stint_history)

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval
                    # Trigger save check
                    save_consumption_history(userpath_fuel_delta, combo_name)


def update_consumption_history():
    """Update consumption history"""
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


def update_stint_history(stint_data: StintData, history_data: deque[StintDataSet]):
    """Update stint history"""
    history_data.appendleft(
        StintDataSet(
            totalLaps=stint_data.totalLaps,
            totalTime=stint_data.totalTime,
            totalFuel=stint_data.totalFuel,
            totalEnergy=stint_data.totalEnergy,
            totalTyreWear=stint_data.totalTyreWear,
            lapTimeDelta=stint_data.lapTimeDelta,
            lapTimeConsistency=stint_data.lapTimeConsistency,
            tyreCompound=stint_data.tyreCompound,
        )
    )
    minfo.history.stintDataVersion += 1


@generator_init
def calc_stint_history(
    stint_data: StintData,
    history_data: deque[StintDataSet],
    minimum_stint_seconds: float,
    minimum_pitstop_seconds: float,
    minimum_tyre_temperature: float,
):
    """Stint history stats"""
    # Stint stats
    reset_stint = True
    stint_running = False

    start_laps = 0
    start_time = 0
    start_fuel = 0
    start_energy = 0
    start_wear = 0

    last_time = 0
    last_wear_avg = 0
    last_fuel_curr = 0
    last_energy_curr = 0
    last_time_stop = 0

    # Stint consistency
    pitting = 1
    last_lap_stime = FLOAT_INF
    stint_laps = 0
    stint_time = 0.0
    stint_fastest = MAX_SECONDS
    consistency = 1.0
    delta = 0.0

    while True:
        yield None
        # Read stint data
        lap_stime = api.read.timing.start()
        lap_number = api.read.lap.number()
        elapsed_time = api.read.session.elapsed()
        in_pits = api.read.vehicle.in_pits()
        in_garage = api.read.vehicle.in_garage()
        wear_avg = 100 - sum(api.read.tyre.wear()) * 25
        fuel_curr = minfo.fuel.amountCurrent
        energy_curr = minfo.energy.amountCurrent

        # Ignore stint
        if (
            in_garage  # ignore while in garage
            or api.read.session.pre_race()  # ignore before race starts
            or abs(last_time - elapsed_time) > 4  # ignore game pause
        ):
            reset_stint = True
            if stint_running and stint_data.totalTime >= minimum_stint_seconds:
                update_stint_history(stint_data, history_data)
        elif not in_pits:
            last_fuel_curr = fuel_curr
            last_energy_curr = energy_curr
            last_wear_avg = wear_avg
            stint_running = True
        elif stint_running:
            if api.read.vehicle.speed() > 1:
                last_time_stop = elapsed_time
            if (last_wear_avg > wear_avg
                or last_fuel_curr < fuel_curr
                or last_energy_curr < energy_curr
                or elapsed_time - last_time_stop > minimum_pitstop_seconds):
                reset_stint = True
                update_stint_history(stint_data, history_data)

        last_time = elapsed_time

        if reset_stint:
            reset_stint = False
            stint_running = False
            # Reset stats
            start_laps = lap_number
            start_time = elapsed_time
            start_fuel = fuel_curr
            start_energy = energy_curr
            start_wear = wear_avg
            # Reset consistency
            pitting = 1
            last_lap_stime = FLOAT_INF
            stint_laps = 0
            stint_time = 0.0
            stint_fastest = MAX_SECONDS
            consistency = 1.0
            delta = 0.0
            # Update compound info once per stint
            class_name = api.read.vehicle.class_name()
            stint_data.tyreCompound = "".join(
                select_compound_symbol(f"{class_name} - {tcmpd_name}")
                for tcmpd_name in api.read.tyre.compound_name()
            )

        if start_fuel < fuel_curr:
            start_fuel = fuel_curr
        if start_energy < energy_curr:
            start_energy = energy_curr

        # Stint delta & consistency
        pitting |= in_pits

        if last_lap_stime != lap_stime:
            last_laptime = lap_stime - last_lap_stime
            if (
                not pitting
                and last_laptime > 0
                and max(api.read.tyre.carcass_temperature()) > minimum_tyre_temperature
            ):
                stint_laps += 1
                stint_time += last_laptime
                if stint_fastest > last_laptime:
                    stint_fastest = last_laptime
                if stint_laps > 1:
                    stint_average = (stint_time - stint_fastest) / (stint_laps - 1)
                    if stint_average > 0:
                        consistency = stint_fastest / stint_average
                        delta = stint_average - stint_fastest
            # Reset
            pitting = (last_laptime <= 0)
            last_lap_stime = lap_stime

        # Current stint data
        stint_data.totalLaps = lap_number - start_laps
        stint_data.totalTime = elapsed_time - start_time
        stint_data.totalFuel = start_fuel - fuel_curr
        stint_data.totalEnergy = start_energy - energy_curr
        stint_data.totalTyreWear = wear_avg - start_wear
        stint_data.lapTimeDelta = delta
        stint_data.lapTimeConsistency = consistency * 100
