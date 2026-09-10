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
Brake bias Widget
"""

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
        font = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size"],
            self.wcfg["font_weight"],
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        self.decimals_bias = max(self.wcfg["decimal_places_brake_bias"], 0)
        self.decimals_delta = max(self.wcfg["decimal_places_baseline_bias_delta"], 0)
        self.decimals_migt = max(self.wcfg["decimal_places_brake_migration"], 1)
        self.prefix_bias = self.wcfg["prefix_brake_bias"]
        self.prefix_delta = self.wcfg["prefix_baseline_bias_delta"]
        self.prefix_migt = self.wcfg["prefix_brake_migration"]
        self.suffix_migt = self.wcfg["suffix_brake_migration"]
        self.sign_text = "%" if self.wcfg["show_percentage_sign"] else ""

        # Brake bias
        if self.wcfg["show_brake_bias"]:
            text_bbias = self.format_brake_bias(0.5)
            self.bar_bbias = self.set_rawtext(
                text=text_bbias,
                width=font_m.width * len(text_bbias) + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_brake_bias"],
                bg_color=self.wcfg["background_color_brake_bias"],
            )
            self.set_primary_orient(
                target=self.bar_bbias,
                column=self.wcfg["display_order_brake_bias"],
            )

        # Baseline bias delta
        if self.wcfg["show_baseline_bias_delta"]:
            text_delta = self.format_bias_delta(0)
            self.bar_delta = self.set_rawtext(
                text=text_delta,
                width=font_m.width * len(text_delta) + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_baseline_bias_delta"],
                bg_color=self.wcfg["background_color_baseline_bias_delta"],
            )
            self.set_primary_orient(
                target=self.bar_delta,
                column=self.wcfg["display_order_baseline_bias_delta"],
            )

        # Brake migration
        if self.wcfg["show_brake_migration"]:
            text_bmigt = self.format_brake_migt(0)
            self.bar_bmigt = self.set_rawtext(
                text=text_bmigt,
                width=font_m.width * len(text_bmigt) + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_brake_migration"],
                bg_color=self.wcfg["background_color_brake_migration"],
            )
            self.set_primary_orient(
                target=self.bar_bmigt,
                column=self.wcfg["display_order_brake_migration"],
            )

        # Last data
        self.baseline_bias = 0

    def timerEvent(self, event):
        """Update when vehicle on track"""
        bbias = api.read.brake.bias_front()

        # Brake bias
        if self.wcfg["show_brake_bias"]:
            self.update_bbias(self.bar_bbias, bbias)

        # Baseline bias delta
        if self.wcfg["show_baseline_bias_delta"]:
            if (not self.baseline_bias  # in case not start from pit
                or ((api.read.vehicle.in_pits() or api.read.session.pre_race())
                     and api.read.vehicle.speed() < 0.1)):
                self.baseline_bias = bbias

            self.update_delta(self.bar_delta, bbias - self.baseline_bias)

        # Brake migration
        if self.wcfg["show_brake_migration"]:
            bmigt = api.read.brake.migration()
            self.update_bmigt(self.bar_bmigt, bmigt)

    # GUI update methods
    def update_bbias(self, target, data):
        """Brake bias"""
        if target.last != data:
            target.last = data
            target.text = self.format_brake_bias(data)
            target.update()

    def update_delta(self, target, data):
        """Baseline bias delta"""
        if target.last != data:
            target.last = data
            target.text = self.format_bias_delta(data)
            target.update()

    def update_bmigt(self, target, data):
        """Brake migration"""
        if target.last != data:
            target.last = data
            target.text = self.format_brake_migt(data)
            target.update()

    # Additional methods
    def format_brake_bias(self, value: float) -> str:
        """Format brake bias"""
        value *= 100
        front = f"{self.prefix_bias}{value:02.{self.decimals_bias}f}"
        if self.wcfg["show_front_and_rear"]:
            return f"{front}:{100 - value:02.{self.decimals_bias}f}"
        return f"{front}{self.sign_text}"

    def format_bias_delta(self, value: float) -> str:
        """Format baseline bias delta"""
        return f"{self.prefix_delta}{value * 100:+01.{self.decimals_delta}f}"

    def format_brake_migt(self, value: float) -> str:
        """Format brake migration"""
        reading = f"{value:.{self.decimals_migt}f}"
        return f"{self.prefix_migt}{reading:.{2 + self.decimals_migt}}{self.suffix_migt}"
