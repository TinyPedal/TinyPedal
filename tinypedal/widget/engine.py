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
Engine Widget
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
        font = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size"],
            self.wcfg["font_weight"],
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        bar_width = font_m.width * 8 + bar_padx

        # Config units
        self.unit_temp = units.set_unit_temperature(self.cfg.units["temperature_unit"])
        self.unit_power = units.set_unit_power(self.cfg.units["power_unit"])
        self.symbol_power = units.set_symbol_power(self.cfg.units["power_unit"])
        self.unit_pres = units.set_unit_pressure(self.cfg.units["turbo_pressure_unit"])
        self.symbol_pres = units.set_symbol_pressure(self.cfg.units["turbo_pressure_unit"])

        # Oil temperature
        if self.wcfg["show_oil_temperature"]:
            self.bar_style_oil = (
                self.wcfg["bkg_color_oil"],
                self.wcfg["warning_color_overheat"],
            )
            self.bar_oil = self.set_rawtext(
                text="Oil T",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_oil"],
                bg_color=self.bar_style_oil[0],
            )
            self.set_primary_orient(
                target=self.bar_oil,
                column=self.wcfg["column_index_oil"],
            )

        # Water temperature
        if self.wcfg["show_water_temperature"]:
            self.bar_style_water = (
                self.wcfg["bkg_color_water"],
                self.wcfg["warning_color_overheat"],
            )
            self.bar_water = self.set_rawtext(
                text="Water T",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_water"],
                bg_color=self.bar_style_water[0],
            )
            self.set_primary_orient(
                target=self.bar_water,
                column=self.wcfg["column_index_water"],
            )

        # Turbo pressure
        if self.wcfg["show_turbo_pressure"]:
            self.bar_turbo = self.set_rawtext(
                text="Turbo",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_turbo"],
                bg_color=self.wcfg["bkg_color_turbo"],
            )
            self.set_primary_orient(
                target=self.bar_turbo,
                column=self.wcfg["column_index_turbo"],
            )

        # Engine RPM
        if self.wcfg["show_rpm"]:
            self.bar_rpm = self.set_rawtext(
                text="RPM",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_rpm"],
                bg_color=self.wcfg["bkg_color_rpm"],
            )
            self.set_primary_orient(
                target=self.bar_rpm,
                column=self.wcfg["column_index_rpm"],
            )

        # Engine RPM maximum
        if self.wcfg["show_rpm_maximum"]:
            self.bar_rpm_max = self.set_rawtext(
                text="MAX RPM",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_rpm_maximum"],
                bg_color=self.wcfg["bkg_color_rpm_maximum"],
            )
            self.set_primary_orient(
                target=self.bar_rpm_max,
                column=self.wcfg["column_index_rpm_maximum"],
            )

        # Engine torque
        if self.wcfg["show_torque"]:
            self.bar_torque = self.set_rawtext(
                text="TORQUE",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_torque"],
                bg_color=self.wcfg["bkg_color_torque"],
            )
            self.set_primary_orient(
                target=self.bar_torque,
                column=self.wcfg["column_index_torque"],
            )

        # Engine power
        if self.wcfg["show_power"]:
            self.bar_power = self.set_rawtext(
                text="POWER",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_power"],
                bg_color=self.wcfg["bkg_color_power"],
            )
            self.set_primary_orient(
                target=self.bar_power,
                column=self.wcfg["column_index_power"],
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Oil temperature
        if self.wcfg["show_oil_temperature"]:
            temp_oil = round(api.read.engine.oil_temperature(), 2)
            self.update_oil(self.bar_oil, temp_oil)

        # Water temperature
        if self.wcfg["show_water_temperature"]:
            temp_water = round(api.read.engine.water_temperature(), 2)
            self.update_water(self.bar_water, temp_water)

        # Turbo pressure
        if self.wcfg["show_turbo_pressure"]:
            turbo = int(api.read.engine.turbo())
            self.update_turbo(self.bar_turbo, turbo)

        # Engine RPM
        if self.wcfg["show_rpm"]:
            rpm = int(api.read.engine.rpm())
            self.update_rpm(self.bar_rpm, rpm)

        # Engine RPM maximum
        if self.wcfg["show_rpm_maximum"]:
            rpm_max = int(api.read.engine.rpm_max())
            self.update_rpm_max(self.bar_rpm_max, rpm_max)

        # Engine torque
        if self.wcfg["show_torque"]:
            torque = round(api.read.engine.torque(), 2)
            self.update_torque(self.bar_torque, torque)

        # Engine power
        if self.wcfg["show_power"]:
            power = round(calc.engine_power(
                api.read.engine.torque(), api.read.engine.rpm()), 2)
            self.update_power(self.bar_power, power)

    # GUI update methods
    def update_oil(self, target, data):
        """Oil temperature"""
        if target.last != data:
            target.last = data
            target.text = f"O{self.unit_temp(data): >6.1f}°"
            target.bg = self.bar_style_oil[data >= self.wcfg["overheat_threshold_oil"]]
            target.update()

    def update_water(self, target, data):
        """Water temperature"""
        if target.last != data:
            target.last = data
            target.text = f"W{self.unit_temp(data): >6.1f}°"
            target.bg = self.bar_style_water[data >= self.wcfg["overheat_threshold_water"]]
            target.update()

    def update_turbo(self, target, data):
        """Turbo pressure"""
        if target.last != data:
            target.last = data
            text = f"{self.unit_pres(data * 0.001):03.3f}"[:5]
            target.text = f"{text}{self.symbol_pres}"
            target.update()

    def update_rpm(self, target, data):
        """Engine RPM"""
        if target.last != data:
            target.last = data
            target.text = f"{data: >5}rpm"
            target.update()

    def update_rpm_max(self, target, data):
        """Engine RPM maximum"""
        if target.last != data:
            target.last = data
            target.text = f"{data: >5}max"
            target.update()

    def update_torque(self, target, data):
        """Engine torque"""
        if target.last != data:
            target.last = data
            text = f"{data: >6.2f}"[:6]
            target.text = f"{text}Nm"
            target.update()

    def update_power(self, target, data):
        """Engine power"""
        if target.last != data:
            target.last = data
            text = f"{self.unit_power(data): >6.2f}"[:6]
            target.text = f"{text}{self.symbol_power}"
            target.update()
