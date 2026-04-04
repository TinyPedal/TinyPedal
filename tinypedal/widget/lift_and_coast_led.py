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
from PySide2.QtWidgets import QWidget

from ..api_control import api
from ._base import Overlay


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout(gap=self.wcfg["double_side_led_gap"])
        self.set_primary_layout(layout=layout)

        # Config variable
        self.double_side_led = self.wcfg["enable_double_side_led"]

        # LEDs
        self.bar_lico_left = LEDBar(
            self,
            led_width=self.wcfg["led_width"],
            led_height=self.wcfg["led_height"],
            led_radius=self.wcfg["led_radius"],
            led_count=self.wcfg["number_of_led"],
            margin=self.wcfg["display_margin"],
            inner_gap=self.wcfg["inner_gap"],
            orientation=self.wcfg["display_orientation"],
            show_background=self.wcfg["show_background"],
            background_color=self.wcfg["background_color"],
            led_outline_color=self.wcfg["led_outline_color"],
            led_outline_width=self.wcfg["led_outline_width"],
            lift_and_coast_color_off=self.wcfg["lift_and_coast_color_off"],
            lift_and_coast_color_low=self.wcfg["lift_and_coast_color_low"],
            lift_and_coast_color_critical=self.wcfg["lift_and_coast_color_critical"],
            tc_activation_color=self.wcfg["tc_activation_color"],
            abs_activation_color=self.wcfg["abs_activation_color"],
            lift_and_coast_multiplier_critical=self.wcfg["lift_and_coast_multiplier_critical"],
        )
        self.set_primary_orient(
            target=self.bar_lico_left,
            column=0,
            default=1,
        )

        if self.double_side_led:
            orientation = self.wcfg["display_orientation"]
            mirror_orientation = orientation if orientation % 2 else orientation + 2
            self.bar_lico_right = LEDBar(
                self,
                led_width=self.wcfg["led_width"],
                led_height=self.wcfg["led_height"],
                led_radius=self.wcfg["led_radius"],
                led_count=self.wcfg["number_of_led"],
                margin=self.wcfg["display_margin"],
                inner_gap=self.wcfg["inner_gap"],
                orientation=mirror_orientation,
                show_background=self.wcfg["show_background"],
                background_color=self.wcfg["background_color"],
                led_outline_color=self.wcfg["led_outline_color"],
                led_outline_width=self.wcfg["led_outline_width"],
                lift_and_coast_color_off=self.wcfg["lift_and_coast_color_off"],
                lift_and_coast_color_low=self.wcfg["lift_and_coast_color_low"],
                lift_and_coast_color_critical=self.wcfg["lift_and_coast_color_critical"],
                tc_activation_color=self.wcfg["tc_activation_color"],
                abs_activation_color=self.wcfg["abs_activation_color"],
                lift_and_coast_multiplier_critical=self.wcfg["lift_and_coast_multiplier_critical"],
            )
            self.set_primary_orient(
                target=self.bar_lico_right,
                column=1,
                default=1,
            )

        # Last data
        self.lico = None
        self.tc_active = None
        self.abs_active = None

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
            self.bar_lico_left.lico = lico
            self.bar_lico_left.tc_active = tc_active
            self.bar_lico_left.abs_active = abs_active
            self.bar_lico_left.update()

            if self.double_side_led:
                self.bar_lico_right.lico = lico
                self.bar_lico_right.tc_active = tc_active
                self.bar_lico_right.abs_active = abs_active
                self.bar_lico_right.update()


class LEDBar(QWidget):
    """LED bar"""

    def __init__(
        self,
        parent,
        led_width: int = 0,
        led_height: int = 0,
        led_radius: float = 0,
        led_count: int = 0,
        margin: int = 0,
        inner_gap: int = 0,
        orientation: int = 0,
        show_background: bool = False,
        background_color: str = "",
        led_outline_color: str = "",
        led_outline_width: int = 0,
        lift_and_coast_color_off: str = "",
        lift_and_coast_color_low: str = "",
        lift_and_coast_color_critical: str = "",
        tc_activation_color: str = "",
        abs_activation_color: str = "",
        lift_and_coast_multiplier_critical: float = 0.8,
    ):
        super().__init__(parent)
        self.show_background = show_background
        self.background_color = background_color
        self.margin = max(margin, 0)
        self.led_radius = max(led_radius, 0)
        self.led_count = max(int(led_count), 3)
        led_width = max(int(led_width), 1)
        led_height = max(int(led_height), 1)
        inner_gap = max(int(inner_gap), 0)

        # Config canvas
        self.vertical = orientation % 2
        if self.vertical:
            self.led_offset = led_height + inner_gap
            display_width = led_width + self.margin * 2
            display_height = led_height * self.led_count + inner_gap * (self.led_count - 1) + self.margin * 2
        else:
            self.led_offset = led_width + inner_gap
            display_width = led_width * self.led_count + inner_gap * (self.led_count - 1) + self.margin * 2
            display_height = led_height + self.margin * 2

        self.rect_viewport = set_viewport_orientation(orientation, display_width, display_height)
        self.rect_led = QRect(0, 0, led_width, led_height)
        self.rect_background = QRect(0, 0, display_width, display_height)

        if led_outline_width > 0:
            self.pen_led = QPen()
            self.pen_led.setColor(led_outline_color)
            self.pen_led.setWidth(led_outline_width)
        else:
            self.pen_led = Qt.NoPen

        self.brush_led = (
            QBrush(lift_and_coast_color_off, Qt.SolidPattern),
            QBrush(lift_and_coast_color_low, Qt.SolidPattern),
            QBrush(lift_and_coast_color_critical, Qt.SolidPattern),
            QBrush(tc_activation_color, Qt.SolidPattern),
            QBrush(abs_activation_color, Qt.SolidPattern),
        )
        self.setFixedSize(display_width, display_height)

        # Last data
        self.lico_critical = lift_and_coast_multiplier_critical
        self.lico = -1
        self.tc_active = False
        self.abs_active = False

    # GUI update methods
    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if self.show_background:
            painter.fillRect(self.rect_background, self.background_color)

        # Draw LICO LED
        painter.setViewport(self.rect_viewport)
        painter.setPen(self.pen_led)
        painter.translate(self.margin, self.margin)

        lico_scaled = self.lico * self.led_count
        is_critical = (self.lico > self.lico_critical) + 1
        full_light = True

        if self.abs_active:
            painter.setBrush(self.brush_led[4])
        elif self.tc_active:
            painter.setBrush(self.brush_led[3])
        elif self.lico <= 0:
            painter.setBrush(self.brush_led[0])
        else:
            full_light = False

        for index in range(self.led_count):
            if not full_light:
                # Progressive
                if index < lico_scaled:
                    painter.setBrush(self.brush_led[is_critical])
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
                painter.translate(0, self.led_offset)
            else:
                painter.translate(self.led_offset, 0)


def set_viewport_orientation(orientation: int, display_width: int, display_height: int):
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
