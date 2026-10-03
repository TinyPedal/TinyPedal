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

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        bar_width = font_m.width * 8 + bar_padx
        self.drive_wheel_allocation = self.wcfg["drive_wheel_allocation"]

        # Config units
        self.unit_power = units.set_unit_power(self.cfg.units["power_unit"])
        self.symbol_power = units.set_symbol_power(self.cfg.units["power_unit"])
        self.unit_pres = units.set_unit_pressure(self.cfg.units["turbo_pressure_unit"])
        self.symbol_pres = units.set_symbol_pressure(self.cfg.units["turbo_pressure_unit"])
        self.unit_weight = units.set_unit_weight(self.cfg.units["weight_unit"])

        # Turbo pressure
        if self.wcfg["show_turbo_pressure"]:
            self.bar_turbo = self.set_rawtext(
                text="Turbo",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_turbo"],
                bg_color=self.wcfg["background_color_turbo"],
            )
            self.set_primary_orient(
                target=self.bar_turbo,
                column=self.wcfg["display_order_turbo"],
            )

        # Engine RPM
        if self.wcfg["show_rpm"]:
            self.bar_rpm = self.set_rawtext(
                text="RPM",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_rpm"],
                bg_color=self.wcfg["background_color_rpm"],
            )
            self.set_primary_orient(
                target=self.bar_rpm,
                column=self.wcfg["display_order_rpm"],
            )

        # Engine RPM maximum
        if self.wcfg["show_rpm_maximum"]:
            self.bar_rpm_max = self.set_rawtext(
                text="MAX RPM",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_rpm_maximum"],
                bg_color=self.wcfg["background_color_rpm_maximum"],
            )
            self.set_primary_orient(
                target=self.bar_rpm_max,
                column=self.wcfg["display_order_rpm_maximum"],
            )

        # Engine torque
        if self.wcfg["show_torque"]:
            self.bar_torque = self.set_rawtext(
                text="TORQUE",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_torque"],
                bg_color=self.wcfg["background_color_torque"],
            )
            self.set_primary_orient(
                target=self.bar_torque,
                column=self.wcfg["display_order_torque"],
            )

        # Engine power
        if self.wcfg["show_power"]:
            self.bar_power = self.set_rawtext(
                text="POWER",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_power"],
                bg_color=self.wcfg["background_color_power"],
            )
            self.set_primary_orient(
                target=self.bar_power,
                column=self.wcfg["display_order_power"],
            )

        # Power to weight ratio
        if self.wcfg["show_power_to_weight_ratio"]:
            self.bar_pwratio = self.set_rawtext(
                text="PW RATIO",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_power_to_weight_ratio"],
                bg_color=self.wcfg["background_color_power_to_weight_ratio"],
            )
            self.set_primary_orient(
                target=self.bar_pwratio,
                column=self.wcfg["display_order_power_to_weight_ratio"],
            )

        # Drive ratio
        if self.wcfg["show_drive_ratio"]:
            self.bar_dwratio = self.set_rawtext(
                text="DW RATIO",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_drive_ratio"],
                bg_color=self.wcfg["background_color_drive_ratio"],
            )
            self.set_primary_orient(
                target=self.bar_dwratio,
                column=self.wcfg["display_order_drive_ratio"],
            )

        # Last data
        self.post_update()

    def post_update(self):
        self.ema_power = 0
        self.max_power_kw = 0

    def timerEvent(self, event):
        """Update when vehicle on track"""
        rpm = api.read.engine.rpm()
        torque = api.read.engine.torque()
        if torque:
            power_kw = calc.engine_power(torque, rpm)
        else:
            power_kw = 0.0
            # Calculate power & torque based on energy consumption if torque n/a
            max_ve = api.read.engine.max_virtual_energy()
            if max_ve > 0:
                power_kw = minfo.energy.rateOfConsumption * max_ve / 100_000
                torque = calc.engine_torque(power_kw, rpm)

        # Turbo pressure
        if self.wcfg["show_turbo_pressure"]:
            turbo = int(api.read.engine.turbo())
            self.update_turbo(self.bar_turbo, turbo)

        # Engine RPM
        if self.wcfg["show_rpm"]:
            self.update_rpm(self.bar_rpm, int(rpm))

        # Engine RPM maximum
        if self.wcfg["show_rpm_maximum"]:
            rpm_max = int(api.read.engine.rpm_max())
            self.update_rpm_max(self.bar_rpm_max, rpm_max)

        # Engine torque
        if self.wcfg["show_torque"]:
            self.update_torque(self.bar_torque, torque)

        # Engine power
        if self.wcfg["show_power"]:
            self.update_power(self.bar_power, power_kw)

        # Power to weight ratio
        if self.wcfg["show_power_to_weight_ratio"]:
            total_static_weight = minfo.wheels.totalStaticWeight
            self.ema_power += 0.2 * (power_kw - self.ema_power)
            if self.max_power_kw < self.ema_power:
                self.max_power_kw = self.ema_power
            self.update_power_ratio(self.bar_pwratio, self.max_power_kw, total_static_weight)

        # Drive ratio
        if self.wcfg["show_drive_ratio"]:
            wheel_speed = api.read.wheel.rotation()
            if self.drive_wheel_allocation == 0:
                wheel_speed = abs(wheel_speed[2] + wheel_speed[3]) / 2
                drive_alloc = "R"
            elif self.drive_wheel_allocation == 1:
                wheel_speed = abs(wheel_speed[0] + wheel_speed[1]) / 2
                drive_alloc = "F"
            else:
                wheel_speed = abs(calc.mean(wheel_speed))
                drive_alloc = "A"
            if wheel_speed > 1:
                engine_speed = rpm * 0.104719755  # rad/s
                drive_ratio = engine_speed / wheel_speed
            else:
                drive_ratio = 0.0
            self.update_drive_ratio(self.bar_dwratio, drive_ratio, drive_alloc)

    # GUI update methods
    def update_turbo(self, target, data):
        """Turbo pressure"""
        if target.last != data:
            target.last = data
            text = f"{self.unit_pres(data * 0.001):03.3f}"
            target.text = f"{text:.5}{self.symbol_pres}"
            target.update()

    def update_rpm(self, target, data):
        """Engine RPM"""
        if target.last != data:
            target.last = data
            target.text = f"{data:>5}rpm"
            target.update()

    def update_rpm_max(self, target, data):
        """Engine RPM maximum"""
        if target.last != data:
            target.last = data
            target.text = f"{data:>5}max"
            target.update()

    def update_torque(self, target, data):
        """Engine torque"""
        if target.last != data:
            target.last = data
            text = f"{data:>6.2f}"
            target.text = f"{text:.6}Nm"
            target.update()

    def update_power(self, target, data):
        """Engine power"""
        if target.last != data:
            target.last = data
            text = f"{self.unit_power(data):>6.2f}"
            target.text = f"{text:.6}{self.symbol_power}"
            target.update()

    def update_power_ratio(self, target, *data):
        """Power to weight ratio"""
        if target.last != data:
            target.last = data
            if data[1] > 0:
                ratio = self.unit_power(data[0]) / self.unit_weight(data[1])
            else:
                ratio = 0.0
            text = f"{ratio:.3f}"
            target.text = f"{text:.5}p/w"
            target.update()

    def update_drive_ratio(self, target, data, drive_alloc):
        """Drive ratio"""
        if target.last != data:
            target.last = data
            text = f"{data:.3f}"
            target.text = f"{text:.5}:1{drive_alloc}"
            target.update()
