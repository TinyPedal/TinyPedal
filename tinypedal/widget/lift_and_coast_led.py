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
Lift and coast LED Widget
"""

from PySide2.QtCore import QRect, Qt
from PySide2.QtGui import QBrush, QPainter, QPen

from ..api_control import api
from ._base import Overlay


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)

        # Config variable
        self.display_margin = max(int(self.wcfg["display_margin"]), 0)
        inner_gap = max(int(self.wcfg["inner_gap"]), 0)

        self.led_width = max(int(self.wcfg["led_width"]), 1)
        self.led_height = max(int(self.wcfg["led_height"]), 1)
        self.led_offset = self.led_width + inner_gap
        self.led_radius = max(self.wcfg["led_radius"], 0)
        self.max_led = max(int(self.wcfg["number_of_led"]), 3)

        display_width = self.led_width * self.max_led + inner_gap * (self.max_led - 1) + self.display_margin * 2
        display_height = self.led_height + self.display_margin * 2

        # Config canvas
        self.vertical = self.wcfg["display_orientation"] % 2
        if self.vertical:
            display_width, display_height = display_height, display_width

        self.rect_viewport = self.set_viewport_orientation(self.wcfg["display_orientation"], display_width, display_height)
        self.resize(display_width, display_height)

        self.rect_led = QRect(0, 0, self.led_width, self.led_height)
        self.rect_background = QRect(0, 0, display_width, display_height)

        if self.wcfg["led_outline_width"] > 0:
            self.pen_led = QPen()
            self.pen_led.setColor(self.wcfg["led_outline_color"])
            self.pen_led.setWidth(self.wcfg["led_outline_width"])
        else:
            self.pen_led = Qt.NoPen

        self.brush_led = (
            QBrush(self.wcfg["lift_and_coast_color_off"], Qt.SolidPattern),
            QBrush(self.wcfg["lift_and_coast_color_low"], Qt.SolidPattern),
            QBrush(self.wcfg["lift_and_coast_color_critical"], Qt.SolidPattern),
            QBrush(self.wcfg["tc_activation_color"], Qt.SolidPattern),
            QBrush(self.wcfg["abs_activation_color"], Qt.SolidPattern),
        )

        # Last data
        self.lico_critical = self.wcfg["lift_and_coast_multiplier_critical"]
        self.lico = -1
        self.tc_active = False
        self.abs_active = False

    def timerEvent(self, event):
        """Update when vehicle on track"""
        update_later = False

        # Lift and coast
        lico = api.read.engine.lift_and_coast_progress()
        if self.lico != lico:
            self.lico = lico
            update_later = True

        # TC active
        tc_active = api.read.switch.tc_active()
        if self.tc_active != tc_active:
            self.tc_active = tc_active
            update_later = True

        # ABS active
        abs_active = api.read.switch.abs_active()
        if self.abs_active != abs_active:
            self.abs_active = abs_active
            update_later = True

        if update_later:
            self.update()

    # GUI update methods
    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setViewport(self.rect_viewport)

        if self.wcfg["show_background"]:
            painter.fillRect(self.rect_background, self.wcfg["background_color"])

        painter.setPen(self.pen_led)
        self.draw_lico_led(
            painter,
            self.lico,
            self.display_margin,
            self.display_margin,
            self.led_offset,
        )

    def draw_lico_led(self, painter, lico, x_offset, y_offset, led_offset):
        """Draw LICO LED"""
        lico_scaled = lico * self.max_led
        full_light = True

        if self.abs_active:
            painter.setBrush(self.brush_led[4])
        elif self.tc_active:
            painter.setBrush(self.brush_led[3])
        elif lico <= 0:
            painter.setBrush(self.brush_led[0])
        else:
            full_light = False

        if self.vertical:
            painter.translate(y_offset, x_offset)
        else:
            painter.translate(x_offset, y_offset)

        for index in range(self.max_led):
            if not full_light:
                # Progressive
                if index < lico_scaled:
                    painter.setBrush(self.brush_led[(lico > self.lico_critical) + 1])
                # Off
                else:
                    painter.setBrush(self.brush_led[0])
            # Draw led
            if self.led_radius:
                painter.drawRoundedRect(self.rect_led, self.led_radius, self.led_radius)
            else:
                painter.drawRect(self.rect_led)
            # Set next offset
            if self.vertical:
                painter.translate(0, led_offset)
            else:
                painter.translate(led_offset, 0)
        # Reset
        painter.resetTransform()

    def set_viewport_orientation(self, orientation: int, display_width: int, display_height: int):
        """Set viewport orientation"""
        orientation -= orientation // 4 * 4
        if orientation == 1:  # vertical, bottom to top
            return QRect(0, display_height, display_width, -display_height)
        if orientation == 2:  # horizontal, right to left
            return QRect(display_width, 0, -display_width, display_height)
        if orientation == 3:  # vertical, top to bottom
            return QRect(0, 0, display_width, display_height)
        # horizontal, left to right
        return QRect(0, 0, display_width, display_height)
