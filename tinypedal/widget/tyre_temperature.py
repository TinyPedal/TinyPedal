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
Tyre temperature Widget
"""

from .. import calculation as calc
from .. import units
from ..api_control import api
from ..const_common import TEXT_NA, TEXT_PLACEHOLDER
from ..userfile.heatmap import (
    HEATMAP_DEFAULT_TYRE,
    load_heatmap_color,
    select_compound_color,
    select_compound_symbol,
    select_tyre_heatmap_name,
)
from ._base import Overlay


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout(
            gap_hori=self.wcfg["horizontal_gap"],
            gap_vert=self.wcfg["vertical_gap"],
        )
        self.set_primary_layout(layout=layout)

        layout_inner = tuple(self.set_grid_layout(gap=self.wcfg["inner_gap"]) for _ in range(4))
        self.set_grid_layout_quad(layout=layout, targets=layout_inner)

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
        self.leading_zero = min(max(self.wcfg["leading_zero"], 1), 3) + 0.0  # no decimal
        self.sign_text = "°" if self.wcfg["show_degree_sign"] else ""
        text_width = 3 + len(self.sign_text) + (self.cfg.units["temperature_unit"] == "Fahrenheit")

        # Config units
        self.unit_temp = units.set_unit_temperature(self.cfg.units["temperature_unit"])

        # Heatmap style list: 0 - fl, 1 - fr, 2 - rl, 3 - rr
        self.heatmap_styles = 4 * [
            load_heatmap_color(
                heatmap_name=self.wcfg["heatmap_name"],
                default_name=HEATMAP_DEFAULT_TYRE,
                swap_style=self.wcfg["swap_style"],
                fg_color=self.wcfg["font_color_surface"],
                bg_color=self.wcfg["background_color_surface"],
            )
        ]

        # Tyre temperature
        base_row = 1
        if self.wcfg["show_inner_center_outer"]:
            temp_count = 3
        else:
            temp_count = 1

        self.bars_stemp = self.set_rawtext(
            text=TEXT_NA,
            width=font_m.width * text_width + bar_padx,
            fixed_height=font_m.height,
            offset_y=font_m.voffset,
            fg_color=self.wcfg["font_color_surface"],
            bg_color=self.wcfg["background_color_surface"],
            count=4 * temp_count,  # 4 tyres x 3 temps
            last=0,
        )
        # Column 0(,1,2), 1(,2,3)
        for idx, inner in enumerate(layout_inner):
            self.set_grid_layout_table_row(
                layout=inner,
                targets=self.bars_stemp[idx * temp_count: idx * temp_count + temp_count],
                column_start=idx % 2,
                row=base_row,
            )

        # Tyre compound
        if self.wcfg["show_tyre_compound"]:
            self.bars_tcmpd = self.set_rawtext(
                text=TEXT_PLACEHOLDER,
                width=font_m.width + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_tyre_compound"],
                bg_color=self.wcfg["background_color_tyre_compound"],
                count=4,
            )
            # Column 1(3), 0
            for idx, inner in enumerate(layout_inner):
                inner.addWidget(self.bars_tcmpd[idx], base_row, (1 - idx % 2) * temp_count)

        # Last data
        self.last_in_pits = -1
        self.last_compounds = ("", "", "", "")

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Update compound while in pit (or switched pit state)
        in_pits = api.read.vehicle.in_pits()
        if in_pits or self.last_in_pits != in_pits:
            self.last_in_pits = in_pits
            compounds = api.read.tyre.compound_class()

            if self.last_compounds != compounds:
                # Heatmap
                if self.wcfg["enable_heatmap_auto_matching"]:
                    for index, name in enumerate(compounds):
                        if self.last_compounds[index] != name:
                            self.update_heatmap(name, index)
                # Tyre compound
                if self.wcfg["show_tyre_compound"]:
                    for tyre_idx, bar_tcmpd in enumerate(self.bars_tcmpd):
                        self.update_tcmpd(bar_tcmpd, compounds[tyre_idx])
                self.last_compounds = compounds

        # Surface temperature: 0 - fl, 3 - fr, 6 - rl, 9 - rr
        if self.wcfg["show_inner_center_outer"]:
            stemp = api.read.tyre.surface_temperature_ico()
            for tyre_idx, bar_stemp in enumerate(self.bars_stemp):
                self.update_stemp(bar_stemp, round(stemp[tyre_idx]), tyre_idx // 3)
        else:  # 0 - fl, 1 - fr, 2 - rl, 3 - rr
            stemp = api.read.tyre.surface_temperature_avg()
            for tyre_idx, bar_stemp in enumerate(self.bars_stemp):
                self.update_stemp(bar_stemp, round(stemp[tyre_idx]), tyre_idx)

    # GUI update methods
    def update_stemp(self, target, data, index):
        """Tyre surface temperature"""
        if target.last != data:
            target.last = data
            if data < -100:
                target.text = TEXT_PLACEHOLDER
            else:
                target.text = f"{self.unit_temp(data):0{self.leading_zero}f}{self.sign_text}"
            target.fg, target.bg = calc.select_grade(self.heatmap_styles[index], data)
            target.update()

    def update_tcmpd(self, target, data):
        """Tyre compound"""
        if target.last != data:
            target.last = data
            target.text = select_compound_symbol(data)
            if self.wcfg["show_compound_color_by_type"]:
                target.fg = select_compound_color(data)
            target.update()

    def update_heatmap(self, compound, index):
        """Heatmap style"""
        self.heatmap_styles[index] = load_heatmap_color(
            heatmap_name=select_tyre_heatmap_name(compound),
            default_name=HEATMAP_DEFAULT_TYRE,
            swap_style=self.wcfg["swap_style"],
            fg_color=self.wcfg["font_color_surface"],
            bg_color=self.wcfg["background_color_surface"],
        )
