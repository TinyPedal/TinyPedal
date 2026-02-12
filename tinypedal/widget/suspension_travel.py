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
        font = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size"],
            self.wcfg["font_weight"],
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)

        font_cap = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size"] * self.wcfg["font_scale_caption"],
            self.wcfg["font_weight"],
        )
        font_cap_m = self.get_font_metrics(font_cap)

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        bar_width = font_m.width * 4 + bar_padx

        # Total travel
        if self.wcfg["show_total_travel"]:
            layout_total = self.set_grid_layout()
            self.bars_total = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_total_travel"],
                bg_color=self.wcfg["bkg_color_total_travel"],
                count=4,
            )
            self.set_grid_layout_quad(
                layout=layout_total,
                targets=self.bars_total,
            )
            self.set_primary_orient(
                target=layout_total,
                column=self.wcfg["column_index_total_travel"],
            )

            if self.wcfg["show_caption"]:
                cap_total = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_total_travel"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["bkg_color_caption"],
                )
                layout_total.addWidget(cap_total, 0, 0, 1, 0)

        # Bump travel
        if self.wcfg["show_bump_travel"]:
            layout_bump = self.set_grid_layout()
            self.bars_bump = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_bump_travel"],
                bg_color=self.wcfg["bkg_color_bump_travel"],
                count=4,
            )
            self.set_grid_layout_quad(
                layout=layout_bump,
                targets=self.bars_bump,
            )
            self.set_primary_orient(
                target=layout_bump,
                column=self.wcfg["column_index_bump_travel"],
            )

            if self.wcfg["show_caption"]:
                cap_bump = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_bump_travel"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["bkg_color_caption"],
                )
                layout_bump.addWidget(cap_bump, 0, 0, 1, 0)

        # Rebound travel
        if self.wcfg["show_rebound_travel"]:
            layout_rebound = self.set_grid_layout()
            self.bars_rebound = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_rebound_travel"],
                bg_color=self.wcfg["bkg_color_rebound_travel"],
                count=4,
            )
            self.set_grid_layout_quad(
                layout=layout_rebound,
                targets=self.bars_rebound,
            )
            self.set_primary_orient(
                target=layout_rebound,
                column=self.wcfg["column_index_rebound_travel"],
            )

            if self.wcfg["show_caption"]:
                cap_rebound = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_rebound_travel"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["bkg_color_caption"],
                )
                layout_rebound.addWidget(cap_rebound, 0, 0, 1, 0)

        # Travel ratio
        if self.wcfg["show_travel_ratio"]:
            layout_ratio = self.set_grid_layout()
            self.bars_ratio = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_travel_ratio"],
                bg_color=self.wcfg["bkg_color_travel_ratio"],
                count=4,
            )
            self.set_grid_layout_quad(
                layout=layout_ratio,
                targets=self.bars_ratio,
            )
            self.set_primary_orient(
                target=layout_ratio,
                column=self.wcfg["column_index_travel_ratio"],
            )

            if self.wcfg["show_caption"]:
                cap_ratio = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_travel_ratio"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["bkg_color_caption"],
                )
                layout_ratio.addWidget(cap_ratio, 0, 0, 1, 0)

        # Minimum position
        if self.wcfg["show_minimum_position"]:
            layout_minpos = self.set_grid_layout()
            self.bars_minpos = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_minimum_position"],
                bg_color=self.wcfg["bkg_color_minimum_position"],
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
                cap_minpos = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_minimum_position"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["bkg_color_caption"],
                )
                layout_minpos.addWidget(cap_minpos, 0, 0, 1, 0)

        # Maximum position
        if self.wcfg["show_maximum_position"]:
            layout_maxpos = self.set_grid_layout()
            self.bars_maxpos = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_maximum_position"],
                bg_color=self.wcfg["bkg_color_maximum_position"],
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
                cap_maxpos = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_maximum_position"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["bkg_color_caption"],
                )
                layout_maxpos.addWidget(cap_maxpos, 0, 0, 1, 0)

        # Live position
        if self.wcfg["show_live_position"]:
            layout_live = self.set_grid_layout()
            self.bars_live = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_live_position"],
                bg_color=self.wcfg["bkg_color_live_position"],
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
                cap_live = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_live_position"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["bkg_color_caption"],
                )
                layout_live.addWidget(cap_live, 0, 0, 1, 0)

    def timerEvent(self, event):
        """Update when vehicle on track"""
        for idx in range(4):
            min_pos = minfo.wheels.minSuspensionPosition[idx]
            max_pos = minfo.wheels.maxSuspensionPosition[idx]
            static_pos = minfo.wheels.staticSuspensionPosition[idx]

            total_travel = max_pos - min_pos

            if static_pos != 0 and static_pos < max_pos:
                bump_travel = max_pos - static_pos
            else:
                bump_travel = 0

            if static_pos != 0 and static_pos > min_pos:
                rebound_travel = static_pos - min_pos
            else:
                rebound_travel = 0

            if total_travel > 0 and total_travel >= bump_travel:
                travel_ratio = bump_travel / total_travel
            else:
                travel_ratio = 0

            # Total travel
            if self.wcfg["show_total_travel"]:
                self.update_travel(self.bars_total[idx], total_travel)

            # Bump travel
            if self.wcfg["show_bump_travel"]:
                self.update_travel(self.bars_bump[idx], bump_travel)

            # Rebound travel
            if self.wcfg["show_rebound_travel"]:
                self.update_travel(self.bars_rebound[idx], rebound_travel)

            # Travel ratio
            if self.wcfg["show_travel_ratio"]:
                self.update_ratio(self.bars_ratio[idx], travel_ratio)

            # Minimum position
            if self.wcfg["show_minimum_position"]:
                self.update_travel(self.bars_minpos[idx], min_pos)

            # Maximum position
            if self.wcfg["show_maximum_position"]:
                self.update_travel(self.bars_maxpos[idx], max_pos)

            # Live position
            if self.wcfg["show_live_position"]:
                live_pos = minfo.wheels.currentSuspensionPosition[idx]
                if self.wcfg["show_live_position_relative_to_static_position"]:
                    live_pos -= static_pos
                self.update_travel(self.bars_live[idx], live_pos)

    # GUI update methods
    def update_travel(self, target, data):
        """Suspension travel data"""
        if target.last != data:
            target.last = data
            target.text = f"{data:.2f}"[:4].strip(".")
            target.update()

    def update_ratio(self, target, data):
        """Travel ratio"""
        if target.last != data:
            target.last = data
            target.text = f"{data:.0%}"
            target.update()
