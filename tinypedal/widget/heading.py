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
Heading Widget
"""

from PySide2.QtCore import QPointF, QRectF, Qt
from PySide2.QtGui import QBrush, QPainter, QPen, QPixmap

from .. import calculation as calc
from ..api_control import api
from ..const_file import ImageFile
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
        self.area_size = max(int(self.wcfg["display_size"]), 20)
        self.area_center = self.area_size * 0.5
        self.decimals = max(int(self.wcfg["decimal_places"]), 0)
        text_width = font_m.width * (5 + self.decimals)
        self.dot_size = max(self.wcfg["dot_size"], 1)

        self.dir_line = (
            QPointF(0, -self.area_center * self.wcfg["direction_line_head_scale"]),
            QPointF(0, self.area_center * self.wcfg["direction_line_tail_scale"])
        )
        self.yaw_line = (
            QPointF(0, -self.area_center * self.wcfg["yaw_line_head_scale"]),
            QPointF(0, self.area_center * self.wcfg["yaw_line_tail_scale"])
        )
        self.slip_angle_line = (
            QPointF(0, -self.area_center * self.wcfg["slip_angle_line_head_scale"]),
            QPointF(0, self.area_center * self.wcfg["slip_angle_line_tail_scale"])
        )
        self.rect_text_yaw = QRectF(
            self.area_size * self.wcfg["yaw_angle_offset_x"] - text_width * 0.5,
            self.area_size * self.wcfg["yaw_angle_offset_y"] - font_m.height * 0.5 + font_m.voffset,
            text_width,
            font_m.height,
        )
        self.rect_text_slip = QRectF(
            self.area_size * self.wcfg["slip_angle_offset_x"] - text_width * 0.5,
            self.area_size * self.wcfg["slip_angle_offset_y"] - font_m.height * 0.5 + font_m.voffset,
            text_width,
            font_m.height,
        )

        # Config canvas
        self.resize(self.area_size, self.area_size)
        self.pixmap_background = QPixmap(self.area_size, self.area_size)
        self.pixmap_dot = QPixmap(self.dot_size * 2, self.dot_size * 2)
        self.pixmap_icon = QPixmap(ImageFile.COMPASS).scaledToWidth(
            int(self.area_size * 1.5),
            mode=Qt.SmoothTransformation
        )

        self.pen_yaw = QPen()
        self.pen_yaw.setCapStyle(Qt.RoundCap)
        self.pen_yaw.setWidth(self.wcfg["yaw_line_width"])
        self.pen_yaw.setColor(self.wcfg["yaw_line_color"])
        self.pen_slip = QPen()
        self.pen_slip.setCapStyle(Qt.RoundCap)
        self.pen_slip.setWidth(self.wcfg["slip_angle_line_width"])
        self.pen_slip.setColor(self.wcfg["slip_angle_line_color"])
        self.pen_direction = QPen()
        self.pen_direction.setCapStyle(Qt.RoundCap)
        self.pen_direction.setWidth(self.wcfg["direction_line_width"])
        self.pen_direction.setColor(self.wcfg["direction_line_color"])
        self.pen_text_yaw = QPen()
        self.pen_text_yaw.setColor(self.wcfg["font_color_yaw_angle"])
        self.pen_text_slip = QPen()
        self.pen_text_slip.setColor(self.wcfg["font_color_slip_angle"])

        self.draw_background(self.area_center)
        self.draw_dot()

        # Last data
        self.veh_ori_yaw = 0
        self.last_pos = 0,0
        self.yaw_angle = 0
        self.slip_angle = 0

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Read speed, position data
        speed = api.read.vehicle.speed()
        pos_curr = (api.read.vehicle.position_longitudinal(),
                    api.read.vehicle.position_lateral())

        # Vehicle orientation yaw
        temp_veh_ori_yaw = calc.rad2deg(api.read.vehicle.orientation_yaw_radians()) + 180

        # Direction of travel yaw angle
        if self.last_pos != pos_curr and speed > 1:
            self.yaw_angle = temp_veh_ori_yaw - calc.rad2deg(calc.oriyaw2rad(
                pos_curr[0] - self.last_pos[0], pos_curr[1] - self.last_pos[1])) + 180
            self.last_pos = pos_curr
        elif speed <= 1:
            self.yaw_angle = 0
            self.last_pos = pos_curr

        # Slip angle
        if speed > 1:
            self.slip_angle = calc.rad2deg(
                (api.read.wheel.slip_angle_fl() + api.read.wheel.slip_angle_fr()) * 0.5)
        else:
            self.slip_angle = 0

        if self.veh_ori_yaw != temp_veh_ori_yaw:
            self.veh_ori_yaw = temp_veh_ori_yaw
            self.update()

    # GUI update methods
    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        # Draw circle background
        painter.drawPixmap(0, 0, self.pixmap_background)
        # Draw compass bearing
        painter.translate(self.area_center, self.area_center)
        painter.rotate(self.veh_ori_yaw)
        painter.drawPixmap(
            -self.area_center, -self.area_center,
            self.area_size, self.area_size,
            self.pixmap_icon)
        painter.resetTransform()
        # Draw yaw line
        if self.wcfg["show_yaw_line"]:
            painter.setPen(self.pen_yaw)
            painter.translate(self.area_center, self.area_center)
            painter.drawPolyline(self.yaw_line)
            painter.resetTransform()
        # Draw slip angle line
        if self.wcfg["show_slip_angle_line"]:
            painter.setPen(self.pen_slip)
            painter.translate(self.area_center, self.area_center)
            painter.rotate(self.slip_angle)
            painter.drawPolyline(self.slip_angle_line)
            painter.resetTransform()
        # Draw direction line
        if self.wcfg["show_direction_line"]:
            painter.setPen(self.pen_direction)
            painter.translate(self.area_center, self.area_center)
            painter.rotate(self.yaw_angle)
            painter.drawPolyline(self.dir_line)
            painter.resetTransform()
        # Draw dot
        if self.wcfg["show_dot"]:
            painter.drawPixmap(self.area_center - self.dot_size, self.area_center - self.dot_size, self.pixmap_dot)
        # Draw text
        if self.wcfg["show_yaw_angle_reading"]:
            painter.setPen(self.pen_text_yaw)
            painter.drawText(
                self.rect_text_yaw,
                Qt.AlignCenter,
                self.format_angle(self.display_yaw_angle(self.yaw_angle))
            )
        if self.wcfg["show_slip_angle_reading"]:
            painter.setPen(self.pen_text_slip)
            painter.drawText(
                self.rect_text_slip,
                Qt.AlignCenter,
                self.format_angle(self.slip_angle)
            )

    def draw_background(self, center):
        """Draw circle background image"""
        if self.wcfg["show_background"]:
            self.pixmap_background.fill(self.wcfg["bkg_color"])
        else:
            self.pixmap_background.fill(Qt.transparent)
        painter = QPainter(self.pixmap_background)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Draw circle background
        if self.wcfg["show_circle_background"]:
            painter.setPen(Qt.NoPen)
            brush = QBrush(Qt.SolidPattern)
            brush.setColor(self.wcfg["bkg_color_circle"])
            painter.setBrush(brush)
            painter.drawEllipse(0, 0, self.area_size, self.area_size)

        # Draw center mark
        if self.wcfg["show_center_mark"]:
            pen = QPen()
            if self.wcfg["center_mark_style"]:
                pen.setStyle(Qt.SolidLine)
            else:
                pen.setStyle(Qt.DashLine)
            mark_scale = self.area_center * min(self.wcfg["center_mark_length_scale"], 1)
            pen.setWidth(self.wcfg["center_mark_width"])
            pen.setColor(self.wcfg["center_mark_color"])
            painter.setPen(pen)
            painter.drawLine(center, center, center - mark_scale, center)
            painter.drawLine(center, center, center, center + mark_scale)
            painter.drawLine(center, center, center, center - mark_scale)
            painter.drawLine(center, center, center + mark_scale, center)

    def draw_dot(self):
        """Draw dot image (one time)"""
        self.pixmap_dot.fill(Qt.transparent)
        painter = QPainter(self.pixmap_dot)
        painter.setRenderHint(QPainter.Antialiasing, True)
        if self.wcfg["dot_outline_width"] > 0:
            pen = QPen()
            pen.setWidth(self.wcfg["dot_outline_width"])
            pen.setColor(self.wcfg["dot_outline_color"])
            painter.setPen(pen)
        else:
            painter.setPen(Qt.NoPen)
        brush = QBrush(Qt.SolidPattern)
        brush.setColor(self.wcfg["dot_color"])
        painter.setBrush(brush)
        painter.drawEllipse(self.dot_size * 0.5, self.dot_size * 0.5, self.dot_size, self.dot_size)

    # Additional methods
    @staticmethod
    def display_yaw_angle(angle):
        """Set yaw angle display range"""
        if angle < -180:
            angle = 360 + angle
        elif angle > 180:
            angle = 360 - angle
        if abs(angle) > 180:
            angle = 360 - abs(angle)
        return angle

    def format_angle(self, angle):
        """Format angle text"""
        if self.wcfg["show_degree_sign"]:
            return f" {abs(angle):.{self.decimals}f}°"
        return f"{abs(angle):.{self.decimals}f}"
