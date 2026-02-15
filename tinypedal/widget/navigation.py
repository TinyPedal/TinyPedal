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
                self.veh_size * 0.5,
                self.veh_size * 0.5,
                self.veh_size,
                self.veh_size,
            )
        else:
            self.veh_shape = (
                QPointF(self.veh_size, self.veh_size * 0.5),
                QPointF(self.veh_size * 1.5, self.veh_size * 1.5),
                QPointF(self.veh_size, self.veh_size * 1.3),
                QPointF(self.veh_size * 0.5, self.veh_size * 1.5),
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

        self.pixmap_veh_player = self.draw_vehicle_pixmap("player")
        self.pixmap_veh_leader = self.draw_vehicle_pixmap("leader")
        self.pixmap_veh_in_pit = self.draw_vehicle_pixmap("in_pit")
        self.pixmap_veh_yellow = self.draw_vehicle_pixmap("yellow")
        self.pixmap_veh_laps_ahead = self.draw_vehicle_pixmap("laps_ahead")
        self.pixmap_veh_laps_behind = self.draw_vehicle_pixmap("laps_behind")
        self.pixmap_veh_same_lap = self.draw_vehicle_pixmap("same_lap")

        self.pen_outline = QPen()
        self.pen_outline.setJoinStyle(Qt.RoundJoin)
        self.pen_outline.setWidth(self.wcfg["map_width"] + self.wcfg["map_outline_width"])
        self.pen_outline.setColor(self.wcfg["map_outline_color"])
        self.pen_map = QPen()
        self.pen_map.setJoinStyle(Qt.RoundJoin)
        self.pen_map.setWidth(self.wcfg["map_width"])
        self.pen_map.setColor(self.wcfg["map_color"])
        self.pen_sfinish = QPen()
        self.pen_sfinish.setWidth(self.wcfg["start_line_width"])
        self.pen_sfinish.setColor(self.wcfg["start_line_color"])
        self.pen_sector = QPen()
        self.pen_sector.setWidth(self.wcfg["sector_line_width"])
        self.pen_sector.setColor(self.wcfg["sector_line_color"])
        self.pen_text = QPen()
        self.pen_text.setColor(self.wcfg["font_color"])

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
            self.pixmap_background.fill(self.wcfg["bkg_color"])
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
            brush.setColor(self.wcfg["bkg_color_circle"])
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
                painter.setPen(self.pen_outline)
                painter.drawPath(self.map_path)

            # Draw map
            painter.setPen(self.pen_map)
            painter.drawPath(self.map_path)

        # Draw start/finish line
        if self.wcfg["show_start_line"] and self.sfinish_path:
            painter.setPen(self.pen_sfinish)
            painter.drawPath(self.sfinish_path)

        # Draw sectors line
        if self.wcfg["show_sector_line"] and self.sector_path:
            painter.setPen(self.pen_sector)
            painter.drawPath(self.sector_path)

        painter.resetTransform()

    def draw_vehicle(self, painter, veh_info, veh_draw_order):
        """Draw vehicles"""
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        if self.wcfg["show_vehicle_standings"]:
            painter.setPen(self.pen_text)

        # Draw vehicle within view range
        for index in veh_draw_order:
            data = veh_info[index]
            # Draw player vehicle
            if data.isPlayer:
                painter.translate(self.area_center, self.veh_offset_y)
                painter.drawPixmap(-self.veh_size, -self.veh_size, self.pixmap_veh_player)

                if self.wcfg["show_vehicle_standings"]:
                    painter.drawText(
                        self.veh_text_shape, Qt.AlignCenter,
                        f"{data.positionOverall}")
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
                painter.drawPixmap(
                    -self.veh_size, -self.veh_size,
                    self.color_veh_pixmap(data))

                if self.wcfg["show_vehicle_standings"]:
                    painter.resetTransform()
                    painter.translate(pos_x, pos_y)
                    painter.drawText(
                        self.veh_text_shape, Qt.AlignCenter,
                        f"{data.positionOverall}")
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

    def draw_vehicle_pixmap(self, suffix):
        """Draw vehicles pixmap"""
        pixmap_veh = QPixmap(self.veh_size * 2, self.veh_size * 2)
        pixmap_veh.fill(Qt.transparent)
        painter = QPainter(pixmap_veh)
        painter.setRenderHint(QPainter.Antialiasing, True)
        if self.wcfg["vehicle_outline_width"] > 0:
            pen = QPen()
            pen.setWidth(self.wcfg["vehicle_outline_width"])
            pen.setColor(self.wcfg["vehicle_outline_color"])
            painter.setPen(pen)
        else:
            painter.setPen(Qt.NoPen)
        brush = QBrush(Qt.SolidPattern)
        brush.setColor(self.wcfg[f"vehicle_color_{suffix}"])
        painter.setBrush(brush)
        if self.wcfg["show_circle_vehicle_shape"]:
            painter.drawEllipse(self.veh_shape)
        else:
            painter.drawPolygon(self.veh_shape)
        return pixmap_veh

    # Additional methods
    def color_veh_pixmap(self, veh_info):
        """Compare lap differences & set color"""
        if veh_info.positionOverall == 1:
            return self.pixmap_veh_leader
        if veh_info.inPit:
            return self.pixmap_veh_in_pit
        if veh_info.isYellow and not veh_info.inPit:
            return self.pixmap_veh_yellow
        if veh_info.isLapped > 0:
            return self.pixmap_veh_laps_ahead
        if veh_info.isLapped < 0:
            return self.pixmap_veh_laps_behind
        return self.pixmap_veh_same_lap

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
