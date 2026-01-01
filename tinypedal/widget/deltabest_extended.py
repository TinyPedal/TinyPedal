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
Deltabest extended Widget
"""

from .. import calculation as calc
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
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        self.freeze_duration = min(max(self.wcfg["freeze_duration"], 0), 30)
        self.decimals = max(self.wcfg["decimal_places"], 1)
        self.delta_display_range = calc.decimal_strip(self.wcfg["delta_display_range"], self.decimals)
        self.max_padding = 3 + self.decimals
        text_def = f"--.{'-' * self.decimals}"

        if self.wcfg["layout"] == 0:
            prefix_just = max(
                len(self.wcfg["prefix_all_time_deltabest"]),
                len(self.wcfg["prefix_session_deltabest"]),
                len(self.wcfg["prefix_stint_deltabest"]),
                len(self.wcfg["prefix_deltalast"]),
            )
        else:
            prefix_just = 0

        self.prefix_atbest = self.wcfg["prefix_all_time_deltabest"].ljust(prefix_just)
        self.prefix_ssbest = self.wcfg["prefix_session_deltabest"].ljust(prefix_just)
        self.prefix_stbest = self.wcfg["prefix_stint_deltabest"].ljust(prefix_just)
        self.prefix_labest = self.wcfg["prefix_deltalast"].ljust(prefix_just)

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # All time deltabest
        if self.wcfg["show_all_time_deltabest"]:
            text_atbest = f"{self.prefix_atbest}{text_def}"
            bar_style_atbest = self.set_qss(
                fg_color=self.wcfg["font_color_all_time_deltabest"],
                bg_color=self.wcfg["bkg_color_all_time_deltabest"]
            )
            self.bar_atbest = self.set_qlabel(
                text=text_atbest,
                style=bar_style_atbest,
                width=font_m.width * len(text_atbest) + bar_padx,
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_atbest,
                column=self.wcfg["column_index_all_time_deltabest"],
            )

        # Session deltabest
        if self.wcfg["show_session_deltabest"]:
            text_ssbest = f"{self.prefix_ssbest}{text_def}"
            bar_style_ssbest = self.set_qss(
                fg_color=self.wcfg["font_color_session_deltabest"],
                bg_color=self.wcfg["bkg_color_session_deltabest"]
            )
            self.bar_ssbest = self.set_qlabel(
                text=text_ssbest,
                style=bar_style_ssbest,
                width=font_m.width * len(text_ssbest) + bar_padx,
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_ssbest,
                column=self.wcfg["column_index_session_deltabest"],
            )

        # Stint deltabest
        if self.wcfg["show_stint_deltabest"]:
            text_stbest = f"{self.prefix_stbest}{text_def}"
            bar_style_stbest = self.set_qss(
                fg_color=self.wcfg["font_color_stint_deltabest"],
                bg_color=self.wcfg["bkg_color_stint_deltabest"]
            )
            self.bar_stbest = self.set_qlabel(
                text=text_stbest,
                style=bar_style_stbest,
                width=font_m.width * len(text_stbest) + bar_padx,
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_stbest,
                column=self.wcfg["column_index_stint_deltabest"],
            )

        # Deltalast
        if self.wcfg["show_deltalast"]:
            text_labest = f"{self.prefix_labest}{text_def}"
            bar_style_labest = self.set_qss(
                fg_color=self.wcfg["font_color_deltalast"],
                bg_color=self.wcfg["bkg_color_deltalast"]
            )
            self.bar_labest = self.set_qlabel(
                text=text_labest,
                style=bar_style_labest,
                width=font_m.width * len(text_labest) + bar_padx,
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_labest,
                column=self.wcfg["column_index_deltalast"],
            )

        # Last data
        self.last_laptimes = [0.0] * 4
        self.new_lap = True

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if minfo.delta.lapTimeCurrent < self.freeze_duration:
            alltime_best = minfo.delta.lapTimeLast - self.last_laptimes[0]
            session_best = minfo.delta.lapTimeLast - self.last_laptimes[1]
            stint_best = minfo.delta.lapTimeLast - self.last_laptimes[2]
            delta_last = minfo.delta.lapTimeLast - self.last_laptimes[3]
            self.new_lap = True
        else:
            if self.new_lap:
                self.last_laptimes[0] = minfo.delta.lapTimeBest
                self.last_laptimes[1] = minfo.delta.lapTimeSession
                self.last_laptimes[2] = minfo.delta.lapTimeStint
                self.last_laptimes[3] = minfo.delta.lapTimeLast
                self.new_lap = False

            alltime_best = minfo.delta.deltaBest
            session_best = minfo.delta.deltaSession
            stint_best = minfo.delta.deltaStint
            delta_last = minfo.delta.deltaLast

        # All time deltabest
        if self.wcfg["show_all_time_deltabest"]:
            self.update_deltabest(self.bar_atbest, alltime_best, self.prefix_atbest)

        # Session deltabest
        if self.wcfg["show_session_deltabest"]:
            self.update_deltabest(self.bar_ssbest, session_best, self.prefix_ssbest)

        # Stint deltabest
        if self.wcfg["show_stint_deltabest"]:
            self.update_deltabest(self.bar_stbest, stint_best, self.prefix_stbest)

        # Deltalast
        if self.wcfg["show_stint_deltabest"]:
            self.update_deltabest(self.bar_labest, delta_last, self.prefix_labest)

    # GUI update methods
    def update_deltabest(self, target, data, prefix):
        """Update deltabest"""
        if target.last != data:
            target.last = data
            text = f"{calc.sym_max(data, self.delta_display_range): >+{self.max_padding}.{self.decimals}f}"[:self.max_padding]
            target.setText(f"{prefix}{text}")
