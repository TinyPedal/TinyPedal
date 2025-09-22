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
Tyre carcass temperature Widget
"""

from functools import partial

from .. import calculation as calc
from ..api_control import api
from ..const_common import TEXT_NA, TEXT_PLACEHOLDER, WHEELS_ZERO
from ..units import set_unit_temperature
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
        layout = self.set_grid_layout(gap=self.wcfg["bar_gap"])
        self.set_primary_layout(layout=layout)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        inner_gap = self.wcfg["inner_gap"]
        self.rate_interval = min(max(self.wcfg["rate_of_change_interval"], 1), 60)
        self.leading_zero = min(max(self.wcfg["leading_zero"], 1), 3) + 0.0  # no decimal
        self.sign_text = "°" if self.wcfg["show_degree_sign"] else ""
        text_width = 3 + len(self.sign_text) + (self.cfg.units["temperature_unit"] == "Fahrenheit")

        # Config units
        self.unit_temp = set_unit_temperature(self.cfg.units["temperature_unit"])

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
        bar_style_ctemp = self.set_qss(
            fg_color=self.wcfg["font_color_carcass"],
            bg_color=self.wcfg["bkg_color_carcass"]
        )

        # Heatmap style list: 0 - fl, 1 - fr, 2 - rl, 3 - rr
        self.heatmap_styles = 4 * [
            load_heatmap_style(
                heatmap_name=self.wcfg["heatmap_name"],
                default_name=HEATMAP_DEFAULT_TYRE,
                swap_style=self.wcfg["swap_style"],
                fg_color=self.wcfg["font_color_carcass"],
                bg_color=self.wcfg["bkg_color_carcass"],
            )
        ]

        # Tyre carcass temperature
        layout_ctemp = self.set_grid_layout(gap=inner_gap)
        self.bars_ctemp = self.set_qlabel(
            text=TEXT_NA,
            style=bar_style_ctemp,
            width=font_m.width * text_width + bar_padx,
            count=4,
            last=0,
        )
        self.set_grid_layout_quad(
            layout=layout_ctemp,
            targets=self.bars_ctemp,
        )
        self.set_primary_orient(
            target=layout_ctemp,
            column=self.wcfg["column_index_carcass"],
        )

        if self.wcfg["show_tyre_compound"]:
            self.bars_tcmpd = self.set_qlabel(
                text=TEXT_PLACEHOLDER,
                style=bar_style_tcmpd,
                width=font_m.width + bar_padx,
                count=2,
            )
            self.set_grid_layout_vert(
                layout=layout_ctemp,
                targets=self.bars_tcmpd,
            )

        # Rate of change
        if self.wcfg["show_rate_of_change"]:
            layout_rtemp = self.set_grid_layout(gap=inner_gap)
            self.bar_style_rtemp = (
                self.set_qss(
                    fg_color=self.wcfg["bkg_color_rate_of_change"],
                    bg_color=self.wcfg["font_color_rate_loss"]),
                self.set_qss(
                    fg_color=self.wcfg["bkg_color_rate_of_change"],
                    bg_color=self.wcfg["font_color_rate_gain"]),
                self.set_qss(
                    fg_color=self.wcfg["bkg_color_rate_of_change"],
                    bg_color=self.wcfg["font_color_rate_of_change"]),
            ) if self.wcfg["swap_style"] else (
                self.set_qss(
                    fg_color=self.wcfg["font_color_rate_loss"],
                    bg_color=self.wcfg["bkg_color_rate_of_change"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_rate_gain"],
                    bg_color=self.wcfg["bkg_color_rate_of_change"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_rate_of_change"],
                    bg_color=self.wcfg["bkg_color_rate_of_change"]),
            )
            self.bars_rdiff = self.set_qlabel(
                text=TEXT_NA,
                style=self.bar_style_rtemp[2],
                width=font_m.width * text_width + bar_padx,
                count=4,
                last=0,
            )
            self.set_grid_layout_quad(
                layout=layout_rtemp,
                targets=self.bars_rdiff,
            )
            self.set_primary_orient(
                target=layout_rtemp,
                column=self.wcfg["column_index_rate_of_change"],
            )

            if self.wcfg["show_tyre_compound"]:
                bars_blank = self.set_qlabel(
                    text="",
                    style=bar_style_tcmpd,
                    width=font_m.width + bar_padx,
                    count=2,
                )
                self.set_grid_layout_vert(
                    layout=layout_rtemp,
                    targets=bars_blank
                )

        # Last data
        self.last_in_pits = -1
        self.last_tcmpd_f = ""
        self.last_tcmpd_r = ""
        self.last_rtemp = list(WHEELS_ZERO)
        self.last_lap_etime = 0
        self.calc_ema_rdiff = partial(
            calc.exp_mov_avg,
            calc.ema_factor(min(max(self.wcfg["rate_of_change_smoothing_samples"], 1), 500))
        )

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

        # Tyre carcass temperature: 0 - fl, 1 - fr, 2 - rl, 3 - rr
        ctemp = api.read.tyre.carcass_temperature()
        for tyre_idx, bar_ctemp in enumerate(self.bars_ctemp):
            self.update_ctemp(bar_ctemp, round(ctemp[tyre_idx]), tyre_idx)

        # Rate of change
        if self.wcfg["show_rate_of_change"]:
            lap_etime = api.read.timing.elapsed()

            if self.last_lap_etime > lap_etime:
                self.last_lap_etime = lap_etime
            elif lap_etime - self.last_lap_etime >= 0.1:
                interval = self.rate_interval / (lap_etime - self.last_lap_etime)
                self.last_lap_etime = lap_etime

                for tyre_idx, bar_rdiff in enumerate(self.bars_rdiff):
                    rdiff = self.calc_ema_rdiff(
                        bar_rdiff.last,
                        (ctemp[tyre_idx] - self.last_rtemp[tyre_idx]) * interval
                    )
                    self.last_rtemp[tyre_idx] = ctemp[tyre_idx]
                    self.update_rdiff(bar_rdiff, rdiff)

    # GUI update methods
    def update_ctemp(self, target, data, index):
        """Tyre carcass temperature"""
        if target.last != data:
            target.last = data
            if data < -100:
                target.setText(TEXT_PLACEHOLDER)
            else:
                target.setText(f"{self.unit_temp(data):0{self.leading_zero}f}{self.sign_text}")
            target.updateStyle(calc.select_grade(self.heatmap_styles[index], data))

    def update_rdiff(self, target, data):
        """Rate of change"""
        if target.last != data:
            target.last = data
            target.setText(f"{self.unit_temp(abs(data)):.1f}"[:3].strip("."))
            target.updateStyle(self.bar_style_rtemp[data > 0])

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
            fg_color=self.wcfg["font_color_carcass"],
            bg_color=self.wcfg["bkg_color_carcass"],
        )
        self.heatmap_styles[index] = heatmap_style
        self.heatmap_styles[index + 1] = heatmap_style
