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
Overlay base common class.
"""

from __future__ import annotations

from time import monotonic
from typing import NamedTuple

from PySide2.QtCore import QPoint
from PySide2.QtWidgets import QApplication, QWidget

from ..validator import generator_init


class FontMetrics(NamedTuple):
    """Font metrics info"""

    width: int = 0
    height: int = 0
    leading: int = 0
    capital: int = 0
    descent: int = 0
    voffset: int = 0


class MousePosition:
    """Mouse position & snapping"""

    __slots__ = (
        "_init_pos",
        "_grid_x",
        "_grid_y",
        "_delta_x",
        "_delta_y",
        "_last_x",
        "_last_y",
        "_screen_name",
        "_grid_move",
        "_grid_size",
        "_snap_gap",
        "_snap_distance",
    )

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset"""
        self._init_pos = None
        self._grid_x = None
        self._grid_y = None
        self._delta_x = 0
        self._delta_y = 0
        self._last_x = 0
        self._last_y = 0
        self._screen_name = None
        self._grid_move = False
        self._grid_size = 1
        self._snap_gap = 0
        self._snap_distance = 0

    def valid(self) -> bool:
        """Is initial position valid"""
        return isinstance(self._init_pos, QPoint)

    def config(self, init_pos: QPoint, grid_move: bool, grid_size: int, snap_gap: int, snap_distance: int):
        """Config mouse move"""
        self._init_pos = init_pos
        self._grid_move = grid_move
        self._grid_size = max(grid_size, 1)
        self._snap_gap = max(0, snap_gap)
        self._snap_distance = max(snap_gap, snap_distance)

    def update_grid(self, widget: QWidget):
        """Update widget snap position grid"""
        # Update grid if active screen name changed
        screen = widget.screen()
        if self._screen_name == screen.name():
            return
        self._screen_name = screen.name()
        # Restricted screen area (excludes task bar, system menu, etc)
        scr_x, scr_y, scr_width, scr_height = screen.availableGeometry().getRect()
        # Full screen area
        scrfull_x, scrfull_y, scrfull_width, scrfull_height = screen.geometry().getRect()
        # Update grid set (avoid duplicates)
        x_grid = {scr_x, scr_x + scr_width, scrfull_x, scrfull_x + scrfull_width}
        y_grid = {scr_y, scr_y + scr_height, scrfull_y, scrfull_y + scrfull_height}
        # Add widget x, y coords
        try:
            for other_widget in QApplication.topLevelWidgets():
                if (
                    not hasattr(other_widget, "widget_name")
                    or widget is other_widget
                    or not other_widget.isVisible()
                    or screen is not other_widget.screen()
                ):
                    continue
                other_x, other_y, other_width, other_height = other_widget.geometry().getRect()
                x_grid.add(other_x)
                x_grid.add(other_x + other_width)
                y_grid.add(other_y)
                y_grid.add(other_y + other_height)
        except (RuntimeError, AttributeError, TypeError, ValueError):
            pass
        # Sort grid (necessary to avoid snapping jumping)
        self._grid_x = sorted(x_grid)
        self._grid_y = sorted(y_grid)

    def moving(self, global_pos: QPoint) -> QPoint:
        """Moving position"""
        pos = global_pos - self._init_pos
        if self._grid_move:
            return pos / self._grid_size * self._grid_size
        return pos

    def snapping(self, widget: QWidget, global_pos: QPoint) -> QPoint:
        """Snapping to reference grid"""
        self.update_grid(widget)
        # Update delta since last pos
        pos = global_pos - self._init_pos
        new_x = pos.x()
        new_y = pos.y()
        widget_width = widget.width()
        widget_height = widget.height()
        self._delta_x = min(max(new_x - self._last_x + self._delta_x, -5), 5)
        self._delta_y = min(max(new_y - self._last_y + self._delta_y, -5), 5)
        self._last_x = new_x
        self._last_y = new_y
        # Horizontal snap
        if self._delta_x < 0:  # moving left
            x_left = new_x
            for x_pos_other in self._grid_x:
                if abs(x_left - x_pos_other) < self._snap_distance:
                    new_x = x_pos_other + self._snap_gap
        elif self._delta_x > 0:  # moving right
            x_right = new_x + widget_width
            for x_pos_other in self._grid_x:
                if abs(x_right - x_pos_other) < self._snap_distance:
                    new_x = x_pos_other - widget_width - self._snap_gap
        # Vertical snap
        if self._delta_y < 0:  # moving up
            y_top = new_y
            for y_pos_other in self._grid_y:
                if abs(y_top - y_pos_other) < self._snap_distance:
                    new_y = y_pos_other + self._snap_gap
        elif self._delta_y > 0:  # moving down
            y_bottom = new_y + widget_height
            for y_pos_other in self._grid_y:
                if abs(y_bottom - y_pos_other) < self._snap_distance:
                    new_y = y_pos_other - widget_height - self._snap_gap
        # Update pos
        pos.setX(new_x)
        pos.setY(new_y)
        return pos


@generator_init
def warning_flash(duration: float, interval: float, max_count: int):
    """Warning flash state"""
    last_condition = False
    highlight = False
    highlight_seconds = max(duration, 0.2)
    highlight_timer = 0.0
    interval_seconds = max(interval, 0.2)
    interval_timer = 0.0
    flash_count = 0
    flash_max = max(max_count, 3)

    while True:
        condition = yield highlight
        elapsed = monotonic()

        if last_condition != condition:
            last_condition = condition
            if condition:
                highlight_timer = elapsed
                highlight = False
                interval_timer = 0
                flash_count = 0

        if not condition:
            highlight = False
            continue
        elif flash_count >= flash_max:
            highlight = True
            continue

        if elapsed - highlight_timer < highlight_seconds:
            if not highlight:
                flash_count += 1
            highlight = True
            interval_timer = elapsed
        else:
            highlight = False
            if elapsed - interval_timer >= interval_seconds:
                highlight_timer = elapsed
