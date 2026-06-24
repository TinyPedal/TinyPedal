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
Acceleration Widget
"""

from .. import units
from ..api_control import api
from ..const_common import MAX_SECONDS, TEXT_PLACEHOLDER
from ._base import Overlay


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout(gap_hori=self.wcfg["bar_gap"])
        self.set_primary_layout(layout=layout)

        # Config font
        font = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size"],
            self.wcfg["font_weight"],
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)

        font_cap = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size"] * 0.8,
            self.wcfg["font_weight"],
        )
        font_cap_m = self.get_font_metrics(font_cap)

        # Config variable
        layout_reversed = self.wcfg["layout"] != 0
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        self.char_width = max(self.wcfg["bar_width"], 4)
        bar_width = font_m.width * self.char_width + bar_padx

        self.decimals_timer = max(self.wcfg["decimal_places_timer"], 0)
        self.decimals_delta = max(self.wcfg["decimal_places_delta"], 0)

        self.timers = tuple(self.set_timers())
        total_slot = len(self.timers)

        # Config units
        self.unit_speed = units.set_unit_speed(self.cfg.units["speed_unit"])

        # Speed range
        self.bars_speed_range = self.set_rawtext(
            font=font_cap,
            text=TEXT_PLACEHOLDER,
            width=bar_width,
            fixed_height=font_cap_m.height,
            offset_y=font_cap_m.voffset,
            fg_color=self.wcfg["font_color_speed_range"],
            bg_color=self.wcfg["background_color_speed_range"],
            count=total_slot,
            last=-MAX_SECONDS,
        )
        self.set_grid_layout_table_row(
            layout=layout,
            targets=self.bars_speed_range,
            row=self.wcfg["display_order_speed_range"],
            right_to_left=layout_reversed,
        )

        # Last timer
        self.timer_color = (
            (
                self.wcfg["font_color_last_timer"],
                self.wcfg["background_color_last_timer"],
            ),
            (
                self.wcfg["font_color_active_timer"],
                self.wcfg["background_color_active_timer"],
            ),
        )
        self.bars_timer_last = self.set_rawtext(
            text=TEXT_PLACEHOLDER,
            width=bar_width,
            fixed_height=font_m.height,
            offset_y=font_m.voffset,
            fg_color=self.timer_color[0][0],
            bg_color=self.timer_color[0][1],
            last=MAX_SECONDS,
            count=total_slot,
        )
        self.set_grid_layout_table_row(
            layout=layout,
            targets=self.bars_timer_last,
            row=self.wcfg["display_order_last"],
            right_to_left=layout_reversed,
        )

        # Best timer
        self.bars_timer_best = self.set_rawtext(
            text=TEXT_PLACEHOLDER,
            width=bar_width,
            fixed_height=font_m.height,
            offset_y=font_m.voffset,
            fg_color=self.wcfg["font_color_best_timer"],
            bg_color=self.wcfg["background_color_best_timer"],
            last=MAX_SECONDS,
            count=total_slot,
        )
        self.set_grid_layout_table_row(
            layout=layout,
            targets=self.bars_timer_best,
            row=self.wcfg["display_order_best"],
            right_to_left=layout_reversed,
        )

        # Delta time
        self.delta_color = (
            self.wcfg["font_color_lap_gain"],
            self.wcfg["font_color_lap_loss"],
            self.wcfg["font_color_delta_time"],
        )
        self.bars_timer_delta = self.set_rawtext(
            text=TEXT_PLACEHOLDER,
            width=bar_width,
            fixed_height=font_m.height,
            offset_y=font_m.voffset,
            fg_color=self.delta_color[2],
            bg_color=self.wcfg["background_color_delta_time"],
            count=total_slot,
            last=MAX_SECONDS,
        )
        self.set_grid_layout_table_row(
            layout=layout,
            targets=self.bars_timer_delta,
            row=self.wcfg["display_order_delta"],
            right_to_left=layout_reversed,
        )

        for index, timer in enumerate(self.timers):
            start = self.unit_speed(timer.speed_start)
            end = self.unit_speed(timer.speed_end)
            self.bars_speed_range[index].text = f"{start:.0f}-{end:.0f}"

    def timerEvent(self, event):
        """Update when vehicle on track"""
        reset_timer = api.read.engine.gear() < 0
        speed = api.read.vehicle.speed()
        elapsed_time = api.read.timing.elapsed()

        for index, timer in enumerate(self.timers):
            if reset_timer:
                timer.reset()

            timer.update(speed, elapsed_time)
            is_active = timer.start_time > 0

            self.update_timer_last(self.bars_timer_last[index], timer.timer if is_active else timer.valid, is_active)
            self.update_timer_best(self.bars_timer_best[index], timer.best)
            self.update_timer_delta(self.bars_timer_delta[index], timer.delta)

    # GUI update methods
    def update_timer_last(self, target, data, is_active):
        """Last acceleration time"""
        if target.last != data:
            target.last = data
            target.fg, target.bg = self.timer_color[is_active]
            if MAX_SECONDS > data > 0:
                text = f"{data:.{self.decimals_timer}f}"[:self.char_width]
            else:
                text = TEXT_PLACEHOLDER
            target.text = text
            target.update()

    def update_timer_best(self, target, data):
        """Best acceleration time"""
        if target.last != data:
            target.last = data
            if MAX_SECONDS > data > 0:
                text = f"{data:.{self.decimals_timer}f}"[:self.char_width]
            else:
                text = TEXT_PLACEHOLDER
            target.text = text
            target.update()

    def update_timer_delta(self, target, data):
        """Delta acceleration time between last & best"""
        if target.last != data:
            target.last = data
            delta_text = f"{data:+.{self.decimals_delta}f}"[:self.char_width]
            color_index = (data >= 0) if data else 2
            target.text = delta_text
            target.fg = self.delta_color[color_index]
            target.update()

    # Additional methods
    def set_timers(self):
        """Set acceleration timers"""
        speed_drop = max(self.wcfg["speed_drop_threshold"], 0)
        for index in range(10):
            if self.wcfg[f"speed_range_{index + 1}_end"] > 0:
                start = self.wcfg[f"speed_range_{index + 1}_start"]
                end = self.wcfg[f"speed_range_{index + 1}_end"]
                yield AccelTimer(start, end, speed_drop)


class AccelTimer:
    """Acceleration timer"""

    __slots__ = (
        "speed_start",
        "speed_end",
        "speed_drop",
        "speed_max",
        "start_time",
        "timer",
        "valid",
        "delta",
        "best",
    )

    def __init__(self, speed_start: float, speed_end: float, speed_drop: float):
        self.speed_start = speed_start
        self.speed_end = max(self.speed_start + 1, speed_end)
        self.speed_drop = speed_drop
        self.reset()

    def reset(self):
        self.speed_max = 0.0
        self.start_time = 0.0
        self.timer = 0.0
        self.valid = MAX_SECONDS
        self.delta = 0.0
        self.best = MAX_SECONDS

    def update(self, speed: float, elapsed_time: float):
        """Update timer"""
        if self.start_time:
            if self.speed_max < speed:
                self.speed_max = speed
            self.timer = elapsed_time - self.start_time

            if speed >= self.speed_end:
                self.start_time = 0.0
                self.valid = self.timer

                if MAX_SECONDS > self.best and MAX_SECONDS > self.valid:
                    self.delta = self.valid - self.best
                else:
                    self.delta = 0.0

                if self.best > self.valid:
                    self.best = self.valid

            if self.speed_max - speed > self.speed_drop or speed < self.speed_start:
                self.start_time = 0.0
                self.timer = 0.0

        elif self.speed_start + 1 > speed > self.speed_start:
            self.start_time = elapsed_time
            self.timer = 0.0
            self.speed_max = speed
