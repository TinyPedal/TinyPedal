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
DRS Widget
"""

from PySide2.QtCore import QRectF, Qt
from PySide2.QtGui import QPainter, QPen

from ..api_control import api
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
        padx = round(font_m.width * self.wcfg["bar_padding_horizontal"])
        pady = round(font_m.capital * self.wcfg["bar_padding_vertical"])
        drs_width = font_m.width * len(self.wcfg["drs_text"]) + padx * 2
        drs_height = int(font_m.capital + pady * 2)

        self.drs_color = (
            (self.wcfg["font_color_not_available"], self.wcfg["bkg_color_not_available"]),
            (self.wcfg["font_color_available"], self.wcfg["bkg_color_available"]),
            (self.wcfg["font_color_allowed"], self.wcfg["bkg_color_allowed"]),
            (self.wcfg["font_color_activated"], self.wcfg["bkg_color_activated"]),
        )

        # Rect
        self.rect_drs = QRectF(0, 0, drs_width, drs_height)
        self.rect_text = self.rect_drs.adjusted(0, font_m.voffset, 0, 0)

        # Config canvas
        self.resize(drs_width, drs_height)
        self.pen_text = QPen()

        # Last data
        self.drs_state = -1

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # DRS update
        drs_state = api.read.switch.drs_status()
        if self.drs_state != drs_state:
            self.drs_state = drs_state
            self.update()

    # GUI update methods
    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.fillRect(self.rect_drs, self.drs_color[self.drs_state][1])
        self.pen_text.setColor(self.drs_color[self.drs_state][0])
        painter.setPen(self.pen_text)
        painter.drawText(self.rect_text, Qt.AlignCenter, self.wcfg["drs_text"])
