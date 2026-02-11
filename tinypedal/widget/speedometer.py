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
Speedometer Widget
"""

from .. import units
from ..api_control import api
from ._base import Overlay


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout(gap=self.wcfg["bar_gap"])
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
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        decimals = max(int(self.wcfg["decimal_places"]), 0)
        zero_offset = (decimals > 0)
        bar_width = font_m.width * (3 + decimals + zero_offset) + bar_padx
        self.leading_zero = min(max(self.wcfg["leading_zero"], 1), 3) + zero_offset + decimals + decimals / 10

        # Config units
        self.unit_speed = units.set_unit_speed(self.cfg.units["speed_unit"])

        # Speed
        if self.wcfg["show_speed"]:
            self.bar_speed_curr = self.set_rawtext(
                text="SPD",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_speed"],
                bg_color=self.wcfg["bkg_color_speed"],
            )
            self.set_primary_orient(
                target=self.bar_speed_curr,
                column=self.wcfg["column_index_speed"],
            )

        if self.wcfg["show_speed_minimum"]:
            self.bar_speed_min = self.set_rawtext(
                text="MIN",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_speed_minimum"],
                bg_color=self.wcfg["bkg_color_speed_minimum"],
            )
            self.set_primary_orient(
                target=self.bar_speed_min,
                column=self.wcfg["column_index_speed_minimum"],
            )

        if self.wcfg["show_speed_maximum"]:
            self.bar_speed_max = self.set_rawtext(
                text="MAX",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_speed_maximum"],
                bg_color=self.wcfg["bkg_color_speed_maximum"],
            )
            self.set_primary_orient(
                target=self.bar_speed_max,
                column=self.wcfg["column_index_speed_maximum"],
            )

        if self.wcfg["show_speed_fastest"]:
            self.bar_speed_fast = self.set_rawtext(
                text="TOP",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_speed_fastest"],
                bg_color=self.wcfg["bkg_color_speed_fastest"],
            )
            self.set_primary_orient(
                target=self.bar_speed_fast,
                column=self.wcfg["column_index_speed_fastest"],
            )

        # Last data
        self.speed_min = -1
        self.speed_max = -1
        self.speed_fast = -1
        self.off_throttle_timer_start = 0
        self.on_throttle_timer_start = 0

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Read speed data
        speed = api.read.vehicle.speed()
        lap_etime = api.read.timing.elapsed()
        raw_throttle = api.read.inputs.throttle_raw()

        # Update current speed
        if self.wcfg["show_speed"]:
            self.update_speed(self.bar_speed_curr, speed)

        # Update minimum speed off throttle
        if self.wcfg["show_speed_minimum"] and raw_throttle < self.wcfg["off_throttle_threshold"]:
            if speed < self.speed_min:
                self.speed_min = speed
                self.off_throttle_timer_start = lap_etime
                self.update_speed(self.bar_speed_min, speed)
            if self.off_throttle_timer_start > lap_etime:
                self.off_throttle_timer_start = lap_etime
            if lap_etime - self.off_throttle_timer_start > self.wcfg["speed_minimum_reset_cooldown"]:
                self.speed_min = speed

        # Update maximum speed on throttle
        if self.wcfg["show_speed_maximum"] and raw_throttle > self.wcfg["on_throttle_threshold"]:
            if speed > self.speed_max:
                self.speed_max = speed
                self.on_throttle_timer_start = lap_etime
                self.update_speed(self.bar_speed_max, speed)
            if self.on_throttle_timer_start > lap_etime:
                self.on_throttle_timer_start = lap_etime
            if lap_etime - self.on_throttle_timer_start > self.wcfg["speed_maximum_reset_cooldown"]:
                self.speed_max = speed

        # Update fastest speed
        if self.wcfg["show_speed_fastest"]:
            if api.read.engine.gear() < 0:  # reset on reverse gear
                self.speed_fast = -1
            if speed > self.speed_fast:
                self.speed_fast = speed
                self.update_speed(self.bar_speed_fast, speed)

    # GUI update methods
    def update_speed(self, target, data):
        """Vehicle speed"""
        if target.last != data:
            target.last = data
            target.text = f"{self.unit_speed(data):0{self.leading_zero}f}"
            target.update()
