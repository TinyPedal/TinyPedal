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
API data adapter
"""
from typing import NamedTuple

from . import _reader


class APIDataReader(NamedTuple):
    """API data reader"""

    state: _reader.State
    brake: _reader.Brake
    emotor: _reader.ElectricMotor
    engine: _reader.Engine
    inputs: _reader.Inputs
    lap: _reader.Lap
    session: _reader.Session
    switch: _reader.Switch
    timing: _reader.Timing
    tyre: _reader.Tyre
    vehicle: _reader.Vehicle
    wheel: _reader.Wheel
