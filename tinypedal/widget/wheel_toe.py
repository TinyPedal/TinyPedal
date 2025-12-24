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
Wheel toe Widget
"""

from functools import partial

from .. import calculation as calc
from ..api_control import api
from ..const_common import TEXT_NA
from ._base import Overlay


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout(gap=self.wcfg["bar_gap"])
        self.set_primary_layout(layout=layout)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        if self.wcfg["show_caption"]:
            bar_style_desc = self.set_qss(
                fg_color=self.wcfg["font_color_caption"],
                bg_color=self.wcfg["bkg_color_caption"],
                font_size=int(self.wcfg['font_size'] * 0.8)
            )
            cap_toe_in = self.set_qlabel(
                text=self.wcfg["caption_text"],
                style=bar_style_desc,
            )
            self.set_primary_orient(
                target=cap_toe_in,
                column=0,
            )

        # Toe in
        layout_toe_in = self.set_grid_layout(
            gap_hori=self.wcfg["horizontal_gap"],
            gap_vert=self.wcfg["vertical_gap"],
        )
        bar_style_toe_in = self.set_qss(
            fg_color=self.wcfg["font_color_toe_in"],
            bg_color=self.wcfg["bkg_color_toe_in"]
        )
        self.decimals_toe_in = max(self.wcfg["decimal_places_toe_in"], 1)
        self.bars_toe_in = self.set_qlabel(
            text=TEXT_NA,
            style=bar_style_toe_in,
            width=font_m.width * (3 + self.decimals_toe_in) + bar_padx,
            count=4,
            last=0,
        )
        self.set_grid_layout_quad(
            layout=layout_toe_in,
            targets=self.bars_toe_in,
        )
        self.set_primary_orient(
            target=layout_toe_in,
            column=1,
        )
        self.calc_ema_toe_in = partial(
            calc.exp_mov_avg,
            calc.ema_factor(self.wcfg["toe_in_smoothing_samples"])
        )

        # Total toe angle
        if self.wcfg["show_total_toe_angle"]:
            bar_style_total = self.set_qss(
                fg_color=self.wcfg["font_color_total_toe_angle"],
                bg_color=self.wcfg["bkg_color_total_toe_angle"]
            )
            self.decimals_total = max(self.wcfg["decimal_places_total_toe_angle"], 1)
            self.bars_total = self.set_qlabel(
                text=TEXT_NA,
                style=bar_style_total,
                width=font_m.width * (2 + self.decimals_total) + bar_padx,
                count=2,
                last=0,
            )
            self.set_grid_layout_vert(
                layout=layout_toe_in,
                targets=self.bars_total,
            )
            self.calc_ema_total = partial(
                calc.exp_mov_avg,
                calc.ema_factor(self.wcfg["total_toe_angle_smoothing_samples"])
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Toe in
        toe_in_set = api.read.wheel.toe_symmetric()
        for toe_in, bar_toe_in in zip(toe_in_set, self.bars_toe_in):
            self.update_toe_in(bar_toe_in, self.calc_ema_toe_in(bar_toe_in.last, toe_in))

        # Total toe angle
        if self.wcfg["show_total_toe_angle"]:
            self.update_total(self.bars_total[0], self.calc_ema_total(self.bars_total[0].last, toe_in_set[0] + toe_in_set[1]))
            self.update_total(self.bars_total[1], self.calc_ema_total(self.bars_total[1].last, toe_in_set[2] + toe_in_set[3]))

    # GUI update methods
    def update_toe_in(self, target, data):
        """Toe in data"""
        if target.last != data:
            target.last = data
            target.setText(f"{calc.rad2deg(data):+.{self.decimals_toe_in + 1}f}"[:3 + self.decimals_toe_in])

    def update_total(self, target, data):
        """Total toe angle data"""
        if target.last != data:
            target.last = data
            target.setText(f"{calc.rad2deg(abs(data)):.{self.decimals_total + 1}f}"[:2 + self.decimals_total])
