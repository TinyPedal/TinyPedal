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
Damage Widget
"""

from PySide2.QtCore import QRect, Qt
from PySide2.QtGui import QBrush, QPainter, QPen

from .. import calculation as calc
from ..api_control import api
from ..const_common import FLOAT_INF
from ._base import Overlay
from ._common import WarningFlash


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
        display_margin = max(int(self.wcfg["display_margin"]), 0)
        inner_gap = max(int(self.wcfg["inner_gap"]), 0)

        parts_max_width = max(int(self.wcfg["parts_max_width"]), 4)
        parts_max_height = max(int(self.wcfg["parts_max_height"]), 4)

        parts_full_width = parts_max_width * 3 + inner_gap * 2
        parts_full_height = parts_max_height * 3 + inner_gap * 2
        parts_width = max(min(
            int(self.wcfg["parts_width"]),
            parts_max_width * 0.5,
            parts_max_height * 0.5), 1)

        display_width = parts_full_width + display_margin * 2
        display_height = parts_full_height + display_margin * 2
        impact_cone_size = max(display_width, display_height)
        self.impact_cone_angle = max(min(self.wcfg["last_impact_cone_angle"], 90), 2)

        # Base style
        self.color_damage_wheel = (
            self.wcfg["suspension_color"],
            self.wcfg["suspension_color_damage_light"],
            self.wcfg["suspension_color_damage_medium"],
            self.wcfg["suspension_color_damage_heavy"],
            self.wcfg["suspension_color_damage_totaled"],
            self.wcfg["wheel_color_detached"],
            self.wcfg["warning_color_detached"],
        )

        # Rect parts
        self.rect_mask = QRect(
            display_margin + parts_width, display_margin + parts_width,
            parts_full_width - parts_width * 2, parts_full_height - parts_width * 2
        )
        self.rects_wheels = self.create_wheels_rect(
            display_margin, parts_width, inner_gap, parts_full_width, parts_full_height
        )
        self.rects_parts = self.create_parts_rect(
            display_margin, inner_gap, parts_width, parts_max_width, parts_max_height
        )

        # Rect
        self.rect_background = QRect(0, 0, display_width, display_height)
        self.rect_integrity = self.rect_background.adjusted(0, font_offset, 0, 0)
        self.rect_impact_cone = QRect(
            display_width * 0.5 - impact_cone_size,
            display_height * 0.5 - impact_cone_size,
            impact_cone_size * 2,
            impact_cone_size * 2
        )

        # Config canvas
        self.resize(display_width, display_height)

        self.pen_text = QPen()
        self.pen_text.setColor(self.wcfg["font_color_integrity"])
        self.brush_cone = QBrush(Qt.SolidPattern)
        self.brush_cone.setColor(self.wcfg["last_impact_cone_color"])

        if self.wcfg["show_detached_warning_flash"]:
            self.warn_flash = WarningFlash(
                self.wcfg["warning_flash_highlight_duration"],
                self.wcfg["warning_flash_interval"],
                FLOAT_INF,
            )

        # Last data
        self.damage_aero = -1.0
        self.damage_body = [0] * 8
        self.damage_wheel = [0] * 4
        self.last_impact_time = None
        self.last_impact_expired = True

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Last impact time & position
        if self.wcfg["show_last_impact_cone"]:
            impact_time = api.read.vehicle.impact_time()

            if self.last_impact_time != impact_time:
                self.last_impact_time = impact_time
                self.last_impact_expired = api.read.vehicle.impact_magnitude() < 1
                self.update()

            if (not self.last_impact_expired and
                api.read.timing.elapsed() - self.last_impact_time
                > self.wcfg["last_impact_cone_duration"]):
                self.last_impact_expired = True
                self.update()

        # Damage body
        temp_damage_body = api.read.vehicle.damage_severity()
        if self.damage_body != temp_damage_body:
            self.damage_body = temp_damage_body
            self.update()

        # Damage aero
        temp_damage_aero = api.read.vehicle.aero_damage()
        if self.damage_aero != temp_damage_aero:
            self.damage_aero = temp_damage_aero
            self.update()

        # Damage wheel
        temp_damage_wheel = tuple(map(self.set_damage_level_wheel,
            api.read.wheel.is_detached(), api.read.wheel.suspension_damage()))
        if self.damage_wheel != temp_damage_wheel:
            self.damage_wheel = temp_damage_wheel
            self.update()

    # GUI update methods
    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        self.draw_damage_body(painter)
        self.draw_mask_background(painter)
        self.draw_damage_wheel(painter)
        if not self.last_impact_expired:
            self.draw_impact_cone(painter)
        if self.wcfg["show_integrity_reading"]:
            self.draw_readings(painter)

    def draw_mask_background(self, painter):
        """Draw mask & background"""
        painter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
        painter.fillRect(self.rect_mask, Qt.white)
        if self.wcfg["show_background"]:  # draw background below mask
            painter.setCompositionMode(QPainter.CompositionMode_DestinationOver)
            painter.fillRect(self.rect_background, self.wcfg["bkg_color"])
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

    def draw_damage_body(self, painter):
        """Draw damage body"""
        for part, damage in zip(self.rects_parts, self.damage_body):
            painter.fillRect(part, self.color_damage_body(damage))

    def draw_damage_wheel(self, painter):
        """Draw damage wheel"""
        for wheel, damage in zip(self.rects_wheels, self.damage_wheel):
            painter.fillRect(wheel, self.color_damage_wheel[damage])

    def draw_impact_cone(self, painter):
        """Draw impact cone"""
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.brush_cone)
        raw_angle = calc.rad2deg(calc.oriyaw2rad(*api.read.vehicle.impact_position()))
        start_angle = 16 * (raw_angle - 90 - self.impact_cone_angle * 0.5)
        length_angle = 16 * self.impact_cone_angle
        painter.drawPie(self.rect_impact_cone, start_angle, length_angle)

    def draw_readings(self, painter):
        """Draw body integrity readings"""
        if self.wcfg["show_aero_integrity_if_available"] and self.damage_aero >= 0:
            damage_value = self.damage_aero
        else:
            damage_value = sum(self.damage_body) / 16
        if not self.wcfg["show_inverted_integrity"]:
            damage_value = 1 - damage_value
        painter.setPen(self.pen_text)
        painter.drawText(self.rect_integrity, Qt.AlignCenter, f"{damage_value:.0%}"[:4])

    # Additional methods
    def color_damage_body(self, value: int) -> str:
        """Damage body color"""
        if value == 1:
            return self.wcfg["body_color_damage_light"]
        if value == 2:
            return self.wcfg["body_color_damage_heavy"]
        if value >= 3:
            if self.wcfg["show_detached_warning_flash"] and self.warn_flash.state(True):
                return self.wcfg["warning_color_detached"]
            return self.wcfg["body_color_detached"]
        return self.wcfg["body_color"]

    def set_damage_level_wheel(self, wheel_detached: bool, susp_wear: float) -> int:
        """Set damage level for wheel and suspension

        Damage level:
            0 no damage.
            1 light suspension damage.
            2 medium suspension damage.
            3 heavy suspension damage.
            4 suspension totaled.
            5 wheel detached.
        """
        if wheel_detached:
            if self.wcfg["show_detached_warning_flash"] and self.warn_flash.state(True):
                return 6
            return 5
        if susp_wear < self.wcfg["suspension_damage_light_threshold"]:
            return 0
        if susp_wear < self.wcfg["suspension_damage_medium_threshold"]:
            return 1
        if susp_wear < self.wcfg["suspension_damage_heavy_threshold"]:
            return 2
        if susp_wear < self.wcfg["suspension_damage_totaled_threshold"]:
            return 3
        return 4

    def create_wheels_rect(
        self, display_margin, parts_width, inner_gap, parts_full_width, parts_full_height):
        """Wheel parts rect, row by row from left to right, top to bottom"""
        wheel_width = max(int(self.wcfg["wheel_width"]), 1)
        wheel_height = max(int(self.wcfg["wheel_height"]), 1)
        offset_w = parts_width + inner_gap
        offset_x = parts_full_width - wheel_width - offset_w
        offset_y = parts_full_height - wheel_height - offset_w
        wheels_pos = (
            (display_margin + offset_w, display_margin + offset_w),  # front left
            (display_margin + offset_x, display_margin + offset_w),  # front right
            (display_margin + offset_w, display_margin + offset_y),  # rear left
            (display_margin + offset_x, display_margin + offset_y),  # rear right
        )
        return tuple(QRect(*pos, wheel_width, wheel_height) for pos in wheels_pos)

    def create_parts_rect(self, display_margin, inner_gap, parts_width, parts_max_width, parts_max_height):
        """Body parts rect, row by row from left to right, top to bottom"""
        offset_y = inner_gap + parts_max_height
        width_ratio = min(max(self.wcfg["parts_width_ratio"], 0.1), 1.0)
        side_scale = width_ratio * 2 / (1 + width_ratio)
        part_side_width = max(round(parts_max_width * side_scale), parts_width)
        part_center_width = parts_max_width * 3 - part_side_width * 2
        parts_pos = (
            # front left
            QRect(display_margin, display_margin, part_side_width, parts_max_height),
            # front center
            QRect(display_margin + inner_gap + part_side_width, display_margin, part_center_width, parts_max_height),
            # front right
            QRect(display_margin + inner_gap * 2 + part_side_width + part_center_width, display_margin, part_side_width, parts_max_height),
            # center left
            QRect(display_margin, display_margin + offset_y, part_side_width, parts_max_height),
            # center right
            QRect(display_margin + inner_gap * 2 + part_side_width + part_center_width, display_margin + offset_y, part_side_width, parts_max_height),
            # rear left
            QRect(display_margin, display_margin + offset_y * 2, part_side_width, parts_max_height),
            # rear center
            QRect(display_margin + inner_gap + part_side_width, display_margin + offset_y * 2, part_center_width, parts_max_height),
            # rear right
            QRect(display_margin + inner_gap * 2 + part_side_width + part_center_width, display_margin + offset_y * 2, part_side_width, parts_max_height),
        )
        return parts_pos
