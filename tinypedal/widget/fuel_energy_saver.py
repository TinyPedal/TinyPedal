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
Fuel energy saver Widget
"""

from math import floor

from .. import calculation as calc
from ..api_control import api
from ..const_common import ENERGY_TYPE_ID, MAX_SECONDS, TEXT_PLACEHOLDER
from ..module_info import minfo
from ..units import set_unit_fuel
from ._base import Overlay


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout(gap_hori=self.wcfg["bar_gap"])
        self.set_primary_layout(layout=layout)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        self.pit_bias = self.wcfg["enable_pit_entry_bias"]
        self.pitstop_threshold = self.wcfg["remaining_pitstop_threshold"]
        layout_reversed = self.wcfg["layout"] != 0
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        self.char_width = max(self.wcfg["bar_width"], 4)
        bar_width = font_m.width * self.char_width + bar_padx
        self.center_slot = min(max(self.wcfg["number_of_less_laps"], 0), 5) + 1 + self.pit_bias  # column offset
        self.total_slot = min(max(self.wcfg["number_of_more_laps"], 1), 10) + 1 + self.center_slot
        self.decimals_consumption = max(self.wcfg["decimal_places_consumption"], 0)
        self.decimals_delta = max(self.wcfg["decimal_places_delta"], 0)
        self.min_reserve = max(self.wcfg["minimum_reserve"], 0)

        # Config units
        self.unit_fuel = set_unit_fuel(self.cfg.units["fuel_unit"])

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # Target lap row
        bar_style_lap = (
            self.set_qss(
                fg_color=self.wcfg["font_color_target_laps"],
                bg_color=self.wcfg["bkg_color_target_laps"],
                font_size=int(self.wcfg['font_size'] * 0.8)),
            self.set_qss(
                fg_color=self.wcfg["font_color_current_laps"],
                bg_color=self.wcfg["bkg_color_current_laps"],
                font_size=int(self.wcfg['font_size'] * 0.8))
        )
        self.bars_target_lap = self.set_qlabel(
            text=TEXT_PLACEHOLDER,
            style=bar_style_lap[0],
            width=bar_width,
            count=self.total_slot,
            last=-MAX_SECONDS,
        )
        if self.pit_bias:
            self.bars_target_lap[0].setText("BIAS")
            self.bars_target_lap[1].setText("LAST")
        else:
            self.bars_target_lap[0].setText("LAST")
        self.bars_target_lap[self.center_slot].updateStyle(bar_style_lap[1])
        self.set_grid_layout_table_row(
            layout=layout,
            targets=self.bars_target_lap,
            row_index=0,
            right_to_left=layout_reversed,
        )

        # Target consumption row
        bar_style_target_use = self.set_qss(
            fg_color=self.wcfg["font_color_target_consumption"],
            bg_color=self.wcfg["bkg_color_target_consumption"]
        )
        self.bars_target_use = self.set_qlabel(
            text=TEXT_PLACEHOLDER,
            style=bar_style_target_use,
            width=bar_width,
            last=-MAX_SECONDS,
            count=self.total_slot,
        )
        self.set_grid_layout_table_row(
            layout=layout,
            targets=self.bars_target_use,
            row_index=1,
            right_to_left=layout_reversed,
        )

        # Delat consumption row
        self.delta_color = (
            self.set_qss(
                fg_color=self.wcfg["font_color_lap_gain"],
                bg_color=self.wcfg["bkg_color_delta_consumption"]),
            self.set_qss(
                fg_color=self.wcfg["font_color_lap_loss"],
                bg_color=self.wcfg["bkg_color_delta_consumption"]),
            self.set_qss(
                fg_color=self.wcfg["font_color_delta_consumption"],
                bg_color=self.wcfg["bkg_color_delta_consumption"])
        )
        self.bars_delta = self.set_qlabel(
            text=TEXT_PLACEHOLDER,
            style=self.delta_color[2],
            width=bar_width,
            count=self.total_slot,
            last=-MAX_SECONDS,
        )
        self.set_grid_layout_table_row(
            layout=layout,
            targets=self.bars_delta,
            row_index=2,
            right_to_left=layout_reversed,
        )

        # Last data
        self.reset_stint = True  # reset stint stats
        self.start_laps = 0  # laps number at start of current stint
        self.last_tyre_life = 0
        self.last_fuel_curr = 0

    def post_update(self):
        self.reset_stint = True

    def timerEvent(self, event):
        """Update when vehicle on track"""
        in_pits = api.read.vehicle.in_pits()
        tyre_life = sum(api.read.tyre.wear())
        lap_num = api.read.lap.number()
        energy_type = api.read.vehicle.max_virtual_energy()
        pit_bias = 0.0

        if energy_type:
            fuel_curr = minfo.energy.amountCurrent
            fuel_est = minfo.energy.estimatedConsumption
            fuel_used_curr = minfo.energy.amountUsedCurrent
            fuel_used_last_raw = minfo.energy.lastLapConsumption
            est_pits = minfo.energy.estimatedNumPitStopsEnd
        else:
            fuel_curr = minfo.fuel.amountCurrent
            fuel_est = minfo.fuel.estimatedConsumption
            fuel_used_curr = minfo.fuel.amountUsedCurrent
            fuel_used_last_raw = minfo.fuel.lastLapConsumption
            est_pits = minfo.fuel.estimatedNumPitStopsEnd

        if self.pit_bias:
            pit_pos = minfo.mapping.pitEntryPosition
            track_length = api.read.lap.track_length()
            if 0 < pit_pos < track_length and est_pits > self.pitstop_threshold:
                pit_bias = 1 - pit_pos / track_length

        # Check stint status
        if not in_pits:
            self.last_fuel_curr = fuel_curr
            self.last_tyre_life = tyre_life
        # Reset stint if changed tyre or refueled or back in garage
        elif (self.last_tyre_life < tyre_life or
            self.last_fuel_curr < fuel_curr or api.read.vehicle.in_garage()):
            self.reset_stint = True

        if self.reset_stint:
            self.reset_stint = False
            self.start_laps = lap_num

        laps_done = max(lap_num - self.start_laps, 0)
        # Total fuel remaining count from start of current lap
        total_fuel_remaining = max(fuel_curr + fuel_used_curr - self.min_reserve + pit_bias * fuel_est, 0)
        # Estimate laps current fuel can last, minus center slot offset
        # Round to 1 decimal to reduce sensitivity
        est_runlaps = floor(round(calc.end_stint_laps(
            total_fuel_remaining, fuel_est), 1)) - self.center_slot

        # Pit entry bias
        if self.pit_bias:
            # Bias percent
            self.update_pit_bias(self.bars_delta[0], pit_bias)
            # Bias amount
            self.update_target_use(self.bars_target_use[0], pit_bias * fuel_est, energy_type)

        # Fuel or energy
        self.update_energy_type(self.bars_delta[self.pit_bias], energy_type)
        # Last lap consumption
        self.update_target_use(self.bars_target_use[self.pit_bias], fuel_used_last_raw, energy_type)

        # Update slots
        for index in range(1 + self.pit_bias, self.total_slot):
            # Progressive fuel saving
            total_laps_target = est_runlaps + index

            # Total laps + extra laps
            if index == self.center_slot:
                target_laps = f"{laps_done}/{laps_done + total_laps_target:d}"
            else:
                target_laps = f"{laps_done + total_laps_target:d}"
            self.update_total_laps(self.bars_target_lap[index], target_laps)

            # Target consumption
            if total_laps_target > 0 and fuel_est > 0:
                target_use = total_fuel_remaining / total_laps_target
            else:
                target_use = -MAX_SECONDS
            self.update_target_use(
                self.bars_target_use[index], target_use, energy_type)

            # Delta consumption
            if total_laps_target > 0 and fuel_est > 0:
                delta = fuel_est - target_use
            else:
                delta = -MAX_SECONDS
            self.update_delta(self.bars_delta[index], delta, energy_type)

    # GUI update methods
    def update_target_use(self, target, data, energy_type):
        """Target consumption"""
        if target.last != data:
            target.last = data
            if data > -MAX_SECONDS:
                if not energy_type:
                    data = self.unit_fuel(data)
                use_text = f"{data:.{self.decimals_consumption}f}"[:self.char_width]
            else:
                use_text = TEXT_PLACEHOLDER
            target.setText(use_text)

    def update_delta(self, target, data, energy_type):
        """Delta consumption between target & current"""
        if target.last != data:
            target.last = data
            if data > -MAX_SECONDS:
                if not energy_type:
                    data = self.unit_fuel(data)
                delta_text = f"{data:+.{self.decimals_delta}f}"[:self.char_width]
                style = self.delta_color[data >= 0]
            else:
                delta_text = TEXT_PLACEHOLDER
                style = self.delta_color[2]
            target.setText(delta_text)
            target.updateStyle(style)

    def update_total_laps(self, target, data):
        """Total laps"""
        if target.last != data:
            target.last = data
            target.setText(data)

    def update_energy_type(self, target, data):
        """Energy type"""
        if target.last != data:
            target.last = data
            target.setText(ENERGY_TYPE_ID[data > 0])

    def update_pit_bias(self, target, data):
        """Pit entry bias"""
        if target.last != data:
            target.last = data
            target.setText(f"{data:.1%}"[:self.char_width])
