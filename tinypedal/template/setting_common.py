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
Default common setting template
"""

from ..const_api import API_DEFAULT_NAME
from ..version import __version__

COMMON_DEFAULT = {
    "preset": {
        "api_name": API_DEFAULT_NAME,
        "version": __version__,
    },
    "overlay": {
        "fixed_position": False,
        "auto_hide": True,
        "enable_grid_move": False,
        "vr_compatibility": False,
    },
    "units": {
        "distance_unit": "Meter",
        "fuel_unit": "Liter",
        "odometer_unit": "Kilometer",
        "power_unit": "Kilowatt",
        "speed_unit": "KPH",
        "temperature_unit": "Celsius",
        "turbo_pressure_unit": "bar",
        "tyre_pressure_unit": "kPa",
    },
    "pace_notes_playback": {
        "enable": False,
        "update_interval": 10,
        "enable_playback_while_in_pit": False,
        "enable_manual_file_selector": False,
        "pace_notes_file_name": "",
        "pace_notes_sound_path": "/",
        "pace_notes_sound_format": "wav",
        "pace_notes_sound_volume": 50,
        "pace_notes_sound_max_duration": 10,
        "pace_notes_sound_max_queue": 5,
        "pace_notes_global_offset": 0,
    },
}
