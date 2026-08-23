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
Car setup file function
"""

from __future__ import annotations

import logging
import os

from ..const_common import CRLF, FLOAT_INF
from ..const_file import FileExt
from ..regex_pattern import rex_special_char

logger = logging.getLogger(__name__)


def set_car_setup_laptime(seconds: float) -> str:
    """Set car setup lap time"""
    if seconds >= FLOAT_INF:
        seconds = 0
    return f"{seconds // 60:.0f}-{seconds % 60 - seconds % 1:02.0f}-{seconds % 1 * 1000:03.0f}"


def set_car_setup_filename(*names: str) -> str:
    """Set car setup filename, strip off invalid and special chars"""
    return rex_special_char.sub("", " - ".join(n for n in names if n))


def remove_car_setup_file(filepath: str, filename: str, extension: str = FileExt.SVM):
    """Remove car setup file"""
    try:
        full_path = f"{filepath}{filename}{extension}"
        if os.path.exists(full_path):
            os.remove(full_path)
        logger.info("USERDATA: %s%s removed", filename, extension)
    except (FileNotFoundError, PermissionError, OSError):
        logger.error("USERDATA: %s not found", filename)


def rename_car_setup_file(filepath: str, old_filename: str, new_filename: str, extension: str = FileExt.SVM):
    """Rename car setup file"""
    try:
        os.rename(
            f"{filepath}{old_filename}{extension}",
            f"{filepath}{new_filename}{extension}",
        )
        logger.info("USERDATA: %s%s updated", new_filename, extension)
    except (FileNotFoundError, PermissionError, OSError):
        logger.error("USERDATA: car setup not found %s", new_filename)


def save_car_setup_file(
    filepath: str, filename: str, dataset: tuple[str],
    extension: str = FileExt.SVM
) -> None:
    """Save car setup file"""
    if len(dataset) < 2:
        return
    with open(f"{filepath}{filename}{extension}", "w", newline="", encoding="utf-8") as temp_file:
        for line in dataset:
            temp_file.write(line)
            temp_file.write(CRLF)
        logger.info("USERDATA: %s%s saved", filename, extension)
