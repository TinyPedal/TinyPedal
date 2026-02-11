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
        font = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size"],
            self.wcfg["font_weight"],
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])

        if self.wcfg["show_caption"]:
            font_cap = self.config_font(
                self.wcfg["font_name"],
                self.wcfg["font_size"] * self.wcfg["font_scale_caption"],
                self.wcfg["font_weight"],
            )
            font_cap_m = self.get_font_metrics(font_cap)

            cap_toe_in = self.set_rawtext(
                font=font_cap,
                text=self.wcfg["caption_text"],
                fixed_height=font_cap_m.height,
                offset_y=font_cap_m.voffset,
                fg_color=self.wcfg["font_color_caption"],
                bg_color=self.wcfg["bkg_color_caption"],
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
        self.decimals_toe_in = max(self.wcfg["decimal_places_toe_in"], 1)
        self.bars_toe_in = self.set_rawtext(
            text=TEXT_NA,
            width=font_m.width * (3 + self.decimals_toe_in) + bar_padx,
            fixed_height=font_m.height,
            offset_y=font_m.voffset,
            fg_color=self.wcfg["font_color_toe_in"],
            bg_color=self.wcfg["bkg_color_toe_in"],
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
            self.decimals_total = max(self.wcfg["decimal_places_total_toe_angle"], 1)
            self.bars_total = self.set_rawtext(
                text=TEXT_NA,
                width=font_m.width * (2 + self.decimals_total) + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_total_toe_angle"],
                bg_color=self.wcfg["bkg_color_total_toe_angle"],
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
            target.text = f"{calc.rad2deg(data):+.{self.decimals_toe_in + 1}f}"[:3 + self.decimals_toe_in]
            target.update()

    def update_total(self, target, data):
        """Total toe angle data"""
        if target.last != data:
            target.last = data
            target.text = f"{calc.rad2deg(abs(data)):.{self.decimals_total + 1}f}"[:2 + self.decimals_total]
            target.update()
