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
Standings data function
"""

from __future__ import annotations

from functools import lru_cache

from ..constant import DATA
from ..decorator import generator_init
from ..module_info import VehicleData, VehiclesInfo


@generator_init
def standings_index_list(
    veh_info: VehiclesInfo,
    is_exclusive_mode: bool,
    is_split_mode: bool,
    min_top_veh: int,
    veh_limit_exclusive: int,
    veh_limit_combined: int,
    veh_limit_other: int,
    veh_limit_player: int,
):
    """Generate standings index list"""
    min_top_veh = min_top_vehicles_in_class(min_top_veh)
    veh_limit_exclusive = max_vehicles_in_class(veh_limit_exclusive, min_top_veh, 2)
    veh_limit_combined = max_vehicles_in_class(veh_limit_combined, min_top_veh, 2)
    veh_limit_other = max_vehicles_in_class(veh_limit_other, min_top_veh, 0)
    veh_limit_player = max_vehicles_in_class(veh_limit_player, min_top_veh, 2)

    dataset_temp = []
    standings_index_list = DATA.STANDINGS_DEFAULT
    last_veh_total = -1
    # Init list
    veh_info.updateStandingsIndex = True

    while True:
        yield standings_index_list

        if veh_info.updateStandingsIndex:
            veh_info.updateStandingsIndex = False

            # Update vehicle dataset
            active_dataset = veh_info.activeDataSet
            veh_total = len(active_dataset)
            if last_veh_total != veh_total:
                last_veh_total = veh_total
                dataset_temp[:] = active_dataset

            plr_data = veh_info.playerData
            # Optimize for one car
            if veh_total <= 1:
                standings_index_list = DATA.STANDINGS_DEFAULT
            # Single class exclusive list
            elif is_exclusive_mode:
                standings_index_list = tuple(
                    standings_index_from_same_class(
                        dataset_temp,
                        min_top_veh,
                        veh_limit_exclusive,
                        plr_data.vehicleClass,
                        plr_data.positionInClass,
                    )
                )
            # Multi-class split list
            elif is_split_mode:
                dataset_temp.sort(key=sort_by_class_group)
                standings_index_list = tuple(
                    standings_index_from_all_classes(
                        dataset_temp,
                        min_top_veh,
                        veh_limit_other,
                        veh_limit_player,
                        plr_data.vehicleClass,
                        plr_data.positionInClass,
                    )
                )
            # Mixed class list
            else:
                dataset_temp.sort(key=sort_by_overall)
                standings_index_list = tuple(
                    calc_standings_index(
                        dataset_temp,
                        min_top_veh,
                        veh_limit_combined,
                        plr_data.positionOverall,
                    )
                )


def standings_index_from_all_classes(
    veh_dataset: list[VehicleData],
    min_top_veh: int,
    veh_limit_other: int,
    veh_limit_player: int,
    plr_class_name: str,
    plr_class_place: int,
):
    """Generate standings index list from all classes"""
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
    veh_dataset: list[VehicleData],
    min_top_veh: int,
    veh_limit_player: int,
    plr_class_name: str,
    plr_class_place: int,
):
    """Generate standings index list from same class only"""
    plr_class_data = (data for data in veh_dataset if plr_class_name == data.vehicleClass)
    class_list = sorted(plr_class_data, key=sort_by_class)
    if class_list:
        yield from calc_standings_index(class_list, min_top_veh, veh_limit_player, plr_class_place)
    else:
        yield -1


def calc_standings_index(
    veh_dataset: list[VehicleData],
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


def split_class_list(veh_dataset: list[VehicleData]):
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

    Args:
        min_top_veh: value range limited in 1 to 5
    """
    return int(min(max(min_top_veh, 1), 5))


def max_vehicles_in_class(max_cls_veh: int, min_top_veh: int, min_add_veh: int = 0) -> int:
    """Maximum number of vehicles in class list

    Args:
        max_cls_veh: maximum vehicles per class limit
        min_top_veh: minimum top vehicles limit
        min_add_veh: minimum addition vehicles limit (for class has local player)
    """
    return max(int(max_cls_veh), min_top_veh + min_add_veh)


# Sorting function
def sort_by_class(data: VehicleData) -> tuple[str, int]:
    """Sort by class"""
    return data.vehicleClass, data.positionOverall


def sort_by_class_group(data: VehicleData) -> int:
    """Sort by class group"""
    return data.classOrder


def sort_by_overall(data: VehicleData) -> int:
    """Sort by overall position"""
    return data.positionOverall


def sort_by_draw_priority(data: VehicleData) -> int:
    """Sort by draw priority"""
    if data.isPlayer:
        return 0
    return data.inPit * -1000 - data.positionOverall


def sort_by_qualification(data: VehicleData) -> tuple[str, int]:
    """Sort by class & qualification"""
    return data.vehicleClass, data.qualifyOverall
