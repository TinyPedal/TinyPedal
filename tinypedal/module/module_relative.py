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

from functools import lru_cache

from .. import api, minfo, realtime_state
from ..calculation import asym_max
from ..constant import DATA
from ..module_info import RelativeInfo, VehicleDataSet
from ..validator import state_timer
from ._base import DataModule

TEMP_RELATIVE_AHEAD = [(0.0, -1)] * DATA.MAX_VEHICLES
TEMP_RELATIVE_BEHIND = [(0.0, -1)] * DATA.MAX_VEHICLES
TEMP_DRAW_ORDER = list(range(DATA.MAX_VEHICLES))


class Realtime(DataModule):
    """Relative & standings data"""

    __slots__ = ()

    def update_data(self):
        """Update module data"""
        _event_wait = self._event.wait
        reset = False
        update_interval = self.idle_interval

        output = minfo.relative
        setting_standings = self.cfg.user.setting["standings"]
        last_version_update = None

        gen_one_second_timer = state_timer(1.0)
        active_veh_dataset = []

        while not _event_wait(update_interval):
            if not realtime_state.paused:

                if not reset:
                    reset = True
                    update_interval = self.active_interval
                    last_veh_total = -1

                # Base info
                veh_total = max(api.read.vehicle.total_vehicles(), 1)
                plr_index = api.read.vehicle.player_index()
                plr_place = api.read.vehicle.place()

                # Update active vehicle dataset
                if last_veh_total != veh_total:
                    last_veh_total = veh_total
                    active_veh_dataset[:] = minfo.vehicles.dataSet[:veh_total]

                # Update vehicle relative
                update_relative_data(
                    output,
                    veh_total,
                    plr_index,
                    next(gen_one_second_timer),
                )

                # Update vehicle class position info
                active_veh_dataset.sort(key=sort_by_class)
                class_count = update_position_in_class(active_veh_dataset)
                plr_class_name = minfo.vehicles.playerData.vehicleClass
                plr_class_place = minfo.vehicles.playerData.positionInClass

                # Check setting
                if last_version_update != self.cfg.version:
                    last_version_update = self.cfg.version
                    is_exclusive_mode = setting_standings["enable_single_class_exclusive_mode"]
                    is_split_mode = setting_standings["enable_multi_class_split_mode"]
                    min_top_veh = min_top_vehicles_in_class(
                        setting_standings["minimum_top_vehicles"])
                    veh_limit_exclusive = max_vehicles_in_class(
                        setting_standings["maximum_vehicles_exclusive_mode"], min_top_veh, 2)
                    veh_limit_combined = max_vehicles_in_class(
                        setting_standings["maximum_vehicles_combined_mode"], min_top_veh, 2)
                    veh_limit_other = max_vehicles_in_class(
                        setting_standings["maximum_vehicles_per_split_others"], min_top_veh, 0)
                    veh_limit_player = max_vehicles_in_class(
                        setting_standings["maximum_vehicles_per_split_player"], min_top_veh, 2)

                # Create standings index list
                if not setting_standings["enable"] or veh_total <= 1:  # optimize for one car
                    standings_index_list = DATA.STANDINGS_DEFAULT
                elif is_exclusive_mode:  # single class exclusive list
                    standings_index_list = tuple(
                        standings_index_from_same_class(
                            active_veh_dataset,
                            min_top_veh,
                            plr_class_name,
                            plr_class_place,
                            veh_limit_exclusive,
                        )
                    )
                elif is_split_mode and class_count > 1:  # multi-class split list
                    active_veh_dataset.sort(key=sort_class_grouped)
                    standings_index_list = tuple(
                        standings_index_from_all_classes(
                            active_veh_dataset,
                            min_top_veh,
                            plr_class_name,
                            plr_class_place,
                            veh_limit_other,
                            veh_limit_player,
                        )
                    )
                else:  # mixed class list
                    active_veh_dataset.sort(key=sort_class_mixed)
                    standings_index_list = tuple(
                        calc_standings_index(
                            active_veh_dataset,
                            min_top_veh,
                            veh_limit_combined,
                            plr_place,
                        )
                    )

                # Output data
                output.standings = standings_index_list

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval
                    create_reference_place.cache_clear()

        create_reference_place.cache_clear()


def update_relative_data(
    output: RelativeInfo,
    veh_total: int,
    plr_index: int,
    update_relative_delta: bool,
):
    """Get vehicles info: relative time gap, classes, places, laptime"""
    laptime_est = api.read.timing.estimated_laptime()
    plr_time = api.read.timing.estimated_time_into()
    recorded_index = 0
    leader_index = 0
    pitter_index = 0
    draw_order = TEMP_DRAW_ORDER[:veh_total]
    relative_delta_ahead = output.relativeDeltaAhead
    relative_delta_behind = output.relativeDeltaBehind

    for index in range(veh_total):
        in_garage = api.read.vehicle.in_garage(index)
        in_pitlane = api.read.vehicle.in_pits(index) or in_garage
        place_overall = api.read.vehicle.place(index)

        # Update relative time gap list
        if index != plr_index and laptime_est and not in_garage:
            opt_time = api.read.timing.estimated_time_into(index)
            diff_time = opt_time - plr_time
            diff_time_ahead = diff_time_behind = diff_time - diff_time // laptime_est * laptime_est
            if diff_time_ahead < 0:
                diff_time_ahead += laptime_est
            if diff_time_behind > 0:
                diff_time_behind -= laptime_est

            TEMP_RELATIVE_AHEAD[recorded_index] = (
                diff_time_ahead,  # 0 relative time gap
                index,  # 1 player index
            )
            TEMP_RELATIVE_BEHIND[recorded_index] = (
                diff_time_behind,  # 0 relative time gap
                index,  # 1 player index
            )
            recorded_index += 1

            if update_relative_delta:  # update at 1 sec interval
                relative_delta_ahead[index].update(diff_time_ahead)
                relative_delta_behind[index].update(-diff_time_behind)

        # Update draw order list
        if place_overall == 1:  # save leader index
            leader_index = index
        elif in_pitlane:  # swap opponent in pit/garage to start
            draw_order[index], draw_order[pitter_index] = draw_order[pitter_index], draw_order[index]
            pitter_index += 1

    # Finalize draw order list
    if 0 <= leader_index < veh_total and leader_index != draw_order[-1]:  # move leader to end
        leader_pos = draw_order.index(leader_index)
        draw_order[leader_pos], draw_order[-1] = draw_order[-1], draw_order[leader_pos]
    if 0 <= plr_index < veh_total and plr_index != leader_index:   # move player to 2nd end if not leader
        player_pos = draw_order.index(plr_index)
        draw_order[player_pos], draw_order[-2] = draw_order[-2], draw_order[player_pos]

    # Sort output in-place
    relative_ahead = TEMP_RELATIVE_AHEAD[:recorded_index]
    relative_ahead.sort(reverse=True)  # by reversed time gap

    relative_behind = TEMP_RELATIVE_BEHIND[:recorded_index]
    relative_behind.sort(reverse=True)  # by reversed time gap

    # Output data
    output.relativeAhead = relative_ahead
    output.relativeBehind = relative_behind
    output.drawOrder = draw_order


def update_position_in_class(sorted_veh_dataset: list[VehicleDataSet]) -> int:
    """Update vehicle position in class"""
    class_order = 0
    class_count = 0
    last_class_name = None
    place_in_class = 0
    index_ahead = -1
    index_leader = -1
    laptime_last_fastest = DATA.MAX_SECONDS
    data_ahead = None
    data_fastest = None

    for data in sorted_veh_dataset:
        index = data.index
        class_name = data.vehicleClass
        laptime_last = data.lastLapTime

        if last_class_name == class_name:
            place_in_class += 1
            if data_ahead:
                data_ahead.classBehindIndex = index
        else:
            class_order = data.positionOverall * 1000  # order by class leader
            class_count += 1
            last_class_name = class_name  # reset class name
            place_in_class = 1  # reset position counter
            index_ahead = -1  # no opponent ahead of class leader
            index_leader = index
            laptime_last_fastest = DATA.MAX_SECONDS  # reset last fastest
            if data_fastest:  # mark fastest last lap
                data_fastest.isClassFastestLastLap = True
                data_fastest = None  # reset

        if laptime_last_fastest > laptime_last > 0:
            laptime_last_fastest = laptime_last
            data_fastest = data

        data.classOrder = class_order + place_in_class
        data.classAheadIndex = index_ahead
        data.classBehindIndex = -1
        data.classLeaderIndex = index_leader
        data.positionInClass = place_in_class
        data.isClassFastestLastLap = False
        # Store ahead
        index_ahead = index
        data_ahead = data

    if data_fastest:  # mark for last class
        data_fastest.isClassFastestLastLap = True
    return class_count


def standings_index_from_all_classes(
    veh_dataset: list[VehicleDataSet],
    min_top_veh: int,
    plr_class_name: str,
    plr_class_place: int,
    veh_limit_other: int,
    veh_limit_player: int,
):
    """Generate class standings index list from all classes"""
    class_collection = split_class_list(veh_dataset)
    for class_list in class_collection:
        if plr_class_name == class_list[0].vehicleClass:  # match class name
            veh_limit = veh_limit_player
            plr_place = plr_class_place  # 1 position in class
        else:
            veh_limit = veh_limit_other
            plr_place = 0
        yield from calc_standings_index(class_list, min_top_veh, veh_limit, plr_place)


def standings_index_from_same_class(
    veh_dataset: list[VehicleDataSet],
    min_top_veh: int,
    plr_class_name: str,
    plr_class_place: int,
    veh_limit_player: int,
):
    """Generate class standings index list from same class only"""
    class_list = [data for data in veh_dataset if plr_class_name == data.vehicleClass]
    if class_list:
        yield from calc_standings_index(class_list, min_top_veh, veh_limit_player, plr_class_place)
    else:
        yield -1


def calc_standings_index(
    veh_dataset: list[VehicleDataSet],
    min_top_veh: int,
    veh_limit: int,
    plr_place: int,
):
    """Calculate vehicle standings index list"""
    veh_total = len(veh_dataset)
    ref_place_list = create_reference_place(min_top_veh, veh_total, plr_place, veh_limit)
    # Match place from reference list to generate standings player index list
    for ref_index in ref_place_list:
        yield veh_dataset[ref_index].index  # player index
    yield -1  # append an empty index as gap between classes


@lru_cache(maxsize=DATA.MAX_CLASSES)
def create_reference_place(
    min_top_veh: int,
    veh_total: int,
    plr_place: int,
    veh_limit: int,
) -> tuple[int, ...]:
    """Create reference place list"""
    if veh_total <= veh_limit:
        return tuple(range(veh_total))
    if plr_place <= min_top_veh:
        return tuple(range(veh_limit))
    # Find nearby slice range relative to player
    max_cut_range = veh_limit - min_top_veh
    # Number of rear slots, should be equal or less than front slots (exclude player slot)
    rear_cut_count = (max_cut_range - 1) // 2  # exclude player slot, then floor divide
    front_cut_count = max_cut_range - rear_cut_count  # include player slot
    # Find front slice limit
    front_cut_raw = max(plr_place - front_cut_count, min_top_veh)
    # Find rear slice limit
    rear_cut_max = min(front_cut_raw + max_cut_range, veh_total)
    front_cut_max = rear_cut_max - max_cut_range
    return tuple(
        index
        for index in range(rear_cut_max)
        if index < min_top_veh or index >= front_cut_max
    )


def split_class_list(veh_dataset: list[VehicleDataSet]):
    """Split class list into class collection"""
    class_name = veh_dataset[0].vehicleClass
    index_start = 0
    index_end = 0
    for data in veh_dataset:
        opt_class_name = data.vehicleClass
        if opt_class_name == class_name:
            index_end += 1
        elif opt_class_name != class_name:
            class_name = opt_class_name
            yield veh_dataset[index_start:index_end]
            index_start = index_end
            index_end += 1
    # Final split
    yield veh_dataset[index_start:index_end]


def min_top_vehicles_in_class(min_top_veh: int) -> int:
    """Minimum number of top vehicles in class list

    min_top_veh: value range limited in 1 to 5
    """
    return int(asym_max(min_top_veh, 1, 5))


def max_vehicles_in_class(max_cls_veh: int, min_top_veh: int, min_add_veh: int = 0) -> int:
    """Maximum number of vehicles in class list

    max_cls_veh: maximum vehicles per class limit
    min_top_veh: minimum top vehicles limit
    min_add_veh: minimum addition vehicles limit (for class has local player)
    """
    return max(int(max_cls_veh), min_top_veh + min_add_veh)


def sort_class_grouped(data: VehicleDataSet) -> int:
    """Sort by class order"""
    return data.classOrder


def sort_class_mixed(data: VehicleDataSet) -> int:
    """Sort mixed class collection by overall position"""
    return data.positionOverall


def sort_by_class(data: VehicleDataSet) -> tuple[str, int]:
    """Sort by class"""
    return data.vehicleClass, data.positionOverall
