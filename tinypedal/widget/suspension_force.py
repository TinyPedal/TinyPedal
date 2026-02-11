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
Suspension force Widget
"""

from .. import calculation as calc
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

        # Suspension force
        layout_inner = self.set_grid_layout(gap_hori=bar_gap_hori, gap_vert=bar_gap_vert)
        self.bars_force = tuple(
            WheelGaugeBar(
                self,
                padding_x=padx,
                bar_width=bar_width,
                bar_height=bar_height,
                offset_y=font_m.voffset,
                input_color=self.wcfg["highlight_color"],
                fg_color=self.wcfg["font_color"],
                bg_color=self.wcfg["bkg_color"],
                right_side=idx % 2,
            ) for idx in range(4)
        )
        self.set_grid_layout_quad(
            layout=layout_inner,
            targets=self.bars_force,
        )
        self.set_primary_orient(
            target=layout_inner,
            column=1,
        )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        force_set = api.read.wheel.suspension_force()
        sum_force = sum(force_set)
        for force, bar_force in zip(force_set, self.bars_force):
            ratio = calc.part_to_whole_ratio(force, sum_force)
            if self.wcfg["show_force_ratio"]:
                force = ratio
            self.update_force(bar_force, round(force), ratio)

    # GUI update methods
    def update_force(self, target, data, ratio):
        """Suspension force & ratio"""
        if target.last != data:
            target.last = data
            target.update_input(ratio)
