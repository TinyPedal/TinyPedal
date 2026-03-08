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
Navigation Widget
"""

from PySide2.QtCore import QPointF, QRectF, Qt
from PySide2.QtGui import QBrush, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient

from .. import calculation as calc
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
        self.area_size = max(int(self.wcfg["display_size"]), 20)
        self.global_scale = self.area_size / max(self.wcfg["view_radius"], 5)
        self.area_center = self.area_size * 0.5
        self.view_range = self.wcfg["view_radius"] * 2.5
        self.veh_offset_y = self.area_size * max(self.wcfg["vehicle_offset"], 0)
        self.veh_size = max(int(self.wcfg["vehicle_size"]), 1)

        if self.wcfg["show_circle_vehicle_shape"]:
            self.veh_shape = QRectF(
                -self.veh_size * 0.5,
                -self.veh_size * 0.5,
                self.veh_size,
                self.veh_size,
            )
        else:
            self.veh_shape = (
                QPointF(0, -self.veh_size * 0.6),
                QPointF(self.veh_size * 0.5, self.veh_size * 0.4),
                QPointF(0, self.veh_size * 0.2),
                QPointF(-self.veh_size * 0.5, self.veh_size * 0.4),
            )
        self.veh_text_shape = QRectF(
            -self.veh_size * 0.5,
            -self.veh_size * 0.5 + font_m.voffset,
            self.veh_size,
            self.veh_size,
        )

        self.map_path = None
        self.sfinish_path = None
        self.sector_path = None
        self.create_map_path()

        # Config canvas
        self.resize(self.area_size, self.area_size)
        self.pixmap_background = QPixmap(self.area_size, self.area_size)
        self.pixmap_mask = QPixmap(self.area_size, self.area_size)

        self.pen_text = {
            "opponent": QPen(self.wcfg["font_color"]),
            "player": QPen(self.wcfg["font_color_player"]),
        }
        self.pen_outline = {
            "opponent": self.set_pen_style(self.wcfg["vehicle_outline_color"], self.wcfg["vehicle_outline_width"]),
            "player": self.set_pen_style(self.wcfg["vehicle_outline_color_player"], self.wcfg["vehicle_outline_width_player"]),
            "map_outline": self.set_pen_style(self.wcfg["map_outline_color"], self.wcfg["map_width"] + self.wcfg["map_outline_width"], True),
            "map": self.set_pen_style(self.wcfg["map_color"], self.wcfg["map_width"], True),
            "sfinish": self.set_pen_style(self.wcfg["start_line_color"], self.wcfg["start_line_width"]),
            "sector": self.set_pen_style(self.wcfg["sector_line_color"], self.wcfg["sector_line_width"]),
        }
        self.brush_overall = {
            "player": self.set_brush_style(self.wcfg["vehicle_color_player"]),
            "leader": self.set_brush_style(self.wcfg["vehicle_color_leader"]),
            "same_lap": self.set_brush_style(self.wcfg["vehicle_color_same_lap"]),
            "laps_ahead": self.set_brush_style(self.wcfg["vehicle_color_laps_ahead"]),
            "laps_behind": self.set_brush_style(self.wcfg["vehicle_color_laps_behind"]),
            "in_pit": self.set_brush_style(self.wcfg["vehicle_color_in_pit"]),
            "yellow": self.set_brush_style(self.wcfg["vehicle_color_yellow"]),
        }

        # Last data
        self.last_veh_data_version = None
        self.last_modified = 0
        self.map_scaled = None
        self.map_size = 1,1
        self.map_offset = 0,0

        self.draw_background()
        self.draw_map_mask_pixmap()
        self.update_map(-1)

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Map
        modified = minfo.mapping.lastModified
        self.update_map(modified)

        # Vehicles
        veh_data_version = minfo.vehicles.dataSetVersion
        if self.last_veh_data_version != veh_data_version:
            self.last_veh_data_version = veh_data_version
            self.update()

    # GUI update methods
    def update_map(self, data):
        """Map update"""
        if self.last_modified != data:
            self.last_modified = data
            self.create_map_path(minfo.mapping.coordinates)

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        # Draw map
        self.draw_map_image(painter)
        # Draw vehicles
        self.draw_vehicle(painter, minfo.vehicles.dataSet, minfo.relative.drawOrder)
        # Apply mask
        if self.wcfg["show_fade_out"]:
            painter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
            painter.drawPixmap(0, 0, self.pixmap_mask)
        # Draw background below map & mask
        if self.wcfg["show_background"] or self.wcfg["show_circle_background"]:
            painter.setCompositionMode(QPainter.CompositionMode_DestinationOver)
            painter.drawPixmap(0, 0, self.pixmap_background)

    def draw_background(self):
        """Draw background"""
        if self.wcfg["show_background"]:
            self.pixmap_background.fill(self.wcfg["background_color"])
        else:
            self.pixmap_background.fill(Qt.transparent)

        # Draw circle background
        if self.wcfg["show_circle_background"]:
            painter = QPainter(self.pixmap_background)
            painter.setRenderHint(QPainter.Antialiasing, True)

            if self.wcfg["circle_outline_width"] > 0:
                pen = QPen()
                pen.setWidth(self.wcfg["circle_outline_width"])
                pen.setColor(self.wcfg["circle_outline_color"])
                painter.setPen(pen)
            else:
                painter.setPen(Qt.NoPen)

            brush = QBrush(Qt.SolidPattern)
            brush.setColor(self.wcfg["background_color_circle"])
            painter.setBrush(brush)
            painter.drawEllipse(
                self.wcfg["circle_outline_width"],
                self.wcfg["circle_outline_width"],
                (self.area_center - self.wcfg["circle_outline_width"]) * 2,
                (self.area_center - self.wcfg["circle_outline_width"]) * 2
            )

    def create_map_path(self, raw_coords=None):
        """Create map path"""
        if raw_coords:
            map_path = QPainterPath()
            dist = calc.distance(raw_coords[0], raw_coords[-1])
            (self.map_scaled, self.map_size, self.map_offset
             ) = calc.zoom_map(raw_coords, self.global_scale)
            for index, coords in enumerate(self.map_scaled):
                if index == 0:
                    map_path.moveTo(*coords)
                else:
                    map_path.lineTo(*coords)
            # Close map loop if start & end distance less than 500 meters
            if dist < 500:
                map_path.closeSubpath()
            # Create start/finish path
            sfinish_path = QPainterPath()
            self.create_sector_path(
                sfinish_path, self.map_scaled, 0, self.wcfg["start_line_length"])
            # Create sectors paths
            sectors_index = minfo.mapping.sectors
            if isinstance(sectors_index, tuple):
                sector_path = QPainterPath()
                for index in sectors_index:
                    self.create_sector_path(
                        sector_path, self.map_scaled, index, self.wcfg["sector_line_length"]
                    )
            else:
                sector_path = None
        else:
            self.map_scaled = None
            self.map_size = 1,1
            self.map_offset = 0,0
            map_path = None
            sfinish_path = None
            sector_path = None

        self.map_path = map_path
        self.sfinish_path = sfinish_path
        self.sector_path = sector_path

    def draw_map_image(self, painter):
        """Draw map image"""
        # Transform map coordinates
        # Player vehicle orientation yaw radians + 180 deg rotation correction
        plr_ori_rad = api.read.vehicle.orientation_yaw_radians() + 3.14159265
        # x, y position & offset relative to player
        rot_pos_x, rot_pos_y = calc.rotate_coordinate(
            plr_ori_rad,   # plr_ori_rad, rotate view
            api.read.vehicle.position_longitudinal() * self.global_scale - self.map_offset[0],
            api.read.vehicle.position_lateral() * self.global_scale - self.map_offset[1]
        )
        # Apply center offset & rotation
        painter.translate(self.area_center - rot_pos_x, self.veh_offset_y - rot_pos_y)
        painter.rotate(calc.rad2deg(plr_ori_rad))

        if self.map_path:
            # Draw map outline
            if self.wcfg["map_outline_width"] > 0:
                painter.setPen(self.pen_outline["map_outline"])
                painter.drawPath(self.map_path)

            # Draw map
            painter.setPen(self.pen_outline["map"])
            painter.drawPath(self.map_path)

        # Draw start/finish line
        if self.wcfg["show_start_line"] and self.sfinish_path:
            painter.setPen(self.pen_outline["sfinish"])
            painter.drawPath(self.sfinish_path)

        # Draw sectors line
        if self.wcfg["show_sector_line"] and self.sector_path:
            painter.setPen(self.pen_outline["sector"])
            painter.drawPath(self.sector_path)

        painter.resetTransform()

    def draw_vehicle(self, painter, veh_info, veh_draw_order):
        """Draw vehicles"""
        if self.wcfg["show_circle_vehicle_shape"]:
            draw_shape = painter.drawEllipse
        else:
            draw_shape = painter.drawPolygon

        # Draw vehicle within view range
        for index in veh_draw_order:
            data = veh_info[index]
            # Draw player vehicle
            if data.isPlayer:
                painter.setPen(self.pen_outline["player"])
                painter.setBrush(self.color_vehicle(data))
                painter.translate(self.area_center, self.veh_offset_y)
                draw_shape(self.veh_shape)

                if self.wcfg["show_vehicle_class_standings"]:
                    painter.setPen(self.pen_text["player"])
                    painter.drawText(self.veh_text_shape, Qt.AlignCenter, f"{data.positionOverall}")
                painter.resetTransform()

            # Draw opponent vehicle in view range
            elif data.relativeStraightDistance < self.view_range:
                # Rotated position relative to player
                # Position = raw position * global scale + offset
                pos_x = data.relativeRotatedPositionX * self.global_scale + self.area_center
                pos_y = data.relativeRotatedPositionY * self.global_scale + self.veh_offset_y
                painter.translate(pos_x, pos_y)

                if not self.wcfg["show_circle_vehicle_shape"]:
                    painter.rotate(calc.rad2deg(-data.relativeOrientationRadians))

                painter.setPen(self.pen_outline["opponent"])
                painter.setBrush(self.color_vehicle(data))
                draw_shape(self.veh_shape)

                if self.wcfg["show_vehicle_class_standings"]:
                    if not self.wcfg["show_circle_vehicle_shape"]:
                        painter.resetTransform()
                        painter.translate(pos_x, pos_y)
                    painter.setPen(self.pen_text["opponent"])
                    painter.drawText(self.veh_text_shape, Qt.AlignCenter, f"{data.positionOverall}")
                painter.resetTransform()

    def draw_map_mask_pixmap(self):
        """Map mask pixmap"""
        self.pixmap_mask.fill(Qt.black)
        painter = QPainter(self.pixmap_mask)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        rad_gra = QRadialGradient(self.area_center, self.area_center, self.area_center)
        rad_gra.setColorAt(calc.zero_one(self.wcfg["fade_in_radius"]), Qt.transparent)
        rad_gra.setColorAt(calc.zero_one(self.wcfg["fade_out_radius"]), Qt.black)
        painter.setBrush(rad_gra)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.area_size, self.area_size)

    # Additional methods
    def color_vehicle(self, veh_info):
        """Compare lap differences & set color"""
        if veh_info.isYellow and not veh_info.inPit:
            return self.brush_overall["yellow"]
        if veh_info.inPit and not veh_info.isPlayer:
            return self.brush_overall["in_pit"]
        if veh_info.isPlayer:
            return self.brush_overall["player"]
        if veh_info.positionOverall == 1:
            return self.brush_overall["leader"]
        if veh_info.isLapped > 0:
            return self.brush_overall["laps_ahead"]
        if veh_info.isLapped < 0:
            return self.brush_overall["laps_behind"]
        return self.brush_overall["same_lap"]

    def create_sector_path(self, path, dataset, node_index, length):
        """Create sector line path"""
        max_node = len(dataset) - 1
        pos_x1, pos_y1, pos_x2, pos_y2 = calc.line_intersect_coords(
            dataset[calc.zero_max(node_index, max_node)],  # point a
            dataset[calc.zero_max(node_index + 1, max_node)],  # point b
            1.57079633,  # 90 degree rotation
            length
        )
        path.moveTo(pos_x1, pos_y1)
        path.lineTo(pos_x2, pos_y2)
        return path

    def set_pen_style(self, color: str, width: int, rounded: bool = False):
        """Set pen style"""
        if width > 0:
            pen = QPen()
            pen.setWidth(width)
            pen.setColor(color)
            if rounded:
                pen.setJoinStyle(Qt.RoundJoin)
        else:
            pen = Qt.NoPen
        return pen

    def set_brush_style(self, color: str):
        """Set brush style"""
        return QBrush(color, Qt.SolidPattern)
