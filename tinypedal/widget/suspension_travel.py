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
Suspension travel Widget
"""

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
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        bar_width = font_m.width * 4 + bar_padx

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

        # Utilized travel
        if self.wcfg["show_utilized_travel"]:
            layout_travel = self.set_grid_layout()
            bar_style_travel = self.set_qss(
                fg_color=self.wcfg["font_color_utilized_travel"],
                bg_color=self.wcfg["bkg_color_utilized_travel"]
            )
            self.bars_travel = self.set_qlabel(
                text=TEXT_NA,
                style=bar_style_travel,
                width=bar_width,
                count=4,
            )
            self.set_grid_layout_quad(
                layout=layout_travel,
                targets=self.bars_travel,
            )
            self.set_primary_orient(
                target=layout_travel,
                column=self.wcfg["column_index_utilized_travel"],
            )

            if self.wcfg["show_caption"]:
                cap_travel = self.set_qlabel(
                    text="susp util",
                    style=bar_style_desc,
                )
                layout_travel.addWidget(cap_travel, 0, 0, 1, 0)

        # Minimum position
        if self.wcfg["show_minimum_position"]:
            layout_minpos = self.set_grid_layout()
            bar_style_minpos = self.set_qss(
                fg_color=self.wcfg["font_color_minimum_position"],
                bg_color=self.wcfg["bkg_color_minimum_position"]
            )
            self.bars_minpos = self.set_qlabel(
                text=TEXT_NA,
                style=bar_style_minpos,
                width=bar_width,
                count=4,
            )
            self.set_grid_layout_quad(
                layout=layout_minpos,
                targets=self.bars_minpos,
            )
            self.set_primary_orient(
                target=layout_minpos,
                column=self.wcfg["column_index_minimum_position"],
            )

            if self.wcfg["show_caption"]:
                cap_minpos = self.set_qlabel(
                    text="min pos",
                    style=bar_style_desc,
                )
                layout_minpos.addWidget(cap_minpos, 0, 0, 1, 0)

        # Maximum position
        if self.wcfg["show_maximum_position"]:
            layout_maxpos = self.set_grid_layout()
            bar_style_maxpos = self.set_qss(
                fg_color=self.wcfg["font_color_maximum_position"],
                bg_color=self.wcfg["bkg_color_maximum_position"]
            )
            self.bars_maxpos = self.set_qlabel(
                text=TEXT_NA,
                style=bar_style_maxpos,
                width=bar_width,
                count=4,
            )
            self.set_grid_layout_quad(
                layout=layout_maxpos,
                targets=self.bars_maxpos,
            )
            self.set_primary_orient(
                target=layout_maxpos,
                column=self.wcfg["column_index_maximum_position"],
            )

            if self.wcfg["show_caption"]:
                cap_maxpos = self.set_qlabel(
                    text="max pos",
                    style=bar_style_desc,
                )
                layout_maxpos.addWidget(cap_maxpos, 0, 0, 1, 0)

        # Live position
        if self.wcfg["show_live_position"]:
            layout_live = self.set_grid_layout()
            bar_style_live = self.set_qss(
                fg_color=self.wcfg["font_color_live_position"],
                bg_color=self.wcfg["bkg_color_live_position"]
            )
            self.bars_live = self.set_qlabel(
                text=TEXT_NA,
                style=bar_style_live,
                width=bar_width,
                count=4,
            )
            self.set_grid_layout_quad(
                layout=layout_live,
                targets=self.bars_live,
            )
            self.set_primary_orient(
                target=layout_live,
                column=self.wcfg["column_index_live_position"],
            )

            if self.wcfg["show_caption"]:
                cap_live = self.set_qlabel(
                    text="live pos",
                    style=bar_style_desc,
                )
                layout_live.addWidget(cap_live, 0, 0, 1, 0)

    def timerEvent(self, event):
        """Update when vehicle on track"""
        for idx in range(4):
            # Utilized travel
            if self.wcfg["show_utilized_travel"]:
                self.update_travel(self.bars_travel[idx], minfo.wheels.utilizedSuspensionTravel[idx])

            # Minimum position
            if self.wcfg["show_minimum_position"]:
                self.update_travel(self.bars_minpos[idx], minfo.wheels.minSuspensionPosition[idx])

            # Maximum position
            if self.wcfg["show_maximum_position"]:
                self.update_travel(self.bars_maxpos[idx], minfo.wheels.maxSuspensionPosition[idx])

            # Live position
            if self.wcfg["show_live_position"]:
                self.update_travel(self.bars_live[idx], minfo.wheels.currentSuspensionPosition[idx])

    # GUI update methods
    def update_travel(self, target, data):
        """Suspension travel data"""
        if target.last != data:
            target.last = data
            target.setText(f"{data:.2f}"[:4].strip("."))
