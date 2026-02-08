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
Electric motor Widget
"""

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
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        bar_width = font_m.width * 8 + bar_padx

        # Config units
        self.unit_temp = units.set_unit_temperature(self.cfg.units["temperature_unit"])
        self.unit_power = units.set_unit_power(self.cfg.units["power_unit"])
        self.symbol_power = units.set_symbol_power(self.cfg.units["power_unit"])

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # Motor temperature
        if self.wcfg["show_motor_temperature"]:
            self.bar_style_motor = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_motor_temperature"],
                    bg_color=self.wcfg["bkg_color_motor_temperature"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_motor_temperature"],
                    bg_color=self.wcfg["warning_color_overheat"])
            )
            self.bar_motor = self.set_qlabel(
                text="M TEMP",
                style=self.bar_style_motor[0],
                width=bar_width,
            )
            self.set_primary_orient(
                target=self.bar_motor,
                column=self.wcfg["column_index_motor_temperature"],
            )

        # Motor water temperature
        if self.wcfg["show_water_temperature"]:
            self.bar_style_water = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_water_temperature"],
                    bg_color=self.wcfg["bkg_color_water_temperature"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_water_temperature"],
                    bg_color=self.wcfg["warning_color_overheat"])
            )
            self.bar_water = self.set_qlabel(
                text="W TEMP",
                style=self.bar_style_water[0],
                width=bar_width,
            )
            self.set_primary_orient(
                target=self.bar_water,
                column=self.wcfg["column_index_water_temperature"],
            )

        # Motor rpm
        if self.wcfg["show_rpm"]:
            bar_style_rpm = self.set_qss(
                fg_color=self.wcfg["font_color_rpm"],
                bg_color=self.wcfg["bkg_color_rpm"]
            )
            self.bar_rpm = self.set_qlabel(
                text="RPM",
                style=bar_style_rpm,
                width=bar_width,
            )
            self.set_primary_orient(
                target=self.bar_rpm,
                column=self.wcfg["column_index_rpm"],
            )

        # Motor torque
        if self.wcfg["show_torque"]:
            bar_style_torque = self.set_qss(
                fg_color=self.wcfg["font_color_torque"],
                bg_color=self.wcfg["bkg_color_torque"]
            )
            self.bar_torque = self.set_qlabel(
                text="TORQUE",
                style=bar_style_torque,
                width=bar_width,
            )
            self.set_primary_orient(
                target=self.bar_torque,
                column=self.wcfg["column_index_torque"],
            )

        # Motor power
        if self.wcfg["show_power"]:
            bar_style_power = self.set_qss(
                fg_color=self.wcfg["font_color_power"],
                bg_color=self.wcfg["bkg_color_power"]
            )
            self.bar_power = self.set_qlabel(
                text="POWER",
                style=bar_style_power,
                width=bar_width,
            )
            self.set_primary_orient(
                target=self.bar_power,
                column=self.wcfg["column_index_power"],
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Motor temperature
        if self.wcfg["show_motor_temperature"]:
            temp_motor = round(api.read.emotor.motor_temperature(), 2)
            self.update_motor(self.bar_motor, temp_motor)

        # Water temperature
        if self.wcfg["show_water_temperature"]:
            temp_water = round(api.read.emotor.water_temperature(), 2)
            self.update_water(self.bar_water, temp_water)

        # Motor rpm
        if self.wcfg["show_rpm"]:
            rpm = int(api.read.emotor.rpm())
            self.update_rpm(self.bar_rpm, rpm)

        # Motor torque
        if self.wcfg["show_torque"]:
            torque = round(api.read.emotor.torque(), 2)
            self.update_torque(self.bar_torque, torque)

        # Motor power
        if self.wcfg["show_power"]:
            power = round(calc.engine_power(
                api.read.emotor.torque(), api.read.emotor.rpm()), 2)
            self.update_power(self.bar_power, power)

    # GUI update methods
    def update_motor(self, target, data):
        """Motor temperature"""
        if target.last != data:
            target.last = data
            target.setText(f"M{self.unit_temp(data): >6.1f}°")
            target.updateStyle(self.bar_style_motor[data >= self.wcfg["overheat_threshold_motor"]])

    def update_water(self, target, data):
        """Water temperature"""
        if target.last != data:
            target.last = data
            target.setText(f"W{self.unit_temp(data): >6.1f}°")
            target.updateStyle(self.bar_style_water[data >= self.wcfg["overheat_threshold_water"]])

    def update_rpm(self, target, data):
        """Motor rpm"""
        if target.last != data:
            target.last = data
            target.setText(f"{data: >5}rpm")

    def update_torque(self, target, data):
        """Motor torque"""
        if target.last != data:
            target.last = data
            text = f"{data: >6.2f}"[:6]
            target.setText(f"{text}Nm")

    def update_power(self, target, data):
        """Motor power"""
        if target.last != data:
            target.last = data
            text = f"{self.unit_power(data): >6.2f}"[:6]
            target.setText(f"{text}{self.symbol_power}")
