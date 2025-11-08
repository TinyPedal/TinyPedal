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
Data modules

Add new module to import list below in ascending order,
file name must match corresponding key name
in template/setting_module.py dictionary.
"""

__all__ = [
    "module_delta",
    "module_energy",
    "module_force",
    "module_fuel",
    "module_hybrid",
    "module_mapping",
    "module_notes",
    "module_relative",
    "module_sectors",
    "module_stats",
    "module_vehicles",
    "module_wheels",
]

from . import *
