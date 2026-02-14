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
Steering wheel Widget
"""

from PySide2.QtCore import QRect, Qt
from PySide2.QtGui import QBrush, QPainter, QPen, QPixmap

from ..api_control import api
from ..const_file import ImageFile
from ..validator import image_exists
from ._base import Overlay


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)

        # Config font
        font = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size"],
            self.wcfg["font_weight"],
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)

        # Config variable
        area_size = max(int(self.wcfg["display_size"] / 2) * 2, 10)
        area_margin = min(max(self.wcfg["display_margin"], 0), int(area_size / 4))
        self.area_center = area_size * 0.5
        wheel_size = area_size - area_margin * 2
        wheel_center = wheel_size * 0.5
        rotation_margin = min(max(self.wcfg["rotation_line_margin"], 0), int(area_size / 4))
        rotation_size = area_size - rotation_margin * 2
        rotation_size_offset = (area_size - rotation_size) * 0.5
        self.decimals = max(int(self.wcfg["decimal_places"]), 0)
        text_width = font_m.width * (5 + self.decimals)

        self.pixmap_wheel = self.load_image(
            filename=ImageFile.STEERING_WHEEL,
            userfile=self.wcfg["custom_steering_wheel_image_file"],
            size=int(wheel_size * 1.5),
            show_custom=self.wcfg["show_custom_steering_wheel"],
        )

        self.rect_bg = QRect(0, 0, area_size, area_size)
        self.rect_wheel = QRect(-wheel_center, -wheel_center, wheel_size, wheel_size)
        self.rect_rotation = QRect(
            rotation_size_offset,
            rotation_size_offset,
            rotation_size,
            rotation_size,
        )
        self.rect_text = QRect(
            area_size * self.wcfg["steering_angle_offset_x"] - text_width * 0.5,
            area_size * self.wcfg["steering_angle_offset_y"] - font_m.height * 0.5 + font_m.voffset,
            text_width,
            font_m.height,
        )

        # Config canvas
        self.resize(area_size, area_size)

        self.pen_rotation = QPen()
        self.pen_rotation.setCapStyle(Qt.FlatCap)
        self.pen_rotation.setColor(self.wcfg["rotation_line_color"])
        self.pen_rotation.setWidth(self.wcfg["rotation_line_width"])
        self.pen_text = QPen()
        self.pen_text.setColor(self.wcfg["font_color_steering_angle"])
        self.brush_circle = QBrush(Qt.SolidPattern)
        self.brush_circle.setColor(self.wcfg["bkg_color_circle"])

        # Last data
        self.steering_angle = 0

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Steering wheel rotation
        if self.wcfg["manual_steering_range"] > 0:
            temp_rot_range = self.wcfg["manual_steering_range"]
        else:
            temp_rot_range = api.read.inputs.steering_range_physical()

        # Steering
        temp_steering_angle = api.read.inputs.steering_raw() * temp_rot_range * 0.5
        if self.steering_angle != temp_steering_angle:
            self.steering_angle = temp_steering_angle
            self.update()

    # GUI update methods
    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        # Draw background
        if self.wcfg["show_background"]:
            painter.fillRect(self.rect_bg, self.wcfg["bkg_color"])
        if self.wcfg["show_circle_background"]:
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.brush_circle)
            painter.drawEllipse(self.rect_bg)
        # Draw steering wheel
        painter.translate(self.area_center, self.area_center)
        painter.rotate(self.steering_angle)
        painter.drawPixmap(self.rect_wheel, self.pixmap_wheel)
        painter.resetTransform()
        # Draw rotation line
        if self.wcfg["show_rotation_line"]:
            if (not self.wcfg["show_rotation_line_while_stationary_only"] or
                self.wcfg["show_rotation_line_while_stationary_only"] and
                api.read.vehicle.speed() < 1):
                painter.setPen(self.pen_rotation)
                painter.drawArc(self.rect_rotation, 1440, -self.steering_angle * 16)
        # Draw text
        if self.wcfg["show_steering_angle"]:
            if self.wcfg["show_degree_sign"]:
                text_angle = f" {abs(self.steering_angle):.{self.decimals}f}°"
            else:
                text_angle = f"{abs(self.steering_angle):.{self.decimals}f}"
            painter.setPen(self.pen_text)
            painter.drawText(self.rect_text, Qt.AlignCenter, text_angle)

    # Additional methods
    @staticmethod
    def load_image(filename: str, userfile: str, size: int, show_custom: bool):
        """Load steering wheel image"""
        if show_custom:
            temp_filename = userfile
            if image_exists(temp_filename):
                filename = temp_filename
        icon_source = QPixmap(filename)
        return icon_source.scaled(size, size, mode=Qt.SmoothTransformation)
