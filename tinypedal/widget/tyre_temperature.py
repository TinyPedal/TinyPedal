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
    load_heatmap_style,
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

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        inner_gap = self.wcfg["inner_gap"]
        self.leading_zero = min(max(self.wcfg["leading_zero"], 1), 3) + 0.0  # no decimal
        self.sign_text = "°" if self.wcfg["show_degree_sign"] else ""
        text_width = 3 + len(self.sign_text) + (self.cfg.units["temperature_unit"] == "Fahrenheit")

        # Config units
        self.unit_temp = units.set_unit_temperature(self.cfg.units["temperature_unit"])

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )
        bar_style_tcmpd = self.set_qss(
            fg_color=self.wcfg["font_color_tyre_compound"],
            bg_color=self.wcfg["bkg_color_tyre_compound"]
        )
        bar_style_stemp = self.set_qss(
            fg_color=self.wcfg["font_color_surface"],
            bg_color=self.wcfg["bkg_color_surface"]
        )

        # Heatmap style list: 0 - fl, 1 - fr, 2 - rl, 3 - rr
        self.heatmap_styles = 4 * [
            load_heatmap_style(
                heatmap_name=self.wcfg["heatmap_name"],
                default_name=HEATMAP_DEFAULT_TYRE,
                swap_style=self.wcfg["swap_style"],
                fg_color=self.wcfg["font_color_surface"],
                bg_color=self.wcfg["bkg_color_surface"],
            )
        ]

        # Tyre temperature
        self.bars_stemp = self.set_table(
            text=TEXT_NA,
            style=bar_style_stemp,
            width=font_m.width * text_width + bar_padx,
            layout=layout,
            inner_gap=inner_gap,
        )

        # Tyre compound
        if self.wcfg["show_tyre_compound"]:
            self.bars_tcmpd = self.set_qlabel(
                text=TEXT_PLACEHOLDER,
                style=bar_style_tcmpd,
                width=font_m.width + bar_padx,
                count=2,
            )
            self.set_grid_layout_vert(
                layout=layout,
                targets=self.bars_tcmpd,
            )

        # Last data
        self.last_in_pits = -1
        self.last_tcmpd_f = ""
        self.last_tcmpd_r = ""

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Update compound while in pit (or switched pit state)
        in_pits = api.read.vehicle.in_pits()
        if in_pits or self.last_in_pits != in_pits:
            self.last_in_pits = in_pits
            class_name = api.read.vehicle.class_name()
            tcmpd_f = f"{class_name} - {api.read.tyre.compound_name_front()}"
            tcmpd_r = f"{class_name} - {api.read.tyre.compound_name_rear()}"

            # Heatmap style
            if self.wcfg["enable_heatmap_auto_matching"]:
                if self.last_tcmpd_f != tcmpd_f:
                    self.update_heatmap(tcmpd_f, 0)
                    self.last_tcmpd_f = tcmpd_f
                if self.last_tcmpd_r != tcmpd_r:
                    self.update_heatmap(tcmpd_r, 2)
                    self.last_tcmpd_r = tcmpd_r

            # Tyre compound
            if self.wcfg["show_tyre_compound"]:
                self.update_tcmpd(self.bars_tcmpd[0], tcmpd_f)
                self.update_tcmpd(self.bars_tcmpd[1], tcmpd_r)

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
                target.setText(TEXT_PLACEHOLDER)
            else:
                target.setText(f"{self.unit_temp(data):0{self.leading_zero}f}{self.sign_text}")
            target.updateStyle(calc.select_grade(self.heatmap_styles[index], data))

    def update_tcmpd(self, target, data):
        """Tyre compound"""
        if target.last != data:
            target.last = data
            target.setText(select_compound_symbol(data))

    def update_heatmap(self, compound, index):
        """Heatmap style"""
        heatmap_style = load_heatmap_style(
            heatmap_name=select_tyre_heatmap_name(compound),
            default_name=HEATMAP_DEFAULT_TYRE,
            swap_style=self.wcfg["swap_style"],
            fg_color=self.wcfg["font_color_surface"],
            bg_color=self.wcfg["bkg_color_surface"],
        )
        self.heatmap_styles[index] = heatmap_style
        self.heatmap_styles[index + 1] = heatmap_style

    # GUI generate methods
    def set_table(self, text, style, width, layout, inner_gap):
        """Set table"""
        if self.wcfg["show_inner_center_outer"]:
            layout_inner = tuple(self.set_grid_layout(gap=inner_gap) for _ in range(4))
            bar_set = self.set_qlabel(
                text=text,
                style=style,
                width=width,
                count=12,  # 3 x 4 tyres
                last=0,
            )
            for idx, inner in enumerate(layout_inner):
                self.set_grid_layout_table_row(inner, bar_set[idx * 3:idx * 3 + 3])
            self.set_grid_layout_quad(layout, layout_inner)
        else:
            bar_set = self.set_qlabel(
                text=text,
                style=style,
                width=width,
                count=4,
                last=0,
            )
            self.set_grid_layout_quad(layout, bar_set)
        return bar_set
