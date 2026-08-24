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
Vehicles module
"""

from __future__ import annotations

from .. import calculation as calc
from .. import realtime_state
from ..api_control import api
from ..const_common import MAX_METERS, MAX_SECONDS
from ..module_info import VehicleDataSet, VehiclesInfo, minfo
from ..userfile.brands import select_brand_name
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
        max_finish_time_diff = max(self.mcfg["finish_time_difference_threshold"], 0)

        gen_low_priority_timer = state_timer(0.2)

        while not _event_wait(update_interval):
            if not realtime_state.paused:

                if not reset:
                    reset = True
                    update_interval = self.active_interval
                    output.dataSetVersion = -1
                    last_veh_total = -1
                    last_session_elapsed = -1
                    last_in_race = -1

                veh_total = output.totalVehicles = api.read.vehicle.total_vehicles()
                if veh_total > 0:
                    update_low_priority = next(gen_low_priority_timer)
                    session_elapsed = api.read.timing.elapsed()
                    in_race = api.read.session.in_race()

                    update_vehicle_data(
                        output,
                        max_lap_diff_ahead,
                        max_lap_diff_behind,
                        update_low_priority,
                        session_elapsed,
                        in_race,
                    )

                    if update_low_priority:

                        if in_race:
                            update_finish_time(output, max_finish_time_diff)

                        if (
                            last_veh_total != veh_total
                            or last_session_elapsed > session_elapsed
                            or last_in_race != in_race
                        ):
                            update_qualify_position(output)
                            output.finishTimeOffset = 0.0
                            output.finishAsLap = True
                            output.finishLapOffset = 0.0

                        last_veh_total = veh_total
                        last_session_elapsed = session_elapsed
                        last_in_race = in_race

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval

        # Must reset on close
        output.finishTimeOffset = 0.0
        output.finishAsLap = True
        output.finishLapOffset = 0.0


def update_vehicle_data(
    output: VehiclesInfo,
    max_lap_diff_ahead: float,
    max_lap_diff_behind: float,
    update_low_priority: bool,
    elapsed_time: float,
    in_race: bool,
) -> None:
    """Update vehicle data"""
    nearest_line = MAX_METERS
    nearest_time_behind = -MAX_SECONDS
    nearest_yellow_ahead = MAX_METERS
    nearest_yellow_behind = -MAX_METERS
    nearest_blue_class = ""

    # Counter
    total_completed_laps = 0
    total_out_pits = 0
    total_in_pits = 0
    total_stopped_pits = 0
    total_pit_requests = 0

    # General data
    track_length = api.read.lap.track_length()
    under_blue = api.read.session.blue_flag()
    speedtrap_distance = minfo.mapping.speedTrapPosition

    # Local player data
    plr_lap_distance = api.read.lap.distance()
    plr_lap_progress_total = api.read.lap.completed_laps() + calc.lap_progress_distance(plr_lap_distance, track_length)
    plr_laptime_est = api.read.timing.estimated_laptime()
    plr_timeinto_est = api.read.timing.estimated_time_into()
    plr_pos_x = api.read.vehicle.position_longitudinal()
    plr_pos_y = api.read.vehicle.position_lateral()
    plr_ori_yaw = api.read.vehicle.orientation_yaw_radians()

    # Update dataset from all vehicles in current session
    for index, data in zip(range(output.totalVehicles), output.dataSet):
        # Temp var only
        laps_completed = api.read.lap.completed_laps(index)
        lap_distance = api.read.lap.distance(index)
        data.speed = speed = api.read.vehicle.speed(index)

        # Update high priority info
        data.isPlayer = api.read.vehicle.is_player(index)
        data.inPit = api.read.vehicle.in_paddock(index)
        data.isYellow = speed < 8 and data.inPit != 2
        data.pitTimer.update(data.inPit, elapsed_time, laps_completed, speed)

        if data.inPit:
            data.licoTimer.elapsed = 0.0
            data.speedTrap.speed = 0.0
        else:
            data.licoTimer.update(elapsed_time, api.read.inputs.throttle_raw(index), api.read.inputs.brake_raw(index))
            data.speedTrap.update(speed, lap_distance, speedtrap_distance, track_length)

        if data.isPlayer:
            data.elapsedTime = elapsed_time
            data.worldPositionX = plr_pos_x
            data.worldPositionY = plr_pos_y
            output.playerIndex = index
            if data.isYellow:
                nearest_yellow_ahead = 0.0
                nearest_yellow_behind = 0.0
        else:
            # Relative position & orientation
            opt_etime = api.read.timing.elapsed(index)
            if data.elapsedTime != opt_etime:
                opt_pos_x = api.read.vehicle.position_longitudinal(index)
                opt_pos_y = api.read.vehicle.position_lateral(index)
                opt_ori_yaw = api.read.vehicle.orientation_yaw_radians(index)
                # Player data update rate may be (twice) higher than opponents
                # Interpolate coordinates to avoid desync
                est_pos_x, est_pos_y = calc.time_interp_coordinate(
                    opt_pos_x,
                    data.worldPositionX,
                    opt_pos_y,
                    data.worldPositionY,
                    opt_etime,
                    data.elapsedTime,
                    elapsed_time,
                )
                data.worldPositionX = opt_pos_x
                data.worldPositionY = opt_pos_y
                data.elapsedTime = opt_etime

                data.relativeOrientationRadians = opt_ori_yaw - plr_ori_yaw
                data.relativeRotatedPositionX, data.relativeRotatedPositionY = calc.rotate_coordinate(
                    plr_ori_yaw - 3.14159265,  # plr_ori_rad, rotate view
                    est_pos_x - plr_pos_x,  # x position related to player
                    est_pos_y - plr_pos_y,  # y position related to player
                )
                # Relative distance & time gap
                data.relativeStraightDistance = calc.distance(
                    (plr_pos_x, plr_pos_y),
                    (est_pos_x, est_pos_y)
                )

            # Nearest straight line distance (non local players)
            if nearest_line > data.relativeStraightDistance:
                nearest_line = data.relativeStraightDistance

        # Update low priority info
        if update_low_priority:
            data.currentLapProgress = calc.lap_progress_distance(lap_distance, track_length)
            data.totalLapProgress = laps_completed + data.currentLapProgress
            data.isLapped = calc.lap_difference(
                data.totalLapProgress, plr_lap_progress_total,
                max_lap_diff_ahead, max_lap_diff_behind
            ) if in_race else 0

            data.positionOverall = api.read.vehicle.place(index)
            data.bestLapTime = api.read.timing.best_laptime(index)
            data.numPitStops = api.read.vehicle.number_pitstops(index, api.read.vehicle.number_penalties(index))
            data.pitRequested = api.read.vehicle.pit_request(index)
            data.driverName = api.read.vehicle.driver_name(index)
            data.vehicleName = api.read.vehicle.vehicle_name(index)
            data.vehicleBrand = select_brand_name(index, data.vehicleName)
            data.vehicleClass = api.read.vehicle.class_name(index)
            data.vehicleIntegrity = api.read.vehicle.integrity(index)
            data.tireCompoundName = api.read.tyre.compound_class(index)
            data.isFinished = api.read.vehicle.finish_state(index) == 1
            data.incidents = api.read.vehicle.incidents(index)

            data.gapBehindNext = calc_gap_behind_next(index)
            data.gapBehindLeader = calc_gap_behind_leader(index)

            opt_index_ahead = data.classAheadIndex
            opt_index_leader = data.classLeaderIndex
            data.gapBehindNextInClass = calc_time_gap_behind(
                opt_index_ahead, index, output.dataSet[opt_index_ahead].totalLapProgress - data.totalLapProgress)
            data.gapBehindLeaderInClass = calc_time_gap_behind(
                opt_index_leader, index, output.dataSet[opt_index_leader].totalLapProgress - data.totalLapProgress)

            lap_start_time = api.read.timing.start(index)
            last_laptime = api.read.timing.last_laptime(index)
            fuel_remaining = api.read.engine.fuel_fraction(index)
            energy_remaining = api.read.engine.virtual_energy(index)

            data.lapTimeHistory.update(lap_start_time, elapsed_time, data.bestLapTime)
            data.isValidLap = last_laptime > 0
            data.lastLapTime = last_laptime if data.isValidLap else data.lapTimeHistory.last

            data.fuelHistory.update(lap_start_time, fuel_remaining)
            data.energyHistory.update(lap_start_time, energy_remaining)
            update_stint_usage(data, fuel_remaining, energy_remaining)

            # Update counter
            total_completed_laps += laps_completed

            if data.inPit == 1:  # in pit (exclude garage)
                total_in_pits += 1
                total_stopped_pits += (speed < 0.1)
            elif data.inPit == 0:  # out pit
                total_out_pits += 1
                total_pit_requests += data.pitRequested
                # Nearest traffic time gap (opponents behind local players)
                opt_time_behind = calc.circular_position_relative(
                    plr_laptime_est,
                    plr_timeinto_est,
                    api.read.timing.estimated_time_into(index),
                )
                if 0 > opt_time_behind > nearest_time_behind:
                    nearest_time_behind = opt_time_behind
                    if under_blue and (not in_race or data.isLapped > 0):
                        nearest_blue_class = data.vehicleClass

            # Nearest yellow flag distance
            if data.isYellow:
                opt_rel_distance = calc.circular_position_relative(
                    track_length, plr_lap_distance, lap_distance)
                if nearest_yellow_ahead > opt_rel_distance >= 0:
                    nearest_yellow_ahead = opt_rel_distance
                if nearest_yellow_behind < opt_rel_distance <= 0:
                    nearest_yellow_behind = opt_rel_distance

            # Save leader info
            if data.positionOverall == 1:
                output.leaderIndex = index
                output.leaderBestLapTime = data.bestLapTime

    if update_low_priority:
        output.nearestTraffic = -nearest_time_behind
        output.nearestYellowAhead = nearest_yellow_ahead
        output.nearestYellowBehind = nearest_yellow_behind
        output.nearestBlueClass = nearest_blue_class

        output.totalOutPits = total_out_pits
        output.totalInPits = total_in_pits
        output.totalStoppedPits = total_stopped_pits
        output.totalPitRequests = total_pit_requests
        output.totalCompletedLaps = total_completed_laps

    # Output extra info
    output.nearestLine = nearest_line
    output.dataSetVersion += 1


def update_finish_time(output: VehiclesInfo, max_finish_time_diff: float) -> None:
    """Estimated finish time & offset based on remaining laps"""
    finish_type = api.read.session.finish_type()
    remaining_time = api.read.session.remaining()
    leader_index = output.leaderIndex
    player_index = output.playerIndex
    leader_pace = output.dataSet[leader_index].lapTimeHistory.average
    player_pace = minfo.delta.lapTimePace

    # Time only
    if finish_type == 0:

        # Final pit stop time offset
        if minfo.energy.available:
            est_pits_late = minfo.energy.estimatedNumPitStopsEnd
        else:
            est_pits_late = minfo.fuel.estimatedNumPitStopsEnd

        if 0.2 < est_pits_late < 1.2:
            final_pit_time = minfo.mapping.pitPassTime + api.read.vehicle.pit_stop_time()
        else:
            final_pit_time = 0.0

        # Leader time
        if leader_index == player_index or output.dataSet[leader_index].isFinished:
            leader_finish_offset = 0.0
            player_lap_offset = 0.0
        else:
            leader_lap_into = api.read.lap.progress(leader_index)
            player_lap_into = api.read.lap.progress(player_index)

            # Leader finish remaining time
            leader_lap_remaining = calc.end_timer_laps_remain(leader_lap_into, leader_pace, remaining_time)
            leader_finish_offset = (1 - leader_lap_remaining % 1) * leader_pace
            leader_finish_time = remaining_time + leader_finish_offset

            # Player finish remaining time without pit
            player_lap_remaining = calc.end_timer_laps_remain(player_lap_into, player_pace, remaining_time)
            player_laps_left_nopit = calc.time_type_laps_remain(calc.ceil(player_lap_remaining), player_lap_into)

            # Player finish remaining time with final pit
            player_lap_remaining = calc.end_timer_laps_remain(player_lap_into, player_pace, remaining_time - final_pit_time)
            player_laps_left_pit = calc.time_type_laps_remain(calc.ceil(player_lap_remaining), player_lap_into)

            # Player finish remaining time towards leader
            to_leader_lap_remaining = calc.end_timer_laps_remain(player_lap_into, player_pace, leader_finish_time)
            to_leader_laps_left = calc.time_type_laps_remain(calc.ceil(to_leader_lap_remaining), player_lap_into)

            # Laps gain
            laps_gain_from_pit = player_laps_left_pit - player_laps_left_nopit
            laps_gain_from_leader = to_leader_laps_left - player_laps_left_nopit

            player_lap_offset = laps_gain_from_leader + laps_gain_from_pit

        output.finishTimeOffset = 0.0
        output.finishAsLap = True
        output.finishLapOffset = player_lap_offset
        return

    # Leader time
    if leader_index >= 0 and 0 < leader_pace < MAX_SECONDS:
        leader_finish_time = leader_pace * api.read.lap.remaining(leader_index)
        leader_finish_offset = max(remaining_time - leader_finish_time, 0.0)
    else:  # default to lap if unavailable
        leader_finish_time = 0.1
        leader_finish_offset = 0.1

    # Player time
    if player_index >= 0 and 0 < player_pace < MAX_SECONDS:
        player_finish_time = player_pace * api.read.lap.remaining(player_index)
        player_finish_offset = max(remaining_time - player_finish_time, 0.0)
    else:  # default to lap if unavailable
        player_finish_time = 0.1
        player_finish_offset = 0.1

    # Laps only
    if finish_type == 1:
        output.finishTimeOffset = -leader_finish_time
        output.finishAsLap = (
            leader_finish_time > 0  # default to lap if unavailable
            and player_finish_time - leader_finish_time < max_finish_time_diff
        )
        return

    # Laps & time
    if finish_type == 2:
        output.finishTimeOffset = leader_finish_offset
        output.finishAsLap = (
            leader_finish_offset > 0
            and leader_finish_offset - player_finish_offset < max_finish_time_diff
        )
        return


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
    lap_diff: float,
) -> float:
    """Calculate interval behind next in class"""
    if ahead_index < 0:
        return 0.0
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


def update_stint_usage(
    data: VehicleDataSet,
    fuel_remaining: float,
    energy_remaining: float,
) -> None:
    """Update stint usage data"""
    if energy_remaining > 0:
        if fuel_remaining > 0:
            est_run_laps = min(data.fuelHistory.laps, data.energyHistory.laps)
        else:
            est_run_laps = data.energyHistory.laps
    elif fuel_remaining > 0:
        est_run_laps = data.fuelHistory.laps
    else:
        est_run_laps = 0.0

    stint_laps_done = data.pitTimer.laps
    stint_laps_est = (stint_laps_done + est_run_laps) if est_run_laps > 0 else 0.0

    if energy_remaining != 0:
        data.energyRemaining = energy_remaining
    elif fuel_remaining > 0:
        data.energyRemaining = fuel_remaining
    else:
        data.energyRemaining = -1

    data.currentStintLaps = stint_laps_done
    data.estimatedStintLaps = stint_laps_est
