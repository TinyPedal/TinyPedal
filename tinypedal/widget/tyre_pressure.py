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
from ..userfile.heatmap import select_compound_color, select_compound_symbol
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
        self.text_width = 3 + (self.cfg.units["tyre_pressure_unit"] != "kPa")
        self.hot_pres_temp = max(self.wcfg["hot_pressure_temperature_threshold"], 0)

        # Config units
        self.unit_pres = units.set_unit_pressure(self.cfg.units["tyre_pressure_unit"])

        # Tyre pressure
        base_row = 1
        self.bar_style_tpres = (
            (
                self.wcfg["background_color_pressure"],
                self.wcfg["font_color_pressure_cold"],
            ),
            (
                self.wcfg["background_color_pressure"],
                self.wcfg["font_color_pressure_hot"],
            ),
        ) if self.wcfg["swap_style"] else (
            (
                self.wcfg["font_color_pressure_cold"],
                self.wcfg["background_color_pressure"],
            ),
            (
                self.wcfg["font_color_pressure_hot"],
                self.wcfg["background_color_pressure"],
            ),
        )
        self.bars_tpres = self.set_rawtext(
            text=TEXT_NA,
            width=font_m.width * self.text_width + bar_padx,
            fixed_height=font_m.height,
            offset_y=font_m.voffset,
            fg_color=self.bar_style_tpres[0][0],
            bg_color=self.bar_style_tpres[0][1],
            count=4,
            last=0,
        )
        # Column 1, 1
        for idx, inner in enumerate(layout_inner):
            inner.addWidget(self.bars_tpres[idx], base_row, 1)

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
            # Column 2, 0
            for idx, inner in enumerate(layout_inner):
                inner.addWidget(self.bars_tcmpd[idx], base_row, (1 - idx % 2) * 2)

        # Pressure deviation
        if self.wcfg["show_pressure_deviation"]:
            self.bars_pdiff = self.set_rawtext(
                text=TEXT_NA,
                width=font_m.width * self.text_width + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_pressure_deviation"],
                bg_color=self.wcfg["background_color_pressure_deviation"],
                count=4,
            )
            # Column 0, 2
            for idx, inner in enumerate(layout_inner):
                inner.addWidget(self.bars_pdiff[idx], base_row, 2 * (idx % 2))

            self.tpavg = list(WHEELS_ZERO)
            update_interval = max(self.wcfg["update_interval"], 0.01)
            average_samples = int(min(max(self.wcfg["average_sampling_duration"], 1), 600) / (update_interval * 0.001))
            self.calc_ema_tpres = partial(
                calc.exp_mov_avg,
                calc.ema_factor(average_samples)
            )

        # Last data
        self.last_in_pits = -1
        self.last_compounds = ("", "", "", "")

    def timerEvent(self, event):
        """Update when vehicle on track"""
        in_pits = api.read.vehicle.in_pits()

        # Update compound while in pit (or switched pit state)
        if in_pits or self.last_in_pits != in_pits:
            self.last_in_pits = in_pits
            compounds = api.read.tyre.compound_class()

            if self.last_compounds != compounds:
                # Tyre compound
                if self.wcfg["show_tyre_compound"]:
                    for tyre_idx, bar_tcmpd in enumerate(self.bars_tcmpd):
                        self.update_tcmpd(bar_tcmpd, compounds[tyre_idx])
                self.last_compounds = compounds

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
            target.text = f"{self.unit_pres(data):.2f}"[:self.text_width].strip(".")
            target.fg, target.bg = self.bar_style_tpres[is_hot]
            target.update()

    def update_pdiff(self, target, data):
        """Pressure deviation"""
        if target.last != data:
            target.last = data
            target.text = f"{self.unit_pres(data):.2f}"[:self.text_width].strip(".")
            target.update()

    def update_tcmpd(self, target, data):
        """Tyre compound"""
        if target.last != data:
            target.last = data
            target.text = select_compound_symbol(data)
            if self.wcfg["show_compound_color_by_type"]:
                target.fg = select_compound_color(data)
            target.update()
