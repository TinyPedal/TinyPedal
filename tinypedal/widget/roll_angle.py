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
Roll angle Widget
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
        self.degree_sign_text = "°" if self.wcfg["show_degree_and_percentage_sign"] else ""
        self.percent_sign_text = "%" if self.wcfg["show_degree_and_percentage_sign"] else ""
        self.decimals = max(int(self.wcfg["decimal_places"]), 1)

        if self.wcfg["layout"] == 0:
            prefix_just = max(
                len(self.wcfg["prefix_roll_angle_front"]),
                len(self.wcfg["prefix_roll_angle_rear"]),
                len(self.wcfg["prefix_roll_angle_difference"]),
                len(self.wcfg["prefix_roll_angle_ratio"]),
            )
        else:
            prefix_just = 0

        self.prefix_rollf = self.wcfg["prefix_roll_angle_front"].ljust(prefix_just)
        self.prefix_rollr = self.wcfg["prefix_roll_angle_rear"].ljust(prefix_just)
        self.prefix_rolld = self.wcfg["prefix_roll_angle_difference"].ljust(prefix_just)
        self.prefix_ratio = self.wcfg["prefix_roll_angle_ratio"].ljust(prefix_just)

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # Roll angle front
        bar_style_rollf = self.set_qss(
            fg_color=self.wcfg["font_color_roll_angle_front"],
            bg_color=self.wcfg["bkg_color_roll_angle_front"],       
        )
        text_rollf = self.format_roll(0, self.prefix_rollf)
        self.bar_rollf = self.set_qlabel(
            text=text_rollf,
            style=bar_style_rollf,
            width=font_m.width * len(text_rollf) + bar_padx,
            last=0,
        )
        self.set_primary_orient(
            target=self.bar_rollf,
            column=self.wcfg["column_index_roll_angle_front"],
        )

        # Roll angle rear
        bar_style_rollr = self.set_qss(
            fg_color=self.wcfg["font_color_roll_angle_rear"],
            bg_color=self.wcfg["bkg_color_roll_angle_rear"],
        )
        text_rollr = self.format_roll(0, self.prefix_rollr)
        self.bar_rollr = self.set_qlabel(
            text=text_rollr,
            style=bar_style_rollr,
            width=font_m.width * len(text_rollr) + bar_padx,
            last=0,
        )
        self.set_primary_orient(
            target=self.bar_rollr,
            column=self.wcfg["column_index_roll_angle_rear"],
        )

        self.calc_ema_roll = partial(
            calc.exp_mov_avg,
            calc.ema_factor(self.wcfg["roll_angle_smoothing_samples"])
        )

        # Roll angle difference
        if self.wcfg["show_roll_angle_difference"]:
            bar_style_rolld = self.set_qss(
                fg_color=self.wcfg["font_color_roll_angle_difference"],
                bg_color=self.wcfg["bkg_color_roll_angle_difference"],
            )
            text_rolld = self.format_roll(0, self.prefix_rolld)
            self.bar_rolld = self.set_qlabel(
                text=text_rolld,
                style=bar_style_rolld,
                width=font_m.width * len(text_rolld) + bar_padx,
            )
            self.set_primary_orient(
                target=self.bar_rolld,
                column=self.wcfg["column_index_roll_angle_difference"],
            )

        # Roll angle ratio
        if self.wcfg["show_roll_angle_ratio"]:
            bar_style_ratio = self.set_qss(
                fg_color=self.wcfg["font_color_roll_angle_ratio"],
                bg_color=self.wcfg["bkg_color_roll_angle_ratio"],
            )
            text_ratio = self.format_ratio(0, self.prefix_ratio)
            self.bar_ratio = self.set_qlabel(
                text=text_ratio,
                style=bar_style_ratio,
                width=font_m.width * len(text_ratio) + bar_padx,
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_ratio,
                column=self.wcfg["column_index_roll_angle_ratio"],
            )
            self.calc_ema_ratio = partial(
                calc.exp_mov_avg,
                calc.ema_factor(self.wcfg["roll_angle_ratio_smoothing_samples"])
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        height_fl, height_fr, height_rl, height_rr = api.read.wheel.ride_height()

        # Roll angle
        rollf_deg = calc.slope_angle(height_fr - height_fl, self.wcfg["wheel_track_front"])
        rollr_deg = calc.slope_angle(height_rr - height_rl, self.wcfg["wheel_track_rear"])

        ema_rollf_deg = self.calc_ema_roll(self.bar_rollf.last, rollf_deg)
        ema_rollr_deg = self.calc_ema_roll(self.bar_rollr.last, rollr_deg)

        self.update_roll(self.bar_rollf, ema_rollf_deg, self.prefix_rollf)
        self.update_roll(self.bar_rollr, ema_rollr_deg, self.prefix_rollr)

        # Roll angle difference
        if self.wcfg["show_roll_angle_difference"]:
            self.update_roll(self.bar_rolld, ema_rollr_deg - ema_rollf_deg, self.prefix_rolld)

        # Roll angle ratio
        if self.wcfg["show_roll_angle_ratio"]:
            rollf_deg = int(rollf_deg * 100)
            rollr_deg = int(rollr_deg * 100)
            if rollf_deg < 0 > rollr_deg or rollf_deg > 0 < rollr_deg:
                ratio = calc.part_to_whole_ratio(abs(rollf_deg), abs(rollf_deg + rollr_deg), 50)
            else:
                ratio = 50
            ema_ratio = self.calc_ema_ratio(self.bar_ratio.last, ratio)
            self.update_ratio(self.bar_ratio, ema_ratio, self.prefix_ratio)

    # GUI update methods
    def update_roll(self, target, data, prefix):
        """Roll angle"""
        if target.last != data:
            target.last = data
            target.setText(self.format_roll(data, prefix))

    def update_ratio(self, target, data, prefix):
        """Roll angle ratio"""
        if target.last != data:
            target.last = data
            target.setText(self.format_ratio(data, prefix))

    def format_roll(self, angle, prefix):
        """Format roll angle"""
        roll_angle = f"{angle:+.{self.decimals}f}"[:self.decimals + 3]
        return f"{prefix}{roll_angle}{self.degree_sign_text}"

    def format_ratio(self, angle, prefix):
        """Format roll angle ratio"""
        roll_angle = f"{angle:.{self.decimals + 1}f}"[:self.decimals + 3]
        return f"{prefix}{roll_angle}{self.percent_sign_text}"
