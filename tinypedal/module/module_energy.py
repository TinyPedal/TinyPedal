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
Energy module
"""

from __future__ import annotations

from .. import calculation as calc
from .. import realtime_state
from ..api_control import api
from ..const_file import FileExt
from ..module_info import minfo
from ._base import DataModule
from .module_fuel import calc_consumption


class Realtime(DataModule):
    """Energy usage data"""

    __slots__ = ()

    def __init__(self, config, module_name):
        super().__init__(config, module_name)

    def update_data(self):
        """Update module data"""
        _event_wait = self._event.wait
        reset = False
        update_interval = self.idle_interval

        userpath_energy_delta = self.cfg.path.energy_delta

        while not _event_wait(update_interval):
            if realtime_state.active:

                if not reset:
                    reset = True
                    update_interval = self.active_interval

                    combo_name = api.read.session.combo_name()
                    gen_calc_energy = calc_consumption(
                        output=minfo.energy,
                        telemetry_func=telemetry_energy,
                        filepath=userpath_energy_delta,
                        filename=combo_name,
                        extension=FileExt.ENERGY,
                        min_delta_distance=self.mcfg["minimum_delta_distance"],
                    )
                    # Reset module output
                    minfo.energy.reset()

                # Run calculation if virtual energy available
                if api.read.vehicle.max_virtual_energy():
                    gen_calc_energy.send(True)

                    # Update hybrid info
                    minfo.hybrid.fuelEnergyRatio = calc.fuel_to_energy_ratio(
                        minfo.fuel.estimatedConsumption,
                        minfo.energy.estimatedConsumption,
                    )
                    minfo.hybrid.fuelEnergyBias = (
                        minfo.fuel.estimatedLaps - minfo.energy.estimatedLaps
                    )

            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval
                    # Trigger save check
                    gen_calc_energy.send(False)


def telemetry_energy() -> tuple[float, float]:
    """Telemetry energy, output in percentage"""
    max_energy = api.read.vehicle.max_virtual_energy()
    if max_energy:
        return 100.0, api.read.vehicle.virtual_energy() / max_energy * 100
    return 100.0, 0.0
