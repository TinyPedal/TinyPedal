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
Mapping module
"""

from .. import calculation as calc
from .. import realtime_state
from ..api_control import api
from ..const_file import FileExt
from ..module_info import MapCoords, MappingInfo, minfo
from ..userfile.track_info import load_track_info, save_track_info
from ..userfile.track_map import load_track_map_file, save_track_map_file
from ..validator import file_last_modified, generator_init
from ._base import DataModule


class Realtime(DataModule):
    """Mapping data"""

    __slots__ = ()

    def __init__(self, config, module_name):
        super().__init__(config, module_name)

    def update_data(self):
        """Update module data"""
        _event_wait = self._event.wait
        reset = False
        vehicle_resets = None
        update_interval = self.idle_interval

        gen_record_track_map = record_track_map(
            output=minfo.mapping,
            filepath=self.cfg.path.track_map,
        )
        gen_record_track_info = record_track_info(
            output=minfo.mapping,
        )

        while not _event_wait(update_interval):
            if realtime_state.active or vehicle_resets != realtime_state.resets:
                vehicle_resets = realtime_state.resets

                if not reset:
                    reset = True
                    update_interval = self.active_interval

                # Recording map data
                gen_record_track_map.send(vehicle_resets)
                gen_record_track_info.send(vehicle_resets)

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval


def set_sunlight_phase(sunrise: str, sunset: str):
    """Set sunlight phase time"""
    sec_sunrise = calc.clock_time_to_seconds(sunrise)
    sec_sunset = calc.clock_time_to_seconds(sunset)
    sec_midday = calc.clockwise_median_time(sec_sunrise, sec_sunset)
    sec_midnight = calc.clockwise_median_time(sec_sunset, sec_sunrise)
    return tuple(sorted((
        (sec_sunrise, 0),
        (sec_midday, 1),
        (sec_sunset, 2),
        (sec_midnight, 3),
    )))


@generator_init
def record_track_info(output: MappingInfo):
    """Update track info"""
    last_reset = None  # reset check
    delayed_save = False

    track_name = ""
    pit_entry = 0.0
    pit_exit = 0.0
    pit_speed = 0.0

    while True:
        reset = yield None

        # Reset
        if last_reset != reset:
            # Save data
            if delayed_save:
                save_track_info(
                    track_name=track_name,
                    # kwargs {key: value}
                    pit_entry=pit_entry,
                    pit_exit=pit_exit,
                    pit_speed=pit_speed,
                )
                delayed_save = False

            # Delay reset until driving
            if not realtime_state.active:
                continue
            last_reset = reset

            # Load track info
            track_name = api.read.session.track_name()
            pit_entry = load_track_info(track_name, "pit_entry")
            pit_exit = load_track_info(track_name, "pit_exit")
            pit_speed = load_track_info(track_name, "pit_speed")
            output.speedTrapPosition = load_track_info(track_name, "speed_trap")
            output.sunlightPhases = set_sunlight_phase(
                load_track_info(track_name, "sunrise"),
                load_track_info(track_name, "sunset"),
            )

            # Set default
            pos_last = 0.0
            last_speed = 0.0
            pitlane_length = 0.0
            last_in_pits = -1
            delayed_save = True

        in_pits = api.read.vehicle.in_pits()

        # Calibrate pit speed limit
        if in_pits and api.read.switch.speed_limiter():
            pos_curr = api.read.lap.distance()
            if pos_last != pos_curr:  # position check
                pos_last = pos_curr
                speed = api.read.vehicle.speed()
                if (api.read.inputs.throttle_raw() > 0.95 and  # full throttle check
                    api.read.inputs.brake_raw() < 0.01 and  # no braking check
                    speed > 1 and  # moving check
                    0.1 > speed - last_speed > 0):  # limit speed delta in 0.0 - 0.1m/s
                    pit_speed = speed
                last_speed = speed

        # Calculate pit lane length
        if last_in_pits != in_pits:
            if last_in_pits != -1 and api.read.vehicle.speed() > 1:  # avoid ESC desync
                if in_pits:  # entering pit
                    pit_entry = max(api.read.lap.distance(), 0.0)
                else:  # exiting pit
                    pit_exit = max(api.read.lap.distance(), 0.0)
            last_in_pits = in_pits
            pitlane_length = calc.pitlane_length(
                api.read.lap.track_length(),
                pit_entry,
                pit_exit,
            )

        output.pitSpeedLimit = pit_speed
        output.pitEntryPosition = pit_entry
        output.pitExitPosition = pit_exit
        output.pitLaneLength = pitlane_length
        output.pitPassTime = pitlane_length / pit_speed if pit_speed else 0.0


@generator_init
def record_track_map(output: MappingInfo, filepath: str):
    """Record map data"""
    last_reset = None  # reset check
    delayed_save = False

    recording = False
    validating = False
    last_sector_idx = -1
    last_lap_stime = -1.0  # last lap start time
    pos_last = 0.0  # last checked player vehicle position
    # File info
    map_exist = False
    last_modified = 0.0
    filename = ""
    # Map data
    output_data = MapCoords()
    recorder_data = MapCoords()
    temp_data = MapCoords()

    while True:
        reset = yield None

        # Reset
        if last_reset != reset:
            # Save data
            if delayed_save:
                save_track_map_file(
                    filepath=filepath,
                    filename=filename,
                    view_box=calc.svg_view_box(output_data.coords, 20),
                    raw_coords=output_data.coords,
                    raw_dists=output_data.dists,
                    sector_index=output_data.sectors,
                    decimals=4,
                )
                output_data.clear()
                delayed_save = False
                #logger.info("map saved, stopped map recording")

            # Delay reset until driving
            if not realtime_state.active:
                continue
            last_reset = reset

            # Check if same map loaded
            filename = api.read.session.track_name()
            modified = file_last_modified(
                filepath=filepath,
                filename=filename,
                extension=FileExt.SVG,
            )
            map_exist = (last_modified == modified > 0)
            last_modified = modified
            if map_exist:
                continue

            # Load map file
            output_data.coords, output_data.dists, output_data.sectors = load_track_map_file(
                filepath=filepath,
                filename=filename,
            )
            if output_data.is_valid():
                output.coordinates = output_data.coords
                output.elevations = output_data.dists
                output.sectors = output_data.sectors
                output.lastModified = last_modified
                map_exist = True
                #logger.info("map exist")
            else:
                output.reset()
                map_exist = False
                #logger.info("map not exist")

            # Reset to defaults
            output_data.clear()
            temp_data.clear()
            recorder_data.clear()
            recording = False
            validating = False
            last_sector_idx = -1
            last_lap_stime = -1.0
            pos_last = 0.0

        # Recording map data
        if map_exist:
            continue

        # Lap start & finish detection
        # Init reset
        lap_stime = api.read.timing.start()
        if last_lap_stime == -1:
            recorder_data.reset()
            last_lap_stime = lap_stime

        # New lap
        if lap_stime > last_lap_stime:
            # End recording
            if recorder_data.coords:
                temp_data.coords = tuple(recorder_data.coords)
                temp_data.dists = tuple(recorder_data.dists)
                temp_data.sectors = tuple(recorder_data.sectors)
                validating = True
            # Reset
            recorder_data.reset()
            last_lap_stime = lap_stime
            pos_last = 0
            recording = True
            #logger.info("map recording")

        # Validate map data after crossing finish line
        if validating:
            laptime_curr = api.read.timing.current_laptime()
            # Save data
            if 1 < laptime_curr <= 8 and api.read.timing.last_laptime() > 0:
                output_data.coords = temp_data.coords
                output_data.dists = temp_data.dists
                output_data.sectors = temp_data.sectors
                # Reset
                temp_data.clear()
                recorder_data.clear()
                recording = False
                validating = False
                delayed_save = True
                last_reset = None  # load recorded map in next loop
            # Switch off validating after 8s
            elif 8 < laptime_curr < 10:
                temp_data.clear()
                validating = False

        # Record map coords
        if recording:
            # Record sector index
            sector_idx = api.read.lap.sector_index()
            if last_sector_idx != sector_idx:
                if sector_idx == 1:
                    recorder_data.sectors[0] = len(recorder_data.coords) - 1
                elif sector_idx == 2:
                    recorder_data.sectors[1] = len(recorder_data.coords) - 1
                last_sector_idx = sector_idx

            # Record driving path
            # Update if position value is different & positive
            pos_curr = api.read.lap.distance()
            if 0 <= pos_curr != pos_last:
                if pos_curr > pos_last:  # position further
                    pos_x = api.read.vehicle.position_longitudinal()
                    pos_y = api.read.vehicle.position_lateral()
                    pos_z = api.read.vehicle.position_vertical()
                    recorder_data.coords.append((pos_x, pos_y))
                    recorder_data.dists.append((pos_curr, pos_z))
                pos_last = pos_curr  # reset last position
