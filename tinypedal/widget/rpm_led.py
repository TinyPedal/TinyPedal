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
RPM LED Widget
"""

from PySide2.QtCore import QRect, Qt
from PySide2.QtGui import QBrush, QPainter, QPen

from ..api_control import api
from ..const_common import FLOAT_INF
from ._base import Overlay
from ._common import warning_flash


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)

        # Config variable
        self.double_side_led = self.wcfg["enable_double_side_led"]
        self.display_margin = max(int(self.wcfg["display_margin"]), 0)
        self.inner_gap = max(int(self.wcfg["inner_gap"]), 0)

        self.led_width = max(int(self.wcfg["led_width"]), 1)
        self.led_height = max(int(self.wcfg["led_height"]), 1)
        self.led_offset = self.led_width + self.inner_gap
        self.led_radius = max(self.wcfg["led_radius"], 0)
        self.max_led = max(int(self.wcfg["number_of_led"]), 3)

        display_width = self.led_width * self.max_led + self.inner_gap * (self.max_led - 1)
        display_height = self.led_height + self.display_margin * 2

        if self.double_side_led:
            display_width += display_width + self.inner_gap + self.display_margin * 2
        else:
            display_width += self.display_margin * 2

        self.display_width = display_width

        # Config canvas
        self.resize(display_width, display_height)

        self.rect_led = QRect(0, 0, self.led_width, self.led_height)
        self.rect_background = QRect(0, 0, display_width, display_height)

        self.pen_led = QPen()
        self.pen_led.setColor(self.wcfg["led_outline_color"])
        self.pen_led.setWidth(self.wcfg["led_outline_width"])

        self.brush_led = (
            QBrush(self.wcfg["rpm_color_off"], Qt.SolidPattern),
            QBrush(self.wcfg["rpm_color_low"], Qt.SolidPattern),
            QBrush(self.wcfg["rpm_color_safe"], Qt.SolidPattern),
            QBrush(self.wcfg["rpm_color_redline"], Qt.SolidPattern),
            QBrush(self.wcfg["rpm_color_critical"], Qt.SolidPattern),
            QBrush(self.wcfg["rpm_color_over_rev"], Qt.SolidPattern),
            QBrush(self.wcfg["speed_limiter_flash_color"], Qt.SolidPattern),
        )

        if self.wcfg["show_speed_limiter_flash"]:
            self.warn_flash = warning_flash(
                self.wcfg["speed_limiter_flash_interval"],
                self.wcfg["speed_limiter_flash_interval"],
                FLOAT_INF,
            )

        # Last data
        self.flicker = False
        self.limiter = 0
        self.rpm_max = 0
        self.rpm_low = 0
        self.rpm_safe = 0
        self.rpm_redline = 0
        self.rpm_critical = 0
        self.rpm_overrev = 0
        self.rpm_scale = 0
        self.rpm = -1
        self.gear_max = 0

    def timerEvent(self, event):
        """Update when vehicle on track"""
        update_later = False

        # RPM reference
        rpm_max = api.read.engine.rpm_max()
        if self.rpm_max != rpm_max:
            self.rpm_max = rpm_max
            self.rpm_low = rpm_max * self.wcfg["rpm_multiplier_low"]
            # offset by rpm low
            self.rpm_safe = rpm_max * self.wcfg["rpm_multiplier_safe"] - self.rpm_low
            self.rpm_redline = rpm_max * self.wcfg["rpm_multiplier_redline"] - self.rpm_low
            self.rpm_critical = rpm_max * self.wcfg["rpm_multiplier_critical"] - self.rpm_low
            self.rpm_overrev = rpm_max * self.wcfg["rpm_multiplier_over_rev"] - self.rpm_low
            # Limit rpm range in low to critical
            self.rpm_scale = self.max_led / max(self.rpm_critical, 0.0000001)
            self.gear_max = api.read.engine.gear_max()

        # Update RPM
        rpm = api.read.engine.rpm()
        if self.rpm != rpm:
            self.rpm = rpm
            update_later = True

        # Update limiter state
        if self.wcfg["show_speed_limiter_flash"]:
            self.limiter = api.read.switch.speed_limiter()
            if self.limiter:
                update_later = True

        if update_later:
            self.update()

    # GUI update methods
    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if self.wcfg["show_background"]:
            painter.fillRect(self.rect_background, self.wcfg["bkg_color"])

        if self.wcfg["led_outline_width"] > 0:
            painter.setPen(self.pen_led)
        else:
            painter.setPen(Qt.NoPen)

        rpm = self.rpm - self.rpm_low

        # Set flicker state
        if self.wcfg["show_speed_limiter_flash"] and self.limiter:
            self.flicker = self.warn_flash.send(True)
        elif (
            self.wcfg["show_rpm_flickering_above_critical"]
            and rpm >= self.rpm_critical
            and api.read.engine.gear() < self.gear_max
        ):
            self.flicker = not self.flicker
        else:
            self.flicker = False

        self.draw_rpm_led(
            painter,
            rpm,
            self.rpm_scale,
            self.display_margin,
            self.display_margin,
            self.led_offset,
        )

        if self.double_side_led:
            self.draw_rpm_led(
                painter,
                rpm,
                self.rpm_scale,
                self.display_width - self.led_width - self.display_margin,
                self.display_margin,
                -self.led_offset,
            )

    def draw_rpm_led(self, painter, rpm, rpm_scale, x_offset, y_offset, led_offset):
        """Draw RPM LED"""
        rpm_scaled = rpm * rpm_scale

        for index in range(self.max_led):
            # Full
            if self.limiter:
                painter.setBrush(self.brush_led[6 if self.flicker else 0])
            elif rpm >= self.rpm_overrev:
                painter.setBrush(self.brush_led[0 if self.flicker else 5])  # over rev
            elif rpm >= self.rpm_critical:
                painter.setBrush(self.brush_led[0 if self.flicker else 4])  # critical
            # Progressive
            elif index < rpm_scaled:
                painter.setBrush(self.color_rpm_led(index / rpm_scale))
            # Off
            else:
                painter.setBrush(self.brush_led[0])

            painter.translate(x_offset, y_offset)
            if self.led_radius:
                painter.drawRoundedRect(self.rect_led, self.led_radius, self.led_radius)
            else:
                painter.drawRect(self.rect_led)
            painter.resetTransform()

            x_offset += led_offset

    def color_rpm_led(self, rpm: float):
        """Set RPM LED color"""
        if rpm < 0:
            return self.brush_led[0]  # off
        if rpm < self.rpm_safe:
            return self.brush_led[1]  # low
        if rpm < self.rpm_redline:
            return self.brush_led[2]  # safe
        if rpm < self.rpm_critical:
            return self.brush_led[3]  # redline
        return self.brush_led[0]
