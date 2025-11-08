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
Radar Widget
"""

from itertools import islice
from typing import NamedTuple

from PySide2.QtCore import QRectF, Qt
from PySide2.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
    QRadialGradient,
)

from .. import calculation as calc
from ..api_control import api
from ..module_info import minfo
from ._base import Overlay


class IndicatorDimension(NamedTuple):
    """Indicator dimension"""

    min_range_x: float = 0
    max_range_x: float = 0
    max_range_y: float = 0
    crit_range: float = 0
    width: float = 0
    edge: float = 0
    offset: float = 0


class DistanceRect(NamedTuple):
    """Distance rectangle"""

    ahead: float = 0
    behind: float = 0
    side: float = 0


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)

        # Config variable
        self.radar_radius = max(self.wcfg["radar_radius"], 5)
        self.area_center = round(  # limit minimum global scale relative to radar radius
            self.radar_radius * max(self.wcfg["global_scale"], 5 / self.radar_radius)
        )  # round to int
        self.area_size = self.area_center * 2
        self.global_scale = self.area_center / self.radar_radius  # recalibrate

        self.veh_width = max(self.wcfg["vehicle_width"], 0.01)
        self.veh_length = max(self.wcfg["vehicle_length"], 0.01)
        self.veh_shape = QRectF(
            -self.veh_width * self.global_scale * 0.5,
            -self.veh_length * self.global_scale * 0.5,
            self.veh_width * self.global_scale,
            self.veh_length * self.global_scale
        )
        self.vehicle_hide_range = self.set_range_dimension("vehicle_maximum_visible_distance")
        self.radar_hide_range = self.set_range_dimension("auto_hide_minimum_distance")
        self.radar_fade_factor = self.set_radar_fade_factor(self.radar_radius)
        self.radar_fade_color = QColor(0, 0, 0)

        # Overlap indicator
        self.indicator_dimension = self.calc_indicator_dimension(self.veh_width, self.veh_length)
        self.indicator_color = QColor(self.wcfg["indicator_color_nearby"])
        self.indicator_color_critical = QColor(self.wcfg["indicator_color_critical"])
        if self.wcfg["show_overlap_indicator_in_cone_style"]:
            cone_angle = max(self.wcfg["overlap_cone_angle"], 10)
            left_start = calc.asym_max(180 - cone_angle / 2, 90, 180)
            right_start = calc.asym_max(0 - cone_angle / 2, -270, 90)
            self.brush_cone_l = QBrush(QRadialGradient(self.area_center, self.area_center, self.area_center))
            self.brush_cone_r = QBrush(QRadialGradient(self.area_center, self.area_center, self.area_center))
            self.gradient_cone = [[0.1, Qt.transparent], [1, Qt.transparent]]
            self.cone_angle_l = left_start * 16, cone_angle * 16
            self.cone_angle_r = right_start * 16, cone_angle * 16

        # Config canvas
        self.resize(self.area_size, self.area_size)
        self.pixmap_mask = QPixmap(self.area_size, self.area_size)
        self.pixmap_marks = QPixmap(self.area_size, self.area_size)
        self.rect_radar = QRectF(0, 0, self.area_size, self.area_size)

        # Vehicle pen & brush
        if self.wcfg["vehicle_outline_width"] > 0:
            self.pen_veh = QPen()
            self.pen_veh.setWidth(self.wcfg["vehicle_outline_width"])
            self.pen_veh.setColor(self.wcfg["vehicle_outline_color"])
        else:
            self.pen_veh = Qt.NoPen
        self.brush_veh = QBrush(Qt.SolidPattern)

        self.draw_radar_marks(self.area_center)
        self.draw_radar_mask()

        # Last data
        self.last_veh_data_version = None
        self.autohide_timer_start = 1
        self.show_radar = True
        self.in_garage = True

    def timerEvent(self, event):
        """Update when vehicle on track"""
        self.in_garage = api.read.vehicle.in_garage()

        # Auto hide radar if no nearby vehicles
        if self.wcfg["auto_hide"]:
            self.set_autohide_state()

        # Vehicles
        veh_data_version = minfo.vehicles.dataSetVersion
        if self.last_veh_data_version != veh_data_version:
            self.last_veh_data_version = veh_data_version
            self.update()

    # GUI update methods
    def paintEvent(self, event):
        """Draw"""
        if self.show_radar:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            # Draw marks
            painter.drawPixmap(0, 0, self.pixmap_marks)
            # Draw vehicles
            self.draw_vehicle(painter, self.indicator_dimension)
            # Apply mask
            if self.wcfg["show_edge_fade_out"]:
                painter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
                painter.drawPixmap(0, 0, self.pixmap_mask)
            # Draw background below map & mask
            if self.wcfg["show_background"]:
                painter.setCompositionMode(QPainter.CompositionMode_DestinationOver)
                painter.fillRect(self.rect_radar, self.wcfg["bkg_color"])
            # Apply radar fade mask
            if self.wcfg["enable_radar_fade"] and not self.in_garage:
                radar_alpha = self.radar_fade_factor * (
                    self.radar_radius - minfo.vehicles.nearestLine)
                if radar_alpha < 1:
                    if radar_alpha < 0:
                        radar_alpha = 0
                    self.radar_fade_color.setAlphaF(radar_alpha)
                    painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
                    painter.fillRect(self.rect_radar, self.radar_fade_color)

    def draw_radar_mask(self):
        """Draw radar mask"""
        self.pixmap_mask.fill(Qt.black)
        painter = QPainter(self.pixmap_mask)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        rad_gra = QRadialGradient(self.area_center, self.area_center, self.area_center)
        rad_gra.setColorAt(calc.zero_one(self.wcfg["edge_fade_in_radius"]), Qt.transparent)
        rad_gra.setColorAt(calc.zero_one(self.wcfg["edge_fade_out_radius"]), Qt.black)
        painter.setBrush(rad_gra)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.area_size, self.area_size)

    def draw_radar_marks(self, center):
        """Draw radar marks & player vehicle"""
        self.pixmap_marks.fill(Qt.transparent)
        painter = QPainter(self.pixmap_marks)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Draw center mark
        pen = QPen()
        pen.setCapStyle(Qt.FlatCap)
        if self.wcfg["show_center_mark"]:
            if not self.wcfg["center_mark_style"]:
                pen.setStyle(Qt.DashLine)
            else:
                pen.setStyle(Qt.SolidLine)
            mark_scale = self.wcfg["center_mark_radius"] * self.global_scale
            pen.setWidth(self.wcfg["center_mark_width"])
            pen.setColor(self.wcfg["center_mark_color"])
            painter.setPen(pen)
            painter.drawLine(center, center, center - mark_scale, center)
            painter.drawLine(center, center, center, center + mark_scale)
            painter.drawLine(center, center, center, center - mark_scale)
            painter.drawLine(center, center, center + mark_scale, center)

        if self.wcfg["show_angle_mark"]:
            if not self.wcfg["angle_mark_style"]:
                pen.setStyle(Qt.DashLine)
            else:
                pen.setStyle(Qt.SolidLine)
            mark_scale = self.wcfg["angle_mark_radius"] * self.global_scale
            mark_scale *= 0.7071  # radius correction
            pen.setWidth(self.wcfg["angle_mark_width"])
            pen.setColor(self.wcfg["angle_mark_color"])
            painter.setPen(pen)
            painter.drawLine(center, center, center - mark_scale, center + mark_scale)
            painter.drawLine(center, center, center + mark_scale, center - mark_scale)
            painter.drawLine(center, center, center - mark_scale, center - mark_scale)
            painter.drawLine(center, center, center + mark_scale, center + mark_scale)

        # Draw circle mark
        if self.wcfg["show_distance_circle"]:
            painter.setBrush(Qt.NoBrush)
            for idx in range(1, 6):
                self.draw_circle_mark(
                    painter, pen,
                    self.wcfg[f"distance_circle_{idx}_style"],
                    self.wcfg[f"distance_circle_{idx}_radius"],
                    self.wcfg[f"distance_circle_{idx}_width"],
                    self.wcfg[f"distance_circle_{idx}_color"]
                )

        # Draw player vehicle (one time only)
        painter.setPen(self.pen_veh)
        self.brush_veh.setColor(self.wcfg["vehicle_color_player"])
        painter.setBrush(self.brush_veh)
        painter.translate(self.area_center, self.area_center)
        painter.drawRoundedRect(
            self.veh_shape,
            self.wcfg["vehicle_border_radius"],
            self.wcfg["vehicle_border_radius"]
        )

    def draw_circle_mark(self, painter, pen, style, radius, width, color):
        """Draw circle mark"""
        if radius <= self.radar_radius and width > 0:
            scale = round(radius * self.global_scale)
            pos = self.area_center - scale
            size = scale * 2
            pen.setStyle(Qt.SolidLine if style else Qt.DashLine)
            pen.setWidth(width)
            pen.setColor(color)
            painter.setPen(pen)
            painter.drawEllipse(pos, pos, size, size)

    def draw_warning_cone(
        self, painter, nearest_left, nearest_right, indicator: IndicatorDimension):
        """Draw warning indicator as cone shape"""
        painter.setPen(Qt.NoPen)
        # Draw left side indicator
        if nearest_left > -indicator.max_range_x:
            self.gradient_cone[0][1] = self.warning_color(abs(nearest_left), indicator)
            self.brush_cone_l.gradient().setStops(self.gradient_cone)
            painter.setBrush(self.brush_cone_l)
            painter.drawPie(self.rect_radar, *self.cone_angle_l)

        # Draw right side indicator
        if nearest_right < indicator.max_range_x:
            self.gradient_cone[0][1] = self.warning_color(abs(nearest_right), indicator)
            self.brush_cone_r.gradient().setStops(self.gradient_cone)
            painter.setBrush(self.brush_cone_r)
            painter.drawPie(self.rect_radar, *self.cone_angle_r)

    def draw_warning_indicator(
        self, painter, nearest_left, nearest_right, indicator: IndicatorDimension):
        """Draw warning indicator"""
        # Draw left side indicator
        if nearest_left > -indicator.max_range_x:
            x_left = self.scale_veh_pos(nearest_left)
            pos_left = x_left - indicator.width + indicator.offset
            lin_gra = QLinearGradient(pos_left, 0, x_left + indicator.offset, 0)
            lin_gra.setColorAt(0, Qt.transparent)
            lin_gra.setColorAt(indicator.edge, self.warning_color(abs(nearest_left), indicator))
            lin_gra.setColorAt(1, Qt.transparent)
            painter.fillRect(pos_left, 0, indicator.width, self.area_size, lin_gra)

        # Draw right side indicator
        if nearest_right < indicator.max_range_x:
            x_right = self.scale_veh_pos(nearest_right)
            pos_right = x_right - indicator.offset
            lin_gra = QLinearGradient(pos_right, 0, x_right + indicator.width - indicator.offset, 0)
            lin_gra.setColorAt(0, Qt.transparent)
            lin_gra.setColorAt(1 - indicator.edge, self.warning_color(abs(nearest_right), indicator))
            lin_gra.setColorAt(1, Qt.transparent)
            painter.fillRect(pos_right, 0, indicator.width, self.area_size, lin_gra)

    def draw_vehicle(self, painter, indicator):
        """Draw opponents vehicles"""
        painter.setPen(self.pen_veh)
        # Real size in meters
        nearest_left = -indicator.max_range_x
        nearest_right = indicator.max_range_x

        # Draw opponent vehicle within radar range
        for veh_info in islice(minfo.vehicles.dataSet, minfo.vehicles.totalVehicles):
            if veh_info.isPlayer:
                continue
            # -x = left, +x = right, -y = ahead, +y = behind
            raw_pos_x = veh_info.relativeRotatedPositionX
            raw_pos_y = veh_info.relativeRotatedPositionY
            if (self.vehicle_hide_range.behind > raw_pos_y > -self.vehicle_hide_range.ahead and
                -self.vehicle_hide_range.side < raw_pos_x < self.vehicle_hide_range.side):

                # Find nearest vehicle coordinates
                if (self.wcfg["show_overlap_indicator"] and
                    abs(raw_pos_x) < indicator.max_range_x and
                    abs(raw_pos_y) < indicator.max_range_y):
                    if -indicator.min_range_x > raw_pos_x > nearest_left:
                        nearest_left = raw_pos_x
                    if indicator.min_range_x < raw_pos_x < nearest_right:
                        nearest_right = raw_pos_x

                # Rotated position relative to player
                pos_x = self.scale_veh_pos(raw_pos_x)
                pos_y = self.scale_veh_pos(raw_pos_y)
                angle_deg = calc.rad2deg(-veh_info.relativeOrientationRadians)

                # Draw vehicle
                self.brush_veh.setColor(self.color_lap_diff(veh_info))
                painter.setBrush(self.brush_veh)
                painter.translate(pos_x, pos_y)
                painter.rotate(angle_deg)
                painter.drawRoundedRect(
                    self.veh_shape,
                    self.wcfg["vehicle_border_radius"],
                    self.wcfg["vehicle_border_radius"]
                )
                painter.resetTransform()

        # Draw overlap indicator below vehicle shape
        if self.wcfg["show_overlap_indicator"]:
            painter.setCompositionMode(QPainter.CompositionMode_DestinationOver)
            if self.wcfg["show_overlap_indicator_in_cone_style"]:
                self.draw_warning_cone(painter, nearest_left, nearest_right, indicator)
            else:
                self.draw_warning_indicator(painter, nearest_left, nearest_right, indicator)

        # Draw circle background
        if self.wcfg["show_circle_background"]:
            painter.setCompositionMode(QPainter.CompositionMode_DestinationOver)
            painter.fillRect(self.rect_radar, self.wcfg["bkg_color_circle"])

    # Additional methods
    def scale_veh_pos(self, position):
        """Scale vehicle position coordinate to global scale"""
        return position * self.global_scale + self.area_center

    def warning_color(self, nearest_x, indicator: IndicatorDimension):
        """Overtaking warning color"""
        alpha = 1 - (nearest_x - indicator.min_range_x) / indicator.max_range_x
        if nearest_x <= indicator.crit_range:
            self.indicator_color_critical.setAlphaF(alpha)  # alpha changes with nearest distance
            return self.indicator_color_critical
        self.indicator_color.setAlphaF(alpha)
        return self.indicator_color

    def color_lap_diff(self, veh_info):
        """Compare lap differences & set color"""
        if veh_info.positionOverall == 1:
            return self.wcfg["vehicle_color_leader"]
        if veh_info.inPit:
            return self.wcfg["vehicle_color_in_pit"]
        if veh_info.isYellow and not veh_info.inPit:
            return self.wcfg["vehicle_color_yellow"]
        if veh_info.isLapped > 0:
            return self.wcfg["vehicle_color_laps_ahead"]
        if veh_info.isLapped < 0:
            return self.wcfg["vehicle_color_laps_behind"]
        return self.wcfg["vehicle_color_same_lap"]

    def set_autohide_state(self):
        """Auto hide radar if in private qualifying or no nearby vehicles"""
        # Always show in garage
        if self.in_garage:
            self.show_radar = True
            return
        # Hide in private qualifying
        if (self.wcfg["auto_hide_in_private_qualifying"] and
            api.read.session.private_qualifying() == 1 and
            api.read.session.session_type() == 2):
            self.show_radar = False
            return
        # Bypass auto hide timer if radar fade enabled
        is_nearby = self.is_nearby()
        if self.wcfg["enable_radar_fade"]:
            self.show_radar = is_nearby
            return
        # Start auto hide timer
        lap_etime = api.read.timing.elapsed()
        if is_nearby:
            self.show_radar = True
            self.autohide_timer_start = lap_etime
        # Update auto hide timer
        if self.autohide_timer_start:
            if lap_etime - self.autohide_timer_start > self.wcfg["auto_hide_time_threshold"]:
                self.show_radar = False
                self.autohide_timer_start = 0
            # Timer start should be smaller than elapsed time, reset if not
            elif self.autohide_timer_start > lap_etime:
                self.autohide_timer_start = 1

    def is_nearby(self):
        """Check nearby vehicles"""
        for veh_info in islice(minfo.vehicles.dataSet, minfo.vehicles.totalVehicles):
            # -x = left, +x = right, -y = ahead, +y = behind
            if (not veh_info.isPlayer and
                self.radar_hide_range.behind > veh_info.relativeRotatedPositionY > -self.radar_hide_range.ahead and
                -self.radar_hide_range.side < veh_info.relativeRotatedPositionX < self.radar_hide_range.side):
                return True
        return False

    def calc_indicator_dimension(self, veh_width, veh_length):
        """Calculate indicator dimension

        Range between player & opponents to show indicator.
        x is left to right range.
        y is forward to backward range.
        """
        min_range_x = veh_width * 0.9  # slightly overlapped
        max_range_x = veh_width * (max(self.wcfg["overlap_nearby_range_multiplier"], 0) + 0.9)
        max_range_y = veh_length * 1.2  # safe range for ahead & behind opponents
        crit_range = veh_width * (max(self.wcfg["overlap_critical_range_multiplier"], 0) + 0.9)
        width = veh_width * max(self.wcfg["indicator_size_multiplier"], 0.01) * self.global_scale
        edge = max((width - 3) / width, 0.001)  # for antialiasing
        offset = veh_width * self.global_scale * 0.5
        return IndicatorDimension(min_range_x, max_range_x, max_range_y, crit_range, width, edge, offset)

    def set_range_dimension(self, prefix):
        """Set range dimension for radar & autohide"""
        if self.wcfg[f"{prefix}_ahead"] < 0:
            min_ahead = self.radar_radius
        else:
            min_ahead = self.wcfg[f"{prefix}_ahead"]

        if self.wcfg[f"{prefix}_behind"] < 0:
            min_behind = self.radar_radius
        else:
            min_behind = self.wcfg[f"{prefix}_behind"]

        if self.wcfg[f"{prefix}_side"] < 0:
            min_side = self.radar_radius
        else:
            min_side = self.wcfg[f"{prefix}_side"]
        return DistanceRect(min_ahead, min_behind, min_side)

    def set_radar_fade_factor(self, radar_radius):
        """Set radar fade factor"""
        range_fade_out = min(max(self.wcfg["radar_fade_out_radius"], 0.5), 1)
        range_fade_in = min(max(self.wcfg["radar_fade_in_radius"], 0.1),
                            range_fade_out - 0.01)  # make sure not exceed fade out range
        range_diff = range_fade_out - range_fade_in
        range_scale = range_fade_out / range_diff
        return range_scale / radar_radius
