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

from .. import api, minfo, realtime_state
from .. import calculation as calc
from ..constant import DATA
from ..module_info import VehicleData, VehiclesInfo
from ..process import standings
from ..userfile.brands import select_brand_name
from ..validator import state_timer
from ._base import DataModule


class Realtime(DataModule):
    """Vehicles info"""

    __slots__ = ()

    def update_data(self):
        """Update module data"""
        _event_wait = self._event.wait
        reset = False
        update_interval = self.idle_interval

        output = minfo.vehicles
        output.update_index()
        dataset_temp = []  # reused for sorting & processing

        max_lap_diff_ahead = self.mcfg["lap_difference_ahead_threshold"]
        max_lap_diff_behind = self.mcfg["lap_difference_behind_threshold"]
        max_finish_time_diff = max(self.mcfg["finish_time_difference_threshold"], 0)

        gen_low_priority_timer = state_timer(0.2)
        in_race = False

        while not _event_wait(update_interval):
            if not realtime_state.paused:

                if not reset:
                    reset = True
                    update_interval = self.active_interval
                    output.dataSetVersion = -1
                    last_active_total = -1
                    last_veh_total = -1
                    last_session_elapsed = -1
                    last_in_race = -1
                    last_player_index = -1

                veh_total = api.read.vehicle.total_vehicles()

                if last_active_total != veh_total:
                    last_active_total = veh_total
                    output.activeDataSet = output.dataSet[:max(veh_total, 1)]
                    output.totalVehicles = veh_total
                    dataset_temp[:] = output.activeDataSet

                if veh_total > 0:
                    update_low_priority = next(gen_low_priority_timer)
                    session_elapsed = api.read.timing.elapsed()

                    update_vehicle_data(
                        output,
                        max_lap_diff_ahead,
                        max_lap_diff_behind,
                        update_low_priority,
                        session_elapsed,
                        in_race,
                    )

                    if update_low_priority:
                        in_race = api.read.session.in_race()
                        player_index = output.playerIndex

                        if (
                            last_veh_total != veh_total
                            or last_player_index != player_index
                            or last_session_elapsed > session_elapsed
                            or last_in_race != in_race
                        ):
                            output.update_dataset()
                            output.reset_finish_offset()

                        last_veh_total = veh_total
                        last_player_index = player_index
                        last_session_elapsed = session_elapsed
                        last_in_race = in_race

                        # Conditional updates
                        if in_race:
                            update_finish_time(output, max_finish_time_diff)

                        # Update one at a time to reduce overhead
                        if output.updateAheadIndex:
                            output.updateAheadIndex = False
                            update_overall_ahead_index(dataset_temp)

                        elif output.updateClassStats:
                            output.updateClassStats = False
                            update_class_stats(dataset_temp)

                        elif output.updateClassOrder:
                            output.updateClassOrder = False
                            update_position_in_class(dataset_temp)
                            # Make sure to update standings after updated class order
                            output.updateStandingsIndex = True
                            output.updateClassField = True

                        elif output.updateDrawOrder:
                            output.updateDrawOrder = False
                            dataset_temp.sort(key=standings.sort_by_draw_priority)
                            output.drawOrder = tuple(dataset_temp)

                        elif output.updateQualifyOrder:
                            output.updateQualifyOrder = False
                            update_qualify_position(dataset_temp)

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval

        # Must reset on close
        output.reset_finish_offset()


def update_vehicle_data(
    output: VehiclesInfo,
    max_lap_diff_ahead: float,
    max_lap_diff_behind: float,
    update_low_priority: bool,
    elapsed_time: float,
    in_race: bool,
) -> None:
    """Update vehicle data"""
    # Low priority
    if update_low_priority:
        nearest_time_behind = DATA.MAX_SECONDS
        nearest_yellow_ahead = DATA.MAX_METERS
        nearest_yellow_behind = -DATA.MAX_METERS
        nearest_blue_class = ""

        under_blue = api.read.session.blue_flag()
        plr_lap_distance = api.read.lap.distance()

        total_completed_laps = 0
        total_out_pits = 0
        total_in_pits = 0
        total_stopped_pits = 0
        total_pit_requests = 0

        _diff_in_pit = False
        _diff_position_overall = False
        _diff_class_name = False
        _diff_laps_completed = False

    # High priority
    nearest_line = DATA.MAX_METERS
    track_length = api.read.lap.track_length()
    speedtrap_distance = minfo.mapping.speedTrapPosition

    plr_pos_x = api.read.vehicle.position_longitudinal()
    plr_pos_y = api.read.vehicle.position_lateral()
    plr_ori_yaw = api.read.vehicle.orientation_yaw()

    # Update dataset from all vehicles in current session
    for index, data in enumerate(output.activeDataSet):
        # Update high priority info
        lap_distance = api.read.lap.distance(index)
        in_pit = api.read.vehicle.in_paddock(index)
        data.speed = speed = api.read.vehicle.speed(index)
        data.isPlayer = is_player = api.read.vehicle.is_player(index)
        data.isYellow = speed < 8 and in_pit != 2

        if in_pit:
            data.licoTimer.elapsed = 0.0
            data.speedTrap.speed = 0.0
        else:
            data.licoTimer.update(elapsed_time, api.read.inputs.throttle_raw(index), api.read.inputs.brake_raw(index))
            data.speedTrap.update(speed, lap_distance, speedtrap_distance, track_length)

        if is_player:
            output.playerData = data  # save player info
            output.playerIndex = index
            data.elapsedTime = elapsed_time
            data.worldPositionX = plr_pos_x
            data.worldPositionY = plr_pos_y
        else:
            # Relative position & orientation
            opt_elapsed_time = api.read.timing.elapsed(index)
            if data.elapsedTime != opt_elapsed_time:
                opt_pos_x = api.read.vehicle.position_longitudinal(index)
                opt_pos_y = api.read.vehicle.position_lateral(index)
                opt_ori_yaw = api.read.vehicle.orientation_yaw(index)
                # Player data update rate may be (twice) higher than opponents
                # Interpolate coordinates to avoid desync
                est_pos_x, est_pos_y = calc.time_interp_coordinate(
                    opt_pos_x,
                    data.worldPositionX,
                    opt_pos_y,
                    data.worldPositionY,
                    opt_elapsed_time,
                    data.elapsedTime,
                    elapsed_time,
                )
                data.worldPositionX = opt_pos_x
                data.worldPositionY = opt_pos_y
                data.elapsedTime = opt_elapsed_time

                data.relativeOrientationRadians = opt_ori_yaw - plr_ori_yaw
                data.relativeRotatedPositionX, data.relativeRotatedPositionY = calc.rotate_coordinate(
                    plr_ori_yaw - 3.14159265,  # plr_ori_rad, rotate view
                    est_pos_x - plr_pos_x,  # x position related to player
                    est_pos_y - plr_pos_y,  # y position related to player
                )
                # Relative distance & time gap
                data.relativeStraightDistance = calc.dist(
                    (plr_pos_x, plr_pos_y),
                    (est_pos_x, est_pos_y),
                )

            # Nearest straight line distance (non local players)
            if nearest_line > data.relativeStraightDistance:
                nearest_line = data.relativeStraightDistance

        # Update low priority info
        if update_low_priority:

            # Lap progress, time gap
            laps_completed = api.read.lap.completed(index)
            data.currentLapProgress = calc.lap_progress_distance(lap_distance, track_length)

            if data.totalLapCompleted != laps_completed:
                data.totalLapCompleted = laps_completed
                _diff_laps_completed = True
            elif 0 < data.currentLapProgress < 1:  # helps avoid desync
                data.totalLapProgress = data.totalLapCompleted + data.currentLapProgress
                data.isLapped = calc.lap_difference(
                    data.totalLapProgress, output.playerData.totalLapProgress,
                    max_lap_diff_ahead, max_lap_diff_behind
                ) if in_race else 0
                update_time_gap_behind(data, output.dataSet, output.leaderIndex)

            # Name
            data.driverName = api.read.vehicle.driver_name(index)
            data.vehicleName = api.read.vehicle.vehicle_model(index)
            data.brandName = select_brand_name(data.vehicleName)
            data.tireCompoundName = api.read.tyre.compound_class(index)

            class_name = api.read.vehicle.class_name(index)
            if data.vehicleClass != class_name:
                data.vehicleClass = class_name
                _diff_class_name = True

            # Damage, incidents, track limits
            data.vehicleIntegrity = api.read.vehicle.integrity(index)
            data.incidents = api.read.vehicle.incidents(index)
            data.trackLimitsPoints = api.read.session.cut_points(index)

            # Pit stop, penalty, finish state
            if data.inPit != in_pit:
                data.inPit = in_pit
                _diff_in_pit = True

            penalties = api.read.vehicle.number_penalties(index)
            data.numPitStops = -penalties if penalties else api.read.vehicle.number_pitstops(index)
            data.penaltyType = api.read.vehicle.penalty_type(index)
            data.finishState = api.read.vehicle.finish_state(index)
            data.pitRequested = api.read.vehicle.pit_request(index)
            data.pitTimer.update(in_pit, elapsed_time, laps_completed, speed)

            # Lap time, validation
            data.bestLapTime = api.read.timing.best_laptime(index)
            last_laptime = api.read.timing.last_laptime(index)
            data.isValidLap = last_laptime > 0
            data.lastLapTime = abs(last_laptime)
            if 100 > lap_distance > 20:  # check only at start of lap
                data.lapTimeHistory.update(last_laptime, laps_completed, data.bestLapTime)

            # Fuel, energy, stint usage
            fuel_remaining = api.read.engine.fuel_fraction(index)
            energy_remaining = api.read.engine.virtual_energy(index)
            data.fuelHistory.update(laps_completed, fuel_remaining)
            data.energyHistory.update(laps_completed, energy_remaining)
            update_stint_usage(data, fuel_remaining, energy_remaining)

            # Overall position
            position_overall = api.read.vehicle.place(index)
            if data.positionOverall != position_overall:
                data.positionOverall = position_overall
                _diff_position_overall = True

            if position_overall == 1:
                output.leaderData = data  # save leader info
                output.leaderIndex = index

            # Update counter
            total_completed_laps += laps_completed

            if in_pit == 0:  # out pit
                total_out_pits += 1
                total_pit_requests += data.pitRequested
                # Nearest traffic time gap (opponents behind local players)
                opt_time_behind = data.relativeGapBehind
                if 0 < opt_time_behind < nearest_time_behind:
                    nearest_time_behind = opt_time_behind
                    if under_blue and (not in_race or data.isLapped > 0):
                        nearest_blue_class = class_name
            elif in_pit == 1:  # in pit (exclude garage)
                total_in_pits += 1
                total_stopped_pits += (speed < 0.1)

            # Nearest yellow flag distance
            if data.isYellow:
                if is_player:
                    nearest_yellow_ahead = 0.0
                    nearest_yellow_behind = 0.0
                else:
                    opt_rel_distance = calc.circular_position_relative(
                        track_length, plr_lap_distance, lap_distance)
                    if nearest_yellow_ahead > opt_rel_distance >= 0:
                        nearest_yellow_ahead = opt_rel_distance
                    if nearest_yellow_behind < opt_rel_distance <= 0:
                        nearest_yellow_behind = opt_rel_distance

    # Output extra info
    if update_low_priority:
        output.nearestTraffic = nearest_time_behind
        output.nearestYellowAhead = nearest_yellow_ahead
        output.nearestYellowBehind = nearest_yellow_behind
        output.nearestBlueClass = nearest_blue_class

        output.totalOutPits = total_out_pits
        output.totalInPits = total_in_pits
        output.totalStoppedPits = total_stopped_pits
        output.totalPitRequests = total_pit_requests
        output.totalCompletedLaps = total_completed_laps

        # Update state
        output.updateDrawOrder |= _diff_position_overall | _diff_in_pit
        output.updateClassField |= _diff_in_pit
        output.updateClassOrder |= _diff_position_overall | _diff_class_name
        output.updateClassStats |= _diff_laps_completed
        output.updateAheadIndex |= _diff_position_overall

    output.nearestLine = nearest_line
    output.dataSetVersion += 1


def update_class_stats(veh_dataset: list[VehicleData]) -> None:
    """Update vehicle class stats"""
    veh_dataset.sort(key=standings.sort_by_class)
    last_class_name = None
    data_fastest = None
    laptime_last_fastest = DATA.MAX_SECONDS

    for data in veh_dataset:
        class_name = data.vehicleClass

        if last_class_name != class_name:
            last_class_name = class_name  # reset class name
            laptime_last_fastest = DATA.MAX_SECONDS  # reset last fastest
            if data_fastest:  # mark fastest last lap
                data_fastest.isClassFastestLastLap = True
                data_fastest = None  # reset

        # Check fastest last lap in class
        data.isClassFastestLastLap = False
        if data.isValidLap:
            laptime_last = data.lastLapTime
            if laptime_last_fastest > laptime_last:
                laptime_last_fastest = laptime_last
                data_fastest = data

    if data_fastest:  # mark for last class
        data_fastest.isClassFastestLastLap = True


def update_position_in_class(veh_dataset: list[VehicleData]) -> None:
    """Update vehicle position in class"""
    veh_dataset.sort(key=standings.sort_by_class)
    class_order = 0
    last_class_name = None
    place_in_class = 0
    index_ahead = -1
    index_leader = -1
    data_ahead = None

    for data in veh_dataset:
        index = data.index
        class_name = data.vehicleClass

        if last_class_name == class_name:
            place_in_class += 1
            if data_ahead:
                data_ahead.classBehindIndex = index
        else:
            class_order = data.positionOverall * 1000  # order by class leader
            last_class_name = class_name  # reset class name
            place_in_class = 1  # reset position counter
            index_ahead = -1  # no opponent ahead of class leader
            index_leader = index

        data.classOrder = class_order + place_in_class
        data.classAheadIndex = index_ahead
        data.classBehindIndex = -1
        data.classLeaderIndex = index_leader
        data.positionInClass = place_in_class

        # Store ahead
        index_ahead = index
        data_ahead = data


def update_qualify_position(veh_dataset: list[VehicleData]) -> None:
    """Update vehicle qualify position"""
    # Update qualify position overall
    for data in veh_dataset:
        data.qualifyOverall = api.read.vehicle.qualification(data.index)
    veh_dataset.sort(key=standings.sort_by_qualification)
    # Update qualify position in class
    qualify_in_class = 0
    last_class_name = None
    for data in veh_dataset:
        class_name = data.vehicleClass
        if last_class_name != class_name:
            last_class_name = class_name
            qualify_in_class = 1
        else:
            qualify_in_class += 1
        data.qualifyInClass = qualify_in_class


def update_overall_ahead_index(veh_dataset: list[VehicleData]) -> None:
    """Update vehicle ahead index by overall position"""
    veh_dataset.sort(key=standings.sort_by_overall)
    ahead_index = -1
    for data in veh_dataset:
        data.overallAheadIndex = ahead_index
        ahead_index = data.index
        data.estimatedLapTime = api.read.timing.estimated_laptime(ahead_index)


def update_finish_time(output: VehiclesInfo, max_finish_time_diff: float) -> None:
    """Estimated finish time & offset based on remaining laps"""
    finish_type = api.read.session.finish_type()
    remaining_time = api.read.session.remaining()
    leader_index = output.leaderIndex
    player_index = output.playerIndex
    leader_pace = output.leaderData.lapTimeHistory.average
    player_pace = minfo.delta.lapTimePace

    # Time only
    if finish_type == 0:

        # Leader time
        if leader_index == player_index or output.leaderData.finishState:
            leader_finish_offset = 0.0
            player_lap_offset = 0.0
        else:
            leader_lap_into = output.leaderData.currentLapProgress
            player_lap_into = output.playerData.currentLapProgress

            # Final pit stop time offset
            if minfo.energy.available:
                est_pits_late = minfo.energy.estimatedNumPitStopsEnd
            else:
                est_pits_late = minfo.fuel.estimatedNumPitStopsEnd

            if 0.2 < est_pits_late < 1.2:
                final_pit_time = minfo.mapping.pitPassTime + api.read.vehicle.pit_stop_time()
            else:
                final_pit_time = 0.0

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
    if leader_index >= 0 and 0 < leader_pace < DATA.MAX_SECONDS:
        leader_finish_time = leader_pace * api.read.lap.remaining(leader_index)
        leader_finish_offset = max(remaining_time - leader_finish_time, 0.0)
    else:  # default to lap if unavailable
        leader_finish_time = 0.1
        leader_finish_offset = 0.1

    # Player time
    if player_index >= 0 and 0 < player_pace < DATA.MAX_SECONDS:
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


def update_time_gap_behind(data: VehicleData, veh_dataset: tuple[VehicleData, ...], overall_index_leader: int) -> None:
    """Update time gap behind"""
    class_index_ahead = data.classAheadIndex
    if class_index_ahead < 0:
        data.gapBehindNextInClass = 0.0
    else:
        data.gapBehindNextInClass = time_interval_behind(veh_dataset[class_index_ahead], data)

    class_index_leader = data.classLeaderIndex
    if class_index_leader < 0:
        data.gapBehindLeaderInClass = 0.0
    else:
        data.gapBehindLeaderInClass = time_interval_behind(veh_dataset[class_index_leader], data)

    overall_index_ahead = data.overallAheadIndex
    if overall_index_ahead < 0:
        data.gapBehindNext = 0.0
    elif overall_index_ahead == class_index_ahead:
        data.gapBehindNext = data.gapBehindNextInClass
    else:
        data.gapBehindNext = time_interval_behind(veh_dataset[overall_index_ahead], data)

    if overall_index_leader < 0:
        data.gapBehindLeader = 0.0
    elif overall_index_leader == class_index_leader:
        data.gapBehindLeader = data.gapBehindLeaderInClass
    else:
        data.gapBehindLeader = time_interval_behind(veh_dataset[overall_index_leader], data)


def time_interval_behind(data_ahead: VehicleData, data_behind: VehicleData) -> float:
    """Calculate time interval behind next"""
    lap_diff = data_ahead.totalLapProgress - data_behind.totalLapProgress
    if lap_diff < 0:  # desync check during double-file formation lap
        return 0.0
    if lap_diff > 1:  # laps
        return int(lap_diff)
    # Time gap between driver ahead and behind
    time_gap = data_ahead.estimatedTimeIntoLap - data_behind.estimatedTimeIntoLap
    if time_gap < 0:  # relatively behind, offset by a full lap time
        time_gap += data_behind.estimatedLapTime
    return time_gap


def update_stint_usage(
    data: VehicleData,
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
