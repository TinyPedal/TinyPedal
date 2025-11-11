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
Timing Widget
"""

from .. import calculation as calc
from ..api_control import api
from ..const_common import MAX_SECONDS, TEXT_NOLAPTIME
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

        if self.wcfg["layout"] == 0:
            prefix_just = max(
                len(self.wcfg["prefix_best"]),
                len(self.wcfg["prefix_last"]),
                len(self.wcfg["prefix_current"]),
                len(self.wcfg["prefix_estimated"]),
                len(self.wcfg["prefix_session_best"]),
                len(self.wcfg["prefix_session_personal_best"]),
                len(self.wcfg["prefix_stint_best"]),
                len(self.wcfg["prefix_average_pace"]),
            )
        else:
            prefix_just = 0

        self.prefix_best = self.wcfg["prefix_best"].ljust(prefix_just)
        self.prefix_last = self.wcfg["prefix_last"].ljust(prefix_just)
        self.prefix_curr = self.wcfg["prefix_current"].ljust(prefix_just)
        self.prefix_esti = self.wcfg["prefix_estimated"].ljust(prefix_just)
        self.prefix_sbst = self.wcfg["prefix_session_best"].ljust(prefix_just)
        self.prefix_spbt = self.wcfg["prefix_session_personal_best"].ljust(prefix_just)
        self.prefix_stbt = self.wcfg["prefix_stint_best"].ljust(prefix_just)
        self.prefix_avpc = self.wcfg["prefix_average_pace"].ljust(prefix_just)

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # Session best laptime
        if self.wcfg["show_session_best"]:
            text_sbst = f"{self.prefix_sbst}{TEXT_NOLAPTIME}"
            bar_style_sbst = self.set_qss(
                fg_color=self.wcfg["font_color_session_best"],
                bg_color=self.wcfg["bkg_color_session_best"]
            )
            self.bar_sbst = self.set_qlabel(
                text=text_sbst,
                style=bar_style_sbst,
                width=font_m.width * len(text_sbst) + bar_padx,
            )
            self.set_primary_orient(
                target=self.bar_sbst,
                column=self.wcfg["column_index_session_best"],
            )

        # Personal best laptime
        if self.wcfg["show_best"]:
            text_best = f"{self.prefix_best}{TEXT_NOLAPTIME}"
            bar_style_best = self.set_qss(
                fg_color=self.wcfg["font_color_best"],
                bg_color=self.wcfg["bkg_color_best"]
            )
            self.bar_best = self.set_qlabel(
                text=text_best,
                style=bar_style_best,
                width=font_m.width * len(text_best) + bar_padx,
            )
            self.set_primary_orient(
                target=self.bar_best,
                column=self.wcfg["column_index_best"],
            )

        # Last laptime
        if self.wcfg["show_last"]:
            text_last = f"{self.prefix_last}{TEXT_NOLAPTIME}"
            self.bar_style_last = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_invalid_laptime"],
                    bg_color=self.wcfg["bkg_color_last"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_last"],
                    bg_color=self.wcfg["bkg_color_last"])
            )
            self.bar_last = self.set_qlabel(
                text=text_last,
                style=self.bar_style_last[1],
                width=font_m.width * len(text_last) + bar_padx,
            )
            self.set_primary_orient(
                target=self.bar_last,
                column=self.wcfg["column_index_last"],
            )

        # Current laptime
        if self.wcfg["show_current"]:
            text_curr = f"{self.prefix_curr}{TEXT_NOLAPTIME}"
            bar_style_curr = self.set_qss(
                fg_color=self.wcfg["font_color_current"],
                bg_color=self.wcfg["bkg_color_current"]
            )
            self.bar_curr = self.set_qlabel(
                text=text_curr,
                style=bar_style_curr,
                width=font_m.width * len(text_curr) + bar_padx,
            )
            self.set_primary_orient(
                target=self.bar_curr,
                column=self.wcfg["column_index_current"],
            )

        # Estimated laptime
        if self.wcfg["show_estimated"]:
            text_esti = f"{self.prefix_esti}{TEXT_NOLAPTIME}"
            bar_style_esti = self.set_qss(
                fg_color=self.wcfg["font_color_estimated"],
                bg_color=self.wcfg["bkg_color_estimated"]
            )
            self.bar_esti = self.set_qlabel(
                text=text_esti,
                style=bar_style_esti,
                width=font_m.width * len(text_esti) + bar_padx,
            )
            self.set_primary_orient(
                target=self.bar_esti,
                column=self.wcfg["column_index_estimated"],
            )

        # Session personal best laptime
        if self.wcfg["show_session_personal_best"]:
            text_spbt = f"{self.prefix_spbt}{TEXT_NOLAPTIME}"
            bar_style_spbt = self.set_qss(
                fg_color=self.wcfg["font_color_session_personal_best"],
                bg_color=self.wcfg["bkg_color_session_personal_best"]
            )
            self.bar_spbt = self.set_qlabel(
                text=text_spbt,
                style=bar_style_spbt,
                width=font_m.width * len(text_spbt) + bar_padx,
            )
            self.set_primary_orient(
                target=self.bar_spbt,
                column=self.wcfg["column_index_session_personal_best"],
            )

        # Stint personal best laptime
        if self.wcfg["show_stint_best"]:
            text_stbt = f"{self.prefix_stbt}{TEXT_NOLAPTIME}"
            bar_style_stbt = self.set_qss(
                fg_color=self.wcfg["font_color_stint_best"],
                bg_color=self.wcfg["bkg_color_stint_best"]
            )
            self.bar_stbt = self.set_qlabel(
                text=text_stbt,
                style=bar_style_stbt,
                width=font_m.width * len(text_stbt) + bar_padx,
            )
            self.set_primary_orient(
                target=self.bar_stbt,
                column=self.wcfg["column_index_stint_best"],
            )

        # Average pace laptime
        if self.wcfg["show_average_pace"]:
            text_avpc = f"{self.prefix_avpc}{TEXT_NOLAPTIME}"
            bar_style_avpc = self.set_qss(
                fg_color=self.wcfg["font_color_average_pace"],
                bg_color=self.wcfg["bkg_color_average_pace"]
            )
            self.bar_avpc = self.set_qlabel(
                text=text_avpc,
                style=bar_style_avpc,
                width=font_m.width * len(text_avpc) + bar_padx,
            )
            self.set_primary_orient(
                target=self.bar_avpc,
                column=self.wcfg["column_index_average_pace"],
            )

        # Last data
        self.player_index = 0
        self.laptime_sbst = MAX_SECONDS

    def post_update(self):
        self.laptime_sbst = MAX_SECONDS  # reset laptime

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Session best laptime
        if self.wcfg["show_session_best"]:
            if (not self.wcfg["show_session_best_from_same_class_only"]
                or api.read.vehicle.same_class(self.player_index)):
                laptime_best_tmp = api.read.timing.best_laptime(self.player_index)
                if 0 < laptime_best_tmp < self.laptime_sbst:
                    self.laptime_sbst = laptime_best_tmp

            if self.player_index < api.read.vehicle.total_vehicles():
                self.player_index += 1
            else:
                self.player_index = 0

            self.update_laptime(self.bar_sbst, self.laptime_sbst, self.prefix_sbst)

        # Personal best laptime
        if self.wcfg["show_best"]:
            laptime_best = minfo.delta.lapTimeBest
            self.update_laptime(self.bar_best, laptime_best, self.prefix_best)

        # Last laptime
        if self.wcfg["show_last"]:
            laptime_last = minfo.delta.lapTimeLast
            # Convert invalid laptime to negative for state compare
            if not minfo.delta.isValidLap:
                laptime_last *= -1
            self.update_laptime(self.bar_last, laptime_last, self.prefix_last, True)

        # Current laptime
        if self.wcfg["show_current"]:
            laptime_curr = minfo.delta.lapTimeCurrent
            self.update_laptime(self.bar_curr, laptime_curr, self.prefix_curr)

        # Estimated laptime
        if self.wcfg["show_estimated"]:
            laptime_esti = minfo.delta.lapTimeEstimated
            self.update_laptime(self.bar_esti, laptime_esti, self.prefix_esti)

        # Session personal best laptime
        if self.wcfg["show_session_personal_best"]:
            laptime_spbt = api.read.timing.best_laptime()
            self.update_laptime(self.bar_spbt, laptime_spbt, self.prefix_spbt)

        # Stint personal best laptime
        if self.wcfg["show_stint_best"]:
            laptime_stbt = minfo.delta.lapTimeStint
            self.update_laptime(self.bar_stbt, laptime_stbt, self.prefix_stbt)

        # Average pace laptime
        if self.wcfg["show_average_pace"]:
            laptime_avpc = minfo.delta.lapTimePace
            self.update_laptime(self.bar_avpc, laptime_avpc, self.prefix_avpc)

    # GUI update methods
    def update_laptime(self, target, data, prefix, verify=False):
        """Update laptime"""
        if target.last != data:
            target.last = data
            if verify:
                target.updateStyle(self.bar_style_last[data > 0])
                data = abs(data)
            if 0 < data < MAX_SECONDS:
                text = f"{prefix}{calc.sec2laptime(data)[:8]: >8}"
            else:
                text = f"{prefix}{TEXT_NOLAPTIME}"
            target.setText(text)
