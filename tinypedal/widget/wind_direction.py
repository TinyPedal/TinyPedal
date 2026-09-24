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
Wind direction Widget
"""

from PySide2.QtCore import QPointF, QRect, Qt
from PySide2.QtGui import QBrush, QPainter, QPen

from .. import calculation as calc
from .. import units
from ..api_control import api
from ..constant import DATA
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
        self.area_margin = min(max(self.wcfg["display_margin"], 0), int(area_size / 4))
        self.area_center = area_center = area_size * 0.5
        self.decimals = max(int(self.wcfg["decimal_places"]), 0)

        # Config units
        self.unit_speed = units.set_unit_speed(self.cfg.units["wind_speed_unit"])
        self.symbol_speed = units.set_symbol_speed(self.cfg.units["wind_speed_unit"])

        # Config canvas
        self.resize(area_size, area_size)
        self.rect_bg = QRect(0, 0, area_size, area_size)
        self.rect_text = QRect(
            area_size * self.wcfg["wind_speed_offset_x"] - area_center,
            area_size * self.wcfg["wind_speed_offset_y"] - font_m.height * 0.5 + font_m.voffset,
            area_size,
            font_m.height,
        )

        # Arrow shape
        self.arrow_shape = (
            QPointF(0, -area_center * self.wcfg["wind_arrow_scale_top"]),
            QPointF(area_center * self.wcfg["wind_arrow_scale_side"], area_center * self.wcfg["wind_arrow_scale_bottom"]),
            QPointF(0, area_center * self.wcfg["wind_arrow_scale_center"]),
            QPointF(-area_center * self.wcfg["wind_arrow_scale_side"], area_center * self.wcfg["wind_arrow_scale_bottom"]),
        )
        self.brush_arrow = (
            QBrush(self.wcfg["wind_arrow_color"], Qt.SolidPattern),
            QBrush(self.wcfg["wind_strength_color_calm"], Qt.SolidPattern),
            QBrush(self.wcfg["wind_strength_color_light"], Qt.SolidPattern),
            QBrush(self.wcfg["wind_strength_color_moderate"], Qt.SolidPattern),
            QBrush(self.wcfg["wind_strength_color_strong"], Qt.SolidPattern),
            QBrush(self.wcfg["wind_strength_color_gale"], Qt.SolidPattern),
            QBrush(self.wcfg["wind_strength_color_storm"], Qt.SolidPattern),
        )

        # Direction mark
        self.pen_dirmark = (
            self.set_pen_style(self.wcfg["direction_mark_minor_color"], self.wcfg["direction_mark_minor_width"]),
            self.set_pen_style(self.wcfg["direction_mark_major_color"], self.wcfg["direction_mark_major_width"]),
            self.set_pen_style(self.wcfg["direction_mark_north_color"], self.wcfg["direction_mark_north_width"]),
        )
        self.pen_text = QPen(self.wcfg["font_color_wind_speed"])
        self.brush_circle = QBrush(self.wcfg["background_color_circle"], Qt.SolidPattern)

        # Last data
        self.vehicle_yaw = 0.0

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Wind direction relative to player orientation
        vehicle_yaw = calc.degrees(api.read.vehicle.orientation_yaw()) + 180
        if self.vehicle_yaw != vehicle_yaw:
            self.vehicle_yaw = vehicle_yaw
            self.update()

    # GUI update methods
    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Draw background
        if self.wcfg["show_background"]:
            painter.fillRect(self.rect_bg, self.wcfg["background_color"])
        if self.wcfg["show_circle_background"]:
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.brush_circle)
            painter.drawEllipse(self.rect_bg)

        painter.translate(self.area_center, self.area_center)
        painter.rotate(self.vehicle_yaw)

        # Draw direction mark
        if self.wcfg["show_direction_mark"]:
            painter_drawLine = painter.drawLine
            # Minor mark
            painter.rotate(-60)
            painter.setPen(self.pen_dirmark[0])
            mark_start = self.area_center - self.area_margin
            mark_end = mark_start * self.wcfg["direction_mark_minor_length"]
            painter_drawLine(0, -mark_start, 0, -mark_end),  # north
            painter_drawLine(0, mark_start, 0, mark_end),  # south
            painter_drawLine(-mark_start, 0, -mark_end, 0),  # west
            painter_drawLine(mark_start, 0, mark_end, 0),  # east
            painter.rotate(30)
            painter_drawLine(0, -mark_start, 0, -mark_end),  # north
            painter_drawLine(0, mark_start, 0, mark_end),  # south
            painter_drawLine(-mark_start, 0, -mark_end, 0),  # west
            painter_drawLine(mark_start, 0, mark_end, 0),  # east
            painter.rotate(30)
            # Major mark
            mark_end = mark_start * self.wcfg["direction_mark_major_length"]
            painter.setPen(self.pen_dirmark[1])
            painter_drawLine(0, mark_start, 0, mark_end),  # south
            painter_drawLine(-mark_start, 0, -mark_end, 0),  # west
            painter_drawLine(mark_start, 0, mark_end, 0),  # east
            # North mark
            mark_end = mark_start * self.wcfg["direction_mark_north_length"]
            painter.setPen(self.pen_dirmark[2])
            painter_drawLine(0, -mark_start, 0, -mark_end),  # north

        # Draw wind arrow
        wind_direction = api.read.session.wind_direction()
        if wind_direction != DATA.FLOAT_INF:  # draw if valid
            wind_speed = api.read.session.wind_speed()
            painter.setPen(Qt.NoPen)
            painter.rotate(wind_direction)
            painter.setBrush(self.wind_strength_color(wind_speed))
            painter.drawPolygon(self.arrow_shape)

            # Draw text
            if self.wcfg["show_wind_speed"]:
                painter.resetTransform()
                if self.wcfg["show_wind_speed_unit"]:
                    text_angle = f"{self.unit_speed(wind_speed):.{self.decimals}f}{self.symbol_speed}"
                else:
                    text_angle = f"{self.unit_speed(wind_speed):.{self.decimals}f}"
                painter.setPen(self.pen_text)
                painter.drawText(self.rect_text, Qt.AlignCenter, text_angle)

    def wind_strength_color(self, wind_speed: float):
        """Wind strength color"""
        if not self.wcfg["show_wind_strength_color"]:
            return self.brush_arrow[0]
        if wind_speed < self.wcfg["wind_strength_threshold_light"]:
            return self.brush_arrow[1]
        if wind_speed < self.wcfg["wind_strength_threshold_moderate"]:
            return self.brush_arrow[2]
        if wind_speed < self.wcfg["wind_strength_threshold_strong"]:
            return self.brush_arrow[3]
        if wind_speed < self.wcfg["wind_strength_threshold_gale"]:
            return self.brush_arrow[4]
        if wind_speed < self.wcfg["wind_strength_threshold_storm"]:
            return self.brush_arrow[5]
        return self.brush_arrow[6]

    def set_pen_style(self, color: str, width: int):
        """Set pen style"""
        if width > 0:
            pen = QPen()
            pen.setWidth(width)
            pen.setColor(color)
        else:
            pen = Qt.NoPen
        return pen
