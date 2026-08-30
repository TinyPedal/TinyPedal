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
from ..const_common import TEXT_NA
from ..module_info import minfo
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

            cap_toe = self.set_rawtext(
                font=font_cap,
                text=self.wcfg["caption_text"],
                fixed_height=font_cap_m.height,
                offset_y=font_cap_m.voffset,
                fg_color=self.wcfg["font_color_caption"],
                bg_color=self.wcfg["background_color_caption"],
            )
            self.set_primary_orient(
                target=cap_toe,
                column=0,
            )

        # Toe angle
        layout_toe = self.set_grid_layout(
            gap_hori=self.wcfg["horizontal_gap"],
            gap_vert=self.wcfg["vertical_gap"],
        )
        self.decimals_toe = max(self.wcfg["decimal_places_toe_angle"], 1)
        self.bars_toe = self.set_rawtext(
            text=TEXT_NA,
            width=font_m.width * (3 + self.decimals_toe) + bar_padx,
            fixed_height=font_m.height,
            offset_y=font_m.voffset,
            fg_color=self.wcfg["font_color_toe_angle"],
            bg_color=self.wcfg["background_color_toe_angle"],
            count=4,
            last=0,
        )
        self.set_grid_layout_quad(
            layout=layout_toe,
            targets=self.bars_toe,
        )
        self.set_primary_orient(
            target=layout_toe,
            column=1,
        )
        self.calc_ema_toe = partial(
            calc.exp_mov_avg,
            calc.ema_factor(self.wcfg["toe_angle_smoothing_samples"])
        )

        # Total toe angle
        if self.wcfg["show_total_toe_angle"]:
            self.bar_style_total = (
                self.wcfg["font_color_total_toe_angle_negative"],
                self.wcfg["font_color_total_toe_angle_positive"],
            )
            self.decimals_total = max(self.wcfg["decimal_places_total_toe_angle"], 1)
            self.bars_total = self.set_rawtext(
                text=TEXT_NA,
                width=font_m.width * (2 + self.decimals_total) + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.bar_style_total[0],
                bg_color=self.wcfg["background_color_total_toe_angle"],
                count=2,
                last=0,
            )
            self.set_grid_layout_vert(
                layout=layout_toe,
                targets=self.bars_total,
            )
            self.calc_ema_total = partial(
                calc.exp_mov_avg,
                calc.ema_factor(self.wcfg["total_toe_angle_smoothing_samples"])
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        symmetric = self.wcfg["enable_symmetric_toe_angle"]

        # Toe angle
        toe_angle_set = minfo.wheels.toeAngle
        for index, bar_toe in enumerate(self.bars_toe):
            if symmetric and index % 2:
                toe_angle = -toe_angle_set[index]
            else:
                toe_angle = toe_angle_set[index]
            self.update_toe(bar_toe, self.calc_ema_toe(bar_toe.last, toe_angle))

        # Total toe angle
        if self.wcfg["show_total_toe_angle"]:
            self.update_total(self.bars_total[0], self.calc_ema_total(self.bars_total[0].last, minfo.wheels.frontToeAngleDifference))
            self.update_total(self.bars_total[1], self.calc_ema_total(self.bars_total[1].last, minfo.wheels.rearToeAngleDifference))

    # GUI update methods
    def update_toe(self, target, data):
        """Toe angle data"""
        if target.last != data:
            target.last = data
            target.text = f"{data:+.{self.decimals_toe + 1}f}"[:3 + self.decimals_toe]
            target.update()

    def update_total(self, target, data):
        """Total toe angle data"""
        if target.last != data:
            target.last = data
            target.text = f"{abs(data):.{self.decimals_total + 1}f}"[:2 + self.decimals_total]
            target.fg = self.bar_style_total[data > 0]
            target.update()
