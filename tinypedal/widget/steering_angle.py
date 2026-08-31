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
Steering angle Widget
"""

from .. import calculation as calc
from .. import units
from ..api_control import api
from ..const_common import TEXT_NA
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
        bar_width = font_m.width * 6 + bar_padx
        self.wheeltrack_front = max(self.wcfg["wheel_track_front"], 1)
        self.wheelbase = max(self.wcfg["wheelbase"], 1)

        # Config units
        self.unit_dist = units.set_unit_distance(self.cfg.units["distance_unit"])
        self.symbol_dist = units.set_symbol_distance(self.cfg.units["distance_unit"])

        # Steering angle
        if self.wcfg["show_steering_angle"]:
            self.bar_steer_angle = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_steering_angle"],
                bg_color=self.wcfg["background_color_steering_angle"],
            )
            self.set_primary_orient(
                target=self.bar_steer_angle,
                column=self.wcfg["display_order_steering_angle"],
            )

        # Front wheel angle
        if self.wcfg["show_front_wheel_angle"]:
            self.bar_wheel_angle = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_front_wheel_angle"],
                bg_color=self.wcfg["background_color_front_wheel_angle"],
            )
            self.set_primary_orient(
                target=self.bar_wheel_angle,
                column=self.wcfg["display_order_front_wheel_angle"],
            )

        # Steering ratio
        if self.wcfg["show_steering_ratio"]:
            self.bar_steer_ratio = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_steering_ratio"],
                bg_color=self.wcfg["background_color_steering_ratio"],
            )
            self.set_primary_orient(
                target=self.bar_steer_ratio,
                column=self.wcfg["display_order_steering_ratio"],
            )

        # Ackermann percentage
        if self.wcfg["show_ackermann_percentage"]:
            self.bar_ackermann_percentage = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_ackermann_percentage"],
                bg_color=self.wcfg["background_color_ackermann_percentage"],
            )
            self.set_primary_orient(
                target=self.bar_ackermann_percentage,
                column=self.wcfg["display_order_ackermann_percentage"],
            )

        # Slip angle difference
        if self.wcfg["show_slip_angle_difference"]:
            self.bar_style_diff_slip_angle = (
                (
                    self.wcfg["font_color_neutral_steer"],
                    self.wcfg["background_color_neutral_steer"],
                ),
                (
                    self.wcfg["font_color_oversteer"],
                    self.wcfg["background_color_oversteer"],
                ),
                (
                    self.wcfg["font_color_understeer"],
                    self.wcfg["background_color_understeer"],
                ),
            )
            self.bar_diff_slip_angle = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.bar_style_diff_slip_angle[0][0],
                bg_color=self.bar_style_diff_slip_angle[0][1],
            )
            self.set_primary_orient(
                target=self.bar_diff_slip_angle,
                column=self.wcfg["display_order_slip_angle_difference"],
            )
            self.ema_diff_slip_angle = 0.0

        # Yaw rate
        if self.wcfg["show_yaw_rate"]:
            self.bar_yaw_rate = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_yaw_rate"],
                bg_color=self.wcfg["background_color_yaw_rate"],
            )
            self.set_primary_orient(
                target=self.bar_yaw_rate,
                column=self.wcfg["display_order_yaw_rate"],
            )

        # Turning radius
        if self.wcfg["show_turning_radius"]:
            self.bar_turning_radius = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_turning_radius"],
                bg_color=self.wcfg["background_color_turning_radius"],
            )
            self.set_primary_orient(
                target=self.bar_turning_radius,
                column=self.wcfg["display_order_turning_radius"],
            )

        # Turning radius under slip angle
        if self.wcfg["show_turning_radius_under_slip_angle"]:
            self.bar_slip_radius = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_turning_radius_under_slip_angle"],
                bg_color=self.wcfg["background_color_turning_radius_under_slip_angle"],
            )
            self.set_primary_orient(
                target=self.bar_slip_radius,
                column=self.wcfg["display_order_turning_radius_under_slip_angle"],
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Steering wheel rotation
        if self.wcfg["manual_steering_range"] > 0:
            steering_range = self.wcfg["manual_steering_range"]
        else:
            steering_range = api.read.inputs.steering_range_physical()

        steer_angle = api.read.inputs.steering_raw() * steering_range * 0.5
        wheel_angle_front_average = minfo.wheels.averageFrontToeAngle
        diff_slip_angle = minfo.wheels.slipAngleDifference

        # Steering angle
        if self.wcfg["show_steering_angle"]:
            self.update_steering_angle(self.bar_steer_angle, steer_angle)

        # Front wheel angle
        if self.wcfg["show_front_wheel_angle"]:
            self.update_wheel_angle(self.bar_wheel_angle, wheel_angle_front_average)

        # Steering ratio
        if self.wcfg["show_steering_ratio"]:
            steer_ratio = calc.steering_ratio(steer_angle, wheel_angle_front_average)
            self.update_steering_ratio(self.bar_steer_ratio, steer_ratio)

        # Ackermann percentage
        if self.wcfg["show_ackermann_percentage"]:
            ackermann_percent = calc.ackermann_percentage(
                minfo.wheels.toeAngle[0],
                minfo.wheels.toeAngle[1],
                self.wheeltrack_front,
                self.wheelbase,
            )
            self.update_ackermann_percentage(self.bar_ackermann_percentage, ackermann_percent)

        # Slip angle difference
        if self.wcfg["show_slip_angle_difference"]:
            self.ema_diff_slip_angle += 0.2 * (diff_slip_angle - self.ema_diff_slip_angle)
            self.update_slip_angle_difference(self.bar_diff_slip_angle, self.ema_diff_slip_angle)

        # Yaw rate
        if self.wcfg["show_yaw_rate"]:
            self.update_yaw_rate(self.bar_yaw_rate, minfo.wheels.yawRate)

        # Turning radius
        if self.wcfg["show_turning_radius"]:
            turning_radius = calc.turning_radius(
                wheel_angle_front_average,
                self.wheelbase,
            )
            self.update_turning_radius(self.bar_turning_radius, turning_radius)

        # Turning radius under slip angle
        if self.wcfg["show_turning_radius_under_slip_angle"]:
            slip_radius = calc.turning_radius(
                wheel_angle_front_average + (minfo.wheels.averageFrontSlipAngle - minfo.wheels.averageRearSlipAngle),
                self.wheelbase,
            )
            self.update_turning_radius(self.bar_slip_radius, slip_radius)

    # GUI update methods
    def update_steering_angle(self, target, data):
        """Steering angle"""
        if target.last != data:
            target.last = data
            target.text = f"{data:+.0f}°"
            target.update()

    def update_wheel_angle(self, target, data):
        """Wheel angle"""
        if target.last != data:
            target.last = data
            target.text = f"{data:+.1f}°"
            target.update()

    def update_steering_ratio(self, target, data):
        """Steering ratio"""
        if target.last != data:
            target.last = data
            text_ratio = f"{abs(data):.2f}"
            target.text = f"{text_ratio:.4}:1"
            target.update()

    def update_ackermann_percentage(self, target, data):
        """Ackermann percentage"""
        if target.last != data:
            target.last = data
            if abs(data) > 9.99:
                data = 0.0
            target.text = f"{data:+.0%}"
            target.update()

    def update_slip_angle_difference(self, target, data):
        """Slip angle difference"""
        if target.last != data:
            target.last = data
            if data > self.wcfg["minimum_understeer_slip_angle_difference"]:
                color_index = 2
            elif data < self.wcfg["minimum_oversteer_slip_angle_difference"]:
                color_index = 1
            else:
                color_index = 0
            target.text = f"{data:+.1f}°"
            target.fg, target.bg = self.bar_style_diff_slip_angle[color_index]
            target.update()

    def update_yaw_rate(self, target, data):
        """Yaw rate"""
        if target.last != data:
            target.last = data
            target.text = f"{calc.degrees(data):+.0f}°/s"
            target.update()

    def update_turning_radius(self, target, data):
        """Turning radius"""
        if target.last != data:
            target.last = data
            radius = calc.sym_max(self.unit_dist(data * 0.001), 9999)
            target.text = f"{radius:+.0f}{self.symbol_dist}"
            target.update()
