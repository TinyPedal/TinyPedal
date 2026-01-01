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
Sector best file function
"""

from __future__ import annotations

import csv
import logging

from ..const_file import FileExt
from ..validator import invalid_save_name

logger = logging.getLogger(__name__)


def load_sector_best_file(
    filepath:str, filename: str, session_id: tuple, defaults: list, extension: str = FileExt.SECTOR
) -> tuple[list, list, list, list]:
    """Load sector best file (*.sector)"""
    try:
        with open(f"{filepath}{filename}{extension}", newline="", encoding="utf-8") as csvfile:
            temp_list = list(csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC))
        # Check if same session
        if (temp_list[0][0] == session_id[0] and  # session_stamp
            temp_list[0][1] <= session_id[1] and  # session_etime
            temp_list[0][2] <= session_id[2]):    # session_tlaps
            # Session best data
            best_s_tb = [temp_list[1][0], temp_list[1][1], temp_list[1][2]]
            best_s_pb = [temp_list[2][0], temp_list[2][1], temp_list[2][2]]
        else:
            best_s_tb = defaults.copy()
            best_s_pb = defaults.copy()
        # All time best data
        all_best_s_tb = [temp_list[3][0], temp_list[3][1], temp_list[3][2]]
        all_best_s_pb = [temp_list[4][0], temp_list[4][1], temp_list[4][2]]
        return best_s_tb, best_s_pb, all_best_s_tb, all_best_s_pb
    except FileNotFoundError:
        logger.info("MISSING: sector best (%s) data", extension)
    except (IndexError, ValueError, TypeError):
        logger.info("MISSING: invalid sector best (%s) data", extension)
    return defaults.copy(), defaults.copy(), defaults.copy(), defaults.copy()


def save_sector_best_file(
    filepath: str, filename: str, dataset: tuple, extension: str = FileExt.SECTOR
) -> None:
    """Save sector best file (*.sector)

    sector(CSV) file structure:
        Line 0: session stamp, session elapsed time, session total laps
        Line 1: session theoretical best sector time
        Line 2: session personal best sector time
        Line 3: all time theoretical best sector time
        Line 4: all time personal best sector time
    """
    if len(dataset) != 5 or invalid_save_name(filename):
        return
    with open(f"{filepath}{filename}{extension}", "w", newline="", encoding="utf-8") as csvfile:
        data_writer = csv.writer(csvfile)
        data_writer.writerows(dataset)
        logger.info("USERDATA: %s%s saved", filename, extension)
