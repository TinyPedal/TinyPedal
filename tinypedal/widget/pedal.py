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
Pedal Widget
"""

from ..api_control import api
from ._base import Overlay
from ._painter import PedalInputBar


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
            self.wcfg["font_weight"]
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)

        pedal_size = self.set_pedal_size(font_m)

        # Throttle
        if self.wcfg["show_throttle"]:
            self.bar_throttle = PedalInputBar(
                self,
                *pedal_size,
                fg_color=self.wcfg["font_color_throttle"],
                bg_color=self.wcfg["bkg_color"],
                input_color=self.wcfg["throttle_color"],
                show_reading=self.wcfg["show_readings"],
                horizontal_style=self.wcfg["enable_horizontal_style"],
            )
            self.set_primary_orient(
                target=self.bar_throttle,
                column=self.wcfg["column_index_throttle"],
                option="enable_horizontal_style",
                default=1,
            )

        # Brake
        if self.wcfg["show_brake"]:
            self.bar_brake = PedalInputBar(
                self,
                *pedal_size,
                fg_color=self.wcfg["font_color_brake"],
                bg_color=self.wcfg["bkg_color"],
                input_color=self.wcfg["brake_color"],
                show_reading=self.wcfg["show_readings"],
                horizontal_style=self.wcfg["enable_horizontal_style"],
            )
            self.set_primary_orient(
                target=self.bar_brake,
                column=self.wcfg["column_index_brake"],
                option="enable_horizontal_style",
                default=1,
            )

        # Clutch
        if self.wcfg["show_clutch"]:
            self.bar_clutch = PedalInputBar(
                self,
                *pedal_size,
                fg_color=self.wcfg["font_color_clutch"],
                bg_color=self.wcfg["bkg_color"],
                input_color=self.wcfg["clutch_color"],
                show_reading=self.wcfg["show_readings"],
                horizontal_style=self.wcfg["enable_horizontal_style"],
            )
            self.set_primary_orient(
                target=self.bar_clutch,
                column=self.wcfg["column_index_clutch"],
                option="enable_horizontal_style",
                default=1,
            )

        # Force feedback
        if self.wcfg["show_ffb_meter"]:
            self.bar_ffb = PedalInputBar(
                self,
                *pedal_size,
                fg_color=self.wcfg["font_color_ffb"],
                bg_color=self.wcfg["bkg_color"],
                input_color=self.wcfg["ffb_color"],
                ffb_color=self.wcfg["ffb_clipping_color"],
                show_reading=self.wcfg["show_readings"],
                horizontal_style=self.wcfg["enable_horizontal_style"],
            )
            self.set_primary_orient(
                target=self.bar_ffb,
                column=self.wcfg["column_index_ffb"],
                option="enable_horizontal_style",
                default=1,
            )

        # Last data
        self.max_brake_pres = 0.01

    def post_update(self):
        self.max_brake_pres = 0.01

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Throttle
        if self.wcfg["show_throttle"]:
            raw_throttle = api.read.inputs.throttle_raw()
            if self.wcfg["show_throttle_filtered"]:
                throttle = raw_throttle + api.read.inputs.throttle()
            else:
                throttle = raw_throttle + raw_throttle
            self.update_pedal(self.bar_throttle, throttle, raw_throttle)

        # Brake
        if self.wcfg["show_brake"]:
            raw_brake = api.read.inputs.brake_raw()
            if self.wcfg["show_brake_filtered"]:
                if self.wcfg["show_brake_pressure"]:
                    f_brake = self.filtered_brake_pressure(api.read.brake.pressure())
                else:
                    f_brake = api.read.inputs.brake()
                brake = raw_brake + f_brake
            else:
                brake = raw_brake + raw_brake
            self.update_pedal(self.bar_brake, brake, raw_brake)

        # Clutch
        if self.wcfg["show_clutch"]:
            raw_clutch = api.read.inputs.clutch_raw()
            if self.wcfg["show_clutch_filtered"]:
                clutch = raw_clutch + api.read.inputs.clutch()
            else:
                clutch = raw_clutch + raw_clutch
            self.update_pedal(self.bar_clutch, clutch, raw_clutch)

        # Force feedback
        if self.wcfg["show_ffb_meter"]:
            ffb = abs(api.read.inputs.force_feedback())
            self.update_ffb(self.bar_ffb, ffb)

    # GUI update methods
    def update_pedal(self, target, data, raw):
        """Pedal update"""
        if target.last != data:
            target.last = data
            target.update_input(raw, data - raw)

    def update_ffb(self, target, data):
        """FFB update"""
        if target.last != data:
            target.last = data
            target.update_input(data, data)

    # Additional methods
    def filtered_brake_pressure(self, value):
        """Percentage filtered brake pressure"""
        brake_pres = sum(value)
        if brake_pres > self.max_brake_pres:
            self.max_brake_pres = brake_pres
        return brake_pres / self.max_brake_pres

    def set_pedal_size(self, font_m):
        """Set pedal size"""
        max_gap = max(self.wcfg["inner_gap"], 0)
        pedal_length = max(int(self.wcfg["bar_length"]), 10)
        pedal_extend = max(int(self.wcfg["max_indicator_height"]), 0) + max_gap
        pedal_uwidth = max(int(self.wcfg["bar_width_unfiltered"]), 1)
        pedal_fwidth = max(int(self.wcfg["bar_width_filtered"]), 1)
        bar_length = pedal_length + pedal_extend
        bar_width = pedal_uwidth + pedal_fwidth
        readings_offset = bar_length * (self.wcfg["readings_offset"] - 0.5)

        if self.wcfg["enable_horizontal_style"]:
            pedal_size = 0, 0, bar_length, bar_width
            raw_size = 0, 0, bar_length, pedal_uwidth
            filtered_size = 0, pedal_uwidth, bar_length, pedal_fwidth
            max_size = pedal_length + max_gap, 0, pedal_extend - max_gap, bar_width
            reading_size = readings_offset, font_m.voffset, bar_length, bar_width
        else:
            pedal_size = 0, 0, bar_width, bar_length
            raw_size = 0, 0, pedal_uwidth, bar_length
            filtered_size = pedal_uwidth, 0, pedal_fwidth, bar_length
            max_size = 0, 0, bar_width, pedal_extend - max_gap
            reading_size = 0, readings_offset + font_m.voffset, bar_width, bar_length
        return (pedal_length, pedal_extend, pedal_size, raw_size,
                filtered_size, max_size, reading_size)
