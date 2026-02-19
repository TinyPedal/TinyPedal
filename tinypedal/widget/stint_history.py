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
Stint history Widget
"""

from __future__ import annotations

from collections import deque

from .. import calculation as calc
from .. import units
from ..api_control import api
from ..module_info import StintData, StintDataSet, minfo
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
        self.stint_slot = max(self.wcfg["stint_history_count"], 1)

        # Config units
        self.unit_fuel = units.set_unit_fuel(self.cfg.units["fuel_unit"])

        # Laps
        if self.wcfg["show_laps"]:
            self.bars_laps = self.set_rawtext(
                text="---",
                width=font_m.width * 3 + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_last_stint_laps"],
                bg_color=self.wcfg["bkg_color_last_stint_laps"],
                count=self.stint_slot + 1,
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
            self.bars_time = self.set_rawtext(
                text="--:--",
                width=font_m.width * 5 + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_last_stint_time"],
                bg_color=self.wcfg["bkg_color_last_stint_time"],
                count=self.stint_slot + 1,
            )
            self.bars_time[0].fg = self.wcfg["font_color_time"]
            self.bars_time[0].bg = self.wcfg["bkg_color_time"]
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_time,
                column_index=self.wcfg["column_index_time"],
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
                fg_color=self.wcfg["font_color_last_stint_fuel"],
                bg_color=self.wcfg["bkg_color_last_stint_fuel"],
                count=self.stint_slot + 1,
            )
            self.bars_fuel[0].fg = self.wcfg["font_color_fuel"]
            self.bars_fuel[0].bg = self.wcfg["bkg_color_fuel"]
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_fuel,
                column_index=self.wcfg["column_index_fuel"],
                bottom_to_top=layout_reversed,
            )

        # Tyre compound
        if self.wcfg["show_tyre"]:
            self.bars_cmpd = self.set_rawtext(
                text="--",
                width=font_m.width * 2 + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_last_stint_tyre"],
                bg_color=self.wcfg["bkg_color_last_stint_tyre"],
                count=self.stint_slot + 1,
            )
            self.bars_cmpd[0].fg = self.wcfg["font_color_tyre"]
            self.bars_cmpd[0].bg = self.wcfg["bkg_color_tyre"]
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_cmpd,
                column_index=self.wcfg["column_index_tyre"],
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
                fg_color=self.wcfg["font_color_last_stint_wear"],
                bg_color=self.wcfg["bkg_color_last_stint_wear"],
                count=self.stint_slot + 1,
            )
            self.bars_wear[0].fg = self.wcfg["font_color_wear"]
            self.bars_wear[0].bg = self.wcfg["bkg_color_wear"]
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_wear,
                column_index=self.wcfg["column_index_wear"],
                bottom_to_top=layout_reversed,
            )

        # Stint delta
        if self.wcfg["show_delta"]:
            decimals_delta = max(self.wcfg["delta_decimal_places"], 1)
            self.width_delta = 3 + decimals_delta
            self.bars_delta = self.set_rawtext(
                text=f"--.{'-' * decimals_delta}",
                width=font_m.width * self.width_delta + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_last_stint_delta"],
                bg_color=self.wcfg["bkg_color_last_stint_delta"],
                count=self.stint_slot + 1,
            )
            self.bars_delta[0].fg = self.wcfg["font_color_delta"]
            self.bars_delta[0].bg = self.wcfg["bkg_color_delta"]
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_delta,
                column_index=self.wcfg["column_index_delta"],
                bottom_to_top=layout_reversed,
            )

        # Stint consistency
        if self.wcfg["show_consistency"]:
            if self.wcfg["show_consistency_sign"]:
                self.sign_consist = "%"
            else:
                self.sign_consist = ""
            decimals_consist = max(self.wcfg["consistency_decimal_places"], 1)
            self.width_consist = 3 + decimals_consist
            self.bars_consist = self.set_rawtext(
                text=f"--.{'-' * decimals_consist}{self.sign_consist}",
                width=font_m.width * (self.width_consist + len(self.sign_consist)) + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_last_stint_consistency"],
                bg_color=self.wcfg["bkg_color_last_stint_consistency"],
                count=self.stint_slot + 1,
            )
            self.bars_consist[0].fg = self.wcfg["font_color_consistency"]
            self.bars_consist[0].bg = self.wcfg["bkg_color_consistency"]
            self.set_grid_layout_table_column(
                layout=layout,
                targets=self.bars_consist,
                column_index=self.wcfg["column_index_consistency"],
                bottom_to_top=layout_reversed,
            )

        # Last data
        self.last_data_version = -1
        self.empty_data = StintData()
        self.update_stint_history(())

    def timerEvent(self, event):
        """Update when vehicle on track"""
        show_energy = self.wcfg["show_virtual_energy_if_available"] and api.read.vehicle.max_virtual_energy()
        stint_data = minfo.history.stintData

        # Current stint data
        if self.wcfg["show_laps"]:
            self.update_laps(self.bars_laps[0], stint_data.totalLaps)
        if self.wcfg["show_time"]:
            self.update_time(self.bars_time[0], stint_data.totalTime)
        if self.wcfg["show_fuel"]:
            if show_energy:
                fuel = stint_data.totalEnergy
                sign_fuel = "E" if self.sign_fuel else ""
            else:
                fuel = self.unit_fuel(stint_data.totalFuel)
                sign_fuel = self.sign_fuel
            self.update_fuel(self.bars_fuel[0], fuel, sign_fuel)
        if self.wcfg["show_tyre"]:
            self.update_cmpd(self.bars_cmpd[0], stint_data.tyreCompound)
        if self.wcfg["show_wear"]:
            self.update_wear(self.bars_wear[0], stint_data.totalTyreWear)
        if self.wcfg["show_delta"]:
            self.update_delta(self.bars_delta[0], stint_data.lapTimeDelta)
        if self.wcfg["show_consistency"]:
            self.update_consist(self.bars_consist[0], stint_data.lapTimeConsistency)

        # History stint data
        if self.last_data_version != minfo.history.stintDataVersion:
            self.last_data_version = minfo.history.stintDataVersion
            self.update_stint_history(minfo.history.stintDataSet)

    # GUI update methods
    def update_laps(self, target, data):
        """Laps data"""
        if target.last != data:
            target.last = data
            if data < 0:
                data = 0
            target.text = f"{data:03.0f}"[:3]
            target.update()

    def update_time(self, target, data):
        """Time data"""
        if target.last != data:
            target.last = data
            if data < 0:
                data = 0
            target.text = calc.sec2stinttime(data)[:5]
            target.update()

    def update_fuel(self, target, data, sign):
        """Fuel data"""
        if target.last != data:
            target.last = data
            if data < 0:
                data = 0
            text_fuel = f"{data:.{self.width_fuel}f}"[:self.width_fuel].strip(".")
            target.text = f"{text_fuel}{sign}"
            target.update()

    def update_cmpd(self, target, data):
        """Compound data"""
        if target.last != data:
            target.last = data
            target.text = data
            target.update()

    def update_wear(self, target, data):
        """Wear data"""
        if target.last != data:
            target.last = data
            if data < 0:
                data = 0
            text_wear = f"{data:.{self.width_wear}f}"[:self.width_wear].strip(".")
            target.text = f"{text_wear}{self.sign_wear}"
            target.update()

    def update_delta(self, target, data):
        """Delta data"""
        if target.last != data:
            target.last = data
            target.text = f"{data:+.{self.width_delta}f}"[:self.width_delta].strip(".")
            target.update()

    def update_consist(self, target, data):
        """Consistency data"""
        if target.last != data:
            target.last = data
            text_consist = f"{data:.{self.width_consist}f}"[:self.width_consist].strip(".")
            target.text = f"{text_consist}{self.sign_consist}"
            target.update()

    def update_stint_history(self, dataset: deque[StintDataSet]):
        """Stint history data"""
        show_energy = self.wcfg["show_virtual_energy_if_available"]
        for index in range(self.stint_slot):
            if index < len(dataset):
                data = dataset[index]
                hidden = False
            else:
                data = self.empty_data
                hidden = not self.wcfg["show_empty_history"]
            index += 1

            if self.wcfg["show_laps"]:
                self.update_laps(self.bars_laps[index], data.totalLaps)
                self.bars_laps[index].setHidden(hidden)

            if self.wcfg["show_time"]:
                self.update_time(self.bars_time[index], data.totalTime)
                self.bars_time[index].setHidden(hidden)

            if self.wcfg["show_fuel"]:
                if show_energy and data.totalEnergy:
                    fuel = data.totalEnergy
                    sign_fuel = "E" if self.sign_fuel else ""
                else:
                    fuel = self.unit_fuel(data.totalFuel)
                    sign_fuel = self.sign_fuel
                self.update_fuel(self.bars_fuel[index], fuel, sign_fuel)
                self.bars_fuel[index].setHidden(hidden)

            if self.wcfg["show_tyre"]:
                self.update_cmpd(self.bars_cmpd[index], data.tyreCompound)
                self.bars_cmpd[index].setHidden(hidden)

            if self.wcfg["show_wear"]:
                self.update_wear(self.bars_wear[index], data.totalTyreWear)
                self.bars_wear[index].setHidden(hidden)

            if self.wcfg["show_delta"]:
                self.update_delta(self.bars_delta[index], data.lapTimeDelta)
                self.bars_delta[index].setHidden(hidden)

            if self.wcfg["show_consistency"]:
                self.update_consist(self.bars_consist[index], data.lapTimeConsistency)
                self.bars_consist[index].setHidden(hidden)
