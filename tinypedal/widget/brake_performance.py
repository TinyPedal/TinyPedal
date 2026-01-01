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
Brake performance Widget
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
        bar_width = font_m.width * 5 + bar_padx

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # Transient max braking rate
        if self.wcfg["show_transient_max_braking_rate"]:
            bar_style_trans_rate = self.set_qss(
                fg_color=self.wcfg["font_color_transient_max_braking_rate"],
                bg_color=self.wcfg["bkg_color_transient_max_braking_rate"]
            )
            self.bar_trans_rate = self.set_qlabel(
                text="0.00g",
                style=bar_style_trans_rate,
                width=bar_width,
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_trans_rate,
                column=self.wcfg["column_index_transient_max_braking_rate"],
            )

        # Max braking rate
        if self.wcfg["show_max_braking_rate"]:
            bar_style_max_rate = self.set_qss(
                fg_color=self.wcfg["font_color_max_braking_rate"],
                bg_color=self.wcfg["bkg_color_max_braking_rate"]
            )
            self.bar_max_rate = self.set_qlabel(
                text="0.00g",
                style=bar_style_max_rate,
                width=bar_width,
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_max_rate,
                column=self.wcfg["column_index_max_braking_rate"],
            )

        # Delta braking rate
        if self.wcfg["show_delta_braking_rate"]:
            self.bar_style_delta_rate = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_delta_braking_rate"],
                    bg_color=self.wcfg["bkg_color_braking_rate_loss"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_delta_braking_rate"],
                    bg_color=self.wcfg["bkg_color_braking_rate_gain"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_delta_braking_rate"],
                    bg_color=self.wcfg["bkg_color_delta_braking_rate"])
            )
            self.bar_delta_rate = self.set_qlabel(
                text="+0.00",
                style=self.bar_style_delta_rate[2],
                width=bar_width,
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_delta_rate,
                column=self.wcfg["column_index_delta_braking_rate"],
            )

        # Front wheel lock duration
        if self.wcfg["show_front_wheel_lock_duration"]:
            bar_style_lock_f = self.set_qss(
                fg_color=self.wcfg["font_color_front_wheel_lock_duration"],
                bg_color=self.wcfg["bkg_color_front_wheel_lock_duration"]
            )
            self.bar_lock_f = self.set_qlabel(
                text="F 0.0",
                style=bar_style_lock_f,
                width=bar_width,
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_lock_f,
                column=self.wcfg["column_index_front_wheel_lock_duration"],
            )

        # Front wheel lock duration
        if self.wcfg["show_rear_wheel_lock_duration"]:
            bar_style_lock_r = self.set_qss(
                fg_color=self.wcfg["font_color_rear_wheel_lock_duration"],
                bg_color=self.wcfg["bkg_color_rear_wheel_lock_duration"]
            )
            self.bar_lock_r = self.set_qlabel(
                text="R 0.0",
                style=bar_style_lock_r,
                width=bar_width,
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_lock_r,
                column=self.wcfg["column_index_rear_wheel_lock_duration"],
            )

        # Last data
        self.lock_timer = WheelLockTimer(
            self.wcfg["show_front_wheel_lock_duration"] or self.wcfg["show_rear_wheel_lock_duration"],
            self.wcfg["wheel_lock_threshold"]
        )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Transient max braking rate
        if self.wcfg["show_transient_max_braking_rate"]:
            transient_rate = minfo.force.transientMaxBrakingRate
            self.update_braking_rate(self.bar_trans_rate, transient_rate)

        # Max braking rate
        if self.wcfg["show_max_braking_rate"]:
            max_rate = minfo.force.maxBrakingRate
            self.update_braking_rate(self.bar_max_rate, max_rate)

        # Delta braking rate
        if self.wcfg["show_delta_braking_rate"]:
            delta_rate = minfo.force.deltaBrakingRate
            self.update_delta_rate(self.bar_delta_rate, delta_rate)

        # Wheel lock duration
        if self.lock_timer.enabled:
            self.lock_timer.calc(
                api.read.inputs.brake_raw(),
                api.read.timing.start(),
                api.read.timing.elapsed(),
                minfo.wheels.slipRatio,
            )

        if self.wcfg["show_front_wheel_lock_duration"]:
            self.update_lock_time_f(self.bar_lock_f, self.lock_timer.front)

        if self.wcfg["show_rear_wheel_lock_duration"]:
            self.update_lock_time_r(self.bar_lock_r, self.lock_timer.rear)

    # GUI update methods
    def update_braking_rate(self, target, data):
        """Braking rate (g force)"""
        if target.last != data:
            target.last = data
            target.setText(f"{data: >4.2f}g"[:5])

    def update_delta_rate(self, target, data):
        """Delta braking rate"""
        if target.last != data:
            target.last = data
            if self.wcfg["show_delta_braking_rate_in_percentage"]:
                max_rate = minfo.force.maxBrakingRate
                if max_rate:
                    data /= max_rate
                else:
                    data = 0
                text = f"{data:+.0%}"
            else:
                text = f"{data:+.2f}"
            target.setText(text[:5])
            target.updateStyle(self.bar_style_delta_rate[data > 0])

    def update_lock_time_f(self, target, data):
        """Front wheel lock duration"""
        if target.last != data:
            target.last = data
            target.setText(f"F{data: >4.1f}"[:5])

    def update_lock_time_r(self, target, data):
        """Rear wheel lock duration"""
        if target.last != data:
            target.last = data
            target.setText(f"R{data: >4.1f}"[:5])


class WheelLockTimer:
    """Wheel lock timer"""

    __slots__ = (
        "enabled",
        "front",
        "rear",
        "_last_elapsed_time",
        "_last_start_time",
        "_lock_threshold",
    )

    def __init__(self, enabled: bool, lock_threshold: float) -> None:
        """
        Args:
            enabled: whether lock timer enabled.
            lock_threshold: wheel lock (slip ratio) detection threshold.
        """
        self.enabled = enabled
        self.front = 0.0
        self.rear = 0.0
        self._last_elapsed_time = 0.0
        self._last_start_time = 0.0
        self._lock_threshold = lock_threshold

    def calc(self, brake_raw: float, start_time: float, elapsed_time: float, slip_ratio: list):
        """Calculate wheel lock duration

        Args:
            brake_raw: raw brake input.
            start_time: current lap start time.
            elapsed_time: current lap elapsed time.
            slip_ratio: slip ratio (4 tyres).
        """
        if brake_raw > 0.03:
            if start_time != self._last_start_time:
                self._last_start_time = start_time
                self.front = 0  # reset on new lap
                self.rear = 0
            delta_etime = elapsed_time - self._last_elapsed_time
            if delta_etime > 0:
                if min(slip_ratio[:2]) < -self._lock_threshold:
                    self.front += delta_etime
                if min(slip_ratio[2:]) < -self._lock_threshold:
                    self.rear += delta_etime
        self._last_elapsed_time = elapsed_time
