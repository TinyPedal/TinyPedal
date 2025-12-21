#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2025 TinyPedal developers, see contributors.md file
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
Friction circle Widget
"""

from collections import deque

from PySide2.QtCore import QPointF, QRectF, Qt
from PySide2.QtGui import QBrush, QColor, QPainter, QPen, QPixmap, QRadialGradient

from .. import calculation as calc
from ..module_info import minfo
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
        text_width = font_m.width * 4
        display_size = max(int(self.wcfg["display_size"]), 20)
        self.display_radius_g = max(self.wcfg["display_radius_g"], 1)
        self.global_scale = (display_size * 0.5) / self.display_radius_g
        self.area_size = display_size + font_m.height * 2
        self.area_center = self.area_size * 0.5

        self.dot_size = max(self.wcfg["dot_size"], 1)
        self.rect_text_top = QRectF(
            self.area_center - text_width * 0.5,
            font_offset,
            text_width,
            font_m.height
        )
        self.rect_text_bottom = QRectF(
            self.area_center - text_width * 0.5,
            self.area_size - font_m.height + font_offset,
            text_width,
            font_m.height
        )
        self.rect_text_left = QRectF(
            0,
            self.area_center - font_m.height + font_offset,
            text_width,
            font_m.height
        )
        self.rect_text_right = QRectF(
            self.area_size - text_width,
            self.area_center - font_m.height + font_offset,
            text_width,
            font_m.height
        )

        # Config canvas
        self.resize(self.area_size, self.area_size)
        self.pixmap_background = QPixmap(self.area_size, self.area_size)
        self.pixmap_dot = QPixmap(self.dot_size * 2, self.dot_size * 2)
        self.pixmap_trace = QPixmap(self.area_size, self.area_size)
        self.pixmap_trace.fill(Qt.transparent)
        if self.wcfg["show_trace_fade_out"]:
            trace_alpha = int(255 * min(max(self.wcfg["trace_fade_out_step"], 0.1), 0.9) / 2)
            self.fademask_color = QColor(0, 0, 0, trace_alpha)
            self.rect_fademask = QRectF(0, 0, self.area_size, self.area_size)

        self.pen_mark = QPen()
        self.pen_trace = QPen()
        self.pen_trace.setWidth(self.wcfg["trace_width"])
        self.pen_trace.setColor(self.wcfg["trace_color"])
        self.pen_trace.setStyle(Qt.SolidLine)
        self.pen_trace.setCapStyle(Qt.RoundCap)
        self.pen_text_raw = QPen()
        self.pen_text_raw.setColor(self.wcfg["font_color"])
        self.pen_text_max = QPen()
        self.pen_text_max.setColor(self.wcfg["font_color_highlight"])

        self.draw_background(self.area_center)
        self.draw_dot()

        # Last data
        self.gforce_raw = 0,0
        self.data_gforce = deque([], max(self.wcfg["trace_max_samples"], 5))
        self.last_x = self.area_center
        self.last_y = self.area_center

    def post_update(self):
        self.data_gforce.clear()

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Read acceleration data
        if self.wcfg["show_inverted_orientation"]:
            temp_gforce_raw = (  # accel top, brake bottom
                round(minfo.force.lgtGForceRaw, 3),
                round(-minfo.force.latGForceRaw, 3),
            )
        else:
            temp_gforce_raw = (  # brake top, accel bottom
                round(-minfo.force.lgtGForceRaw, 3),
                round(minfo.force.latGForceRaw, 3),
            )

        if self.gforce_raw != temp_gforce_raw:
            self.gforce_raw = temp_gforce_raw
            # Scale position coordinate to global
            self.last_x = temp_gforce_raw[1] * self.global_scale + self.area_center
            self.last_y = temp_gforce_raw[0] * self.global_scale + self.area_center
            if self.wcfg["show_trace"]:
                self.data_gforce.append(QPointF(self.last_x, self.last_y))
                self.draw_trace()
            self.update()

    # GUI update methods
    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        # Draw g circle background
        painter.drawPixmap(0, 0, self.pixmap_background)
        # Draw max average g circle
        if self.wcfg["show_max_average_lateral_g_circle"]:
            self.draw_circle_mark(
                painter,
                self.wcfg["max_average_lateral_g_circle_style"],
                minfo.force.maxAvgLatGForce,
                self.wcfg["max_average_lateral_g_circle_width"],
                self.wcfg["max_average_lateral_g_circle_color"]
            )
        # Draw trace
        if self.wcfg["show_trace"]:
            painter.drawPixmap(0, 0, self.pixmap_trace)
        # Draw dot
        if self.wcfg["show_dot"]:
            painter.drawPixmap(
                self.last_x - self.dot_size, self.last_y - self.dot_size, self.pixmap_dot)
        # Draw text
        if self.wcfg["show_readings"]:
            self.draw_text(painter)

    def draw_background(self, center):
        """Draw g circle background (one time)"""
        if self.wcfg["show_background"]:
            self.pixmap_background.fill(self.wcfg["bkg_color"])
        else:
            self.pixmap_background.fill(Qt.transparent)
        painter = QPainter(self.pixmap_background)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if self.wcfg["show_circle_background"]:
            painter.setPen(Qt.NoPen)
            scale = round(self.display_radius_g * self.global_scale)
            if self.wcfg["show_fade_out"]:
                rad_gra = QRadialGradient(center, center, scale)
                rad_gra.setColorAt(
                    calc.zero_one(self.wcfg["fade_in_radius"]),
                    self.wcfg["bkg_color_circle"])
                rad_gra.setColorAt(
                    calc.zero_one(self.wcfg["fade_out_radius"]),
                    Qt.transparent)
                painter.setBrush(rad_gra)
            else:
                brush = QBrush(Qt.SolidPattern)
                brush.setColor(self.wcfg["bkg_color_circle"])
                painter.setBrush(brush)
            painter.drawEllipse(center - scale, center - scale, scale * 2, scale * 2)

        # Draw center mark
        if self.wcfg["show_center_mark"]:
            if self.wcfg["center_mark_style"]:
                self.pen_mark.setStyle(Qt.SolidLine)
            else:
                self.pen_mark.setStyle(Qt.DashLine)
            scale = self.global_scale * min(
                self.wcfg["center_mark_radius_g"], self.display_radius_g
            )
            self.pen_mark.setWidth(self.wcfg["center_mark_width"])
            self.pen_mark.setColor(self.wcfg["center_mark_color"])
            painter.setPen(self.pen_mark)
            painter.drawLine(center, center, center - scale, center)
            painter.drawLine(center, center, center, center + scale)
            painter.drawLine(center, center, center, center - scale)
            painter.drawLine(center, center, center + scale, center)

        # Draw circle mark
        if self.wcfg["show_reference_circle"]:
            painter.setBrush(Qt.NoBrush)
            for idx in range(1, 6):
                self.draw_circle_mark(
                    painter,
                    self.wcfg[f"reference_circle_{idx}_style"],
                    self.wcfg[f"reference_circle_{idx}_radius_g"],
                    self.wcfg[f"reference_circle_{idx}_width"],
                    self.wcfg[f"reference_circle_{idx}_color"]
                )

    def draw_circle_mark(self, painter, style, radius, width, color):
        """Draw circle mark"""
        if radius <= self.display_radius_g and width > 0:
            scale = round(radius * self.global_scale)
            pos = self.area_center - scale
            size = scale * 2
            self.pen_mark.setStyle(Qt.SolidLine if style else Qt.DashLine)
            self.pen_mark.setWidth(width)
            self.pen_mark.setColor(color)
            painter.setPen(self.pen_mark)
            painter.drawEllipse(pos, pos, size, size)

    def draw_trace(self):
        """Draw trace image"""
        painter = QPainter(self.pixmap_trace)
        painter.setRenderHint(QPainter.Antialiasing, True)
        if self.wcfg["show_trace_fade_out"]:
            painter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
            painter.fillRect(self.rect_fademask, self.fademask_color)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        else:
            self.pixmap_trace.fill(Qt.transparent)
        painter.setPen(self.pen_trace)
        if self.wcfg["trace_style"]:
            painter.drawPoints(self.data_gforce)
        else:
            painter.drawPolyline(self.data_gforce)

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

    def draw_text(self, painter):
        """Draw text"""
        # Current G reading
        painter.setPen(self.pen_text_raw)
        painter.drawText(
            self.rect_text_top,
            Qt.AlignCenter,
            f"{abs(self.gforce_raw[0]):.2f}"
        )
        painter.drawText(
            self.rect_text_right,
            Qt.AlignCenter,
            f"{abs(self.gforce_raw[1]):.2f}"
        )
        # Max G reading
        painter.setPen(self.pen_text_max)
        painter.drawText(
            self.rect_text_bottom,
            Qt.AlignCenter,
            f"{minfo.force.maxLgtGForce:.2f}"[:4]
        )
        painter.drawText(
            self.rect_text_left,
            Qt.AlignCenter,
            f"{minfo.force.maxLatGForce:.2f}"[:4]
        )
