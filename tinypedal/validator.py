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
Validator function
"""

from __future__ import annotations

import logging
import os
import re
import time
from functools import partial
from math import isfinite
from time import monotonic
from typing import Any, Callable

from .constant import DATA, FILE
from .regex_pattern import CFG_INVALID_FILENAME, rex_hex_color

logger = logging.getLogger(__name__)


# Value validate
def infnan_to_zero(value: Any) -> float:
    """Convert invalid value (inf or nan) to zero"""
    if isfinite(value):
        return value
    return 0


def bytes_to_str(bytestring: bytes | Any, char_encoding: str = "utf-8") -> str:
    """Convert bytes to string"""
    if isinstance(bytestring, bytes):
        return bytestring.decode(encoding=char_encoding, errors="replace").rstrip()
    return ""


def bytes_decoder(encoding: str = "utf-8") -> Callable[[bytes], str]:
    """Set bytes to string decode function"""
    if encoding:
        encoding = encoding.lower()
    else:
        encoding = "utf-8"
    return partial(bytes_to_str, char_encoding=encoding)


def is_allowed_filename(filename: str) -> bool:
    """Is allowed setting file name"""
    return re.search(CFG_INVALID_FILENAME, filename, flags=re.IGNORECASE) is None


def invalid_save_name(name: str) -> bool:
    """Is invalid save name"""
    return name == "" or name[:3] == " - " or name[-3:] == " - "


def is_string_number(value: str) -> bool:
    """Validate string number"""
    try:
        float(value)
        return True
    except ValueError:
        return False


def valid_sectors(sector_time: list | Any, max_time: float = DATA.MAX_SECONDS) -> bool:
    """Is valid sector time"""
    if isinstance(sector_time, list):
        return all(0 < sec < max_time for sec in sector_time)
    return 0 < sector_time < max_time


def is_same_session(
    combo_name: str, session_id: tuple[int, int, int],
    last_session_id: tuple[str, int, int, int]) -> bool:
    """Check if same session, car, track combo"""
    return (
        combo_name == last_session_id[0] and
        last_session_id[1] == session_id[0] and  # session time stamp
        last_session_id[2] <= session_id[1] and  # session elapsed time
        last_session_id[3] <= session_id[2]  # total completed laps
    )


# File validate
def file_last_modified(filepath: str = "", filename: str = "", extension: str = "") -> float:
    """Check file last modified time, 0 if file not exist"""
    filename_full = f"{filepath}{filename}{extension}"
    if os.path.exists(filename_full):
        return os.path.getmtime(filename_full)
    return 0


def image_exists(filepath: str, extension: str = FILE.EXT_PNG, max_size: int = 10_240_000) -> bool:
    """Validate image file path, file format (default PNG), max file size (default < 10MB)"""
    return (
        os.path.exists(filepath) and
        os.path.getsize(filepath) < max_size and
        filepath.lower().endswith(extension)
    )


def is_json_data(data: Any) -> bool:
    """Is valid json data"""
    return isinstance(data, (dict, list))


# Delta list validate
def valid_delta_set(data: tuple) -> tuple:
    """Validate delta data set"""
    # Final row value(second column) must be higher than previous row
    if data[-1][1] < data[-2][1]:
        raise ValueError
    # Check distance greater than next row for first 10 rows
    for idx in range(11, 0, -1):
        if data[idx][0] > data[idx + 1][0]:
            raise ValueError
    # Delta list must have at least 10 lines of samples
    if len(data) < 10:
        raise ValueError
    return data


def valid_delta_raw(dataset: list[tuple[float, float]], final: float, column: int) -> bool:
    """Validate raw delta data set"""
    try:
        if len(dataset) < 10:  # minimum 10 data samples
            return False
        # Remove rows if source value higher than final value
        while dataset[-1][column] > final:
            dataset.pop()
            if not dataset:
                return False
        return True
    except (AttributeError, TypeError, IndexError):
        return False


# Value type validate
def valid_value_type(value: Any, default: Any) -> Any:
    """Validate if value is same type as default, return default value if False"""
    if isinstance(value, type(default)):
        return value
    return default


def convert_value_type(value: Any, default: Any, target_type: type) -> Any:
    """Convert any value type to target type, revert to default if fails"""
    try:
        return target_type(value)
    except (TypeError, ValueError, OverflowError):
        return default


def dict_value_type(data: dict, default_data: dict) -> dict:
    """Validate and correct dictionary value type"""
    return {
        key: type(def_value)(data.get(key, def_value))
        for key, def_value in default_data.items()
    }


# Color validate
def is_hex_color(color_str: str | Any) -> bool:
    """Validate HEX color string"""
    if isinstance(color_str, str):
        return rex_hex_color.search(color_str) is not None
    return False


# Time format validate
def is_clock_format(_format: str) -> bool:
    """Validate clock time format"""
    try:
        time.strftime(_format)
        return True
    except ValueError:
        return False


# Timer
def state_timer(interval: float, last: float = 0):
    """State timer

    Args:
        interval: time interval in seconds.
        last: last time stamp in seconds.
    Yields:
        is_timeout: bool.
    """
    while True:
        seconds = monotonic()
        if seconds - last >= interval:
            last = seconds
            yield True
        else:
            yield False
