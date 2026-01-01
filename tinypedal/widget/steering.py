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
Steering Widget
"""

from PySide2.QtCore import QRectF, Qt
from PySide2.QtGui import QPainter, QPen, QPixmap

from .. import calculation as calc
from ..api_control import api
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
            self.wcfg["font_weight"]
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)
        font_offset = self.calc_font_offset(font_m)

        # Config variable
        padx = round(font_m.width * self.wcfg["bar_padding_horizontal"])
        pady = round(font_m.capital * self.wcfg["bar_padding_vertical"])
        text_height = int(font_m.capital + pady * 2) * self.wcfg["show_steering_angle"]

        self.bar_edge = max(self.wcfg["bar_edge_width"], 0)
        self.bar_width = max(self.wcfg["bar_width"], 20)
        self.bar_height = max(self.wcfg["bar_height"], text_height)

        side_width = self.bar_edge + self.bar_width
        text_pad = self.bar_edge + padx

        # Rect
        self.rect_steer = QRectF(0, 0, side_width * 2, self.bar_height)
        self.rect_steerpos = QRectF(0, 0, side_width, self.bar_height)
        self.rect_text = self.rect_steer.adjusted(text_pad, font_offset, -text_pad, 0)

        self.rect_center = QRectF(side_width - 1, 0, 2, self.bar_height)
        self.rect_edge_l = QRectF(0, 0, self.bar_edge, self.bar_height)
        self.rect_edge_r = QRectF(self.bar_edge + self.bar_width * 2, 0, self.bar_edge, self.bar_height)

        # Config canvas
        self.resize(side_width * 2, self.bar_height)
        self.pixmap_mark = QPixmap(side_width * 2, self.bar_height)

        self.pen_text = QPen()
        self.pen_text.setColor(self.wcfg["font_color"])

        self.draw_scale_mark()

        # Last data
        self.raw_steering = 0
        self.rot_range = 0

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Steering wheel rotation
        if self.wcfg["manual_steering_range"] > 0:
            temp_rot_range = self.wcfg["manual_steering_range"]
        else:
            temp_rot_range = api.read.inputs.steering_range_physical()

        # Recalculate scale mark
        if self.wcfg["show_scale_mark"] and self.rot_range != temp_rot_range:
            self.rot_range = temp_rot_range
            mark_gap, mark_num = self.scale_mark(
                self.wcfg["scale_mark_degree"],
                self.rot_range,
                self.bar_width
            )
            self.draw_scale_mark(mark_gap, mark_num)

        # Steering
        temp_raw_steering = api.read.inputs.steering_raw()
        if self.raw_steering != temp_raw_steering:
            self.raw_steering = temp_raw_steering
            self.update()

    # GUI update methods
    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.fillRect(self.rect_steer, self.wcfg["bkg_color"])

        # Draw steering
        steer_pos = self.steer_position(self.raw_steering, self.bar_width * 2)
        self.rect_steerpos.setLeft(self.bar_edge + steer_pos)
        painter.fillRect(self.rect_steerpos, self.wcfg["steering_color"])

        # Draw edge & scale marks
        painter.drawPixmap(0, 0, self.pixmap_mark)

        # Draw readings
        if self.wcfg["show_steering_angle"]:
            painter.setPen(self.pen_text)
            angle = self.raw_steering * self.rot_range * 0.5
            if angle < 0:
                painter.drawText(self.rect_text, Qt.AlignLeft | Qt.AlignVCenter, f"{-angle:.0f}")
            elif angle > 0:
                painter.drawText(self.rect_text, Qt.AlignRight | Qt.AlignVCenter, f"{angle:.0f}")

    def draw_scale_mark(self, mark_gap=90, mark_num=0):
        """Draw scale mark"""
        self.pixmap_mark.fill(Qt.transparent)
        painter = QPainter(self.pixmap_mark)
        if self.wcfg["show_scale_mark"] and mark_num:
            mark_color = self.wcfg["scale_mark_color"]
            offset = self.bar_edge + self.bar_width
            for idx in range(mark_num):
                gap = mark_gap * (idx + 1)
                painter.fillRect(offset - gap, 0, 1, self.bar_height, mark_color)
                painter.fillRect(offset + gap, 0, 1, self.bar_height, mark_color)
        # Edge center mark
        edge_color = self.wcfg["bar_edge_color"]
        painter.fillRect(self.rect_edge_l, edge_color)
        painter.fillRect(self.rect_edge_r, edge_color)
        painter.fillRect(self.rect_center, edge_color)

    # Additional methods
    @staticmethod
    def scale_mark(degree, rot_range, width):
        """Scale mark gap (degree), mark counts"""
        mark_num = max(int(rot_range / max(degree, 10) * 0.5), 0)
        if rot_range != 0:
            return degree / (rot_range * 0.5) * width, mark_num
        return 0, mark_num

    @staticmethod
    def steer_position(pos, length):
        """Delta position"""
        return (length - calc.sym_max(pos * -length, length)) * 0.5
