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
Wheel alignment Widget
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
        bar_width = font_m.width * 5 + bar_padx

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )
        bar_style_desc = self.set_qss(
            fg_color=self.wcfg["font_color_caption"],
            bg_color=self.wcfg["bkg_color_caption"],
            font_size=int(self.wcfg['font_size'] * 0.8)
        )

        # Camber
        if self.wcfg["show_camber"]:
            layout_camber = self.set_grid_layout()
            bar_style_camber = self.set_qss(
                fg_color=self.wcfg["font_color_camber"],
                bg_color=self.wcfg["bkg_color_camber"]
            )
            self.bars_camber = self.set_qlabel(
                text=TEXT_NA,
                style=bar_style_camber,
                width=bar_width,
                count=4,
                last=0,
            )
            self.set_grid_layout_quad(
                layout=layout_camber,
                targets=self.bars_camber,
            )
            self.set_primary_orient(
                target=layout_camber,
                column=self.wcfg["column_index_camber"],
            )
            self.calc_ema_camber = partial(
                calc.exp_mov_avg,
                calc.ema_factor(self.wcfg["camber_smoothing_samples"])
            )

            if self.wcfg["show_caption"]:
                cap_camber = self.set_qlabel(
                    text="camber",
                    style=bar_style_desc,
                )
                layout_camber.addWidget(cap_camber, 0, 0, 1, 0)

        # Toe in
        if self.wcfg["show_toe_in"]:
            layout_toein = self.set_grid_layout()
            bar_style_toein = self.set_qss(
                fg_color=self.wcfg["font_color_toe_in"],
                bg_color=self.wcfg["bkg_color_toe_in"]
            )
            self.bars_toein = self.set_qlabel(
                text=TEXT_NA,
                style=bar_style_toein,
                width=bar_width,
                count=4,
                last=0,
            )
            self.set_grid_layout_quad(
                layout=layout_toein,
                targets=self.bars_toein,
            )
            self.set_primary_orient(
                target=layout_toein,
                column=self.wcfg["column_index_toe_in"],
            )
            self.calc_ema_toein = partial(
                calc.exp_mov_avg,
                calc.ema_factor(self.wcfg["toe_in_smoothing_samples"])
            )

            if self.wcfg["show_caption"]:
                cap_toein = self.set_qlabel(
                    text="toe in",
                    style=bar_style_desc,
                )
                layout_toein.addWidget(cap_toein, 0, 0, 1, 0)

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Camber
        if self.wcfg["show_camber"]:
            camber_set = api.read.wheel.camber()
            for camber, bar_camber in zip(camber_set, self.bars_camber):
                self.update_wheel(bar_camber, self.calc_ema_camber(bar_camber.last, camber))

        # Toe in
        if self.wcfg["show_toe_in"]:
            toein_set = api.read.wheel.toe_symmetric()
            for toein, bar_toein in zip(toein_set, self.bars_toein):
                self.update_wheel(bar_toein, self.calc_ema_toein(bar_toein.last, toein))

    # GUI update methods
    def update_wheel(self, target, data):
        """Wheel data"""
        if target.last != data:
            target.last = data
            target.setText(f"{calc.rad2deg(data):+.2f}"[:5])
