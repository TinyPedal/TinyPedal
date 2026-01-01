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
Differential Widget
"""

from ..api_control import api
from ..module_info import minfo
from ._base import Overlay


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout(gap=self.wcfg["bar_gap"])
        self.set_primary_layout(layout=layout)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        self.decimals = max(self.wcfg["decimal_places"], 0)
        self.max_padding = 3 + self.decimals + (self.decimals > 0)

        if self.wcfg["layout"] == 0:
            prefix_just = max(
                len(self.wcfg["prefix_power_front"]),
                len(self.wcfg["prefix_coast_front"]),
                len(self.wcfg["prefix_power_rear"]),
                len(self.wcfg["prefix_coast_rear"]),
            )
        else:
            prefix_just = 0

        self.prefix_power_f = self.wcfg["prefix_power_front"].ljust(prefix_just)
        self.prefix_coast_f = self.wcfg["prefix_coast_front"].ljust(prefix_just)
        self.prefix_power_r = self.wcfg["prefix_power_rear"].ljust(prefix_just)
        self.prefix_coast_r = self.wcfg["prefix_coast_rear"].ljust(prefix_just)

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # Power locking front
        if self.wcfg["show_power_locking_front"]:
            text_power_front = f"{self.prefix_power_f}{self.format_reading(1)}"
            bar_style_power_front = self.set_qss(
                fg_color=self.wcfg["font_color_power_locking_front"],
                bg_color=self.wcfg["bkg_color_power_locking_front"]
            )
            self.bar_power_front = self.set_qlabel(
                text=text_power_front,
                style=bar_style_power_front,
                width=font_m.width * len(text_power_front) + bar_padx,
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_power_front,
                column=self.wcfg["column_index_power_locking_front"],
            )

        # Coast locking front
        if self.wcfg["show_coast_locking_front"]:
            text_coast_front = f"{self.prefix_coast_f}{self.format_reading(1)}"
            bar_style_coast_front = self.set_qss(
                fg_color=self.wcfg["font_color_coast_locking_front"],
                bg_color=self.wcfg["bkg_color_coast_locking_front"]
            )
            self.bar_coast_front = self.set_qlabel(
                text=text_coast_front,
                style=bar_style_coast_front,
                width=font_m.width * len(text_coast_front) + bar_padx,
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_coast_front,
                column=self.wcfg["column_index_coast_locking_front"],
            )

        # Power locking rear
        if self.wcfg["show_power_locking_rear"]:
            text_power_rear = f"{self.prefix_power_r}{self.format_reading(1)}"
            bar_style_power_rear = self.set_qss(
                fg_color=self.wcfg["font_color_power_locking_rear"],
                bg_color=self.wcfg["bkg_color_power_locking_rear"]
            )
            self.bar_power_rear = self.set_qlabel(
                text=text_power_rear,
                style=bar_style_power_rear,
                width=font_m.width * len(text_power_rear) + bar_padx,
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_power_rear,
                column=self.wcfg["column_index_power_locking_rear"],
            )

        # Coast locking rear
        if self.wcfg["show_coast_locking_rear"]:
            text_coast_rear = f"{self.prefix_coast_r}{self.format_reading(1)}"
            bar_style_coast_rear = self.set_qss(
                fg_color=self.wcfg["font_color_coast_locking_rear"],
                bg_color=self.wcfg["bkg_color_coast_locking_rear"]
            )
            self.bar_coast_rear = self.set_qlabel(
                text=text_coast_rear,
                style=bar_style_coast_rear,
                width=font_m.width * len(text_coast_rear) + bar_padx,
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_coast_rear,
                column=self.wcfg["column_index_coast_locking_rear"],
            )

        # Last data
        self.power_timer_f = DiffLockingTimer(self.wcfg["power_locking_reset_cooldown"])
        self.coast_timer_f = DiffLockingTimer(self.wcfg["coast_locking_reset_cooldown"])
        self.power_timer_r = DiffLockingTimer(self.wcfg["power_locking_reset_cooldown"])
        self.coast_timer_r = DiffLockingTimer(self.wcfg["coast_locking_reset_cooldown"])

    def timerEvent(self, event):
        """Update when vehicle on track"""
        lap_etime = api.read.timing.elapsed()
        raw_throttle = api.read.inputs.throttle_raw()
        locking_front = minfo.wheels.lockingPercentFront
        locking_rear = minfo.wheels.lockingPercentRear
        on_throttle = raw_throttle > self.wcfg["on_throttle_threshold"]
        off_throttle = raw_throttle < self.wcfg["off_throttle_threshold"]

        # Power locking front
        if self.wcfg["show_power_locking_front"] and on_throttle:
            min_power_f = self.power_timer_f.update(locking_front, lap_etime)
            self.update_locking(self.bar_power_front, min_power_f, self.prefix_power_f)

        # Coast locking front
        if self.wcfg["show_coast_locking_front"] and off_throttle:
            min_coast_f = self.coast_timer_f.update(locking_front, lap_etime)
            self.update_locking(self.bar_coast_front, min_coast_f, self.prefix_coast_f)

        # Power locking rear
        if self.wcfg["show_power_locking_rear"] and on_throttle:
            min_power_r = self.power_timer_r.update(locking_rear, lap_etime)
            self.update_locking(self.bar_power_rear, min_power_r, self.prefix_power_r)

        # Coast locking rear
        if self.wcfg["show_coast_locking_rear"] and off_throttle:
            min_coast_r = self.coast_timer_r.update(locking_rear, lap_etime)
            self.update_locking(self.bar_coast_rear, min_coast_r, self.prefix_coast_r)

    # GUI update methods
    def update_locking(self, target, data, prefix):
        """Differential locking percent"""
        if target.last != data:
            target.last = data
            target.setText(f"{prefix}{self.format_reading(data)}")

    # Additional methods
    def format_reading(self, value):
        """Format reading"""
        if self.wcfg["show_inverted_locking"]:
            value = 1 - value
        return f"{value: >{self.max_padding}.{self.decimals}%}"[:self.max_padding]


class DiffLockingTimer:
    """Differential locking timer"""

    __slots__ = (
        "_cooldown",
        "_timer",
        "_min_locking",
    )

    def __init__(self, cooldown: float) -> None:
        """
        Args:
            cooldown: minimum locking percent reset cooldown (seconds).
        """
        self._cooldown = cooldown
        self._timer = 0.0
        self._min_locking = 1.0

    def update(self, locking: float, elapsed_time: float) -> float:
        """Update minimum locking percent

        Args:
            locking: locking percent (fraction).
            elapsed_time: current lap elapsed time.

        Returns:
            Minimum locking percent (fraction).
        """
        if self._min_locking > locking:
            self._min_locking = locking
            self._timer = elapsed_time
        elif elapsed_time - self._timer > self._cooldown:
            self._min_locking = 1  # reset
        elif self._timer > elapsed_time:  # timer correction
            self._timer = elapsed_time
        return self._min_locking
