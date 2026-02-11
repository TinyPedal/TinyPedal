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
Deltabest Widget
"""

from PySide2.QtCore import QRectF, Qt
from PySide2.QtGui import QPainter, QPen

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
            self.wcfg["font_weight"],
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)

        # Config variable
        self.laptime_source = f"lapTime{self.wcfg['deltabest_source']}"
        self.delta_source = f"delta{self.wcfg['deltabest_source']}"
        bar_gap = self.wcfg["bar_gap"]
        padx = round(font_m.width * self.wcfg["bar_padding_horizontal"])
        pady = round(font_m.capital * self.wcfg["bar_padding_vertical"])
        self.dbar_length = int(self.wcfg["bar_length"] * 0.5)
        dbar_height = int(self.wcfg["bar_height"])

        self.decimals = max(self.wcfg["decimal_places"], 1)
        self.delta_display_range = calc.decimal_strip(self.wcfg["delta_display_range"], self.decimals)
        self.max_padding = 4 + self.decimals
        self.delta_width = font_m.width * self.max_padding + padx * 2
        delta_height = font_m.capital + pady * 2

        if self.wcfg["layout"] == 0:
            pos_y1 = 0
        else:
            pos_y1 = delta_height + bar_gap

        if self.wcfg["show_delta_bar"]:
            pos_x2 = self.dbar_length - self.delta_width * 0.5
        else:
            pos_x2 = 0

        if self.wcfg["layout"] == 0 and self.wcfg["show_delta_bar"]:
            pos_y2 = dbar_height + bar_gap
        else:
            pos_y2 = 0

        self.rect_deltabar = QRectF(0, pos_y1, self.dbar_length * 2, dbar_height)
        self.rect_deltapos = QRectF(0, pos_y1, self.dbar_length, dbar_height)
        self.rect_delta = QRectF(pos_x2, pos_y2, self.delta_width, delta_height)
        self.rect_text_delta = self.rect_delta.adjusted(0, font_m.voffset, 0, 0)

        self.freeze_duration = min(max(self.wcfg["freeze_duration"], 0), 30)
        self.delta_color = self.wcfg["bkg_color_time_gain"], self.wcfg["bkg_color_time_loss"]

        # Config canvas
        if self.wcfg["show_delta_bar"]:
            self.resize(self.dbar_length * 2, dbar_height + bar_gap + delta_height)
        else:
            self.resize(self.delta_width, delta_height)

        self.pen_text = QPen()

        # Last data
        self.delta_best = 0
        self.last_laptime = 0
        self.new_lap = True

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if minfo.delta.lapTimeCurrent < self.freeze_duration:
            temp_best = minfo.delta.lapTimeLast - self.last_laptime
            self.new_lap = True
        else:
            if self.new_lap:
                self.last_laptime = getattr(minfo.delta, self.laptime_source)
                self.new_lap = False

            temp_best = getattr(minfo.delta, self.delta_source)

        if self.delta_best != temp_best:
            self.delta_best = temp_best
            self.update()

    # GUI update methods
    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        delta_pos = self.delta_position(
            self.wcfg["bar_display_range"],
            self.delta_best,
            self.dbar_length)
        highlight_color = self.delta_color[self.delta_best > 0]

        # Draw deltabar
        if self.wcfg["show_delta_bar"]:
            self.rect_deltapos.setLeft(delta_pos)
            painter.fillRect(self.rect_deltabar, self.wcfg["bkg_color_deltabar"])
            painter.fillRect(self.rect_deltapos, highlight_color)

            if self.wcfg["show_animated_deltabest"]:
                pos_x = calc.zero_max(
                    delta_pos - self.delta_width * 0.5,
                    self.dbar_length * 2 - self.delta_width,
                )
                self.rect_delta.moveLeft(pos_x)
                self.rect_text_delta.moveLeft(pos_x)

        # Draw delta readings
        if self.wcfg["swap_style"]:
            self.pen_text.setColor(self.wcfg["bkg_color_deltabest"])
            bg_color = highlight_color
        else:
            self.pen_text.setColor(highlight_color)
            bg_color =  self.wcfg["bkg_color_deltabest"]

        painter.fillRect(self.rect_delta, bg_color)
        painter.setPen(self.pen_text)
        painter.drawText(
            self.rect_text_delta,
            Qt.AlignCenter,
            f"{calc.sym_max(self.delta_best, self.delta_display_range):+.{self.decimals}f}"[:self.max_padding]
        )

    # Additional methods
    @staticmethod
    def delta_position(rng, delta, length):
        """Delta position"""
        return (1 - calc.sym_max(delta, rng) / rng) * length
