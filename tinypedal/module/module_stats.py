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
Stats module
"""

from __future__ import annotations

from time import localtime, strftime

from .. import calculation as calc
from .. import realtime_state
from ..api_control import api
from ..constant import DATA
from ..decorator import generator_init
from ..module_info import DriverStats, StatsInfo, minfo
from ..userfile.brands import select_brand_name
from ..userfile.car_setup import (
    rename_car_setup_file,
    save_car_setup_file,
    set_car_setup_filename,
    set_car_setup_laptime,
)
from ..userfile.driver_stats import load_driver_stats, save_driver_stats
from ._base import DataModule


class Realtime(DataModule):
    """Delta time data"""

    __slots__ = ()

    def __init__(self, config, module_name):
        super().__init__(config, module_name)

    def update_data(self):
        """Update module data"""
        _event_wait = self._event.wait
        reset = False
        vehicle_resets = None
        update_interval = self.idle_interval

        gen_auto_backup_car_setup = auto_backup_car_setup(
            filepath=self.cfg.path.car_setups,
        )
        gen_record_driver_stats = record_driver_stats(
            output=minfo.stats,
            filepath=self.cfg.path.config,
            vehicle_classification=self.mcfg["vehicle_classification"],
            max_moved_distance=1500 * update_interval,
            podium_by_class=self.mcfg["enable_podium_by_class"]
        )

        while not _event_wait(update_interval):

            # Ignore stats while in spectate or override mode
            if not realtime_state.singleton or realtime_state.spectating or realtime_state.overriding:
                if reset:
                    reset = False  # make sure stats not saved
                    update_interval = self.idle_interval
                continue

            if realtime_state.active or vehicle_resets != realtime_state.resets:
                vehicle_resets = realtime_state.resets

                if not reset:
                    reset = True
                    update_interval = self.active_interval

                gen_record_driver_stats.send(vehicle_resets)

                if self.cfg.telemetry["enable_auto_backup_car_setup"]:
                    gen_auto_backup_car_setup.send(vehicle_resets)

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval


def stats_keys(vehicle_classification: str) -> tuple[str, str]:
    """Stats key names"""
    if vehicle_classification == "Class":
        name = api.read.vehicle.class_name()
    elif vehicle_classification == "Class - Brand":
        brand_name = select_brand_name(api.read.vehicle.vehicle_model())
        class_name = api.read.vehicle.class_name()
        if brand_name:
            name = f"{class_name} - {brand_name}"
        else:  # fallback to class name
            name = class_name
    else:
        name = api.read.vehicle.vehicle_model()
    return api.read.session.track_name(), name


def finish_position(podium_by_class: bool) -> int:
    """Get finish position"""
    # Overall position
    plr_place = api.read.vehicle.place()
    if not podium_by_class:
        return plr_place
    # Position in class
    veh_total = api.read.vehicle.total_vehicles()
    plr_class = api.read.vehicle.class_name()
    total_class_vehicle = 0
    place_higher = 0
    for index in range(veh_total):
        if api.read.vehicle.class_name(index) == plr_class:
            total_class_vehicle += 1
            if api.read.vehicle.place(index) > plr_place:
                place_higher += 1
    return total_class_vehicle - place_higher


@generator_init
def record_driver_stats(
    output: StatsInfo,
    filepath: str,
    vehicle_classification: str,
    max_moved_distance: float,
    podium_by_class: bool,
):
    """Record driver stats"""
    last_reset = None  # reset check
    delayed_save = False

    driver_stats = DriverStats()

    while True:
        reset = yield None

        # Reset
        if last_reset != reset:
            # Save data
            if delayed_save:
                save_driver_stats(
                    key_list=stats_keys(vehicle_classification),
                    stats_update=driver_stats,
                    filepath=filepath,
                )
                delayed_save = False

            # Delay reset until driving
            if not realtime_state.active:
                continue
            last_reset = reset

            # Load driver stats
            driver_stats.reset()
            loaded_stats = load_driver_stats(
                key_list=stats_keys(vehicle_classification),
                filepath=filepath,
            )
            delayed_save = True

            is_pit_lap = 0
            last_lap_number = DATA.MAX_LAPS
            last_elapsed_time = DATA.FLOAT_INF
            laptime_best = DATA.FLOAT_INF
            last_num_penalties = 99999
            fuel_last = 0.0
            last_finish_state = 99999
            gps_last = (DATA.FLOAT_INF, DATA.FLOAT_INF, DATA.FLOAT_INF)

        # General
        lap_number = api.read.lap.completed()
        elapsed_time = api.read.timing.elapsed()
        is_pit_lap |= api.read.vehicle.in_pits()
        session_type = api.read.session.session_type()
        laptime_curr = api.read.timing.current_laptime()

        # Best lap time
        laptime_last = api.read.timing.last_laptime()
        if laptime_curr < 2 and laptime_best > laptime_last > 1:  # validate lap time
            laptime_best = laptime_last
            # Personal best (any session)
            if driver_stats.pb > laptime_last:
                driver_stats.pb = laptime_last
            # Qualifying best
            if session_type == 2:
                if driver_stats.qb > laptime_last:
                    driver_stats.qb = laptime_last
            # Race best
            elif session_type == 4:
                if driver_stats.rb > laptime_last:
                    driver_stats.rb = laptime_last

        # Driven distance
        gps_curr = api.read.vehicle.position_xyz()
        if gps_last != gps_curr:
            moved_distance = calc.distance(gps_last, gps_curr)
            if moved_distance < max_moved_distance:
                driver_stats.meters += moved_distance
            gps_last = gps_curr

        # Laps complete
        if last_lap_number > lap_number:
            last_lap_number = lap_number
        elif last_lap_number < lap_number and laptime_curr > 2:
            if laptime_last > 0: # valid lap check
                driver_stats.valid += 1  # 1 lap at a time
            elif not is_pit_lap:  # only count non-pit invalid lap
                driver_stats.invalid += 1
            is_pit_lap = 0
            last_lap_number = lap_number

        # Seconds spent
        if last_elapsed_time > elapsed_time:
            last_elapsed_time = elapsed_time
        elif last_elapsed_time < elapsed_time:
            if api.read.vehicle.speed() > 1:  # while speed > 1m/s
                driver_stats.seconds += elapsed_time - last_elapsed_time
            last_elapsed_time = elapsed_time

        # Fuel consumed (liter)
        fuel_curr = api.read.engine.fuel()
        if fuel_last < fuel_curr:
            fuel_last = fuel_curr
        elif fuel_last > fuel_curr:
            driver_stats.liters += fuel_last - fuel_curr
            fuel_last = fuel_curr

        # Race session stats
        if session_type == 4:
            # Penalties
            num_penalties = api.read.vehicle.number_penalties()
            if last_num_penalties > num_penalties:
                last_num_penalties = num_penalties
            elif last_num_penalties < num_penalties:
                driver_stats.penalties += num_penalties - last_num_penalties
                last_num_penalties = num_penalties

            # Finish place
            finish_state = api.read.vehicle.finish_state()
            if last_finish_state > finish_state:
                last_finish_state = finish_state
            elif 0 == last_finish_state < finish_state:
                last_finish_state = finish_state
                if finish_state == 1:  # finished
                    driver_stats.races += 1
                    finish_place = finish_position(podium_by_class)
                    if finish_place == 1:
                        driver_stats.wins += 1
                    if finish_place <= 3:
                        driver_stats.podiums += 1

        # Output stats data
        output.metersDriven = driver_stats.meters + loaded_stats.meters


@generator_init
def auto_backup_car_setup(filepath: str):
    """Auto backup car setup"""
    last_reset = None  # reset check
    data_available = False

    best_laptime = DATA.FLOAT_INF
    temp_data = ()
    data_hash = 0
    last_data_hash = 0
    temp_filename = ""

    while True:
        reset = yield None

        # Reset
        if last_reset != reset:
            # Save data
            if data_available:
                # Rename temporary file with additional info after back to garage
                if temp_filename:
                    rename_car_setup_file(
                        filepath=filepath,
                        old_filename=temp_filename,
                        new_filename=f"{temp_filename} - {set_car_setup_laptime(best_laptime)}",
                    )
                data_available = False

            # Delay reset until driving
            if not realtime_state.active:
                continue
            last_reset = reset

            best_laptime = DATA.FLOAT_INF
            temp_filename = ""

        # Get setup data while not in pits
        if not api.read.vehicle.in_pits():
            # Stint best time
            if data_available:
                last_laptime = api.read.timing.last_laptime()
                if 0 < last_laptime < best_laptime:
                    best_laptime = last_laptime
            else:
                temp_data = api.read.vehicle.setup()
                if temp_data:
                    data_available = True
                    data_hash = hash(temp_data)
                    # Save temporary file first
                    if last_data_hash != data_hash:
                        temp_filename = set_car_setup_filename(
                            api.alias,
                            strftime("%Y-%m-%d %H-%M-%S", localtime()),
                            api.read.session.track_name(),
                            api.read.vehicle.class_name(),
                            select_brand_name(api.read.vehicle.vehicle_model()),
                        )
                        save_car_setup_file(
                            filepath=filepath,
                            filename=temp_filename,
                            dataset=temp_data,
                        )
                    # Reset
                    temp_data = ()
                    last_data_hash = data_hash
