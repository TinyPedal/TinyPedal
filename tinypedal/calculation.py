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
Calculation function
"""

from __future__ import annotations

from math import acos, atan, atan2, ceil, cos, degrees, dist, hypot, radians, sin
from statistics import fmean
from typing import Sequence, Tuple

from .const_common import FLOAT_INF

CoordXY = Tuple[float, float]

distance = dist  # coordinates distance
mean = fmean
vel2speed = hypot  # velocity to speed
rad2deg = degrees  # radians to degrees
oriyaw2rad = atan2  # orientation yaw to radians
deg2rad = radians  # degrees to radians


# Common
def sym_max(value: float, rng: float) -> float:
    """Symmetric min-max value range"""
    if value > rng:
        return rng
    if value < -rng:
        return -rng
    return value


def asym_max(value: float, min_rng: float, max_rng: float) -> float:
    """Asymmetric min-max value range"""
    if value > max_rng:
        return max_rng
    if value < min_rng:
        return min_rng
    return value


def zero_max(value: float, max_rng: float) -> float:
    """Zero to max value range"""
    if value > max_rng:
        return max_rng
    if value < 0:
        return 0
    return value


def zero_one(value: float) -> float:
    """Zero to one value range"""
    if value > 1:
        return 1
    if value < 0:
        return 0
    return value


def min_nonzero(data: tuple[float, ...]) -> float:
    """Minimum non-zero positive value"""
    return min(value for value in data if value > 0)


def decimal_strip(raw_range: float, max_decimals: int) -> float:
    """Strip off unwanted decimal places according to max number of decimals"""
    value_str = str(raw_range)
    pos = value_str.find(".") + 1
    if pos <= 0:
        return raw_range
    return float(value_str[:pos + max_decimals])


def mean_iter(average: float, value: float, num_samples: int) -> float:
    """Average value"""
    return (average * num_samples + value) / (num_samples + 1)


def min_vs_avg(data: Sequence) -> float:
    """Min vs average"""
    return abs(min(data) - mean(data))


def max_vs_avg(data: Sequence) -> float:
    """Max vs average"""
    return abs(max(data) - mean(data))


def max_vs_min(data: Sequence) -> float:
    """Max vs min"""
    return max(data) - min(data)


def engine_power(torque: float, rpm: float) -> float:
    """Engine power (kW)"""
    if torque > 0:
        return torque * rpm / 9549.3
    return 0


def rake(height_fl: float, height_fr: float, height_rl: float, height_rr: float) -> float:
    """Raw rake (front & rear ride height difference in millmeters)"""
    return (height_rr + height_rl - height_fr - height_fl) * 0.5


def gforce(value: float, g_accel: float = 9.8) -> float:
    """G force"""
    if g_accel:
        return value / g_accel
    return 0


def force_ratio(value1: float, value2: float, min_limit: float = 1) -> float:
    """Force ratio from Newtons"""
    if value2 > min_limit or value2 < -min_limit:
        return abs(100 * value1 / value2)
    return 0


def part_to_whole_ratio(part: float, whole: float, median: float = 0) -> float:
    """Part to whole ratio"""
    abs_part = abs(part)
    abs_whole = abs(whole)
    if abs_whole > 0:
        if abs_part < abs_whole:
            return 100 * part / whole
        return 100
    return median


def braking_rate(lgt_gforce: float, is_braking: bool, not_impacted: bool = True) -> float:
    """Braking rate (longitudinal G force)"""
    if is_braking and not_impacted:
        return lgt_gforce
    return 0.0


def rotate_coordinate(ori_rad: float, pos_x: float, pos_y: float) -> CoordXY:
    """Rotate x y coordinates"""
    sin_rad = sin(ori_rad)
    cos_rad = cos(ori_rad)
    return (cos_rad * pos_x - sin_rad * pos_y,
            cos_rad * pos_y + sin_rad * pos_x)


def lap_progress_distance(dist_into: float, length: float) -> float:
    """Current lap progress (distance into lap) fraction"""
    if length < 1:
        return 0
    value = dist_into / length
    if value > 1:
        return 1
    if value < 0:
        return 0
    return value


def lap_progress_correction(percent: float, laptime: float) -> float:
    """Lap progress desync correction"""
    if percent > 0.5 > laptime:
        return 0
    return percent


def lap_progress_offset(laptime: float, lap_into: float, seconds_delay: float) -> float:
    """Lap progress offset (fraction) by seconds delay, such as pit stop"""
    if laptime:
        return lap_into - seconds_delay / laptime
    return 0


def lap_progress_difference(ahead_laptime: float, behind_laptime: float) -> float:
    """Lap progress difference (fraction) between player ahead & behind"""
    if behind_laptime > ahead_laptime > 0:
        return (behind_laptime - ahead_laptime) / behind_laptime
    if ahead_laptime > behind_laptime > 0:
        return (ahead_laptime - behind_laptime) / ahead_laptime
    return 0


def circular_relative_distance(circle_length: float, plr_dist: float, opt_dist: float) -> float:
    """Relative distance between opponent & player in a circle"""
    rel_dist = opt_dist - plr_dist
    # Relative dist is greater than half of track length
    if abs(rel_dist) > circle_length * 0.5:
        if opt_dist > plr_dist:
            rel_dist -= circle_length  # opponent is behind player
        elif opt_dist < plr_dist:
            rel_dist += circle_length  # opponent is ahead player
    return rel_dist


def lap_difference(
    opt_laps: float, plr_laps: float, lap_ahead: float = 1, lap_behind: float = 1) -> float:
    """Calculate lap difference between target opponent and player

    Positive: lap(s) ahead.
    Negative: lap(s) behind.
    Zero: on same lap.
    """
    lap_diff = opt_laps - plr_laps
    if lap_diff > lap_ahead or lap_diff < -lap_behind:
        return lap_diff
    return 0


def relative_time_gap(rel_dist: float, plr_speed: float, opt_speed: float) -> float:
    """Relative time gap between opponent & player"""
    speed = max(plr_speed, opt_speed)
    if speed > 1:
        return abs(rel_dist / speed)
    return 0


def pitlane_length(track_length: float, pit_entry: float, pit_exit: float) -> float:
    """Calculate pitlane length"""
    if pit_entry != 0 != pit_exit:  # check valid position
        pit_length = pit_exit - pit_entry
        if pit_entry > pit_exit:
            pit_length += track_length
    else:
        pit_length = 0.0
    return pit_length


def linear_interp(x: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """Linear interpolation"""
    x_diff = x2 - x1
    if x_diff:
        return y1 + (x - x1) * (y2 - y1) / x_diff
    return y1


def slope_percent(height: float, length: float) -> float:
    """Slope percent"""
    if length:
        return height / length
    return 0


def slope_angle(height: float, length: float) -> float:
    """Slope angle (degree)"""
    if length:
        return rad2deg(atan(height / length))
    return 0


def arc_length(angle: float, radius: float) -> float:
    """Arc length"""
    return abs(angle * radius * 3.14159265 / 180)


def arc_angle(length: float, radius: float) -> float:
    """Arc angle (degree)"""
    if radius:
        return length * 180 / (radius * 3.14159265)
    return 0


def curvature(radius: float) -> float:
    """Curvature"""
    if radius:
        return 1 / radius
    return 0


def tri_coords_circle_center(
    x1: float, y1: float, x2: float, y2: float, x3: float, y3: float) -> CoordXY:
    """Tri-coordinates circle center x, y"""
    p = 0.00000001  # bypass zero division
    k1 = (y2 - y1 + p) / (x2 - x1 + p)
    k2 = (y3 - y2 + p) / (x3 - x2 + p)
    s1 = (x1 + x2) / (2 * k1)
    s2 = 1 / k2 - 1 / k1 + p
    x = ((x2 + x3) / (2 * k2) + (y3 - y1) / 2 - s1) / s2
    y =  s1 - x / k1 + (y1 + y2) / 2
    return x, y


def tri_coords_angle(a_len: float, b_len: float, c_len: float) -> float:
    """Tri-coordinates angle (radians)"""
    bc2_len = 2 * b_len * c_len
    if bc2_len:
        cos_a = (b_len * b_len + c_len * c_len - a_len * a_len) / bc2_len
        return acos(cos_a)
    return 0


def quad_coords_angle(
    coords_center: CoordXY, coords_start: CoordXY, coords_mid: CoordXY, coords_end: CoordXY) -> float:
    """Quad-coordinates angle (degree)"""
    center1_edge = distance(coords_start, coords_mid)
    center2_edge = distance(coords_mid, coords_end)
    start_edge = distance(coords_center, coords_start)
    mid_edge = distance(coords_center, coords_mid)
    end_edge = distance(coords_center, coords_end)
    rad1 = tri_coords_angle(center1_edge, start_edge, mid_edge)
    rad2 = tri_coords_angle(center2_edge, mid_edge, end_edge)
    return rad2deg(rad1 + rad2)


def turning_direction(yaw_rad: float, x1: float, y1: float, x2: float, y2: float) -> int:
    """Calculate turning direction

    Returns:
        -1 = left turning, 1 = right turning, 0 = no turning.
    """
    point_y = rotate_coordinate(-yaw_rad, x2 - x1, y2 - y1)[1]
    if point_y > 0:
        return 1
    if point_y < 0:
        return -1
    return 0


# Timing
def clock_time(seconds: float, start: float = 0, scale: float = 1) -> float:
    """Clock time (seconds) looped in full 24 hours, 0 to 86400"""
    time_curr = start + seconds * scale
    return time_curr - time_curr // 86400 * 86400


def sec2hourminute(seconds: float) -> str:
    """Seconds to hour:minute (hour:min)"""
    return f"{seconds // 3600:02.0f}:{seconds // 60 % 60:02.0f}"


def sec2sessiontime(seconds: float) -> str:
    """Session time (hour:min:sec)"""
    return f"{seconds // 3600:02.0f}:{seconds // 60 % 60:02.0f}:{round(seconds) % 60:02.0f}"


def sec2laptime(seconds: float) -> str:
    """Lap time (min:sec.ms)"""
    if seconds > 60:
        return f"{seconds // 60:.0f}:{seconds % 60:06.3f}"
    return f"{seconds % 60:.3f}"


def sec2laptime_full(seconds: float) -> str:
    """Lap time full (min:sec.ms)"""
    return f"{seconds // 60:.0f}:{seconds % 60:06.3f}"


def sec2stinttime(seconds: float) -> str:
    """Stint time (min:sec)"""
    return f"{seconds // 60:02.0f}:{int(seconds) % 60:02.0f}"


def delta_telemetry(
    dataset: list, position: float, target: float,
    condition: bool = True, position_column: int = 0, target_column: int = 1) -> float:
    """Calculate delta telemetry data"""
    if not condition:
        return 0
    index_higher = binary_search_higher_column(
        dataset, position, 0, len(dataset) - 1, position_column)
    if index_higher > 0:
        index_lower = index_higher - 1
        return target - linear_interp(
            position,
            dataset[index_lower][position_column],
            dataset[index_lower][target_column],
            dataset[index_higher][position_column],
            dataset[index_higher][target_column],
        )
    return 0


def clock_time_scale_sync(scaled_sec: float, elapsed_sec: float, start_sec: float) -> int:
    """Synchronize clock time scale multiplier

    Args:
        scaled_sec: scaled track clock time (seconds)
        elapsed_sec: current non-scaled session elapsed time (seconds)
        start_sec: current session start time stamp (seconds)
    """
    if elapsed_sec:
        return round((scaled_sec // 86400 * 86400 + scaled_sec - start_sec) / elapsed_sec)
    return 1


def exp_mov_avg(factor: float, ema_last: float, source: float) -> float:
    """Calculate exponential moving average"""
    return ema_last + factor * (source - ema_last)


def ema_factor(samples: int) -> float:
    """Calculate smoothing factor for exponential moving average"""
    return 2 / (samples + 1)


def accumulated_sum(data: list, end_index: int) -> float:
    """Calculate accumulated sum"""
    return sum(data[:end_index + 1])


# Search
def search_column_key(key: Sequence, column: int | None = None):
    """Search column key"""
    if column is None:
        return key
    return key[column]


def linear_search_higher(data: Sequence, target: float, column: int | None = None) -> int:
    """linear search nearest value higher index from unordered list"""
    #key = lambda x:x[column] if column >= 0 else x
    end = len(data) - 1
    nearest = FLOAT_INF
    for index, data_row in enumerate(data):
        if target <= search_column_key(data_row, column) < nearest:
            nearest = search_column_key(data_row, column)
            end = index
    return end


def binary_search_lower(data: Sequence, target: float, start: int, end: int) -> int:
    """Binary search nearest value lower index from ordered list"""
    while start <= end:
        center = (start + end) // 2
        if target == data[center]:
            return center
        if target > data[center]:
            start = center + 1
        else:
            end = center - 1
    return end


def binary_search_higher(data: Sequence, target: float, start: int, end: int) -> int:
    """Binary search nearest value higher index from ordered list"""
    while start < end:
        center = (start + end) // 2
        if target == data[center]:
            return center
        if target > data[center]:
            start = center + 1
        else:
            end = center
    return end


def binary_search_lower_column(
    data: Sequence, target: float, start: int, end: int, column: int = 0) -> int:
    """Binary search nearest value lower index from ordered list with column index"""
    while start <= end:
        center = (start + end) // 2
        if target == data[center][column]:
            return center
        if target > data[center][column]:
            start = center + 1
        else:
            end = center - 1
    return end


def binary_search_higher_column(
    data: Sequence[Sequence], target: float, start: int, end: int, column: int = 0) -> int:
    """Binary search nearest value higher index from ordered list with column index"""
    while start < end:
        center = (start + end) // 2
        if target == data[center][column]:
            return center
        if target > data[center][column]:
            start = center + 1
        else:
            end = center
    return end


def select_grade(data: Sequence[Sequence], source: float) -> str:
    """Select grade (linear lower) from reference list (column: 0 target, 1 value)"""
    last = data[0][1]
    for target, value in data:
        if target > source:
            return last
        last = value
    return last


# Plot
def zoom_map(coords: Sequence[CoordXY], map_scale: float, margin: int = 0):
    """Zoom map data to specific scale, then add margin"""
    # Separate X & Y coordinates
    x_range, y_range = tuple(zip(*coords))
    # Offset X, Y
    map_offset = min(x_range) * map_scale - margin, min(y_range) * map_scale - margin
    # Map width, height
    map_size = max(x_range) * map_scale + margin, max(y_range) * map_scale + margin
    # Scale map coordinates
    x_range_scaled = (x_pos * map_scale - map_offset[0] for x_pos in x_range)
    y_range_scaled = (y_pos * map_scale - map_offset[1] for y_pos in y_range)
    return tuple(zip(x_range_scaled, y_range_scaled)), map_size, map_offset


def rotate_map(coords: Sequence[CoordXY], angle: int):
    """Rotate map coordinates"""
    rot_rad = deg2rad(angle)
    for x, y in coords:
        yield rotate_coordinate(rot_rad, x, y)


def scale_map(coords: Sequence[CoordXY], area_size: int, margin: int = 0, angle: int = 0):
    """Scale map data"""
    # Rotate & separate X & Y coordinates
    if angle != 0:
        x_range, y_range = tuple(zip(*rotate_map(coords, angle)))
    else:
        x_range, y_range = tuple(zip(*coords))
    # Map size: x=width, y=height
    map_range = min(x_range), max(x_range), min(y_range), max(y_range)
    map_size = map_range[1] - map_range[0], map_range[3] - map_range[2]
    # Display area / map_size
    map_scale = (area_size - margin * 2) / max(map_size[0], map_size[1])
    # Alignment offset
    if map_size[0] > map_size[1]:
        map_offset = margin, (area_size - map_size[1] * map_scale) * 0.5
    else:
        map_offset = (area_size - map_size[0] * map_scale) * 0.5, margin
    x_range_scaled = ((x_pos - map_range[0]) * map_scale + map_offset[0] for x_pos in x_range)
    y_range_scaled = ((y_pos - map_range[2]) * map_scale + map_offset[1] for y_pos in y_range)
    return tuple(zip(x_range_scaled, y_range_scaled)), map_range, map_scale, map_offset


def scale_elevation(coords: Sequence[CoordXY], area_width: int, area_height: int):
    """Scale elevation data"""
    # Separate X & Y coordinates
    x_range, y_range = tuple(zip(*coords))
    # Map size: x=width, y=height
    map_range = min(x_range), max(x_range), min(y_range), max(y_range)
    map_size = map_range[1] - map_range[0], map_range[3] - map_range[2]
    # Display area / map_size
    map_scale = area_width / map_size[0], area_height / map_size[1]
    x_range_scaled = ((x_pos - map_range[0]) * map_scale[0] for x_pos in x_range)
    y_range_scaled = ((y_pos - map_range[2]) * map_scale[1] for y_pos in y_range)
    return tuple(zip(x_range_scaled, y_range_scaled)), map_range, map_scale


def svg_view_box(coords: Sequence[CoordXY], margin: int = 0) -> str:
    """Map bounding box"""
    # Separate X & Y coordinates
    x_range, y_range = tuple(zip(*coords))
    # Map size: x=width, y=height
    map_range = min(x_range), max(x_range), min(y_range), max(y_range)
    map_size = map_range[1] - map_range[0], map_range[3] - map_range[2]
    x1 = map_range[0] - margin
    y1 = map_range[2] - margin
    x2 = map_size[0] + margin * 2
    y2 = map_size[1] + margin * 2
    return f"{x1:.4f} {y1:.4f} {x2:.4f} {y2:.4f}"


def skip_map_nodes(total: int, limit: int, detail_level: int) -> int:
    """Skip map nodes"""
    if detail_level <= 0:
        skip_node = 0
    else:
        skip_node = total // limit + (detail_level - 1)
    return skip_node


def line_intersect_coords(
    coord_a: CoordXY, coord_b: CoordXY, rad: float, length: float):
    """Create intersect line coordinates from 2 coordinates

    coord_a: coordinate A
    coord_b: coordinate B
    rad: amount rotation (radians) to apply
    length: length between coordinates
    """
    yaw_rad = oriyaw2rad(
        coord_b[1] - coord_a[1],
        coord_b[0] - coord_a[0]
    )
    pos_x1, pos_y1 = rotate_coordinate(
        yaw_rad + rad,
        length,  # x pos
        0  # y pos
    )
    pos_x2, pos_y2 = rotate_coordinate(
        yaw_rad - rad,
        length,  # x pos
        0  # y pos
    )
    return (pos_x1 + coord_a[0],
            pos_y1 + coord_a[1],
            pos_x2 + coord_a[0],
            pos_y2 + coord_a[1])


# Fuel
def lap_type_full_laps_remain(laps_total: int, laps_finished: int) -> int:
    """Lap type race remaining laps count from finish line"""
    return laps_total - laps_finished


def lap_type_laps_remain(full_laps_remain: int, lap_into: float) -> float:
    """Lap type race remaining laps count from current on track position"""
    return full_laps_remain - lap_into


def end_timer_laps_remain(lap_into: float, laptime_last: float, seconds_remain: float) -> float:
    """Estimated remaining laps(fraction) count from finish line after race timer ended"""
    if laptime_last:
        if seconds_remain <= 0:
            return lap_into
        return seconds_remain / laptime_last + lap_into
    return 0


def time_type_full_laps_remain(laptime_last: float, seconds_remain: float) -> int:
    """Estimated full remaining laps count from finish line after race timer ended"""
    # alternative-lap-into = laptime_current / laptime_last % 1
    return ceil(end_timer_laps_remain(0, laptime_last, seconds_remain))


def time_type_laps_remain(full_laps_remain: int, lap_into: float) -> float:
    """Time type race remaining laps count from current on track position"""
    return max(full_laps_remain - lap_into, 0)


def total_fuel_needed(laps_remain: float, consumption: float, fuel_in_tank: float) -> float:
    """Total additional fuel needed"""
    return laps_remain * consumption - fuel_in_tank


def end_lap_consumption(consumption: float, consumption_delta: float, condition: bool) -> float:
    """Estimate fuel consumption"""
    if condition:
        return consumption + consumption_delta
    return consumption


def end_stint_fuel(fuel_in_tank: float, consumption_into_lap: float, consumption: float) -> float:
    """Estimate end-stint remaining fuel before pitting"""
    if consumption:
        # Total fuel at start of current lap
        fuel_at_lap_start = fuel_in_tank + consumption_into_lap
        # Fraction of lap counts * estimate fuel consumption
        return fuel_at_lap_start / consumption % 1 * consumption
    return 0


def end_stint_laps(fuel_in_tank: float, consumption: float) -> float:
    """Estimate laps current fuel can last to end of stint"""
    if consumption:
        # Laps = remaining fuel / estimate fuel consumption
        return fuel_in_tank / consumption
    return 0


def end_stint_minutes(laps_runnable: float, laptime_last: float) -> float:
    """Estimate minutes current fuel can last (based on estimate laps) to end of stint"""
    return laps_runnable * laptime_last / 60


def pit_in_countdown_laps(laps_remain: float, lap_into: float) -> float:
    """Estimate countdown laps till last chance to pit-in"""
    return laps_remain - (laps_remain + lap_into) % 1


def end_lap_empty_capacity(capacity_total: float, fuel_in_tank: float, consumption: float) -> float:
    """Estimate empty capacity at end of current lap"""
    # Total capacity - fuel at start of current lap + estimate fuel consumption
    return capacity_total - fuel_in_tank + consumption


def end_stint_pit_counts(fuel_needed: float, capacity_total: float) -> float:
    """Estimate end-stint pit stop counts"""
    if capacity_total:
        # Pit counts = required fuel / empty capacity
        return fuel_needed / capacity_total
    return 0


def end_lap_pit_counts(fuel_needed: float, capacity_empty: float, capacity_total: float) -> float:
    """Estimate end-lap pit stop counts"""
    if capacity_empty < 0:
        capacity_empty = 0
    # Amount fuel can be added without exceeding capacity
    fuel_addable = min(fuel_needed, capacity_empty)
    # Pit count of current stint, 1 if exceed empty capacity or no empty space
    pit_counts_before = fuel_addable / capacity_empty if capacity_empty else 1
    # Pit counts after current stint
    pit_counts_after = (fuel_needed - fuel_addable) / capacity_total if capacity_total else 0
    # Total pit counts add together
    return pit_counts_before + pit_counts_after


def one_less_pit_stop_consumption(
    pit_counts_late: float, capacity_total: float, fuel_in_tank: float, laps_remain: float) -> float:
    """Estimate fuel consumption for one less pit stop"""
    if laps_remain:
        pit_counts = ceil(pit_counts_late) - 1
        # Consumption = total fuel / laps
        return (pit_counts * capacity_total + fuel_in_tank) / laps_remain
    return 0


def fuel_to_energy_ratio(fuel: float, energy: float) -> float:
    """Fuel to energy ratio"""
    if energy:
        return fuel / energy
    return 0


# Wear
def wear_lifespan_in_laps(remaining: float, wear_last_lap: float) -> float:
    """Wear lifespan in laps = remaining / last lap wear"""
    if wear_last_lap > 0:
        est_laps = remaining / wear_last_lap
    else:
        est_laps = 999
    if est_laps > 999:
        est_laps = 999
    return est_laps


def wear_lifespan_in_mins(remaining: float, wear_last_lap: float, laptime: float) -> float:
    """Wear lifespan in minutes = remaining / last lap wear * laptime / 60"""
    if laptime <= 0:
        return 999
    if wear_last_lap > 0:
        est_mins = remaining / wear_last_lap * laptime / 60
    else:
        est_mins = 999
    if est_mins > 999:
        est_mins = 999
    return est_mins


def end_stint_tread(remaining: float, wear_last_lap: float, laps_remain: float) -> float:
    """Estimate end-stint remaining tyre tread (%) before pitting"""
    return remaining - wear_last_lap * laps_remain


def wear_weighted(wear_curr_lap: float, wear_last_lap: float, lap_into: float) -> float:
    """Weighted wear difference between last and current lap based on lap progression"""
    if wear_curr_lap >= wear_last_lap:
        return wear_curr_lap
    lap_into *= lap_into  # square
    return wear_curr_lap * lap_into + wear_last_lap * (1 - lap_into)


# Wheel
def rot2radius(speed: float, angular_speed: float) -> float:
    """Angular speed to radius"""
    if angular_speed:
        return abs(speed / angular_speed)
    return 0


def slip_ratio(w_rot: float, w_radius: float, v_speed: float) -> float:
    """Slip ratio (percentage), speed unit in m/s"""
    if v_speed > 1:
        return abs(w_rot) * w_radius / v_speed - 1
    return 0


def slip_angle(v_lat: float, v_lgt: float) -> float:
    """Slip angle (radians)"""
    if v_lgt:
        return atan(v_lat / v_lgt)
    return 0


def wheel_axle_rotation(rot_left: float, rot_right: float) -> float:
    """Wheel axle rotation"""
    # Make sure both wheels rotate towards same direction
    if rot_left >= 0 <= rot_right or rot_left <= 0 >= rot_right:
        return (rot_left + rot_right) / 2
    return 0


def wheel_rotation_bias(rot_axle: float, rot_left: float, rot_right: float) -> float:
    """Wheel rotation bias (difference) against axle rotation"""
    if rot_axle:
        return abs((rot_left - rot_right) / rot_axle)
    return 0


def wheel_rotation_ratio(rot_axle: float, rot_left: float) -> float:
    """Calculate wheel rotation ratio between left and right wheel on same axle"""
    if rot_axle:
        return rot_left / rot_axle / 2
    return 0.5


def differential_locking_percent(rot_axle: float, rot_left: float) -> float:
    """Differential (wheel) locking percent

    0% = one wheel completely spinning or locked, 100% = both wheel rotated at same speed.
    """
    if rot_axle:
        return 1 - abs(rot_left / rot_axle - 1)
    return 0
