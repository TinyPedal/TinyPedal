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
Track map Widget
"""

from PySide2.QtCore import QRectF, Qt
from PySide2.QtGui import QBrush, QPainter, QPainterPath, QPen, QPixmap

from .. import calculation as calc
from ..api_control import api
from ..formatter import random_color_class
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
        self.show_position_in_class = self.wcfg["enable_multi_class_styling"] and self.wcfg["show_position_in_class"]
        self.display_detail_level = max(self.wcfg["display_detail_level"], 0)

        veh_size_base = self.wcfg["font_size"] + round(font_m.width * self.wcfg["bar_padding"])
        veh_size_opt = veh_size_base * max(self.wcfg["vehicle_scale"], 1.0)
        veh_size_plr = veh_size_base * max(self.wcfg["vehicle_scale_player"], 1.0)

        self.veh_shape = QRectF(-veh_size_opt * 0.5, -veh_size_opt * 0.5, veh_size_opt, veh_size_opt)
        self.veh_shape_player = QRectF(-veh_size_plr * 0.5, -veh_size_plr * 0.5, veh_size_plr, veh_size_plr)
        self.veh_text_shape = QRectF(-veh_size_base * 0.5, -veh_size_base * 0.5 + font_m.voffset, veh_size_base, veh_size_base)

        # Config canvas
        self.area_size = max(self.wcfg["area_size"], 100)
        self.area_margin = min(max(self.wcfg["area_margin"], 0), int(self.area_size/4))
        self.temp_map_size = self.area_size - self.area_margin * 2

        self.resize(self.area_size, self.area_size)
        self.pixmap_map = QPixmap(self.area_size, self.area_size)
        self.pen_veh = (
            self.set_veh_pen_style(self.wcfg["vehicle_outline_color"], self.wcfg["vehicle_outline_width"]),
            self.set_veh_pen_style(self.wcfg["vehicle_outline_player_color"], self.wcfg["vehicle_outline_player_width"]),
            self.set_veh_pen_style(self.wcfg["vehicle_outline_color_laps_ahead"], self.wcfg["vehicle_outline_width_laps_ahead"]),
            self.set_veh_pen_style(self.wcfg["vehicle_outline_color_laps_behind"], self.wcfg["vehicle_outline_width_laps_behind"]),
        )
        self.pen_text = QPen(self.wcfg["font_color"]), QPen(self.wcfg["font_color_player"])

        self.brush_classes = {}
        self.brush_overall = self.set_veh_brush_style(
            "player","leader","in_pit","yellow","laps_ahead","laps_behind","same_lap"
        )

        if self.wcfg["show_pitout_prediction"]:
            self.show_while_requested = self.wcfg["show_pitout_prediction_while_requested_pitstop"]
            self.prediction_count = min(max(self.wcfg["number_of_prediction"], 1), 20)
            self.pitout_time_offset = max(self.wcfg["pitout_time_offset"], 0)
            self.min_pit_time = self.wcfg["pitout_duration_minimum"] + self.pitout_time_offset
            self.pit_time_increment = max(self.wcfg["pitout_duration_increment"], 1)
            if self.wcfg["enabled_fixed_pitout_prediction"]:
                self.fixed_pit_times = tuple(sorted(set(self.set_fixed_pit_time())))
            self.pen_pit_styles = (
                self.set_veh_pen_style(self.wcfg["prediction_outline_color"], self.wcfg["prediction_outline_width"]),
                QPen(self.wcfg["font_color_pitstop_duration"]),
            )
            self.pit_text_shape = QRectF(
                -veh_size_base * 0.5 - 2,
                font_m.voffset - veh_size_opt * 0.5 - veh_size_base - 3,
                veh_size_base + 4,
                veh_size_base,
            )

        if self.wcfg["show_proximity_circle"]:
            self.pen_proximity = self.set_veh_pen_style(
                self.wcfg["proximity_circle_color"],
                self.wcfg["proximity_circle_width"],
            )
            self.rect_proximity = QRectF()

        # Last data
        self.last_modified = 0
        self.last_veh_data_version = None
        self.circular_map = True
        self.map_scaled = None
        self.map_range = (0, 10, 0, 10)
        self.map_scale = 1.0
        self.map_offset = (0, 0)
        self.map_orient = 0.0  # radians

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
            raw_data = minfo.mapping.coordinates if data != -1 else None
            map_path = self.create_map_path(raw_data)
            self.draw_map_image(map_path, self.circular_map)
            if self.wcfg["show_proximity_circle"]:
                self.update_proximity_rect()

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap_map)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if self.map_scaled:
            self.draw_vehicle_on_map(
                painter, minfo.vehicles.dataSet, minfo.relative.drawOrder
            )
        else:
            self.draw_vehicle_on_circle(
                painter, minfo.vehicles.dataSet, minfo.relative.drawOrder
            )

        if self.wcfg["show_pitout_prediction"]:
            self.draw_pitout_prediction(
                painter,
                self.map_scaled,
                minfo.vehicles.dataSet[minfo.vehicles.playerIndex],
            )

    def create_map_path(self, raw_coords=None):
        """Create map path"""
        map_path = QPainterPath()
        if raw_coords:
            dist = calc.distance(raw_coords[0], raw_coords[-1])
            angle = max(int(self.wcfg["display_orientation"]), 0)
            angle = angle - angle // 360 * 360
            self.map_orient = calc.deg2rad(angle)
            (self.map_scaled, self.map_range, self.map_scale, self.map_offset
             ) = calc.scale_map(raw_coords, self.area_size, self.area_margin, angle)

            total_nodes = len(self.map_scaled) - 1
            skip_node = calc.skip_map_nodes(total_nodes, self.temp_map_size * 3, self.display_detail_level)
            last_skip = 0
            for index, coords in enumerate(self.map_scaled):
                if index == 0:
                    map_path.moveTo(*coords)
                elif index >= total_nodes:  # don't skip last node
                    map_path.lineTo(*coords)
                elif last_skip >= skip_node:
                    map_path.lineTo(*coords)
                    last_skip = 0
                last_skip += 1

            # Close map loop if start & end distance less than 500 meters
            if dist < 500:
                map_path.closeSubpath()
                self.circular_map = True
            else:
                self.circular_map = False

        # Temp(circular) map
        else:
            self.map_scaled = None
            self.circular_map = True
            self.map_orient = 0
            map_path.addEllipse(
                self.area_margin,
                self.area_margin,
                self.temp_map_size,
                self.temp_map_size,
            )
        return map_path

    def draw_map_image(self, map_path, circular_map=True):
        """Draw map image separately"""
        if self.wcfg["show_background"]:
            self.pixmap_map.fill(self.wcfg["bkg_color"])
        else:
            self.pixmap_map.fill(Qt.transparent)
        painter = QPainter(self.pixmap_map)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Draw map inner background
        if self.wcfg["show_map_background"] and circular_map:
            brush = QBrush(Qt.SolidPattern)
            brush.setColor(self.wcfg["bkg_color_map"])
            painter.setBrush(brush)
            painter.setPen(Qt.NoPen)
            painter.drawPath(map_path)
            painter.setBrush(Qt.NoBrush)

        # Set pen style
        pen = QPen()
        pen.setJoinStyle(Qt.RoundJoin)

        # Draw map outline
        if self.wcfg["map_outline_width"] > 0:
            pen.setWidth(self.wcfg["map_width"] + self.wcfg["map_outline_width"])
            pen.setColor(self.wcfg["map_outline_color"])
            painter.setPen(pen)
            painter.drawPath(map_path)

        # Draw map
        pen.setWidth(self.wcfg["map_width"])
        pen.setColor(self.wcfg["map_color"])
        painter.setPen(pen)
        painter.drawPath(map_path)

        # Draw sector
        if self.map_scaled:
            # SF line
            if self.wcfg["show_start_line"]:
                pen.setWidth(self.wcfg["start_line_width"])
                pen.setColor(self.wcfg["start_line_color"])
                painter.setPen(pen)
                pos_x1, pos_y1, pos_x2, pos_y2 = calc.line_intersect_coords(
                    self.map_scaled[0],  # point a
                    self.map_scaled[1],  # point b
                    1.57079633,  # 90 degree rotation
                    self.wcfg["start_line_length"]
                )
                painter.drawLine(pos_x1, pos_y1, pos_x2, pos_y2)

            # Sector lines
            sectors_index = minfo.mapping.sectors
            if self.wcfg["show_sector_line"] and isinstance(sectors_index, tuple):
                pen.setWidth(self.wcfg["sector_line_width"])
                pen.setColor(self.wcfg["sector_line_color"])
                painter.setPen(pen)

                for index in sectors_index:
                    pos_x1, pos_y1, pos_x2, pos_y2 = calc.line_intersect_coords(
                        self.map_scaled[index],  # point a
                        self.map_scaled[index + 1],  # point b
                        1.57079633,  # 90 degree rotation
                        self.wcfg["sector_line_length"]
                    )
                    painter.drawLine(pos_x1, pos_y1, pos_x2, pos_y2)
        else:
            # SF line
            if self.wcfg["show_start_line"]:
                pen.setWidth(self.wcfg["start_line_width"])
                pen.setColor(self.wcfg["start_line_color"])
                painter.setPen(pen)
                painter.drawLine(
                    self.area_margin - self.wcfg["start_line_length"],
                    self.area_size * 0.5,
                    self.area_margin + self.wcfg["start_line_length"],
                    self.area_size * 0.5
                )

    def draw_vehicle_on_circle(self, painter, veh_info, veh_draw_order):
        """Draw vehicles on temporary circle map"""
        offset = self.area_size * 0.5

        for index in veh_draw_order:
            data = veh_info[index]

            inpit_offset = self.wcfg["font_size"] * data.inPit
            pos_x, pos_y = calc.rotate_coordinate(
                6.2831853 * data.currentLapProgress,
                self.temp_map_size / -2 + inpit_offset,  # x pos
                0,  # y pos
            )
            painter.translate(offset + pos_x, offset + pos_y)

            painter.setPen(self.outline_vehicle(data))
            painter.setBrush(self.color_vehicle(data))

            if data.isPlayer:
                painter.drawEllipse(self.veh_shape_player)
            else:
                painter.drawEllipse(self.veh_shape)

            # Draw text standings
            if self.wcfg["show_vehicle_standings"]:
                if self.show_position_in_class:
                    place_veh = data.positionInClass
                else:
                    place_veh = data.positionOverall
                painter.setPen(self.pen_text[data.isPlayer])
                painter.drawText(self.veh_text_shape, Qt.AlignCenter, f"{place_veh}")
            painter.resetTransform()

    def draw_vehicle_on_map(self, painter, veh_info, veh_draw_order):
        """Draw vehicles on track map"""
        # Position = coords * scale - (min_range * scale - offset)
        x_offset = self.map_range[0] * self.map_scale - self.map_offset[0]  # min range x, offset x
        y_offset = self.map_range[2] * self.map_scale - self.map_offset[1]  # min range y, offset y

        for index in veh_draw_order:
            data = veh_info[index]

            if self.map_orient:
                rot_x, rot_y = calc.rotate_coordinate(self.map_orient, data.worldPositionX, data.worldPositionY)
                pos_x = rot_x * self.map_scale - x_offset
                pos_y = rot_y * self.map_scale - y_offset
            else:
                pos_x = data.worldPositionX * self.map_scale - x_offset
                pos_y = data.worldPositionY * self.map_scale - y_offset
            painter.translate(pos_x, pos_y)

            painter.setPen(self.outline_vehicle(data))
            painter.setBrush(self.color_vehicle(data))

            if data.isPlayer:
                painter.drawEllipse(self.veh_shape_player)
                if self.wcfg["show_proximity_circle"]:
                    painter.setPen(self.pen_proximity)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(self.rect_proximity)
            else:
                painter.drawEllipse(self.veh_shape)

            # Draw text standings
            if self.wcfg["show_vehicle_standings"]:
                if self.show_position_in_class:
                    place_veh = data.positionInClass
                else:
                    place_veh = data.positionOverall
                painter.setPen(self.pen_text[data.isPlayer])
                painter.drawText(self.veh_text_shape, Qt.AlignCenter, f"{place_veh}")
            painter.resetTransform()

    def draw_pitout_prediction(self, painter, map_data, plr_veh_info):
        """Draw pitout prediction circles"""
        # Skip drawing
        if not plr_veh_info.inPit:
            if not self.show_while_requested:  # if not in pit
                return
            if not plr_veh_info.pitRequested:  # not requested pit
                return

        # Verify data set
        if not map_data:  # x, y coords
            return
        dist_data = minfo.mapping.elevations
        if not dist_data:  # distance, z coords
            return
        deltabest_data = minfo.delta.deltaBestData  # distance, seconds
        deltabest_max_index = len(deltabest_data) - 1
        if deltabest_max_index < 2:
            return
        laptime_best = deltabest_data[-1][1]
        laptime_pace = minfo.delta.lapTimePace
        if laptime_best < 1 or laptime_pace < 1:
            return

        laptime_scale = laptime_best / laptime_pace
        dist_end_index = min(len(dist_data), len(map_data)) - 1

        # Calculate pit timer & target time
        if plr_veh_info.pitRequested and not plr_veh_info.inPit:  # out pit lane
            pitin_time = target_node_time(minfo.mapping.pitEntryPosition, deltabest_data, deltabest_max_index, laptime_scale)
            pos_curr_time = target_node_time(api.read.lap.distance(), deltabest_data, deltabest_max_index, laptime_scale)
            pit_timer = pos_curr_time - pitin_time
            target_pit_time = self.min_pit_time
        else:  # in pit lane
            pit_timer = plr_veh_info.pitTimer.elapsed
            target_pit_time = target_pitstop_duration(pit_timer, self.min_pit_time, self.pit_time_increment)

        # Find time_into from deltabest_data, scale to match laptime_pace
        pitout_time = target_node_time(minfo.mapping.pitExitPosition, deltabest_data, deltabest_max_index, laptime_scale)
        pitout_time_extend = pit_timer + pitout_time

        painter.setBrush(Qt.NoBrush)

        for target_pit_time in self.get_target_pit_time(target_pit_time, pit_timer):
            # Calc estimated pitout_time_into based on laptime_pace
            offset_time_into = pitout_time_extend - target_pit_time
            pitout_time_into = (offset_time_into - offset_time_into // laptime_pace * laptime_pace) * laptime_scale
            # Find estimated distance from deltabest_data
            index_higher = calc.binary_search_higher_column(
                deltabest_data, pitout_time_into, 0, deltabest_max_index, 1)
            if index_higher > 0:
                index_lower = index_higher - 1
                estimate_dist = calc.linear_interp(
                    pitout_time_into,
                    deltabest_data[index_lower][1],
                    deltabest_data[index_lower][0],
                    deltabest_data[index_higher][1],
                    deltabest_data[index_higher][0],
                )
            else:
                estimate_dist = 0

            dist_node_index = calc.binary_search_higher_column(dist_data, estimate_dist, 0, dist_end_index)
            painter.translate(*map_data[dist_node_index])
            painter.setPen(self.pen_pit_styles[0])
            painter.drawEllipse(self.veh_shape)

            # Draw text pitstop duration
            if self.wcfg["show_pitstop_duration"]:
                painter.fillRect(self.pit_text_shape, self.wcfg["bkg_color_pitstop_duration"])
                painter.setPen(self.pen_pit_styles[1])
                text_time = f"{min(target_pit_time - self.pitout_time_offset, 999):.0f}"
                painter.drawText(self.pit_text_shape, Qt.AlignCenter, text_time)

            painter.resetTransform()

    def get_target_pit_time(self, target_pit_time: float, pit_timer: float):
        """Generate target pit time"""
        max_prediction = self.prediction_count
        # Fixed time
        if self.wcfg["enabled_fixed_pitout_prediction"]:
            pass_time = minfo.mapping.pitPassTime
            valid_count = 0
            for fixed_time in self.fixed_pit_times:
                if valid_count >= max_prediction:
                    break
                fixed_time += pass_time
                if fixed_time > pit_timer:
                    valid_count += 1
                    yield fixed_time
        # Auto incremented time
        else:
            increment = self.pit_time_increment
            for idx in range(max_prediction):
                yield target_pit_time + increment * idx

    def classes_style(self, class_name: str) -> str:
        """Get vehicle class style from brush cache"""
        if class_name in self.brush_classes:
            return self.brush_classes[class_name]
        # Get vehicle class style from user defined dictionary
        brush = QBrush(Qt.SolidPattern)
        styles = self.cfg.user.classes.get(class_name)
        if styles is not None:
            brush.setColor(styles["color"])
        else:
            brush.setColor(random_color_class(class_name))
        # Add to brush cache
        self.brush_classes[class_name] = brush
        return brush

    def update_proximity_rect(self):
        """Update proximity circle rect"""
        proxi_radius = max(self.wcfg["proximity_circle_radius"], 1)
        proxi_x = -proxi_radius * self.map_scale
        proxi_y = proxi_radius * 2 * self.map_scale
        self.rect_proximity.setRect(proxi_x, proxi_x, proxi_y, proxi_y)

    # Additional methods
    def outline_vehicle(self, veh_info):
        """Set vehicle outline"""
        if veh_info.isPlayer:
            return self.pen_veh[1]
        if not self.wcfg["show_lap_difference_outline"]:
            return self.pen_veh[0]
        if veh_info.isLapped > 0:
            return self.pen_veh[2]
        if veh_info.isLapped < 0:
            return self.pen_veh[3]
        return self.pen_veh[0]

    def color_vehicle(self, veh_info):
        """Set vehicle color"""
        if veh_info.isYellow and not veh_info.inPit:
            return self.brush_overall["yellow"]
        if veh_info.inPit and not veh_info.isPlayer:
            return self.brush_overall["in_pit"]
        if self.wcfg["enable_multi_class_styling"]:
            if self.wcfg["show_custom_player_color_in_multi_class"] and veh_info.isPlayer:
                return self.brush_overall["player"]
            return self.classes_style(veh_info.vehicleClass)
        if veh_info.isPlayer:
            return self.brush_overall["player"]
        if veh_info.positionOverall == 1:
            return self.brush_overall["leader"]
        if veh_info.isLapped > 0:
            return self.brush_overall["laps_ahead"]
        if veh_info.isLapped < 0:
            return self.brush_overall["laps_behind"]
        return self.brush_overall["same_lap"]

    def set_veh_pen_style(self, color: str, width: int):
        """Set vehicle pen style"""
        if width > 0:
            pen_veh = QPen()
            pen_veh.setWidth(width)
            pen_veh.setColor(color)
        else:
            pen_veh = Qt.NoPen
        return pen_veh

    def set_veh_brush_style(self, *suffixes: str) -> dict:
        """Set vehicle brush style"""
        return {
            suffix: QBrush(self.wcfg[f"vehicle_color_{suffix}"], Qt.SolidPattern)
            for suffix in suffixes
        }

    def set_fixed_pit_time(self):
        """Set fixed target pit time"""
        for idx in range(1, 11):
            fixed_time = self.wcfg[f"fixed_pitstop_duration_{idx}"]
            if fixed_time >= 0:
                yield fixed_time + self.pitout_time_offset


def target_pitstop_duration(pit_timer: float, min_pit_time: float, pit_time_increment: float) -> float:
    """Target pitstop duration = min pit duration + pit duration increment * number of increments"""
    overflow_increments = max(pit_timer - min_pit_time + pit_time_increment, 0) // pit_time_increment
    return min_pit_time + pit_time_increment * overflow_increments


def target_node_time(position: float, delta_data: tuple, max_index: int, laptime_scale: float) -> float:
    """Calculate target node time from target position and deltabest dataset"""
    pitin_node_index = calc.binary_search_higher_column(delta_data, position, 0, max_index, 0)
    return delta_data[pitin_node_index][1] / laptime_scale
