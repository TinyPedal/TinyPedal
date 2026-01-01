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
Fuel/Energy delta file function
"""

from __future__ import annotations

import csv
import logging

from ..validator import invalid_save_name, valid_delta_set

logger = logging.getLogger(__name__)


def load_fuel_delta_file(
    filepath: str, filename: str, extension: str, defaults: tuple
) -> tuple[tuple, float, float]:
    """Load fuel/energy delta file (*.fuel, *.energy)"""
    try:
        with open(f"{filepath}{filename}{extension}", newline="", encoding="utf-8") as csvfile:
            data_reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
            temp_list = tuple(tuple(data) for data in data_reader)
        # Validate data
        lastlist = valid_delta_set(temp_list)
        used_last = lastlist[-1][1]
        laptime_last = lastlist[-1][2]
        return lastlist, used_last, laptime_last
    except FileNotFoundError:
        logger.info("MISSING: consumption delta (%s) data", extension)
    except (IndexError, ValueError, TypeError):
        logger.info("MISSING: invalid consumption delta (%s) data", extension)
    return defaults


def save_fuel_delta_file(
    filepath: str, filename: str, extension: str, dataset: tuple
) -> None:
    """Save fuel/energy delta file (*.fuel, *.energy)"""
    if len(dataset) < 10 or invalid_save_name(filename):
        return
    with open(f"{filepath}{filename}{extension}", "w", newline="", encoding="utf-8") as csvfile:
        data_writer = csv.writer(csvfile)
        data_writer.writerows(dataset)
        logger.info("USERDATA: %s%s saved", filename, extension)
