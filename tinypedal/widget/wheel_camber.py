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
Wheel camber Widget
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
            cap_camber = self.set_qlabel(
                text=self.wcfg["caption_text"],
                style=bar_style_desc,
            )
            self.set_primary_orient(
                target=cap_camber,
                column=0,
            )

        # Camber
        layout_camber = self.set_grid_layout(
            gap_hori=self.wcfg["horizontal_gap"],
            gap_vert=self.wcfg["vertical_gap"],
        )
        bar_style_camber = self.set_qss(
            fg_color=self.wcfg["font_color_camber"],
            bg_color=self.wcfg["bkg_color_camber"]
        )
        self.decimals_camber = max(self.wcfg["decimal_places_camber"], 1)
        self.bars_camber = self.set_qlabel(
            text=TEXT_NA,
            style=bar_style_camber,
            width=font_m.width * (3 + self.decimals_camber) + bar_padx,
            count=4,
            last=0,
        )
        self.set_grid_layout_quad(
            layout=layout_camber,
            targets=self.bars_camber,
        )
        self.set_primary_orient(
            target=layout_camber,
            column=1,
        )
        self.calc_ema_camber = partial(
            calc.exp_mov_avg,
            calc.ema_factor(self.wcfg["camber_smoothing_samples"])
        )

        # Camber difference
        if self.wcfg["show_camber_difference"]:
            bar_style_cdiff = self.set_qss(
                fg_color=self.wcfg["font_color_camber_difference"],
                bg_color=self.wcfg["bkg_color_camber_difference"]
            )
            self.decimals_cdiff = max(self.wcfg["decimal_places_camber_difference"], 1)
            self.bars_cdiff = self.set_qlabel(
                text=TEXT_NA,
                style=bar_style_cdiff,
                width=font_m.width * (3 + self.decimals_cdiff) + bar_padx,
                count=2,
                last=0,
            )
            self.set_grid_layout_vert(
                layout=layout_camber,
                targets=self.bars_cdiff,
            )
            self.calc_ema_cdiff = partial(
                calc.exp_mov_avg,
                calc.ema_factor(self.wcfg["camber_difference_smoothing_samples"])
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Camber
        camber_set = api.read.wheel.camber()
        for camber, bar_camber in zip(camber_set, self.bars_camber):
            self.update_camber(bar_camber, self.calc_ema_camber(bar_camber.last, camber))

        # Camber difference
        if self.wcfg["show_camber_difference"]:
            self.update_cdiff(self.bars_cdiff[0], self.calc_ema_cdiff(self.bars_cdiff[0].last, camber_set[0] - camber_set[1]))
            self.update_cdiff(self.bars_cdiff[1], self.calc_ema_cdiff(self.bars_cdiff[1].last, camber_set[2] - camber_set[3]))

    # GUI update methods
    def update_camber(self, target, data):
        """Camber data"""
        if target.last != data:
            target.last = data
            target.setText(f"{calc.rad2deg(data):+.{self.decimals_camber}f}"[:3 + self.decimals_camber])

    def update_cdiff(self, target, data):
        """Camber difference data"""
        if target.last != data:
            target.last = data
            target.setText(f"{calc.rad2deg(data):+.{self.decimals_cdiff}f}"[:3 + self.decimals_cdiff])
