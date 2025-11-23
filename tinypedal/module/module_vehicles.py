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
Vehicles module
"""

from __future__ import annotations

from .. import calculation as calc
from .. import realtime_state
from ..api_control import api
from ..const_common import MAX_METERS, MAX_SECONDS
from ..module_info import VehicleDataSet, VehiclesInfo, minfo
from ..validator import state_timer
from ._base import DataModule


class Realtime(DataModule):
    """Vehicles info"""

    __slots__ = ()

    def __init__(self, config, module_name):
        super().__init__(config, module_name)

    def update_data(self):
        """Update module data"""
        _event_wait = self._event.wait
        reset = False
        update_interval = self.idle_interval

        output = minfo.vehicles
        max_lap_diff_ahead = self.mcfg["lap_difference_ahead_threshold"]
        max_lap_diff_behind = self.mcfg["lap_difference_behind_threshold"]

        gen_low_priority_timer = state_timer(0.2)

        while not _event_wait(update_interval):
            if not realtime_state.paused:

                if not reset:
                    reset = True
                    update_interval = self.active_interval
                    output.dataSetVersion = -1
                    last_veh_total = 0

                veh_total = output.totalVehicles = api.read.vehicle.total_vehicles()
                if veh_total > 0:
                    update_vehicle_data(
                        output,
                        minfo.relative.classes,
                        max_lap_diff_ahead,
                        max_lap_diff_behind,
                        next(gen_low_priority_timer),
                    )

                if last_veh_total != veh_total:
                    last_veh_total = veh_total
                    if veh_total > 0:
                        update_qualify_position(output)

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval


def update_vehicle_data(
    output: VehiclesInfo,
    class_pos_list: list,
    max_lap_diff_ahead: float,
    max_lap_diff_behind: float,
    update_low_priority: bool,
) -> None:
    """Update vehicle data"""
    # General data
    track_length = api.read.lap.track_length()
    in_race = api.read.session.in_race()
    elapsed_time = api.read.timing.elapsed()

    nearest_line = MAX_METERS
    nearest_time_behind = -MAX_SECONDS
    nearest_yellow_ahead = MAX_METERS
    nearest_yellow_behind = -MAX_METERS

    # Local player data
    plr_lap_distance = api.read.lap.distance()
    plr_lap_progress_total = api.read.lap.completed_laps() + calc.lap_progress_distance(plr_lap_distance, track_length)
    plr_laptime_est = api.read.timing.estimated_laptime()
    plr_timeinto_est = api.read.timing.estimated_time_into()

    # Update dataset from all vehicles in current session
    for index, data, class_pos in zip(range(output.totalVehicles), output.dataSet, class_pos_list):
        # Temp var only
        laps_completed = api.read.lap.completed_laps(index)
        lap_distance = api.read.lap.distance(index)
        speed = api.read.vehicle.speed(index)

        # Update high priority info
        data.isPlayer = api.read.vehicle.is_player(index)
        data.currentLapProgress = calc.lap_progress_distance(lap_distance, track_length)
        data.totalLapProgress = laps_completed + data.currentLapProgress
        data.isYellow = speed < 8
        data.inPit = api.read.vehicle.in_paddock(index)
        data.pitTimer.update(api.read.vehicle.slot_id(index), data.inPit, elapsed_time, laps_completed, speed)
        data.worldPositionX = api.read.vehicle.position_longitudinal(index)
        data.worldPositionY = api.read.vehicle.position_lateral(index)

        if data.isPlayer:
            output.playerIndex = index
            if data.isYellow:
                nearest_yellow_ahead = 0.0
                nearest_yellow_behind = 0.0
        else:
            # Relative position & orientation
            plr_pos_x = api.read.vehicle.position_longitudinal()
            plr_pos_y = api.read.vehicle.position_lateral()
            plr_ori_yaw = api.read.vehicle.orientation_yaw_radians()
            opt_ori_yaw = api.read.vehicle.orientation_yaw_radians(index)

            data.relativeOrientationRadians = opt_ori_yaw - plr_ori_yaw
            data.relativeRotatedPositionX, data.relativeRotatedPositionY = calc.rotate_coordinate(
                plr_ori_yaw - 3.14159265,  # plr_ori_rad, rotate view
                data.worldPositionX - plr_pos_x,     # x position related to player
                data.worldPositionY - plr_pos_y,     # y position related to player
            )

            # Relative distance & time gap
            data.relativeStraightDistance = calc.distance(
                (plr_pos_x, plr_pos_y),
                (data.worldPositionX, data.worldPositionY)
            )
            data.isLapped = calc.lap_difference(
                data.totalLapProgress, plr_lap_progress_total,
                max_lap_diff_ahead, max_lap_diff_behind
            ) if in_race else 0

            # Nearest straight line distance (non local players)
            if nearest_line > data.relativeStraightDistance:
                nearest_line = data.relativeStraightDistance
            # Nearest traffic time gap (opponents behind local players)
            if not data.inPit:
                opt_time_behind = calc.circular_relative_distance(
                    plr_laptime_est,
                    plr_timeinto_est,
                    api.read.timing.estimated_time_into(index),
                )
                if 0 > opt_time_behind > nearest_time_behind:
                    nearest_time_behind = opt_time_behind
            # Nearest yellow flag distance
            if data.isYellow:
                opt_rel_distance = calc.circular_relative_distance(
                    track_length, plr_lap_distance, lap_distance)
                if nearest_yellow_ahead > opt_rel_distance >= 0:
                    nearest_yellow_ahead = opt_rel_distance
                if nearest_yellow_behind < opt_rel_distance <= 0:
                    nearest_yellow_behind = opt_rel_distance

        # Update low priority info
        if update_low_priority:
            opt_index_ahead = class_pos[4]
            opt_index_leader = class_pos[6]
            data.positionInClass = class_pos[1]
            data.classBestLapTime = class_pos[3]
            data.isClassFastestLastLap = class_pos[7]

            data.positionOverall = api.read.vehicle.place(index)
            data.lastLapTime = api.read.timing.last_laptime(index)
            data.bestLapTime = api.read.timing.best_laptime(index)
            data.numPitStops = api.read.vehicle.number_pitstops(index, api.read.vehicle.number_penalties(index))
            data.pitRequested = api.read.vehicle.pit_request(index)
            data.driverName = api.read.vehicle.driver_name(index)
            data.vehicleName = api.read.vehicle.vehicle_name(index)
            data.vehicleClass = api.read.vehicle.class_name(index)
            data.tireCompoundFront = f"{data.vehicleClass} - {api.read.tyre.compound_name_front(index)}"
            data.tireCompoundRear = f"{data.vehicleClass} - {api.read.tyre.compound_name_rear(index)}"

            data.gapBehindNext = calc_gap_behind_next(index)
            data.gapBehindLeader = calc_gap_behind_leader(index)
            data.gapBehindNextInClass = calc_time_gap_behind(opt_index_ahead, index, track_length, data.totalLapProgress)
            data.gapBehindLeaderInClass = calc_time_gap_behind(opt_index_leader, index, track_length, data.totalLapProgress)

            data.vehicleIntegrity = api.read.vehicle.integrity(index)
            data.lapTimeHistory.update(api.read.timing.start(index), elapsed_time, data.lastLapTime)

            update_stint_usage(data, laps_completed)

            # Save leader info
            if data.positionOverall == 1:
                output.leaderIndex = index
                output.leaderBestLapTime = data.bestLapTime

    # Output extra info
    output.nearestLine = nearest_line
    output.nearestTraffic = -nearest_time_behind
    output.nearestYellowAhead = nearest_yellow_ahead
    output.nearestYellowBehind = nearest_yellow_behind
    output.dataSetVersion += 1


def update_qualify_position(output: VehiclesInfo) -> None:
    """Update qualify position"""
    temp_class = sorted((
        api.read.vehicle.class_name(index),  # 0 class name
        api.read.vehicle.qualification(index),  # 1 qualification position
        index,  # 2 player index
    ) for index in range(output.totalVehicles))
    # Update position
    qualify_in_class = 0
    last_class_name = None
    for class_name, qualify_overall, plr_index in temp_class:
        if last_class_name != class_name:
            last_class_name = class_name
            qualify_in_class = 1
        else:
            qualify_in_class += 1
        output.dataSet[plr_index].qualifyOverall = qualify_overall
        output.dataSet[plr_index].qualifyInClass = qualify_in_class


def calc_time_gap_behind(
    ahead_index: int,
    behind_index: int,
    track_length: float,
    lap_progress_total: float,
) -> float:
    """Calculate interval behind next in class"""
    if ahead_index < 0:
        return 0.0
    opt_lap_progress = calc.lap_progress_distance(api.read.lap.distance(ahead_index), track_length)
    opt_lap_progress_total = api.read.lap.completed_laps(ahead_index) + opt_lap_progress
    lap_diff = opt_lap_progress_total - lap_progress_total
    if lap_diff >= 1 or lap_diff <= -1:  # laps
        return int(abs(lap_diff))
    # Time gap between driver ahead and behind
    time_gap = api.read.timing.estimated_time_into(ahead_index) - api.read.timing.estimated_time_into(behind_index)
    # Check lap diff (positive) for position correction
    # in case the ahead driver is momentarily behind (such as during double-file formation lap)
    if time_gap < 0 < lap_diff:
        time_gap += api.read.timing.estimated_laptime(behind_index)
    return abs(time_gap)


def calc_gap_behind_next(index: int) -> float:
    """Calculate interval behind next"""
    laps_behind_next = api.read.lap.behind_next(index)
    if laps_behind_next > 0:
        return laps_behind_next
    return api.read.timing.behind_next(index)


def calc_gap_behind_leader(index: int) -> float:
    """Calculate interval behind leader"""
    laps_behind_leader = api.read.lap.behind_leader(index)
    if laps_behind_leader > 0:
        return laps_behind_leader
    return api.read.timing.behind_leader(index)


def update_stint_usage(data: VehicleDataSet, laps_completed: int) -> None:
    """Update stint usage data"""
    (ve_remaining, ve_used, total_laps_done, stint_laps_est, stint_laps_done
     ) = api.read.vehicle.stint_usage(data.driverName)

    # Estimated stint laps
    data.estimatedStintLaps = stint_laps_est
    if stint_laps_done > 0:
        data.currentStintLaps = stint_laps_done
    else:
        data.currentStintLaps = laps_completed - data.pitTimer.lap_stopped

    # Stint energy usage
    if ve_remaining <= -1.0 or ve_used <= 0 or (data.pitTimer.pitting and not data.inPit):
        data.energyRemaining = ve_remaining
    else:  # Apply linear interpolation at 95% of expected lap usage
        data.energyRemaining = ve_remaining - ve_used * 0.95 * (data.totalLapProgress - total_laps_done)
