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

from collections import deque

from .. import calculation as calc
from .. import units
from ..api_control import api
from ..const_common import FLOAT_INF, MAX_SECONDS
from ..module_info import minfo
from ..userfile.heatmap import select_compound_symbol
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
        stint_slot = max(self.wcfg["stint_history_count"], 1)
        self.minimum_stint_seconds = self.wcfg["minimum_stint_threshold_minutes"] * 60
        self.minimum_pitstop_seconds = max(self.wcfg["minimum_pitstop_threshold_seconds"], 0.0)

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
                count=stint_slot + 1,
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
                count=stint_slot + 1,
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
            self.bars_fuel = self.set_rawtext(
                text="-.---",
                width=font_m.width * 5 + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_last_stint_fuel"],
                bg_color=self.wcfg["bkg_color_last_stint_fuel"],
                count=stint_slot + 1,
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
                count=stint_slot + 1,
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
            self.bars_wear = self.set_rawtext(
                text="---",
                width=font_m.width * 3 + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_last_stint_wear"],
                bg_color=self.wcfg["bkg_color_last_stint_wear"],
                count=stint_slot + 1,
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
            self.bars_delta = self.set_rawtext(
                text="--.--",
                width=font_m.width * 5 + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_last_stint_delta"],
                bg_color=self.wcfg["bkg_color_last_stint_delta"],
                count=stint_slot + 1,
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
            self.bars_consist = self.set_rawtext(
                text="--.---",
                width=font_m.width * 6 + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_last_stint_consistency"],
                bg_color=self.wcfg["bkg_color_last_stint_consistency"],
                count=stint_slot + 1,
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
        self.last_time = 0
        self.stint_running = False
        self.reset_stint = True
        self.start_laps = 0
        self.start_time = 0
        self.start_fuel = 0
        self.start_wear = 0
        self.last_wear_avg = 0
        self.last_fuel_curr = 0
        self.last_time_stop = 0
        self.stint_consistency = StintConsistency()
        # 0=total laps, 1=total time, 2=total fuel, 3=tyre compound, 4=total tyre wear, 5=delta, 6=consistency
        self.stint_data = [0,0,0,"--",0,0,0]
        self.empty_data = tuple(self.stint_data)
        self.history_data = deque([self.empty_data for _ in range(stint_slot)], stint_slot)
        self.update_stint_history()

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Read stint data
        lap_num = api.read.lap.number()
        time_curr = api.read.session.elapsed()
        in_pits = api.read.vehicle.in_pits()
        in_garage = api.read.vehicle.in_garage()
        wear_avg = 100 - sum(api.read.tyre.wear()) * 25

        # Check if virtual energy available
        if self.wcfg["show_virtual_energy_if_available"] and api.read.vehicle.max_virtual_energy():
            fuel_curr = minfo.energy.amountCurrent
        else:
            fuel_curr = self.unit_fuel(minfo.fuel.amountCurrent)

        # Ignore stint
        if (
            in_garage  # ignore while in garage
            or api.read.session.pre_race()  # ignore before race starts
            or abs(self.last_time - time_curr) > 4  # ignore game pause
        ):
            self.reset_stint = True
            if self.stint_running and self.stint_data[1] >= self.minimum_stint_seconds:
                self.update_stint_history(self.stint_data)
        elif not in_pits:
            self.last_fuel_curr = fuel_curr
            self.last_wear_avg = wear_avg
            self.stint_running = True
        elif self.stint_running:
            if api.read.vehicle.speed() > 1:
                self.last_time_stop = time_curr
            if (self.last_wear_avg > wear_avg
                or self.last_fuel_curr < fuel_curr
                or time_curr - self.last_time_stop > self.minimum_pitstop_seconds):
                self.reset_stint = True
                self.update_stint_history(self.stint_data)

        self.last_time = time_curr

        if self.reset_stint:
            self.start_laps = lap_num
            self.start_time = time_curr
            self.start_fuel = fuel_curr
            self.start_wear = wear_avg
            self.reset_stint = False
            self.stint_running = False
            self.stint_consistency.reset()
            # Update compound info once per stint
            class_name = api.read.vehicle.class_name()
            self.stint_data[3] = "".join(
                select_compound_symbol(f"{class_name} - {tcmpd_name}")
                for tcmpd_name in api.read.tyre.compound_name()
            )

        if self.start_fuel < fuel_curr:
            self.start_fuel = fuel_curr

        # Current stint data
        self.stint_consistency.update(in_pits, api.read.timing.start())
        self.stint_data[0] = max(lap_num - self.start_laps, 0)
        self.stint_data[1] = max(time_curr - self.start_time, 0)
        self.stint_data[2] = max(self.start_fuel - fuel_curr, 0)
        self.stint_data[4] = max(wear_avg - self.start_wear, 0)
        self.stint_data[5] = self.stint_consistency.delta
        self.stint_data[6] = self.stint_consistency.consistency * 100

        if self.wcfg["show_laps"]:
            self.update_laps(self.bars_laps[0], self.stint_data[0])
        if self.wcfg["show_time"]:
            self.update_time(self.bars_time[0], self.stint_data[1])
        if self.wcfg["show_fuel"]:
            self.update_fuel(self.bars_fuel[0], self.stint_data[2])
        if self.wcfg["show_tyre"]:
            self.update_cmpd(self.bars_cmpd[0], self.stint_data[3])
        if self.wcfg["show_wear"]:
            self.update_wear(self.bars_wear[0], self.stint_data[4])
        if self.wcfg["show_delta"]:
            self.update_delta(self.bars_delta[0], self.stint_data[5])
        if self.wcfg["show_consistency"]:
            self.update_consist(self.bars_consist[0], self.stint_data[6])

    # GUI update methods
    def update_cmpd(self, target, data):
        """Compound data"""
        if target.last != data:
            target.last = data
            target.text = data
            target.update()

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
            target.text = calc.sec2stinttime(data)[:5]
            target.update()

    def update_fuel(self, target, data):
        """Fuel data"""
        if target.last != data:
            target.last = data
            target.text = f"{data:.3f}"[:5]
            target.update()

    def update_wear(self, target, data):
        """Wear data"""
        if target.last != data:
            target.last = data
            target.text = f"{data:02.0f}%"[:3]
            target.update()

    def update_delta(self, target, data):
        """Delta data"""
        if target.last != data:
            target.last = data
            target.text = f"{data:+05.2f}"[:5].strip(".")
            target.update()

    def update_consist(self, target, data):
        """Consistency data"""
        if target.last != data:
            target.last = data
            target.text = f"{f'{data:.3f}':.5}%"
            target.update()

    def update_stint_history(self, new_stint_data=None):
        """Stint history data"""
        if new_stint_data:
            self.history_data.appendleft(tuple(new_stint_data))

        for index, data in enumerate(self.history_data):
            index += 1

            if data[1]:
                hidden = False
            else:
                data = self.empty_data
                hidden = not self.wcfg["show_empty_history"]

            if self.wcfg["show_laps"]:
                self.update_laps(self.bars_laps[index], data[0])
                self.bars_laps[index].setHidden(hidden)

            if self.wcfg["show_time"]:
                self.update_time(self.bars_time[index], data[1])
                self.bars_time[index].setHidden(hidden)

            if self.wcfg["show_fuel"]:
                self.update_fuel(self.bars_fuel[index], data[2])
                self.bars_fuel[index].setHidden(hidden)

            if self.wcfg["show_tyre"]:
                self.update_cmpd(self.bars_cmpd[index], data[3])
                self.bars_cmpd[index].setHidden(hidden)

            if self.wcfg["show_wear"]:
                self.update_wear(self.bars_wear[index], data[4])
                self.bars_wear[index].setHidden(hidden)

            if self.wcfg["show_delta"]:
                self.update_delta(self.bars_delta[index], data[5])
                self.bars_delta[index].setHidden(hidden)

            if self.wcfg["show_consistency"]:
                self.update_consist(self.bars_consist[index], data[6])
                self.bars_consist[index].setHidden(hidden)


class StintConsistency:
    """Stint consistency data"""

    def __init__(self):
        self.reset()

    def update(self, in_pits: bool, lap_stime: float):
        """Calculate stint delta & consistency"""
        self._pitting |= in_pits

        if self._last_lap_stime != lap_stime:
            last_laptime = lap_stime - self._last_lap_stime

            if last_laptime <= 0:
                self._last_lap_stime = lap_stime
                self._pitting = 1
                return

            if not self._pitting:
                self._stint_laps += 1
                self._stint_time += last_laptime
                if self._stint_fastest > last_laptime:
                    self._stint_fastest = last_laptime
                if self._stint_laps > 1:
                    stint_average = (self._stint_time - self._stint_fastest) / (self._stint_laps - 1)
                    if stint_average > 0:
                        self.consistency = self._stint_fastest / stint_average
                        self.delta = stint_average - self._stint_fastest
            # Reset
            self._pitting = 0
            self._last_lap_stime = lap_stime

    def reset(self):
        """Reset"""
        self._pitting = 1
        self._last_lap_stime = FLOAT_INF
        self._stint_laps = 0
        self._stint_time = 0.0
        self._stint_fastest = MAX_SECONDS
        self.consistency = 1.0
        self.delta = 0.0
