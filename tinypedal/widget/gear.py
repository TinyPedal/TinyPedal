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
Gear Widget
"""

from .. import units
from ..api_control import api
from ..module_info import minfo
from ._base import Overlay
from ._painter import GearGaugeBar, ProgressBar, TextBar


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
            self.wcfg["font_weight_gear"]
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)

        if self.wcfg["show_speed_below_gear"]:
            font_scale_speed = self.wcfg["font_scale_speed"]
        else:
            font_scale_speed = 1
        font_speed = self.config_font(
            self.wcfg["font_name"],
            round(self.wcfg["font_size"] * font_scale_speed),
            self.wcfg["font_weight_speed"]
        )

        font_rpm = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size_rpm"],
            self.wcfg["font_weight_rpm"]
        )
        font_batt = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size_battery"],
            self.wcfg["font_weight_battery"]
        )

        # Config units
        self.unit_speed = units.set_unit_speed(self.cfg.units["speed_unit"])

        # Gear gauge
        (limiter_width, gauge_width, gauge_height, gear_size, speed_size
         ) = self.set_gauge_size(font_m, font_scale_speed)
        self.gauge_color = (
            self.wcfg["bkg_color"],  # 0, -4 flicker
            self.wcfg["rpm_color_safe"],  # 1
            self.wcfg["rpm_color_redline"],  # 2
            self.wcfg["rpm_color_over_rev"],  # 3
        )
        self.bar_gauge = GearGaugeBar(
            self,
            width=gauge_width,
            height=gauge_height,
            font_speed=font_speed,
            gear_size=gear_size,
            speed_size=speed_size,
            fg_color=self.wcfg["font_color"],
            bg_color=self.wcfg["bkg_color"],
            show_speed=self.wcfg["show_speed"],
        )
        self.set_primary_orient(
            target=self.bar_gauge,
            column=self.wcfg["column_index_gauge"],
        )

        # RPM bar
        if self.wcfg["show_rpm_bar"]:
            font_rpm_m = self.get_font_metrics(font_rpm)
            self.bar_rpmbar = ProgressBar(
                self,
                width=gauge_width,
                height=max(self.wcfg["rpm_bar_height"], 1),
                offset_x=self.wcfg["rpm_reading_offset_x"],
                offset_y=font_rpm_m.voffset,
                font=font_rpm,
                input_color=self.wcfg["rpm_bar_color"],
                fg_color=self.wcfg["font_color_rpm"],
                bg_color=self.wcfg["rpm_bar_bkg_color"],
                decimals=self.wcfg["rpm_decimal_places"],
                show_reading=self.wcfg["show_rpm_reading"],
                align=self.set_text_alignment(self.wcfg["rpm_reading_text_alignment"]),
                right_side=self.wcfg["show_inverted_rpm"],
            )
            self.set_primary_orient(
                target=self.bar_rpmbar,
                column=self.wcfg["column_index_rpm"],
            )

        # Battery bar
        if self.wcfg["show_battery_bar"]:
            font_batt_m = self.get_font_metrics(font_batt)
            self.battbar_color = (
                self.wcfg["battery_bar_color"],
                self.wcfg["battery_bar_color_regen"],
                self.wcfg["warning_color_low_battery"],
                self.wcfg["warning_color_high_battery"],
            )
            self.bar_battbar = ProgressBar(
                self,
                width=gauge_width,
                height=max(self.wcfg["battery_bar_height"], 1),
                offset_x=self.wcfg["battery_reading_offset_x"],
                offset_y=font_batt_m.voffset,
                font=font_batt,
                input_color=self.battbar_color[0],
                fg_color=self.wcfg["font_color_battery"],
                bg_color=self.wcfg["battery_bar_bkg_color"],
                decimals=self.wcfg["battery_decimal_places"],
                show_reading=self.wcfg["show_battery_reading"],
                align=self.set_text_alignment(self.wcfg["battery_reading_text_alignment"]),
                right_side=self.wcfg["show_inverted_battery"],
            )
            self.bar_battbar.state = None
            self.set_primary_orient(
                target=self.bar_battbar,
                column=self.wcfg["column_index_battery"],
            )

        # Speed limiter
        if self.wcfg["show_speed_limiter"]:
            self.bar_limiter = TextBar(
                self,
                width=limiter_width,
                height=gauge_height,
                font_offset=font_m.voffset,
                fg_color=self.wcfg["font_color_speed_limiter"],
                bg_color=self.wcfg["bkg_color_speed_limiter"],
                text=self.wcfg["speed_limiter_text"],
            )
            self.set_primary_orient(
                target=self.bar_limiter,
                column=self.wcfg["column_index_gauge"],
                row=1,
            )

        # Last data
        self.flicker = 0
        self.shifting_timer_start = 0
        self.shifting_timer = 0
        self.rpm_safe = 0
        self.rpm_red = 0
        self.rpm_crit = 0
        self.rpm_range = 0
        self.rpm_max = 0
        self.gear_max = 0
        self.last_gear = 0

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # RPM reference
        rpm_max = api.read.engine.rpm_max()
        if self.rpm_max != rpm_max:
            self.rpm_max = rpm_max
            self.rpm_safe = int(rpm_max * self.wcfg["rpm_multiplier_safe"])
            self.rpm_red = int(rpm_max * self.wcfg["rpm_multiplier_redline"])
            self.rpm_crit = int(rpm_max * self.wcfg["rpm_multiplier_critical"])
            self.rpm_range = rpm_max - self.rpm_safe
            self.gear_max = api.read.engine.gear_max()

        # Shifting timer
        gear = api.read.engine.gear()
        lap_etime = api.read.timing.elapsed()
        if self.last_gear != gear:
            self.last_gear = gear
            self.shifting_timer_start = lap_etime
        self.shifting_timer = lap_etime - self.shifting_timer_start

        # Gauge
        rpm = api.read.engine.rpm()
        speed = api.read.vehicle.speed()
        self.update_gauge(self.bar_gauge, rpm, gear, speed)

        # RPM bar
        if self.wcfg["show_rpm_bar"]:
            self.update_rpmbar(self.bar_rpmbar, rpm)

        # Battery bar
        if self.wcfg["show_battery_bar"]:
            battery = minfo.hybrid.batteryCharge
            motor_state = minfo.hybrid.motorState
            self.update_battbar(self.bar_battbar, battery, motor_state)

        # Speed limier
        if self.wcfg["show_speed_limiter"]:
            limiter = api.read.switch.speed_limiter()
            self.update_limiter(self.bar_limiter, limiter)

    # GUI update methods
    def update_gauge(self, target, rpm, gear, speed):
        """Gauge bar"""
        gauge_state = rpm + gear + speed
        if target.last != gauge_state:
            target.last = gauge_state
            color_index = self.color_rpm(rpm, gear, speed)
            target.update_input(
                gear,
                self.unit_speed(speed),
                color_index,
                self.gauge_color[color_index],
            )

    def update_rpmbar(self, target, data):
        """RPM bar"""
        if target.last != data:
            target.last = data
            rpm_offset = data - self.rpm_safe
            if self.rpm_range > 0 <= rpm_offset:  # show only above offset
                rpm_percent = rpm_offset / self.rpm_range
            else:
                rpm_percent = 0
            target.update_input(rpm_percent, data)

    def update_battbar(self, target, data, state):
        """Battery bar"""
        available = state > 0  # available check only
        if target.state != available:
            target.state = available
            # Hide if electric motor unavailable
            target.setHidden(not available)
        charge = state + data  # add state to finalize last change
        if target.last != charge:
            target.last = charge
            if state == 3:
                color_index = 1
            elif data >= self.wcfg["high_battery_threshold"]:
                color_index = 3
            elif data <= self.wcfg["low_battery_threshold"]:
                color_index = 2
            else:
                color_index = 0
            target.input_color = self.battbar_color[color_index]
            target.update_input(data * 0.01, data)

    def update_limiter(self, target, data):
        """Limiter"""
        if target.last != data:
            target.last = data
            target.setHidden(not data)

    # Additional methods
    def color_rpm(self, rpm, gear, speed):
        """RPM indicator color"""
        self.flicker = not self.flicker
        if (self.wcfg["show_rpm_flickering_above_critical"] and
            self.flicker and
            gear < self.gear_max and
            rpm >= self.rpm_crit):
            return -4
        if (not gear and
            speed > self.wcfg["neutral_warning_speed_threshold"] and
            self.shifting_timer >= self.wcfg["neutral_warning_time_threshold"]
            ) or rpm > self.rpm_max:
            return 3
        if rpm >= self.rpm_red:
            return 2
        if rpm >= self.rpm_safe:
            return 1
        return 0

    def set_gauge_size(self, font_m, font_scale_speed):
        """Set gauge size"""
        inner_gap = self.wcfg["inner_gap"]
        padx = round(font_m.width * self.wcfg["bar_padding_horizontal"])
        pady = round(font_m.capital * self.wcfg["bar_padding_vertical"])
        limiter_width = (
            font_m.width * len(self.wcfg["speed_limiter_text"])
            + round(font_m.width * self.wcfg["speed_limiter_padding_horizontal"]) * 2)

        gear_width = font_m.width + padx * 2
        gear_height = font_m.capital + pady * 2
        speed_width = round(font_m.width * 3 * font_scale_speed) + padx * 2
        speed_height = round(font_m.capital * font_scale_speed) + pady * 2

        if self.wcfg["show_speed_below_gear"]:
            gauge_width = gear_width
            gauge_height = gear_height + (inner_gap + speed_height) * self.wcfg["show_speed"]
            speed_size = (0, gear_height + inner_gap + font_m.voffset, gear_width, speed_height)

        else:
            gauge_width = gear_width + (inner_gap + speed_width) * self.wcfg["show_speed"]
            gauge_height = gear_height
            speed_size = (gear_width + inner_gap, font_m.voffset, speed_width, gear_height)
        gear_size = (0, font_m.voffset, gear_width, gear_height)
        return limiter_width, gauge_width, gauge_height, gear_size, speed_size
