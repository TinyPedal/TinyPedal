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
Engine temperature Widget
"""

from functools import partial

from .. import calculation as calc
from .. import units
from ..api_control import api
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
        self.rate_interval = min(max(self.wcfg["rate_of_change_interval"], 1), 60)

        if self.wcfg["layout"] == 0:
            width_oil = max(
                len(self.wcfg["prefix_oil_temperature"]),
                len(self.wcfg["prefix_water_temperature"]),
            )
            width_water = width_oil
        else:
            width_oil = len(self.wcfg["prefix_oil_temperature"])
            width_water = len(self.wcfg["prefix_water_temperature"])

        self.prefix_oil = self.wcfg["prefix_oil_temperature"]
        self.prefix_water = self.wcfg["prefix_water_temperature"]

        # Config units
        self.unit_temp = units.set_unit_temperature(self.cfg.units["temperature_unit"])

        self.bar_style_rate = (
            self.wcfg["font_color_rate_loss"],
            self.wcfg["font_color_rate_gain"],
            self.wcfg["font_color_rate_of_change"],
        )
        self.calc_ema_rdiff = partial(
            calc.exp_mov_avg,
            calc.ema_factor(self.wcfg["rate_of_change_smoothing_samples"])
        )

        # Oil temperature
        if self.wcfg["show_oil_temperature"]:
            layout_oil = self.set_grid_layout()
            self.bar_style_oil_temp = (
                self.wcfg["background_color_oil_temperature"],
                self.wcfg["warning_color_overheat"],
            )
            self.bar_oil_temp = self.set_rawtext(
                text="0.000°",
                width=font_m.width * 6 + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_oil_temperature"],
                bg_color=self.bar_style_oil_temp[0],
                last=0,
            )
            layout_oil.addWidget(self.bar_oil_temp, 0, 1)
            if self.wcfg["show_temperature_prefix"]:
                self.bar_oil_prefix = self.set_rawtext(
                    text=self.prefix_oil,
                    width=font_m.width * width_oil + bar_padx,
                    fixed_height=font_m.height,
                    offset_y=font_m.voffset,
                    fg_color=self.wcfg["font_color_prefix"],
                    bg_color=self.wcfg["background_color_prefix"],
                )
                layout_oil.addWidget(self.bar_oil_prefix, 0, 0)
            if self.wcfg["show_rate_of_change"]:
                self.bar_oil_rate = self.set_rawtext(
                    text="0.0",
                    width=font_m.width * 3 + bar_padx,
                    fixed_height=font_m.height,
                    offset_y=font_m.voffset,
                    fg_color=self.bar_style_rate[2],
                    bg_color=self.wcfg["background_color_rate_of_change"],
                    last=0,
                )
                layout_oil.addWidget(self.bar_oil_rate, 0, 2)
            if self.wcfg["show_net_change_per_lap"]:
                self.bar_oil_net = self.set_rawtext(
                    text="0.0",
                    width=font_m.width * 3 + bar_padx,
                    fixed_height=font_m.height,
                    offset_y=font_m.voffset,
                    fg_color=self.bar_style_rate[2],
                    bg_color=self.wcfg["background_color_rate_of_change"],
                    last=0,
                )
                layout_oil.addWidget(self.bar_oil_net, 0, 3)
            self.set_primary_orient(
                target=layout_oil,
                column=self.wcfg["display_order_oil_temperature"],
            )

        # Water temperature
        if self.wcfg["show_water_temperature"]:
            layout_water = self.set_grid_layout()
            self.bar_style_water_temp = (
                self.wcfg["background_color_water_temperature"],
                self.wcfg["warning_color_overheat"],
            )
            self.bar_water_temp = self.set_rawtext(
                text="0.000°",
                width=font_m.width * 6 + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_water_temperature"],
                bg_color=self.bar_style_water_temp[0],
                last=0,
            )
            layout_water.addWidget(self.bar_water_temp, 0, 1)
            if self.wcfg["show_temperature_prefix"]:
                self.bar_water_prefix = self.set_rawtext(
                    text=self.prefix_water,
                    width=font_m.width * width_water + bar_padx,
                    fixed_height=font_m.height,
                    offset_y=font_m.voffset,
                    fg_color=self.wcfg["font_color_prefix"],
                    bg_color=self.wcfg["background_color_prefix"],
                )
                layout_water.addWidget(self.bar_water_prefix, 0, 0)
            if self.wcfg["show_rate_of_change"]:
                self.bar_water_rate = self.set_rawtext(
                    text="0.0",
                    width=font_m.width * 3 + bar_padx,
                    fixed_height=font_m.height,
                    offset_y=font_m.voffset,
                    fg_color=self.bar_style_rate[2],
                    bg_color=self.wcfg["background_color_rate_of_change"],
                    last=0,
                )
                layout_water.addWidget(self.bar_water_rate, 0, 2)
            if self.wcfg["show_net_change_per_lap"]:
                self.bar_water_net = self.set_rawtext(
                    text="0.0",
                    width=font_m.width * 3 + bar_padx,
                    fixed_height=font_m.height,
                    offset_y=font_m.voffset,
                    fg_color=self.bar_style_rate[2],
                    bg_color=self.wcfg["background_color_rate_of_change"],
                    last=0,
                )
                layout_water.addWidget(self.bar_water_net, 0, 3)
            self.set_primary_orient(
                target=layout_water,
                column=self.wcfg["display_order_water_temperature"],
            )

        # Last data
        self.last_lap_etime = 0
        self.last_lap_stime = 0
        self.last_temp_oil = 0
        self.last_temp_water = 0

    def timerEvent(self, event):
        """Update when vehicle on track"""
        lap_stime = api.read.timing.start()
        lap_etime = api.read.timing.elapsed()

        interval = 0
        if self.last_lap_etime > lap_etime:
            self.last_lap_etime = lap_etime
        elif lap_etime - self.last_lap_etime >= 0.1:
            interval = self.rate_interval / (lap_etime - self.last_lap_etime)
            self.last_lap_etime = lap_etime

        new_lap = False
        if self.last_lap_stime != lap_stime:
            self.last_lap_stime = lap_stime
            new_lap = True

        # Oil temperature
        if self.wcfg["show_oil_temperature"]:
            temp_oil = api.read.engine.oil_temperature()
            self.update_oil(self.bar_oil_temp, temp_oil)

            if self.wcfg["show_rate_of_change"] and interval:
                rate_oil = self.calc_ema_rdiff(
                    self.bar_oil_rate.last,
                    (temp_oil - self.last_temp_oil) * interval
                )
                self.last_temp_oil = temp_oil
                self.update_rate(self.bar_oil_rate, rate_oil)

            if self.wcfg["show_net_change_per_lap"] and new_lap:
                self.update_net(self.bar_oil_net, temp_oil, self.bar_oil_net.last)

        # Water temperature
        if self.wcfg["show_water_temperature"]:
            temp_water = api.read.engine.water_temperature()
            self.update_water(self.bar_water_temp, temp_water)

            if self.wcfg["show_rate_of_change"] and interval:
                rate_water = self.calc_ema_rdiff(
                    self.bar_water_rate.last,
                    (temp_water - self.last_temp_water) * interval
                )
                self.last_temp_water = temp_water
                self.update_rate(self.bar_water_rate, rate_water)

            if self.wcfg["show_net_change_per_lap"] and new_lap:
                self.update_net(self.bar_water_net, temp_water, self.bar_water_net.last)

    # GUI update methods
    def update_oil(self, target, data):
        """Oil temperature"""
        if target.last != data:
            target.last = data
            text_temp = f"{self.unit_temp(data):.3f}"
            target.text = f"{text_temp:.5}°"
            target.bg = self.bar_style_oil_temp[data >= self.wcfg["overheat_threshold_oil"]]
            target.update()

    def update_water(self, target, data):
        """Water temperature"""
        if target.last != data:
            target.last = data
            text_temp = f"{self.unit_temp(data):.3f}"
            target.text = f"{text_temp:.5}°"
            target.bg = self.bar_style_water_temp[data >= self.wcfg["overheat_threshold_water"]]
            target.update()

    def update_rate(self, target, data):
        """Rate of change"""
        if target.last != data:
            target.last = data
            target.text = f"{self.unit_temp(abs(data)):.1f}"[:3].strip(".")
            target.fg = self.bar_style_rate[data > 0]
            target.update()

    def update_net(self, target, data, last):
        """Net change per lap"""
        if target.last != data:
            target.last = data
            change = data - last
            target.text = f"{self.unit_temp(abs(change)):.1f}"[:3].strip(".")
            target.fg = self.bar_style_rate[change > 0]
            target.update()
