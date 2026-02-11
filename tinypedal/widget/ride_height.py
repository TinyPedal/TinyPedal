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
Ride height Widget
"""

from ..api_control import api
from ._base import Overlay
from ._painter import WheelGaugeBar


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        bar_gap = self.wcfg["bar_gap"]
        bar_gap_hori = self.wcfg["horizontal_gap"]
        bar_gap_vert = self.wcfg["vertical_gap"]
        layout = self.set_grid_layout(gap=bar_gap)
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
        padx = round(font_m.width * self.wcfg["bar_padding_horizontal"])
        pady = round(font_m.capital * self.wcfg["bar_padding_vertical"])
        bar_width = max(self.wcfg["bar_width"], 20)
        bar_height = int(font_m.capital + pady * 2)
        ride_height_offset = (
            self.wcfg["ride_height_offset_front_left"],
            self.wcfg["ride_height_offset_front_right"],
            self.wcfg["ride_height_offset_rear_left"],
            self.wcfg["ride_height_offset_rear_right"],
        )
        max_range = max(int(self.wcfg["ride_height_max_range"]), 10)

        # Caption
        if self.wcfg["show_caption"]:
            font_cap = self.config_font(
                self.wcfg["font_name"],
                self.wcfg["font_size"] * self.wcfg["font_scale_caption"],
                self.wcfg["font_weight"],
            )
            font_cap_m = self.get_font_metrics(font_cap)

            cap_bar = self.set_rawtext(
                font=font_cap,
                text=self.wcfg["caption_text"],
                fixed_height=font_cap_m.height,
                offset_y=font_cap_m.voffset,
                fg_color=self.wcfg["font_color_caption"],
                bg_color=self.wcfg["bkg_color_caption"],
            )
            self.set_primary_orient(
                target=cap_bar,
                column=0,
            )

        # Ride height
        layout_inner = self.set_grid_layout(gap_hori=bar_gap_hori, gap_vert=bar_gap_vert)
        self.rideh_color = (
            self.wcfg["bkg_color"],
            self.wcfg["warning_color_bottoming"],
        )
        self.bars_rideh = tuple(
            WheelGaugeBar(
                self,
                padding_x=padx,
                bar_width=bar_width,
                bar_height=bar_height,
                offset_y=font_m.voffset,
                display_range=max_range,
                input_color=self.wcfg["highlight_color"],
                fg_color=self.wcfg["font_color"],
                bg_color=self.wcfg["bkg_color"],
                right_side=idx % 2,
            ) for idx in range(4)
        )
        for bar_rideh, offset in zip(self.bars_rideh, ride_height_offset):
            bar_rideh.offset = offset
        self.set_grid_layout_quad(
            layout=layout_inner,
            targets=self.bars_rideh,
        )
        self.set_primary_orient(
            target=layout_inner,
            column=1,
        )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        rideh_set = api.read.wheel.ride_height()
        for rideh, bar_rideh in zip(rideh_set, self.bars_rideh):
            self.update_rideh(bar_rideh, round(rideh))

    # GUI update methods
    def update_rideh(self, target, data):
        """Ride height"""
        if target.last != data:
            target.last = data
            target.bg_color = self.rideh_color[data < target.offset]
            target.update_input(data)
