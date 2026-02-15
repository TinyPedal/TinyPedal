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
Elevation Widget
"""

from PySide2.QtCore import QRectF, Qt
from PySide2.QtGui import QBrush, QPainter, QPainterPath, QPen, QPixmap

from .. import calculation as calc
from .. import units
from ..api_control import api
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
            self.wcfg["font_weight"],
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)

        # Config variable
        self.display_width = max(self.wcfg["display_width"], 20)
        self.display_height = max(self.wcfg["display_height"], 10)
        self.display_margin_top = min(max(self.wcfg["display_margin_top"], 0), int(self.display_height / 2))
        self.display_margin_bottom = min(max(self.wcfg["display_margin_bottom"], 0), int(self.display_height / 2))
        self.display_detail_level = max(self.wcfg["display_detail_level"], 0)

        self.rect_text_elevation = QRectF(
            self.display_width * self.wcfg["elevation_reading_offset_x"] - font_m.width * 5,
            self.display_height * self.wcfg["elevation_reading_offset_y"] - font_m.height * 0.5 + font_m.voffset,
            font_m.width * 10,
            font_m.height,
        )
        self.rect_text_scale = QRectF(
            self.display_width * self.wcfg["elevation_scale_offset_x"] - font_m.width * 5,
            self.display_height * self.wcfg["elevation_scale_offset_y"] - font_m.height * 0.5 + font_m.voffset,
            font_m.width * 10,
            font_m.height,
        )
        self.elevation_text_alignment = self.set_text_alignment(self.wcfg["elevation_reading_text_alignment"])
        self.scale_text_alignment = self.set_text_alignment(self.wcfg["elevation_scale_text_alignment"])

        # Config units
        self.unit_dist = units.set_unit_distance(self.cfg.units["distance_unit"])
        self.symbol_dist = units.set_symbol_distance(self.cfg.units["distance_unit"])

        # Config canvas
        self.resize(self.display_width, self.display_height)
        self.pixmap_background = QPixmap(self.display_width, self.display_height)
        self.pixmap_progress = QPixmap(self.display_width, self.display_height)
        self.pixmap_progress_line = QPixmap(self.display_width, self.display_height)
        self.pixmap_marks = QPixmap(self.display_width, self.display_height)

        self.pen_mark = QPen()
        self.pen_mark.setWidth(self.wcfg["position_mark_width"])
        self.pen_mark.setColor(self.wcfg["position_mark_color"])
        self.pen_text = QPen()
        self.pen_text.setColor(self.wcfg["font_color"])

        # Last data
        self.last_modified = 0
        self.veh_pos = 0
        self.map_scaled = None
        self.map_range = (0,10,0,10)
        self.map_scale = 1,1

        self.update_elevation(-1)

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Elevation map
        modified = minfo.mapping.lastModified
        self.update_elevation(modified)

        # Vehicle position
        temp_veh_pos = self.display_width * api.read.lap.progress()
        if self.veh_pos != temp_veh_pos:
            self.veh_pos = temp_veh_pos
            self.update()

    # GUI update methods
    def update_elevation(self, data):
        """Elevation map update"""
        if self.last_modified != data:
            self.last_modified = data
            raw_data = minfo.mapping.elevations if data != -1 else None
            map_path = self.create_elevation_path(raw_data)
            self.draw_background(map_path)
            self.draw_progress(map_path)
            self.draw_progress_line(map_path)
            self.draw_marks(map_path)

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.drawPixmap(0, 0, self.pixmap_background)

        # Draw elevation progress
        if self.wcfg["show_elevation_progress"]:
            painter.drawPixmap(0, 0, self.pixmap_progress, 0, 0, self.veh_pos, 0)

        # Draw marks
        painter.drawPixmap(0, 0, self.pixmap_marks)

        if self.wcfg["show_elevation_progress_line"]:
            painter.drawPixmap(0, 0, self.pixmap_progress_line, 0, 0, self.veh_pos, 0)

        if self.wcfg["show_position_mark"]:
            painter.setPen(self.pen_mark)
            painter.drawLine(self.veh_pos, 0, self.veh_pos, self.display_height)

        # Draw readings
        painter.setPen(self.pen_text)
        if self.wcfg["show_elevation_reading"]:
            painter.drawText(
                self.rect_text_elevation,
                self.elevation_text_alignment,
                f"{self.unit_dist(api.read.vehicle.position_vertical()):.1f}{self.symbol_dist}"
            )
        if self.wcfg["show_elevation_scale"]:
            # Format elevation scale (meter or feet per pixel)
            map_scale = round(self.unit_dist(1 / self.map_scale[1]), 2) if self.map_scale[1] else 1
            painter.drawText(
                self.rect_text_scale,
                self.scale_text_alignment,
                f"1:{map_scale}"
            )

    def create_elevation_path(self, raw_coords=None):
        """Create elevation path"""
        map_path = QPainterPath()
        if raw_coords:
            self.map_scaled, self.map_range, self.map_scale = calc.scale_elevation(
                raw_coords,
                self.display_width,
                self.display_height - self.display_margin_top - self.display_margin_bottom)

            # Correct start & finish nodes position
            sf_y_average = (self.map_scaled[0][1] + self.map_scaled[-1][1]) * 0.5

            # Set boundary start node
            map_path.moveTo(-999, self.map_scaled[-2][1])  # 2nd last node y pos

            # Set middle nodes
            total_nodes = len(self.map_scaled) - 1
            skip_node = calc.skip_map_nodes(total_nodes, self.display_width, self.display_detail_level)
            last_dist = 0
            last_skip = 0
            for index, coords in enumerate(self.map_scaled):
                if index == 0:
                    map_path.lineTo(0, sf_y_average)
                elif index >= total_nodes:  # don't skip last node
                    map_path.lineTo(self.display_width, sf_y_average)
                elif coords[0] > last_dist and last_skip >= skip_node:
                    map_path.lineTo(*coords)
                    last_skip = 0
                    last_dist = coords[0]
                last_skip += 1

            # Set boundary end node
            map_path.lineTo(self.display_width + 999, self.map_scaled[1][1])  # 2nd node y pos
            map_path.lineTo(self.display_width + 999, -999)
            map_path.lineTo(-999, -999)
            map_path.closeSubpath()

        # Temp map
        else:
            self.map_scaled = None
            map_path.moveTo(-999, self.display_height * 0.5)
            map_path.lineTo(self.display_width + 999, self.display_height * 0.5)
            map_path.lineTo(self.display_width + 999, -999)
            map_path.lineTo(-999, -999)
            map_path.closeSubpath()

        return map_path

    def draw_background(self, map_path):
        """Draw background image"""
        if self.wcfg["show_background"]:
            self.pixmap_background.fill(self.wcfg["bkg_color"])
        else:
            self.pixmap_background.fill(Qt.transparent)
        painter = QPainter(self.pixmap_background)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Set vertical flip to correct elevation direction
        painter.setViewport(0, self.display_height, self.display_width, -self.display_height)

        # Add margin offset
        if self.map_scaled:
            painter.translate(0, self.display_margin_bottom)

        # Draw elevation background
        if self.wcfg["show_elevation_background"]:
            brush = QBrush(Qt.SolidPattern)
            brush.setColor(self.wcfg["bkg_color_elevation"])
            painter.setBrush(brush)
            painter.setPen(Qt.NoPen)
            painter.drawPath(map_path)

    def draw_progress(self, map_path):
        """Draw progress image"""
        self.pixmap_progress.fill(Qt.transparent)
        painter = QPainter(self.pixmap_progress)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Set vertical flip to correct elevation direction
        painter.setViewport(0, self.display_height, self.display_width, -self.display_height)

        # Add margin offset
        if self.map_scaled:
            painter.translate(0, self.display_margin_bottom)

        # Draw elevation progress
        brush = QBrush(Qt.SolidPattern)
        brush.setColor(self.wcfg["elevation_progress_color"])
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawPath(map_path)

    def draw_progress_line(self, map_path):
        """Draw progress line image"""
        self.pixmap_progress_line.fill(Qt.transparent)
        painter = QPainter(self.pixmap_progress_line)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Set vertical flip to correct elevation direction
        painter.setViewport(0, self.display_height, self.display_width, -self.display_height)

        # Add margin offset
        if self.map_scaled:
            painter.translate(0, self.display_margin_bottom)

        # Draw elevation progress line
        pen = QPen()
        pen.setJoinStyle(Qt.RoundJoin)
        pen.setWidth(self.wcfg["elevation_progress_line_width"])
        pen.setColor(self.wcfg["elevation_progress_line_color"])
        painter.setPen(pen)
        painter.drawPath(map_path)

    def draw_marks(self, map_path):
        """Draw marks image"""
        self.pixmap_marks.fill(Qt.transparent)
        painter = QPainter(self.pixmap_marks)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Set vertical flip to correct elevation direction
        painter.setViewport(0, self.display_height, self.display_width, -self.display_height)

        # Add margin offset
        if self.map_scaled:
            painter.translate(0, self.display_margin_bottom)

        # Set pen style
        pen = QPen()
        pen.setJoinStyle(Qt.RoundJoin)

        # Draw elevation line
        if self.wcfg["show_elevation_line"]:
            pen.setWidth(self.wcfg["elevation_line_width"])
            pen.setColor(self.wcfg["elevation_line_color"])
            painter.setPen(pen)
            painter.drawPath(map_path)

        # Draw start line
        if self.wcfg["show_start_line"]:
            pen.setWidth(self.wcfg["start_line_width"])
            pen.setColor(self.wcfg["start_line_color"])
            painter.setPen(pen)
            painter.drawLine(0, -999, 0, 999)
            painter.drawLine(self.display_width, -999, self.display_width, 999)

        # Draw sector line
        sectors_index = minfo.mapping.sectors
        if self.wcfg["show_sector_line"] and self.map_scaled and isinstance(sectors_index, tuple):
            pen.setWidth(self.wcfg["sector_line_width"])
            pen.setColor(self.wcfg["sector_line_color"])
            painter.setPen(pen)
            for index in sectors_index:
                pos_x = self.map_scaled[index][0]
                painter.drawLine(pos_x, -999, pos_x, 999)

        # Draw zero elevation line
        if self.wcfg["show_zero_elevation_line"] and self.map_scaled:
            pen.setWidth(self.wcfg["zero_elevation_line_width"])
            pen.setColor(self.wcfg["zero_elevation_line_color"])
            painter.setPen(pen)
            # scale * (0pos - min_range)
            zero_elevation = self.map_scale[1] * -self.map_range[2]
            painter.drawLine(0, zero_elevation, self.display_width, zero_elevation)
