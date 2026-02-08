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
Lap time history Widget
"""

from .. import calculation as calc
from .. import units
from ..api_control import api
from ..const_common import TEXT_NOLAPTIME
from ..module_info import ConsumptionDataSet, minfo
from ._base import Overlay


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout(gap_vert=self.wcfg["bar_gap"])
        self.set_primary_layout(layout=layout)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        layout_reversed = self.wcfg["layout"] != 0
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        self.history_slot = min(max(self.wcfg["lap_time_history_count"], 1), 100)

        # Config units
        self.unit_fuel = units.set_unit_fuel(self.cfg.units["fuel_unit"])

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # Laps
        if self.wcfg["show_laps"]:
            bar_style_laps = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_laps"],
                    bg_color=self.wcfg["bkg_color_laps"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_last_laps"],
                    bg_color=self.wcfg["bkg_color_last_laps"])
            )
            self.bars_laps = self.set_qlabel(
                text="---",
                style=bar_style_laps[1],
                width=font_m.width * 3 + bar_padx,
                count=self.history_slot + 1,
            )
            self.bars_laps[0].updateStyle(bar_style_laps[0])
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_laps,
                column_index=self.wcfg["column_index_laps"],
                bottom_to_top=layout_reversed,
            )

        # Time
        if self.wcfg["show_time"]:
            self.bar_style_time = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_time"],
                    bg_color=self.wcfg["bkg_color_time"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_last_time"],
                    bg_color=self.wcfg["bkg_color_last_time"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_invalid_laptime"],
                    bg_color=self.wcfg["bkg_color_last_time"])
            )
            self.bars_time = self.set_qlabel(
                text=TEXT_NOLAPTIME,
                style=self.bar_style_time[1],
                width=font_m.width * 8 + bar_padx,
                count=self.history_slot + 1,
            )
            self.bars_time[0].updateStyle(self.bar_style_time[0])
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_time,
                column_index=self.wcfg["column_index_time"],
                bottom_to_top=layout_reversed,
            )

        # Lap time delta
        if self.wcfg["show_delta"]:
            self.bar_style_delta = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_delta"],
                    bg_color=self.wcfg["bkg_color_delta"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_last_delta"],
                    bg_color=self.wcfg["bkg_color_last_delta"])
            )
            self.bars_delta = self.set_qlabel(
                text="--.--",
                style=self.bar_style_delta[1],
                width=font_m.width * 5 + bar_padx,
                count=self.history_slot + 1,
            )
            self.bars_delta[0].updateStyle(self.bar_style_delta[0])
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_delta,
                column_index=self.wcfg["column_index_delta"],
                bottom_to_top=layout_reversed,
            )

        # Fuel
        if self.wcfg["show_fuel"]:
            bar_style_fuel = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_fuel"],
                    bg_color=self.wcfg["bkg_color_fuel"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_last_fuel"],
                    bg_color=self.wcfg["bkg_color_last_fuel"])
            )
            self.bars_fuel = self.set_qlabel(
                text="-.--",
                style=bar_style_fuel[1],
                width=font_m.width * 4 + bar_padx,
                count=self.history_slot + 1,
            )
            self.bars_fuel[0].updateStyle(bar_style_fuel[0])
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_fuel,
                column_index=self.wcfg["column_index_fuel"],
                bottom_to_top=layout_reversed,
            )

        # Tyre wear
        if self.wcfg["show_wear"]:
            bar_style_wear = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_wear"],
                    bg_color=self.wcfg["bkg_color_wear"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_last_wear"],
                    bg_color=self.wcfg["bkg_color_last_wear"])
            )
            self.bars_wear = self.set_qlabel(
                text="---",
                style=bar_style_wear[1],
                width=font_m.width * 3 + bar_padx,
                count=self.history_slot + 1,
            )
            self.bars_wear[0].updateStyle(bar_style_wear[0])
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_wear,
                column_index=self.wcfg["column_index_wear"],
                bottom_to_top=layout_reversed,
            )

        # Last data
        self.empty_data = ConsumptionDataSet()
        self.last_data_version = -1
        self.last_max_energy = 0.0
        self.update_laps_history(())

    def timerEvent(self, event):
        """Update when vehicle on track"""
        max_energy = api.read.vehicle.max_virtual_energy()
        # Check if virtual energy available
        if self.wcfg["show_virtual_energy_if_available"] and max_energy:
            temp_fuel_est = minfo.energy.estimatedConsumption
        else:
            temp_fuel_est = self.unit_fuel(minfo.fuel.estimatedConsumption)

        # Current laps data
        if self.wcfg["show_laps"]:
            self.update_laps(self.bars_laps[0], api.read.lap.number())
        if self.wcfg["show_time"]:
            self.update_time(self.bars_time[0], minfo.delta.lapTimeEstimated)
        if self.wcfg["show_delta"]:
            self.update_delta(self.bars_delta[0], minfo.delta.deltaLast)
        if self.wcfg["show_fuel"]:
            self.update_fuel(self.bars_fuel[0], temp_fuel_est)
        if self.wcfg["show_wear"]:
            self.update_wear(self.bars_wear[0], calc.mean(minfo.wheels.estimatedTreadWear))

        # History laps data
        if (
            self.last_data_version != minfo.history.consumptionDataVersion
            or self.last_max_energy != max_energy
        ):
            self.last_data_version = minfo.history.consumptionDataVersion
            self.last_max_energy = max_energy
            self.update_laps_history(minfo.history.consumptionDataSet)

    # GUI update methods
    def update_laps(self, target, data):
        """Laps data"""
        if target.last != data:
            target.last = data
            target.setText(f"{data:03.0f}"[:3])

    def update_time(self, target, data):
        """Time data"""
        if target.last != data:
            target.last = data
            target.setText(calc.sec2laptime_full(data)[:8])

    def update_delta(self, target, data):
        """Delta data"""
        if target.last != data:
            target.last = data
            target.setText(f"{calc.sym_max(data, 99.9):+.3f}"[:5])

    def update_fuel(self, target, data):
        """Fuel data"""
        if target.last != data:
            target.last = data
            target.setText(f"{data:04.2f}"[:4])

    def update_wear(self, target, data):
        """Wear data"""
        if target.last != data:
            target.last = data
            target.setText(f"{data:03.1f}"[:3])

    def update_laps_history(self, dataset):
        """Laps history data"""
        is_energy = bool(self.wcfg["show_virtual_energy_if_available"] and api.read.vehicle.max_virtual_energy())
        for index in range(self.history_slot):
            if index < len(dataset):
                data = dataset[index]
                hidden = False
            else:
                data = self.empty_data
                hidden = not self.wcfg["show_empty_history"]
            index += 1

            if self.wcfg["show_laps"]:
                self.update_laps(self.bars_laps[index], data.lapNumber)
                self.bars_laps[index].setHidden(hidden)

            if self.wcfg["show_time"]:
                self.update_time(self.bars_time[index], data.lapTimeLast)
                invalid = (2 - data.isValidLap) if (data.lapTimeLast > 0) else 1
                self.bars_time[index].updateStyle(self.bar_style_time[invalid])
                self.bars_time[index].setHidden(hidden)

            if self.wcfg["show_delta"]:
                last_data = dataset[index] if index < len(dataset) else self.empty_data
                self.update_delta(self.bars_delta[index], data.lapTimeLast - last_data.lapTimeLast)
                self.bars_delta[index].setHidden(hidden)

            if self.wcfg["show_fuel"]:
                self.update_fuel(self.bars_fuel[index], data.lastLapUsedEnergy if is_energy else data.lastLapUsedFuel)
                self.bars_fuel[index].setHidden(hidden)

            if self.wcfg["show_wear"]:
                self.update_wear(self.bars_wear[index], data.tyreAvgWearLast)
                self.bars_wear[index].setHidden(hidden)
