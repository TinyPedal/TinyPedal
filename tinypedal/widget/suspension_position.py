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
Suspension position Widget
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
            self.wcfg["font_weight"]
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)
        font_offset = self.calc_font_offset(font_m)

        # Config variable
        padx = round(font_m.width * self.wcfg["bar_padding_horizontal"])
        pady = round(font_m.capital * self.wcfg["bar_padding_vertical"])
        bar_width = max(self.wcfg["bar_width"], 20)
        bar_height = int(font_m.capital + pady * 2)
        max_range = max(int(self.wcfg["position_max_range"]), 10)
        mark_color = (
            self.wcfg["third_spring_position_mark_color"]
            if self.wcfg["show_third_spring_position_mark"]
            else ""
        )

        # Caption
        if self.wcfg["show_caption"]:
            bar_style_desc = self.set_qss(
                fg_color=self.wcfg["font_color_caption"],
                bg_color=self.wcfg["bkg_color_caption"],
                font_family=self.wcfg["font_name"],
                font_size=int(self.wcfg['font_size'] * self.wcfg['font_scale_caption']),
                font_weight=self.wcfg["font_weight"],
            )
            cap_bar = self.set_qlabel(
                text=self.wcfg["caption_text"],
                style=bar_style_desc,
                fixed_width=bar_width * 2 + bar_gap_hori,
            )
            self.set_primary_orient(
                target=cap_bar,
                column=0,
            )

        # Suspension position
        layout_inner = self.set_grid_layout(gap_hori=bar_gap_hori, gap_vert=bar_gap_vert)
        self.susp_color = (
            self.wcfg["positive_position_color"],
            self.wcfg["negative_position_color"],
        )
        self.bars_susp = tuple(
            WheelGaugeBar(
                self,
                padding_x=padx,
                bar_width=bar_width,
                bar_height=bar_height,
                font_offset=font_offset,
                max_range=max_range,
                input_color=self.wcfg["positive_position_color"],
                fg_color=self.wcfg["font_color"],
                bg_color=self.wcfg["bkg_color"],
                mark_width=max(self.wcfg["third_spring_position_mark_width"], 1),
                mark_color=mark_color,
                right_side=idx % 2,
            ) for idx in range(4)
        )
        self.set_grid_layout_quad(
            layout=layout_inner,
            targets=self.bars_susp,
        )
        self.set_primary_orient(
            target=layout_inner,
            column=1,
        )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        susp_set = api.read.wheel.suspension_deflection()

        if self.wcfg["show_third_spring_position_mark"]:
            third_set = api.read.wheel.third_spring_deflection()
            for susp, third, bar_susp in zip(susp_set, third_set, self.bars_susp):
                self.update_susp_third(bar_susp, round(susp), third)
        else:
            for susp, bar_susp in zip(susp_set, self.bars_susp):
                self.update_susp(bar_susp, round(susp))

    # GUI update methods
    def update_susp(self, target, data):
        """Suspension position"""
        if target.last != data:
            target.last = data
            target.input_color = self.susp_color[data < 0]
            target.update_input(abs(data))

    def update_susp_third(self, target, data, third):
        """Suspension position with third spring"""
        if target.last != data:
            target.last = data
            target.input_color = self.susp_color[data < 0]
            target.update_input_mark(abs(data), abs(third))
