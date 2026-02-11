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
Brake temperature Widget
"""

from functools import partial

from .. import calculation as calc
from .. import units
from ..api_control import api
from ..const_common import TEXT_NA, TEXT_PLACEHOLDER
from ..userfile.heatmap import (
    HEATMAP_DEFAULT_BRAKE,
    load_heatmap_color,
    select_brake_heatmap_name,
    set_predefined_brake_name,
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
        font = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size"],
            self.wcfg["font_weight"],
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        inner_gap = self.wcfg["inner_gap"]
        self.leading_zero = min(max(self.wcfg["leading_zero"], 1), 3) + 0.0  # no decimal
        self.sign_text = "°" if self.wcfg["show_degree_sign"] else ""
        text_width = 3 + len(self.sign_text) + (self.cfg.units["temperature_unit"] == "Fahrenheit")
        self.off_brake_duration = max(self.wcfg["off_brake_duration"], 0)

        # Config units
        self.unit_temp = units.set_unit_temperature(self.cfg.units["temperature_unit"])

        # Heatmap style list: 0 - fl, 1 - fr, 2 - rl, 3 - rr
        self.heatmap_styles = 4 * [
            load_heatmap_color(
                heatmap_name=self.wcfg["heatmap_name"],
                default_name=HEATMAP_DEFAULT_BRAKE,
                swap_style=not self.wcfg["swap_style"],
                fg_color=self.wcfg["font_color_temperature"],
                bg_color=self.wcfg["bkg_color_temperature"],
            )
        ]

        # Brake temperature
        layout_btemp = self.set_grid_layout(gap=inner_gap)
        self.bars_btemp = self.set_rawtext(
            text=TEXT_NA,
            width=font_m.width * text_width + bar_padx,
            fixed_height=font_m.height,
            offset_y=font_m.voffset,
            fg_color=self.wcfg["font_color_temperature"],
            bg_color=self.wcfg["bkg_color_temperature"],
            count=4,
            last=0,
        )
        self.set_grid_layout_quad(
            layout=layout_btemp,
            targets=self.bars_btemp,
        )
        self.set_primary_orient(
            target=layout_btemp,
            column=self.wcfg["column_index_temperature"],
        )

        # Average brake temperature
        if self.wcfg["show_average"]:
            layout_btavg = self.set_grid_layout(gap=inner_gap)
            self.bars_btavg = self.set_rawtext(
                text=TEXT_NA,
                width=font_m.width * text_width + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_average"],
                bg_color=self.wcfg["bkg_color_average"],
                count=4,
                last=0,
            )
            self.set_grid_layout_quad(
                layout=layout_btavg,
                targets=self.bars_btavg,
            )
            self.set_primary_orient(
                target=layout_btavg,
                column=self.wcfg["column_index_average"],
            )
            update_interval = max(self.wcfg["update_interval"], 0.01)
            average_samples = int(min(max(self.wcfg["average_sampling_duration"], 1), 600) / (update_interval * 0.001))
            self.calc_ema_btemp = partial(calc.exp_mov_avg, calc.ema_factor(average_samples))

        # Last data
        self.last_in_pits = -1
        self.last_vehicle_name = None
        self.last_lap_etime = 0
        self.off_brake_timer = 0

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Update while in pit (or switched pit state)
        in_pits = api.read.vehicle.in_pits()
        if in_pits or self.last_in_pits != in_pits:
            self.last_in_pits = in_pits

            # Heatmap style
            if self.wcfg["enable_heatmap_auto_matching"]:
                vehicle_name = api.read.vehicle.vehicle_name()
                if self.last_vehicle_name != vehicle_name:
                    self.last_vehicle_name = vehicle_name
                    self.update_heatmap(api.read.vehicle.class_name(), vehicle_name)

        # Brake temperature
        btemp = api.read.brake.temperature()
        for brake_idx, bar_btemp in enumerate(self.bars_btemp):
            self.update_btemp(bar_btemp, round(btemp[brake_idx]), brake_idx)

        # Brake average temperature
        if self.wcfg["show_average"]:
            lap_etime = api.read.timing.elapsed()
            if self.last_lap_etime != lap_etime:
                self.last_lap_etime = lap_etime

                if self.off_brake_timer > lap_etime:
                    self.off_brake_timer = lap_etime

                if api.read.inputs.brake_raw() > 0.01:
                    self.off_brake_timer = lap_etime

                # Update if braked in the past 1 second
                if lap_etime - self.off_brake_timer <= self.off_brake_duration:
                    for brake_idx, bar_btavg in enumerate(self.bars_btavg):
                        btavg = self.calc_ema_btemp(bar_btavg.last, btemp[brake_idx])
                        self.update_btavg(bar_btavg, btavg)

    # GUI update methods
    def update_btemp(self, target, data, index):
        """Brake temperature"""
        if target.last != data:
            target.last = data
            if data < -100:
                target.text = TEXT_PLACEHOLDER
            else:
                target.text = f"{self.unit_temp(data):0{self.leading_zero}f}{self.sign_text}"
            target.fg, target.bg = calc.select_grade(self.heatmap_styles[index], data)
            target.update()

    def update_btavg(self, target, data):
        """Brake average temperature"""
        if target.last != data:
            target.last = data
            if data < -100:
                target.text = TEXT_PLACEHOLDER
            else:
                target.text = f"{self.unit_temp(data):0{self.leading_zero}f}{self.sign_text}"
            target.update()

    # Additional methods
    def update_heatmap(self, class_name: str, vehicle_name: str):
        """Update heatmap"""
        heatmap_f = select_brake_heatmap_name(
            set_predefined_brake_name(class_name, vehicle_name, True)
        )
        heatmap_r = select_brake_heatmap_name(
            set_predefined_brake_name(class_name, vehicle_name, False)
        )
        heatmap_style_f = load_heatmap_color(
            heatmap_name=heatmap_f,
            default_name=HEATMAP_DEFAULT_BRAKE,
            swap_style=not self.wcfg["swap_style"],
            fg_color=self.wcfg["font_color_temperature"],
            bg_color=self.wcfg["bkg_color_temperature"],
        )
        heatmap_style_r = load_heatmap_color(
            heatmap_name=heatmap_r,
            default_name=HEATMAP_DEFAULT_BRAKE,
            swap_style=not self.wcfg["swap_style"],
            fg_color=self.wcfg["font_color_temperature"],
            bg_color=self.wcfg["bkg_color_temperature"],
        )
        self.heatmap_styles[0] = heatmap_style_f
        self.heatmap_styles[1] = heatmap_style_f
        self.heatmap_styles[2] = heatmap_style_r
        self.heatmap_styles[3] = heatmap_style_r
