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
Driver stats file function
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from time import sleep
from typing import KeysView, get_type_hints

from ..const_common import MAX_SECONDS
from ..const_file import FileExt, StatsFile
from ..validator import convert_value_type, purge_data_key
from .json_setting import (
    create_backup_file,
    save_and_verify_json_file,
    save_json_file,
    set_backup_timestamp,
)

logger = logging.getLogger(__name__)


@dataclass
class DriverStats:
    """Driver stats data

    Attributes:
        pb: personal best lap time.
        qb: qualifying best lap time.
        rb: race best lap time.
        meters: meters driven.
        seconds: seconds spent driving.
        liters: liters of fuel consumed.
        valid: valid laps.
        invalid: invalid laps.
        penalties: penalties recieved in race.
        races: number of races completed.
        wins: number of wins.
        podiums: number of podiums.
    """

    pb: float = MAX_SECONDS
    qb: float = MAX_SECONDS
    rb: float = MAX_SECONDS
    meters: float = 0.0
    seconds: float = 0.0
    liters: float = 0.0
    valid: int = 0
    invalid: int = 0
    penalties: int = 0
    races: int = 0
    wins: int = 0
    podiums: int = 0

    @classmethod
    def keys(cls) -> KeysView[str]:
        """Get key name list"""
        return cls.__annotations__.keys()

    @staticmethod
    def is_lap_time(key: str) -> bool:
        """Is lap time"""
        return key in ("pb", "qb", "rb")


def validate_stats_file(stats_user: dict) -> dict:
    """Validate stats file

    Full validation for every primary key (track name) and secondary key (vehicle name),
    Only required for loading file in Driver Stats Viewer.
    """
    for key in stats_user:
        if not isinstance(stats_user[key], dict):
            stats_user[key] = {}
        sub_value = stats_user[key]
        for sub_key in sub_value:
            if not isinstance(sub_value[sub_key], dict):
                sub_value[sub_key] = {}
    return stats_user


def get_sub_dict(source: dict, key_name: str) -> dict:
    """Get sub dict, create new if not exist"""
    sub_dict = source.get(key_name)
    if not isinstance(sub_dict, dict):
        source[key_name] = {}
        sub_dict = source[key_name]
    return sub_dict


def load_driver_stats(
    key_list: tuple[str, str], filepath: str, filename: str = StatsFile.DRIVER
) -> DriverStats:
    """Load driver stats"""
    stats_user = load_stats_json_file(
        filepath=filepath,
        filename=filename,
    )
    if stats_user is None:
        return DriverStats()
    # Get data from matching key
    loaded_dict = stats_user
    for key in key_list:
        temp_dict = loaded_dict.get(key)
        if not isinstance(temp_dict, dict):  # not exist, set to default
            return DriverStats()
        loaded_dict = temp_dict
    # Add data to DriverStats
    try:
        return DriverStats(**purge_data_key(loaded_dict, DriverStats.keys()))
    except (AttributeError, TypeError, KeyError, ValueError):
        return DriverStats()


def save_driver_stats(
    key_list: tuple[str, str], stats_update: DriverStats, filepath: str, filename: str = StatsFile.DRIVER
) -> None:
    """Save driver stats"""
    if not key_list or not all(key_list):  # ignore invalid key name
        return
    # Load stats with limited attempts
    load_attempts = 10
    while load_attempts > 0:
        stats_user = load_stats_json_file(
            filepath=filepath,
            filename=filename,
            show_log=False,
        )
        if stats_user is not None:
            break
        load_attempts -= 1
        logger.info("USERDATA: unable to load %s%s, %s attempt(s) left", filename, FileExt.STATS, load_attempts)
        sleep(0.05)
    # Create backup if failed to load stats
    if stats_user is None:
        logger.info("USERDATA: unable to load %s%s, creating backup", filename, FileExt.STATS)
        if not create_backup_file(f"{filename}{FileExt.STATS}", filepath, set_backup_timestamp(), show_log=True):
            return  # abort saving if failed to create backup
        stats_user = {}  # reset stats
    # Get data from matching key
    loaded_dict = stats_user
    for key in key_list:
        loaded_dict = get_sub_dict(loaded_dict, key)
    # Verify and update new data
    default_dict = DriverStats.__dict__
    default_type = get_type_hints(DriverStats)
    for key, value in stats_update.__dict__.items():
        # Add new default value if not exists
        if key not in loaded_dict:
            loaded_dict[key] = default_dict[key]
        # Check value type, auto correct if mismatch
        if not isinstance(loaded_dict[key], default_type[key]):
            loaded_dict[key] = convert_value_type(loaded_dict[key], default_dict[key], default_type[key])
        # Update laptime value faster than old value
        if DriverStats.is_lap_time(key):
            if loaded_dict[key] <= 0:  # reset invalid time
                loaded_dict[key] = MAX_SECONDS
            if loaded_dict[key] > value > 0:
                loaded_dict[key] = value
            continue
        # Update value (increment)
        loaded_dict[key] += value
    # Save new data
    save_stats_json_file(
        stats_user=stats_user,
        filepath=filepath,
        filename=filename,
    )


def load_stats_json_file(
    filepath: str, filename: str = StatsFile.DRIVER, extension: str = FileExt.STATS, show_log: bool = True
) -> dict | None:
    """Load stats json file, create new if not exists, or returns "None" if invalid"""
    try:
        with open(f"{filepath}{filename}{extension}", "r", encoding="utf-8") as jsonfile:
            stats_user = json.load(jsonfile)
            if not isinstance(stats_user, dict):
                raise TypeError
            return stats_user
    except FileNotFoundError:
        if show_log:
            logger.info("MISSING: %s stats (%s) data, create new stats", filename, extension)
        stats_user = {}
        save_json_file(stats_user, filename, filepath, extension, compact_json=True)
        return stats_user
    except (AttributeError, TypeError, KeyError, ValueError):
        if show_log:
            logger.info("MISSING: invalid %s stats (%s) data", filename, extension)
    return None


def save_stats_json_file(
    stats_user: dict, filepath: str, filename: str = StatsFile.DRIVER, extension: str = FileExt.STATS
) -> None:
    """Save stats to json file"""
    save_and_verify_json_file(
        dict_user=stats_user,
        filename=f"{filename}{extension}",
        filepath=filepath,
        max_attempts=10,
        compact_json=True,
    )
