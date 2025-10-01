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
Weight distribution Widget
"""

from functools import partial

from .. import calculation as calc
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
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        self.percent_sign_text = "%" if self.wcfg["show_percentage_sign"] else ""
        self.decimals = max(int(self.wcfg["decimal_places"]), 1)

        if self.wcfg["layout"] == 0:
            prefix_just = max(
                len(self.wcfg["prefix_front_to_rear_distribution"]),
                len(self.wcfg["prefix_left_to_right_distribution"]),
                len(self.wcfg["prefix_cross_weight"]),
            )
        else:
            prefix_just = 0

        self.prefix_distf = self.wcfg["prefix_front_to_rear_distribution"].ljust(prefix_just)
        self.prefix_distl = self.wcfg["prefix_left_to_right_distribution"].ljust(prefix_just)
        self.prefix_cross = self.wcfg["prefix_cross_weight"].ljust(prefix_just)

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # Front to rear distribution
        if self.wcfg["show_front_to_rear_distribution"]:
            bar_style_distf = self.set_qss(
                fg_color=self.wcfg["font_color_front_to_rear_distribution"],
                bg_color=self.wcfg["bkg_color_front_to_rear_distribution"],
            )
            text_distf = self.format_dist(0, self.prefix_distf)
            self.bar_distf = self.set_qlabel(
                text=text_distf,
                style=bar_style_distf,
                width=font_m.width * len(text_distf) + bar_padx,
            )
            self.set_primary_orient(
                target=self.bar_distf,
                column=self.wcfg["column_index_front_to_rear_distribution"],
            )

        # Left to right distribution
        if self.wcfg["show_left_to_right_distribution"]:
            bar_style_distl = self.set_qss(
                fg_color=self.wcfg["font_color_left_to_right_distribution"],
                bg_color=self.wcfg["bkg_color_left_to_right_distribution"],
            )
            text_distl = self.format_dist(0, self.prefix_distl)
            self.bar_distl = self.set_qlabel(
                text=text_distl,
                style=bar_style_distl,
                width=font_m.width * len(text_distl) + bar_padx,
            )
            self.set_primary_orient(
                target=self.bar_distl,
                column=self.wcfg["column_index_left_to_right_distribution"],
            )

        # Cross weight
        if self.wcfg["show_cross_weight"]:
            bar_style_cross = self.set_qss(
                fg_color=self.wcfg["font_color_cross_weight"],
                bg_color=self.wcfg["bkg_color_cross_weight"],
            )
            text_cross = self.format_dist(0, self.prefix_cross)
            self.bar_cross = self.set_qlabel(
                text=text_cross,
                style=bar_style_cross,
                width=font_m.width * len(text_cross) + bar_padx,
            )
            self.set_primary_orient(
                target=self.bar_cross,
                column=self.wcfg["column_index_cross_weight"],
            )

        # Last data
        self.ema_distf = 0
        self.ema_distl = 0
        self.ema_cross = 0
        self.calc_ema_ratio = partial(
            calc.exp_mov_avg,
            calc.ema_factor(min(max(self.wcfg["smoothing_samples"], 1), 500))
        )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        load_fl, load_fr, load_rl, load_rr = api.read.tyre.load()
        total_load = load_fl + load_fr + load_rl + load_rr

        # Fallback to suspension load if tyre load data not avaiable
        if total_load <= 0:
            load_fl, load_fr, load_rl, load_rr = api.read.wheel.suspension_force()
            total_load = load_fl + load_fr + load_rl + load_rr

        # Front to rear distribution
        if self.wcfg["show_front_to_rear_distribution"]:
            self.ema_distf = self.calc_ema_ratio(self.ema_distf, calc.part_to_whole_ratio((load_fl + load_fr), total_load))
            self.update_dist(self.bar_distf, self.ema_distf, self.prefix_distf)

        # Left to right distribution
        if self.wcfg["show_left_to_right_distribution"]:
            self.ema_distl = self.calc_ema_ratio(self.ema_distl, calc.part_to_whole_ratio((load_fl + load_rl), total_load))
            self.update_dist(self.bar_distl, self.ema_distl, self.prefix_distl)

        # Cross weight
        if self.wcfg["show_cross_weight"]:
            self.ema_cross = self.calc_ema_ratio(self.ema_cross, calc.part_to_whole_ratio((load_fr + load_rl), total_load))
            self.update_dist(self.bar_cross, self.ema_cross, self.prefix_cross)

    # GUI update methods
    def update_dist(self, target, data, prefix):
        """Weight distribution ratio"""
        if target.last != data:
            target.last = data
            target.setText(self.format_dist(data, prefix))

    def format_dist(self, angle, prefix):
        """Format distribution ratio"""
        ratio = f"{angle:.{self.decimals + 1}f}"[:self.decimals + 3]
        return f"{prefix}{ratio}{self.percent_sign_text}"
