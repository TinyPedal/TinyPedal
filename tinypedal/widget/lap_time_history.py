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
        font = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size"],
            self.wcfg["font_weight"],
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)

        # Config variable
        layout_reversed = self.wcfg["layout"] != 0
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        self.history_slot = min(max(self.wcfg["lap_time_history_count"], 1), 100)

        # Config units
        self.unit_fuel = units.set_unit_fuel(self.cfg.units["fuel_unit"])

        # Laps
        if self.wcfg["show_laps"]:
            self.bars_laps = self.set_rawtext(
                text="---",
                width=font_m.width * 3 + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_last_laps"],
                bg_color=self.wcfg["bkg_color_last_laps"],
                count=self.history_slot + 1,
            )
            self.bars_laps[0].fg = self.wcfg["font_color_laps"]
            self.bars_laps[0].bg = self.wcfg["bkg_color_laps"]
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_laps,
                column_index=self.wcfg["column_index_laps"],
                bottom_to_top=layout_reversed,
            )

        # Time
        if self.wcfg["show_time"]:
            self.bar_style_time = (
                (
                    self.wcfg["font_color_time"],
                    self.wcfg["bkg_color_time"],
                ),
                (
                    self.wcfg["font_color_last_time"],
                    self.wcfg["bkg_color_last_time"],
                ),
                (
                    self.wcfg["font_color_invalid_laptime"],
                    self.wcfg["bkg_color_last_time"],
                ),
            )
            self.bars_time = self.set_rawtext(
                text=TEXT_NOLAPTIME,
                width=font_m.width * 8 + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.bar_style_time[1][0],
                bg_color=self.bar_style_time[1][1],
                count=self.history_slot + 1,
            )
            self.bars_time[0].fg = self.bar_style_time[0][0]
            self.bars_time[0].bg = self.bar_style_time[0][1]
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_time,
                column_index=self.wcfg["column_index_time"],
                bottom_to_top=layout_reversed,
            )

        # Lap time delta
        if self.wcfg["show_delta"]:
            self.bar_style_delta = (
                (
                    self.wcfg["font_color_delta"],
                    self.wcfg["bkg_color_delta"],
                ),
                (
                    self.wcfg["font_color_last_delta"],
                    self.wcfg["bkg_color_last_delta"],
                ),
            )
            decimals_delta = max(self.wcfg["delta_decimal_places"], 1)
            self.width_delta = 3 + decimals_delta
            self.bars_delta = self.set_rawtext(
                text=f"--.{'-' * decimals_delta}",
                width=font_m.width * self.width_delta + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.bar_style_delta[1][0],
                bg_color=self.bar_style_delta[1][1],
                count=self.history_slot + 1,
            )
            self.bars_delta[0].fg = self.bar_style_delta[0][0]
            self.bars_delta[0].bg = self.bar_style_delta[0][1]
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_delta,
                column_index=self.wcfg["column_index_delta"],
                bottom_to_top=layout_reversed,
            )

        # Fuel
        if self.wcfg["show_fuel"]:
            if self.wcfg["show_fuel_sign"]:
                self.sign_fuel = units.set_symbol_fuel(self.cfg.units["fuel_unit"])[0].upper()
            else:
                self.sign_fuel = ""
            decimals_fuel = max(self.wcfg["fuel_decimal_places"], 1)
            self.width_fuel = 2 + decimals_fuel
            self.bars_fuel = self.set_rawtext(
                text=f"-.{'-' * decimals_fuel}{self.sign_fuel}",
                width=font_m.width * (self.width_fuel + len(self.sign_fuel)) + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_last_fuel"],
                bg_color=self.wcfg["bkg_color_last_fuel"],
                count=self.history_slot + 1,
            )
            self.bars_fuel[0].fg = self.wcfg["font_color_fuel"]
            self.bars_fuel[0].bg = self.wcfg["bkg_color_fuel"]
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_fuel,
                column_index=self.wcfg["column_index_fuel"],
                bottom_to_top=layout_reversed,
            )

        # Tyre wear
        if self.wcfg["show_wear"]:
            if self.wcfg["show_wear_sign"]:
                self.sign_wear = "%"
            else:
                self.sign_wear = ""
            decimals_wear = max(self.wcfg["wear_decimal_places"], 1)
            self.width_wear = 2 + decimals_wear
            self.bars_wear = self.set_rawtext(
                text=f"-.{'-' * decimals_wear}{self.sign_wear}",
                width=font_m.width * (self.width_wear + len(self.sign_wear)) + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_last_wear"],
                bg_color=self.wcfg["bkg_color_last_wear"],
                count=self.history_slot + 1,
            )
            self.bars_wear[0].fg = self.wcfg["font_color_wear"]
            self.bars_wear[0].bg = self.wcfg["bkg_color_wear"]
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

        # Current laps data
        if self.wcfg["show_laps"]:
            self.update_laps(self.bars_laps[0], api.read.lap.number())
        if self.wcfg["show_time"]:
            self.update_time(self.bars_time[0], minfo.delta.lapTimeEstimated)
        if self.wcfg["show_delta"]:
            self.update_delta(self.bars_delta[0], minfo.delta.deltaLast)
        if self.wcfg["show_fuel"]:
            if self.wcfg["show_virtual_energy_if_available"] and max_energy:
                fuel = minfo.energy.estimatedConsumption
                sign_fuel = "E" if self.sign_fuel else ""
            else:
                fuel = self.unit_fuel(minfo.fuel.estimatedConsumption)
                sign_fuel = self.sign_fuel
            self.update_fuel(self.bars_fuel[0], fuel, sign_fuel)
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
            target.text = f"{data:03.0f}"[:3]
            target.update()

    def update_time(self, target, data):
        """Time data"""
        if target.last != data:
            target.last = data
            target.text = calc.sec2laptime_full(data)[:8]
            target.update()

    def update_delta(self, target, data):
        """Delta data"""
        if target.last != data:
            target.last = data
            target.text = f"{calc.sym_max(data, 99.9):+.{self.width_delta}f}"[:self.width_delta].strip(".")
            target.update()

    def update_fuel(self, target, data, sign):
        """Fuel data"""
        if target.last != data:
            target.last = data
            text_fuel = f"{data:.{self.width_fuel}f}"[:self.width_fuel].strip(".")
            target.text = f"{text_fuel}{sign}"
            target.update()

    def update_wear(self, target, data):
        """Wear data"""
        if target.last != data:
            target.last = data
            text_wear = f"{data:.{self.width_wear}f}"[:self.width_wear].strip(".")
            target.text = f"{text_wear}{self.sign_wear}"
            target.update()

    def update_laps_history(self, dataset):
        """Laps history data"""
        show_energy = self.wcfg["show_virtual_energy_if_available"]
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
                invalid = (2 - data.isValidLap) if (data.lapTimeLast > 0) else 1
                self.bars_time[index].fg = self.bar_style_time[invalid][0]
                self.bars_time[index].bg = self.bar_style_time[invalid][1]
                self.update_time(self.bars_time[index], data.lapTimeLast)
                self.bars_time[index].setHidden(hidden)

            if self.wcfg["show_delta"]:
                last_data = dataset[index] if index < len(dataset) else self.empty_data
                self.update_delta(self.bars_delta[index], data.lapTimeLast - last_data.lapTimeLast)
                self.bars_delta[index].setHidden(hidden)

            if self.wcfg["show_fuel"]:
                if show_energy and data.lastLapUsedEnergy:
                    fuel = data.lastLapUsedEnergy
                    sign_fuel = "E" if self.sign_fuel else ""
                else:
                    fuel = self.unit_fuel(data.lastLapUsedFuel)
                    sign_fuel = self.sign_fuel
                self.update_fuel(self.bars_fuel[index], fuel, sign_fuel)
                self.bars_fuel[index].setHidden(hidden)

            if self.wcfg["show_wear"]:
                self.update_wear(self.bars_wear[index], data.tyreAvgWearLast)
                self.bars_wear[index].setHidden(hidden)
