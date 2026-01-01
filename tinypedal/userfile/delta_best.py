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
Delta best file function
"""

from __future__ import annotations

import csv
import logging

from ..const_file import FileExt
from ..validator import invalid_save_name, valid_delta_set

logger = logging.getLogger(__name__)


def load_delta_best_file(
    filepath: str, filename: str, defaults: tuple, extension: str = FileExt.CSV
) -> tuple[tuple, float]:
    """Load delta best file (*.csv)"""
    try:
        with open(f"{filepath}{filename}{extension}", newline="", encoding="utf-8") as csvfile:
            data_reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
            temp_list = tuple(tuple(data) for data in data_reader)
        # Validate data
        bestlist = valid_delta_set(temp_list)
        laptime_best = bestlist[-1][1]
        return bestlist, laptime_best
    except FileNotFoundError:
        logger.info("MISSING: delta best (%s) data", extension)
    except (IndexError, ValueError, TypeError):
        logger.info("MISSING: invalid delta best (%s) data", extension)
    return defaults


def save_delta_best_file(
    filepath: str, filename: str, dataset: tuple, extension: str = FileExt.CSV
) -> None:
    """Save delta best file (*.csv)"""
    if len(dataset) < 10 or invalid_save_name(filename):
        return
    with open(f"{filepath}{filename}{extension}", "w", newline="", encoding="utf-8") as csvfile:
        data_writer = csv.writer(csvfile)
        data_writer.writerows(dataset)
        logger.info("USERDATA: %s%s saved", filename, extension)
