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
Tyre pressure Widget
"""

from functools import partial

from .. import calculation as calc
from .. import units
from ..api_control import api
from ..const_common import TEXT_NA, TEXT_PLACEHOLDER, WHEELS_ZERO
from ..userfile.heatmap import select_compound_symbol
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
        self.text_width = 3 + (self.cfg.units["tyre_pressure_unit"] != "kPa")
        self.hot_pres_temp = max(self.wcfg["hot_pressure_temperature_threshold"], 0)

        # Config units
        self.unit_pres = units.set_unit_pressure(self.cfg.units["tyre_pressure_unit"])

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
        self.bar_style_tpres = (
            self.set_qss(
                fg_color=self.wcfg["bkg_color_pressure"],
                bg_color=self.wcfg["font_color_pressure_cold"]),
            self.set_qss(
                fg_color=self.wcfg["bkg_color_pressure"],
                bg_color=self.wcfg["font_color_pressure_hot"]),
        ) if self.wcfg["swap_style"] else (
            self.set_qss(
                fg_color=self.wcfg["font_color_pressure_cold"],
                bg_color=self.wcfg["bkg_color_pressure"]),
            self.set_qss(
                fg_color=self.wcfg["font_color_pressure_hot"],
                bg_color=self.wcfg["bkg_color_pressure"]),
        )

        # Tyre pressure
        layout_tpres = self.set_grid_layout(gap=inner_gap)
        self.bars_tpres = self.set_qlabel(
            text=TEXT_NA,
            style=self.bar_style_tpres[0],
            width=font_m.width * self.text_width + bar_padx,
            count=4,
            last=0,
        )
        self.set_grid_layout_quad(
            layout=layout_tpres,
            targets=self.bars_tpres,
        )
        self.set_primary_orient(
            target=layout_tpres,
            column=self.wcfg["column_index_pressure"],
        )

        if self.wcfg["show_tyre_compound"]:
            self.bars_tcmpd = self.set_qlabel(
                text=TEXT_PLACEHOLDER,
                style=bar_style_tcmpd,
                width=font_m.width + bar_padx,
                count=2,
            )
            self.set_grid_layout_vert(
                layout=layout_tpres,
                targets=self.bars_tcmpd,
            )

        # Pressure deviation
        if self.wcfg["show_pressure_deviation"]:
            layout_pdiff = self.set_grid_layout(gap=inner_gap)
            bar_style_pdiff = self.set_qss(
                fg_color=self.wcfg["font_color_pressure_deviation"],
                bg_color=self.wcfg["bkg_color_pressure_deviation"]
            )
            self.bars_pdiff = self.set_qlabel(
                text=TEXT_NA,
                style=bar_style_pdiff,
                width=font_m.width * self.text_width + bar_padx,
                count=4,
            )
            self.set_grid_layout_quad(
                layout=layout_pdiff,
                targets=self.bars_pdiff,
            )
            self.set_primary_orient(
                target=layout_pdiff,
                column=self.wcfg["column_index_pressure_deviation"],
            )

            self.tpavg = list(WHEELS_ZERO)
            update_interval = max(self.wcfg["update_interval"], 0.01)
            average_samples = int(min(max(self.wcfg["average_sampling_duration"], 1), 600) / (update_interval * 0.001))
            self.calc_ema_tpres = partial(
                calc.exp_mov_avg,
                calc.ema_factor(average_samples)
            )

            if self.wcfg["show_tyre_compound"]:
                bars_blank = self.set_qlabel(
                    text="",
                    style=bar_style_tcmpd,
                    width=font_m.width + bar_padx,
                    count=2,
                )
                self.set_grid_layout_vert(
                    layout=layout_pdiff,
                    targets=bars_blank
                )

        # Last data
        self.last_in_pits = -1

    def timerEvent(self, event):
        """Update when vehicle on track"""
        in_pits = api.read.vehicle.in_pits()

        # Update compound while in pit (or switched pit state)
        if in_pits or self.last_in_pits != in_pits:
            self.last_in_pits = in_pits
            class_name = api.read.vehicle.class_name()
            tcmpd_f = f"{class_name} - {api.read.tyre.compound_name_front()}"
            tcmpd_r = f"{class_name} - {api.read.tyre.compound_name_rear()}"

            # Tyre compound
            if self.wcfg["show_tyre_compound"]:
                self.update_tcmpd(self.bars_tcmpd[0], tcmpd_f)
                self.update_tcmpd(self.bars_tcmpd[1], tcmpd_r)

        # Tyre pressure: 0 - fl, 1 - fr, 2 - rl, 3 - rr
        tpres = api.read.tyre.pressure()
        ctemp = api.read.tyre.carcass_temperature()
        for tyre_idx, bar_tpres in enumerate(self.bars_tpres):
            self.update_tpres(bar_tpres, tpres[tyre_idx], ctemp[tyre_idx] >= self.hot_pres_temp)

        # Pressure deviation
        if self.wcfg["show_pressure_deviation"]:
            peak_pres = max(self.tpavg)
            for tyre_idx, bar_pdiff in enumerate(self.bars_pdiff):
                self.update_pdiff(bar_pdiff, peak_pres - self.tpavg[tyre_idx])
                self.tpavg[tyre_idx] = self.calc_ema_tpres(self.tpavg[tyre_idx], tpres[tyre_idx])

    # GUI update methods
    def update_tpres(self, target, data, is_hot):
        """Tyre pressure"""
        if target.last != data:
            target.last = data
            target.setText(f"{self.unit_pres(data):.2f}"[:self.text_width].strip("."))
            target.updateStyle(self.bar_style_tpres[is_hot])

    def update_pdiff(self, target, data):
        """Pressure deviation"""
        if target.last != data:
            target.last = data
            target.setText(f"{self.unit_pres(abs(data)):.2f}"[:self.text_width].strip("."))

    def update_tcmpd(self, target, data):
        """Tyre compound"""
        if target.last != data:
            target.last = data
            target.setText(select_compound_symbol(data))
