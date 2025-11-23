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
Track map viewer
"""

import os

from PySide2.QtCore import QPoint, QPointF, QRect, Qt, Signal
from PySide2.QtGui import QPainter, QPainterPath, QPen
from PySide2.QtWidgets import (
    QAbstractSpinBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .. import calculation as calc
from ..const_file import ConfigType, FileExt, FileFilter
from ..setting import cfg
from ..userfile.track_map import load_track_map_file
from ._common import BaseDialog, CompactButton, UIScaler
from .config import UserConfig


class TrackMapViewer(BaseDialog):
    """Track map viewer"""

    def __init__(self, parent, filepath: str = "", filename: str = ""):
        super().__init__(parent)
        self.set_utility_title("Track Map Viewer")

        # Set panel
        self.trackmap_panel = self.set_layout_trackmap()

        # Set layout
        layout_main = QVBoxLayout()
        layout_main.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        layout_main.addWidget(self.trackmap_panel)
        self.setLayout(layout_main)

        # Pre-load track map if exists
        if filepath and filename:
            self.trackmap.load_trackmap(filepath, filename)

    def set_layout_trackmap(self):
        """Set track map panel"""
        self.trackmap = MapView(self)

        layout_map_wrap = QVBoxLayout()
        layout_map_wrap.addWidget(self.trackmap)
        layout_map_wrap.setContentsMargins(0, 0, 0, 0)

        frame_trackmap = QFrame(self)
        frame_trackmap.setLayout(layout_map_wrap)
        frame_trackmap.setFrameShape(QFrame.StyledPanel)

        layout_trackmap = QVBoxLayout()
        layout_trackmap.addLayout(self.trackmap.set_button_layout())
        layout_trackmap.addWidget(frame_trackmap)
        layout_trackmap.addLayout(self.trackmap.set_control_layout())
        layout_trackmap.setContentsMargins(0, 0, 0, 0)

        trackmap_panel = QFrame(self)
        trackmap_panel.setMinimumSize(UIScaler.size(38), UIScaler.size(38))
        trackmap_panel.setLayout(layout_trackmap)
        return trackmap_panel


class MapView(QWidget):
    """Map view"""

    reloaded = Signal(bool)

    def __init__(self, parent):
        super().__init__(parent)
        # Style
        self.load_config(False)
        self.pen = QPen()
        self.pen.setJoinStyle(Qt.RoundJoin)
        self.rect_info = QRect(0, 0, 1, 1)

        # Map data
        self.raw_coords = None
        self.raw_dists = None

        self.map_path = None
        self.sfinish_path = None
        self.sector1_path = None
        self.sector2_path = None

        self.map_filename = ""
        self.map_length = 0
        self.map_scale = 1
        self.map_seek_dist = 0
        self.map_seek_index = 0
        self.map_nodes = 0
        self.curve_nodes = 10
        self.center_x = 0
        self.center_y = 0
        self.marked_dists = set()
        self.marked_coords = []
        self.highlighted_coords = None

        # Toggle
        self.osd = {
            "map_info": True,
            "position_info": True,
            "curve_info": True,
            "slope_info": True,
            "separator1":"",
            "center_mark": True,
            "distance_circle": True,
            "osculating_circle": True,
            "curve_section": True,
            "marked_coordinates": True,
            "highlighted_coordinates": True,
            "separator2":"",
            "dark_background": cfg.application["window_color_theme"] == "Dark",
        }

        # Set layout
        self.set_controls()
        layout_inner_control = QHBoxLayout()
        layout_inner_control.setAlignment(Qt.AlignBottom)
        layout_inner_control.addWidget(self.slider_pos_dist)
        self.setLayout(layout_inner_control)

    def load_config(self, is_reload: bool = True):
        """Load config"""
        self.ecfg = cfg.user.config["track_map_viewer"]
        self.distance_circle_radius = [
            self.ecfg[f"distance_circle_{idx}_radius"] for idx in range(10)
        ]
        self.curve_grades = [
            (self.ecfg["curve_grade_hairpin"], "Hairpin"),
            *[(self.ecfg[f"curve_grade_{idx}"], str(idx))
            for idx in range(1, 9) if self.ecfg[f"curve_grade_{idx}"] >= 0],
            (self.ecfg["curve_grade_straight"], "Straight"),
        ]
        self.curve_grades.sort()
        self.length_grades = [
            (self.ecfg["length_grade_short"], "Short"),
            (self.ecfg["length_grade_normal"], "Normal"),
            (self.ecfg["length_grade_long"], "Long"),
            (self.ecfg["length_grade_very_long"], "Very Long"),
            (self.ecfg["length_grade_extra_long"], "Extra Long"),
            (self.ecfg["length_grade_extremely_long"], "Extremely Long"),
        ]
        self.length_grades.sort()
        self.slope_grades = [
            (self.ecfg["slope_grade_flat"], "Flat"),
            (self.ecfg["slope_grade_gentle"], "Gentle"),
            (self.ecfg["slope_grade_moderate"], "Moderate"),
            (self.ecfg["slope_grade_steep"], "Steep"),
            (self.ecfg["slope_grade_extreme"], "Extreme"),
            (self.ecfg["slope_grade_cliff"], "Cliff"),
        ]
        self.slope_grades.sort()
        if is_reload:
            self.spinbox_pos_dist.setSingleStep(self.ecfg["position_increment_step"])
            self.slider_pos_dist.setSingleStep(self.ecfg["position_increment_step"])
            self.update()

    def set_controls(self):
        """Set controls"""
        # Context menu
        self.map_context_menu = self.set_context_menu()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)

        # Outer controls
        self.edit_filename = QLineEdit()
        self.edit_filename.setReadOnly(True)
        self.edit_filename.setPlaceholderText("Track Map Name")

        self.spinbox_map_scale = QDoubleSpinBox()
        self.spinbox_map_scale.setRange(0.01, 10)
        self.spinbox_map_scale.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)
        self.spinbox_map_scale.setDecimals(2)
        self.spinbox_map_scale.setAlignment(Qt.AlignRight)
        self.spinbox_map_scale.setValue(1)
        self.spinbox_map_scale.valueChanged.connect(self.update_control)

        self.spinbox_nodes = QSpinBox()
        self.spinbox_nodes.setRange(3, 9999)
        self.spinbox_nodes.setSingleStep(1)
        self.spinbox_nodes.setAlignment(Qt.AlignRight)
        self.spinbox_nodes.setValue(self.curve_nodes)
        self.spinbox_nodes.valueChanged.connect(self.update_control)

        self.spinbox_pos_dist = QSpinBox()
        self.spinbox_pos_dist.setRange(0, 0)
        self.spinbox_pos_dist.setSingleStep(self.ecfg["position_increment_step"])
        self.spinbox_pos_dist.setWrapping(True)
        self.spinbox_pos_dist.setAccelerated(True)
        self.spinbox_pos_dist.setAlignment(Qt.AlignRight)
        self.spinbox_pos_dist.setValue(0)
        self.spinbox_pos_dist.valueChanged.connect(self.update_pos_spinbox)

        # Inner controls
        self.slider_pos_dist = QSlider(Qt.Horizontal)
        self.slider_pos_dist.setRange(0, 0)
        self.slider_pos_dist.setSingleStep(self.ecfg["position_increment_step"])
        self.slider_pos_dist.valueChanged.connect(self.update_pos_slider)

    def set_button_layout(self):
        """Set button layout"""
        button_load = CompactButton("Load Map")
        button_load.clicked.connect(self.open_trackmap)

        button_config = CompactButton("Config")
        button_config.clicked.connect(self.open_config_dialog)

        layout_button = QHBoxLayout()
        layout_button.addWidget(button_load)
        layout_button.addWidget(self.edit_filename)
        layout_button.addWidget(button_config)
        return layout_button

    def set_control_layout(self):
        """Set control layout"""
        layout_control = QHBoxLayout()
        layout_control.addWidget(QLabel("Zoom:"))
        layout_control.addWidget(self.spinbox_map_scale)
        layout_control.addStretch(1)
        layout_control.addWidget(QLabel("Position:"))
        layout_control.addWidget(self.spinbox_pos_dist)
        layout_control.addWidget(QLabel("Nodes:"))
        layout_control.addWidget(self.spinbox_nodes)
        return layout_control

    def update_pos_slider(self):
        """Update slider position"""
        self.map_seek_dist = self.slider_pos_dist.value()
        self.spinbox_pos_dist.setValue(self.map_seek_dist)
        self.update()

    def update_pos_spinbox(self):
        """Update spinbox position"""
        self.map_seek_dist = self.spinbox_pos_dist.value()
        self.slider_pos_dist.setValue(self.map_seek_dist)
        self.update()

    def update_control(self):
        """Update control"""
        self.map_scale = self.spinbox_map_scale.value()
        self.curve_nodes = self.spinbox_nodes.value()
        self.update()

    def reset_control(self):
        """Reset control"""
        self.spinbox_pos_dist.setValue(0)
        self.slider_pos_dist.setRange(0, self.map_length)
        self.spinbox_pos_dist.setRange(0, self.map_length)
        self.edit_filename.setText(self.map_filename)
        self.marked_dists.clear()
        self.marked_coords.clear()
        self.highlighted_coords = None

    def update_highlighted_coords(self):
        """Update highlighted coordinates"""
        if not self.raw_coords:
            return
        dist = self.spinbox_pos_dist.value()
        index = calc.binary_search_higher_column(
            self.raw_dists, dist, 0, self.map_nodes - 1)
        self.highlighted_coords = self.raw_coords[index]
        self.update()

    def update_marked_coords(self, temp_dists: set):
        """Update marked coordinates"""
        if not temp_dists or not self.raw_coords:
            return
        if temp_dists == self.marked_dists:
            return
        end_node = self.map_nodes - 1
        self.marked_coords.clear()
        for dist in temp_dists:
            if 0 <= dist <= self.map_length:
                index = calc.binary_search_higher_column(
                    self.raw_dists, dist, 0, end_node)
                self.marked_coords.append(QPointF(*self.raw_coords[index]))
        self.marked_dists = temp_dists
        self.update()

    def set_context_menu(self):
        """Set context menu"""
        menu = QMenu(self)
        for key, item in self.osd.items():
            if key.startswith("separator"):
                menu.addSeparator()
                continue
            option = menu.addAction(key.title().replace("_", " "))
            option.setCheckable(True)
            option.setChecked(item)
        return menu

    def open_context_menu(self, position: QPoint):
        """Open context menu"""
        action = self.map_context_menu.exec_(self.mapToGlobal(position))
        if not action:
            return
        name = action.text().replace(" ", "_").lower()
        self.osd[name] = not self.osd[name]
        self.update()

    def open_config_dialog(self):
        """Open config"""
        _dialog = UserConfig(
            parent=self,
            key_name="track_map_viewer",
            cfg_type=ConfigType.CONFIG,
            user_setting=cfg.user.config,
            default_setting=cfg.default.config,
            reload_func=self.load_config,
        )
        _dialog.open()

    def open_trackmap(self):
        """Open trackmap"""
        filename_full = QFileDialog.getOpenFileName(self, dir=cfg.path.track_map, filter=FileFilter.SVG)[0]
        if not filename_full:
            return

        filepath = os.path.dirname(filename_full) + "/"
        filename = os.path.splitext(os.path.basename(filename_full))[0]
        self.load_trackmap(filepath=filepath, filename=filename)

    def load_trackmap(self, filepath: str, filename: str):
        """Load trackmap"""
        if not os.path.exists(f"{filepath}{filename}{FileExt.SVG}"):
            msg_text = f"Cannot find track map for<br><b>{filename}</b><br>"
            QMessageBox.warning(self, "Error", msg_text)
            return

        self.raw_coords, self.raw_dists, sector_index = load_track_map_file(
            filepath=filepath,
            filename=filename,
        )

        if self.raw_coords and len(self.raw_coords) > 9:
            self.map_length = self.raw_dists[-1][0]
            self.map_nodes = len(self.raw_coords)
            self.map_filename = filename
            self.create_map_path(self.raw_coords, sector_index)
        else:
            self.map_length = 0
            self.map_nodes = 0
            self.map_filename = ""
            msg_text = (
                "Unable to load track map file from<br>"
                f"<b>{filepath}{filename}{FileExt.SVG}</b><br><br>"
                "Only support SVG file that generated with TinyPedal."
            )
            QMessageBox.warning(self, "Error", msg_text)

        self.reset_control()
        self.update()
        self.reloaded.emit(True)

    def create_map_path(self, raw_coords, sectors_index):
        """Create map path"""
        map_path = QPainterPath()
        sfinish_path = QPainterPath()
        sector1_path = QPainterPath()
        sector1_path = QPainterPath()

        for index, coords in enumerate(raw_coords):
            if index == 0:
                map_path.moveTo(*coords)
            else:
                map_path.lineTo(*coords)
        # Close map loop if start & end distance less than 500 meters
        if calc.distance(raw_coords[0], raw_coords[-1]) < 500:
            map_path.closeSubpath()
        # Create start/finish path
        sfinish_path = self.create_sector_path(
            sfinish_path, self.ecfg["start_line_length"], 0, 1)
        # Create sectors paths
        sector1_path = self.create_sector_path(
            sector1_path, self.ecfg["sector_line_length"],
            sectors_index[0], sectors_index[0] + 1)
        sector1_path = self.create_sector_path(
            sector1_path, self.ecfg["sector_line_length"],
            sectors_index[1], sectors_index[1] + 1)

        self.map_path = map_path
        self.sfinish_path = sfinish_path
        self.sector1_path = sector1_path
        self.sector2_path = sector1_path

    def create_sector_path(self, sector_path, length, node_idx1, node_idx2):
        """Create sector line"""
        pos_x1, pos_y1, pos_x2, pos_y2 = calc.line_intersect_coords(
            self.raw_coords[node_idx1],  # point a
            self.raw_coords[node_idx2],  # point b
            1.57079633,  # 90 degree rotation
            length
        )
        sector_path.moveTo(pos_x1, pos_y1)
        sector_path.lineTo(pos_x2, pos_y2)
        return sector_path

    def wheelEvent(self, event):
        """Mouse wheel control map scale"""
        scale = self.spinbox_map_scale.value()
        if event.angleDelta().y() > 0:
            if scale >= 0.1:
                zoom_step = 0.05
            else:
                zoom_step = 0.01
            scale += zoom_step
        else:
            if scale > 0.1:
                zoom_step = 0.05
            else:
                zoom_step = 0.01
            scale -= zoom_step
        self.spinbox_map_scale.setValue(scale)

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if self.osd["dark_background"]:
            bkg_color = self.ecfg["bkg_color_dark"]
        else:
            bkg_color = self.ecfg["bkg_color_light"]
        painter.fillRect(0, 0, self.size().width(), self.size().height(), bkg_color)

        if not self.raw_coords:
            return

        # Locate position node index
        self.map_seek_index = calc.binary_search_higher_column(
            self.raw_dists, self.map_seek_dist, 0, self.map_nodes - 1)

        # Raw coordinates
        pos_x, pos_y = self.raw_coords[self.map_seek_index]
        pos_dist, pos_z = self.raw_dists[self.map_seek_index]

        # Transform coordinates
        self.center_x = self.size().width() / 2
        self.center_y = self.size().height() / 2
        center_offset_x = self.center_x - pos_x * self.map_scale
        center_offset_y = self.center_y - pos_y * self.map_scale

        # Calculation
        curve_section = list(gen_section_path(
            self.map_nodes, self.curve_nodes, self.map_seek_index, self.raw_coords))
        mid_index = int(len(curve_section)/2)
        point_one = curve_section[0].x(), curve_section[0].y()
        point_sec = curve_section[1].x(), curve_section[1].y()
        point_mid = curve_section[mid_index].x(), curve_section[mid_index].y()
        point_end = curve_section[-1].x(), curve_section[-1].y()
        arc_center_pos = calc.tri_coords_circle_center(*point_one, *point_mid, *point_end)
        arc_radius = calc.distance(point_one, arc_center_pos)
        arc_angle = calc.quad_coords_angle(
            arc_center_pos, point_one, point_mid, point_end)
        yaw_radians = calc.oriyaw2rad(
            point_sec[1] - point_one[1], point_sec[0] - point_one[0])
        turn_direct = calc.turning_direction(
            yaw_radians, *point_one, *point_end)

        curve_length = calc_section_length(
            self.map_length, self.map_nodes, self.curve_nodes,
            self.map_seek_index, self.raw_dists)
        length_desc = calc.select_grade(self.length_grades, curve_length)
        curve_desc = curve_description(arc_radius, turn_direct, self.curve_grades)

        slope_delta = calc_section_height_delta(
            self.map_nodes, self.curve_nodes, self.map_seek_index, self.raw_dists)
        slope_percent = calc.slope_percent(slope_delta, curve_length)
        slope_angle = calc.slope_angle(slope_delta, curve_length)
        slope_desc = calc.select_grade(self.slope_grades, abs(slope_percent))

        # Apply transform
        painter.translate(center_offset_x, center_offset_y)
        painter.scale(self.map_scale, self.map_scale)

        # Draw map
        self.draw_map_image(painter)
        self.draw_osculating_circle(
            painter, arc_center_pos, arc_radius, point_one, point_end)
        self.draw_curve(painter, curve_section)
        self.draw_marked_coords(painter)

        painter.resetTransform()

        self.draw_distance_circle(painter)
        self.draw_center_mark(painter, yaw_radians)

        # Draw info
        self.update_info_rect(painter)
        self.draw_map_info(painter)
        self.draw_curve_info(
            painter, curve_length, arc_radius, arc_angle, curve_desc, length_desc)
        self.draw_slope_info(
            painter, slope_percent, slope_angle, slope_delta, slope_desc)
        self.draw_position_info(painter, pos_x, pos_y, pos_z, pos_dist)

    def draw_map_image(self, painter):
        """Draw map image"""
        # Draw map outline
        if self.ecfg["map_outline_width"] > 0:
            self.pen.setWidth(self.ecfg["map_width"] + self.ecfg["map_outline_width"])
            self.pen.setColor(self.ecfg["map_outline_color"])
            painter.setPen(self.pen)
            painter.drawPath(self.map_path)

        # Draw map
        self.pen.setWidth(self.ecfg["map_width"])
        self.pen.setColor(self.ecfg["map_color"])
        painter.setPen(self.pen)
        painter.drawPath(self.map_path)

        # Draw start/finish line
        self.pen.setWidth(self.ecfg["start_line_width"])
        self.pen.setColor(self.ecfg["start_line_color"])
        painter.setPen(self.pen)
        painter.drawPath(self.sfinish_path)

        # Draw sectors line
        self.pen.setWidth(self.ecfg["sector_line_width"])
        self.pen.setColor(self.ecfg["sector_line_color"])
        painter.setPen(self.pen)
        painter.drawPath(self.sector1_path)
        painter.drawPath(self.sector2_path)

    def draw_osculating_circle(
        self, painter, arc_center_pos, arc_radius, point_one, point_end):
        """Draw osculating circle"""
        if self.osd["osculating_circle"]:
            self.pen.setWidth(self.ecfg["osculating_circle_width"])
            self.pen.setColor(self.ecfg["osculating_circle_color"])
            painter.setPen(self.pen)
            painter.drawLine(*arc_center_pos, *point_one)  # radius line
            painter.drawLine(*arc_center_pos, *point_end)  # radius line
            painter.drawEllipse(
                arc_center_pos[0] - arc_radius,
                arc_center_pos[1] - arc_radius,
                arc_radius * 2, arc_radius * 2)

    def draw_curve(self, painter, curve_section):
        """Draw curve"""
        if self.osd["curve_section"]:
            self.pen.setWidth(self.ecfg["curve_section_width"])
            self.pen.setColor(self.ecfg["curve_section_color"])
            painter.setPen(self.pen)
            painter.drawPolyline(curve_section)

    def draw_marked_coords(self, painter):
        """Draw marked coordinates"""
        if self.osd["marked_coordinates"] and self.marked_coords:
            self.pen.setWidth(self.ecfg["marked_coordinates_size"])
            self.pen.setColor(self.ecfg["marked_coordinates_color"])
            painter.setPen(self.pen)
            painter.drawPoints(self.marked_coords)

        if self.osd["highlighted_coordinates"] and self.highlighted_coords:
            self.pen.setWidth(self.ecfg["highlighted_coordinates_width"])
            self.pen.setColor(self.ecfg["highlighted_coordinates_color"])
            painter.setPen(self.pen)
            x, y = self.highlighted_coords
            highlighted_size = self.ecfg["highlighted_coordinates_size"]
            painter.drawRect(
                x - highlighted_size,
                y - highlighted_size,
                highlighted_size * 2,
                highlighted_size * 2
            )

    def draw_distance_circle(self, painter):
        """Draw distance circle"""
        if self.osd["distance_circle"]:
            self.pen.setWidth(self.ecfg["distance_circle_width"])
            self.pen.setColor(self.ecfg["distance_circle_color"])
            painter.setPen(self.pen)
            for circle_radius in self.distance_circle_radius:
                if circle_radius > 0:
                    circle_radius *= self.map_scale
                    painter.drawEllipse(
                        self.center_x - circle_radius,
                        self.center_y - circle_radius,
                        circle_radius * 2, circle_radius * 2)

    def draw_center_mark(self, painter, yaw_radians):
        """Draw center mark"""
        if self.osd["center_mark"]:
            self.pen.setWidth(self.ecfg["center_mark_width"])
            self.pen.setColor(self.ecfg["center_mark_color"])
            painter.setPen(self.pen)

            center_mark_radius = self.ecfg["center_mark_radius"]
            painter.translate(self.center_x, self.center_y)
            painter.rotate(calc.rad2deg(yaw_radians))
            painter.drawLine(-center_mark_radius, 0, center_mark_radius, 0)
            painter.drawLine(0, -center_mark_radius, 0, center_mark_radius)
            painter.resetTransform()

    def update_info_rect(self, painter):
        """Update info rect"""
        margin = self.ecfg["inner_margin"]
        self.rect_info.setRect(
            margin, margin, (self.center_x - margin) * 2,
            (self.center_y - margin - self.slider_pos_dist.height()) * 2
        )
        if self.osd["dark_background"]:
            font_color = self.ecfg["font_color_light"]
        else:
            font_color = self.ecfg["font_color_dark"]
        self.pen.setColor(font_color)
        painter.setPen(self.pen)

    def draw_map_info(self, painter):
        """Draw map info"""
        if self.osd["map_info"]:
            painter.drawText(
                self.rect_info, Qt.AlignRight,
                f"{self.map_length:.3f}m ({self.map_nodes} nodes)"
            )

    def draw_curve_info(
        self, painter, curve_length, arc_radius, arc_angle, curve_desc, length_desc):
        """Draw curve info"""
        if self.osd["curve_info"]:
            painter.drawText(
                self.rect_info, Qt.AlignLeft,
                (
                    f"Curve: {curve_length:.3f}m ({length_desc})\n"
                    f"Radius: {arc_radius:.3f}m ({curve_desc})\n"
                    f"Angle: {arc_angle:.3f}°"
                    #f"Curvature: {calc.curvature(arc_radius):.6f}"
                )
            )

    def draw_slope_info(self, painter, slope_percent, slope_angle, slope_delta, slope_desc):
        """Draw slope info"""
        if self.osd["slope_info"]:
            painter.drawText(
                self.rect_info, Qt.AlignLeft | Qt.AlignBottom,
                (
                    f"Slope: {slope_percent:.3%} ({slope_desc})\n"
                    f"Angle: {slope_angle:.3f}°\n"
                    f"Delta: {slope_delta:.3f}m"
                )
            )

    def draw_position_info(self, painter, pos_x, pos_y, pos_z, pos_dist):
        """Draw position info"""
        if self.osd["position_info"]:
            painter.drawText(
                self.rect_info, Qt.AlignRight | Qt.AlignBottom,
                (
                    f"{pos_dist:.3f}m (node {self.map_seek_index + 1})\n"
                    f"{pos_x:.3f}m, {pos_y:.3f}m, {pos_z:.3f}m"
                )
            )


def gen_section_path(
    total_nodes: int, section_nodes: int, seek_index: int, raw_coords: tuple):
    """Generate section path from selected nodes"""
    max_nodes = int(min(section_nodes, total_nodes - 2))
    for index in range(max_nodes):
        index += seek_index
        if index >= total_nodes:
            index -= total_nodes
        yield QPointF(*raw_coords[index])


def calc_section_length(
    map_length: float, total_nodes: int, section_nodes: int,
    seek_index: int, raw_dists: tuple) -> float:
    """Calculate section length from selected nodes"""
    max_nodes = int(min(section_nodes, total_nodes - 2))
    end_index = seek_index + max_nodes
    if end_index >= total_nodes:
        length = (
            map_length - raw_dists[seek_index][0]
            + raw_dists[end_index - total_nodes][0])
    else:
        length = raw_dists[end_index][0] - raw_dists[seek_index][0]
    return length


def calc_section_height_delta(
    total_nodes: int, section_nodes: int, seek_index: int, raw_dists: tuple) -> float:
    """Calculate section height delta from selected nodes"""
    max_nodes = int(min(section_nodes, total_nodes - 2))
    end_index = seek_index + max_nodes
    if end_index >= total_nodes:
        end_index -= total_nodes
    height_delta = raw_dists[end_index][1] - raw_dists[seek_index][1]
    return height_delta


def curve_description(arc_radius: float, turn_direct: int, curve_grade: tuple) -> str:
    """Curve description"""
    if arc_radius >= curve_grade[-1][0]:
        return curve_grade[-1][1]
    if turn_direct > 0:
        direct_desc = "Right"
    else:
        direct_desc = "Left"
    curve_desc = calc.select_grade(curve_grade, arc_radius)
    return f"{direct_desc} {curve_desc}"
