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

from .. import calculation as calc
from .. import realtime_state
from ..api_control import api
from ..const_common import FLOAT_INF, MAX_SECONDS
from ..module_info import ConsumptionDataSet, HistoryInfo, StintDataSet, minfo
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
        vehicle_resets = None
        update_interval = self.idle_interval

        gen_stint_history = record_stint_history(
            output=minfo.history,
            minimum_stint_seconds=self.mcfg["minimum_stint_threshold_minutes"] * 60,
            minimum_pitstop_seconds=max(self.mcfg["minimum_pitstop_threshold_seconds"], 0.0),
            minimum_tyre_temperature=max(self.mcfg["minimum_tyre_temperature_threshold"], 0.0),
        )
        gen_consumption_history = record_consumption_history(
            output=minfo.history,
            filepath=self.cfg.path.fuel_delta,
        )

        while not _event_wait(update_interval):
            if realtime_state.active or vehicle_resets != realtime_state.resets:
                vehicle_resets = realtime_state.resets

                if not reset:
                    reset = True
                    update_interval = self.active_interval

                # Update history
                gen_consumption_history.send(vehicle_resets)
                gen_stint_history.send(vehicle_resets)

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval


@generator_init
def record_consumption_history(output: HistoryInfo, filepath: str):
    """Update consumption history"""
    last_reset = None  # reset check
    delayed_save = False

    combo_name = ""

    while True:
        reset = yield None

        # Reset
        if last_reset != reset:
            # Save data
            if delayed_save:
                save_consumption_history_file(
                    dataset=output.consumptionDataSet,
                    filepath=filepath,
                    filename=combo_name,
                )
                delayed_save = False

            # Delay reset until driving
            if not realtime_state.active:
                continue
            last_reset = reset

            # Load data
            combo_name = api.read.session.combo_name()
            dataset = load_consumption_history_file(
                filepath=filepath,
                filename=combo_name,
            )
            output.consumptionDataSet.clear()
            output.consumptionDataSet.extend(dataset)
            output.consumptionDataVersion += 1

        # Update at start of lap
        if (
            minfo.delta.lapTimeCurrent > 10
            or minfo.delta.lapTimeCurrent < 2
            or minfo.delta.lapTimeLast <= 0
        ):
            continue

        # Update consumption history
        lap_number = api.read.lap.number()
        if (
            output.consumptionDataSet[0].lapTimeLast != minfo.delta.lapTimeLast
            or output.consumptionDataSet[0].lapNumber != lap_number
        ):
            output.consumptionDataSet.appendleft(
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
            output.consumptionDataVersion += 1
            delayed_save = True


@generator_init
def record_stint_history(
    output: HistoryInfo,
    minimum_stint_seconds: float,
    minimum_pitstop_seconds: float,
    minimum_tyre_temperature: float,
):
    """Record stint history"""
    last_reset = None  # reset check

    stint_data = output.stintDataCurrent
    history_data = output.stintDataSet

    # Stint stats
    reset_stint = True
    stint_running = False
    update_stint_history = False

    start_laps = 0
    start_time = 0
    start_fuel = 0
    start_energy = 0
    start_wear = 0

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
        reset = yield None

        # Read stint data
        lap_stime = api.read.timing.start()
        lap_number = api.read.lap.number()
        elapsed_time = api.read.session.elapsed()
        in_pits = api.read.vehicle.in_pits()
        wear_avg = 100 - sum(api.read.tyre.wear()) * 25
        fuel_curr = minfo.fuel.amountCurrent
        energy_curr = minfo.energy.amountCurrent

        # Ignore stint
        if (
            last_reset != reset  # vehicle resets
            or api.read.session.pre_race()  # ignore before race starts
        ):
            last_reset = reset
            reset_stint = True
            if stint_running and stint_data.totalTime >= minimum_stint_seconds:
                update_stint_history = True
        elif not in_pits:
            last_fuel_curr = fuel_curr
            last_energy_curr = energy_curr
            last_wear_avg = wear_avg
            stint_running = True
        elif stint_running:
            if api.read.vehicle.speed() > 1:
                last_time_stop = elapsed_time
            if (
                last_wear_avg > wear_avg
                or last_fuel_curr < fuel_curr
                or last_energy_curr < energy_curr
                or elapsed_time - last_time_stop > minimum_pitstop_seconds
            ):
                reset_stint = True
                update_stint_history = True

        if update_stint_history:
            update_stint_history = False
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
            output.stintDataVersion += 1

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
            stint_data.tyreCompound = "".join(
                select_compound_symbol(compound_class)
                for compound_class in api.read.tyre.compound_class()
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
