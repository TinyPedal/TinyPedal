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
Track clock Widget
"""

from time import gmtime, strftime

from .. import calculation as calc
from ..api_control import api
from ..const_common import TEXT_NA, TEXT_TREND_SIGN
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
        font = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size"],
            self.wcfg["font_weight"],
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        self.time_scale_override = max(int(self.wcfg["track_clock_time_scale"]), 0)

        # Track clock
        if self.wcfg["show_track_clock"]:
            text_clock = strftime(self.wcfg["track_clock_format"], gmtime(0))
            self.bar_track_clock = self.set_rawtext(
                text=text_clock,
                width=font_m.width * len(text_clock) + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_track_clock"],
                bg_color=self.wcfg["bkg_color_track_clock"],
            )
            self.set_primary_orient(
                target=self.bar_track_clock,
                column=self.wcfg["column_index_track_clock"],
            )

        # Track clock time scale
        if self.wcfg["show_time_scale"]:
            self.prefix_time_scale = self.wcfg["prefix_time_scale"]
            text_time_scale = f"{self.prefix_time_scale}1"
            self.bar_time_scale = self.set_rawtext(
                text=text_time_scale,
                width=font_m.width * (1 + len(text_time_scale)) + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_time_scale"],
                bg_color=self.wcfg["bkg_color_time_scale"],
            )
            self.set_primary_orient(
                target=self.bar_time_scale,
                column=self.wcfg["column_index_time_scale"],
            )

        # Sunlight phase countdown
        if self.wcfg["show_sunlight_phase_countdown"]:
            layout_phase = self.set_grid_layout()
            text_countdown = f"-{calc.sec2countdown(0)}"
            self.bar_countdown = self.set_rawtext(
                text=text_countdown,
                width=font_m.width * len(text_countdown) + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_sunlight_phase_countdown"],
                bg_color=self.wcfg["bkg_color_sunlight_phase_countdown"],
            )
            layout_phase.addWidget(self.bar_countdown, 0, 0)

            self.bar_style_phase = (
                self.wcfg["font_color_phase_day"],
                self.wcfg["font_color_phase_night"],
            )
            self.bar_phase_sign = self.set_rawtext(
                text=TEXT_TREND_SIGN[0],
                width=font_m.width + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.bar_style_phase[0],
                bg_color=self.wcfg["bkg_color_sunlight_phase_countdown"],
            )
            layout_phase.addWidget(self.bar_phase_sign, 0, 1)
            self.set_primary_orient(
                target=layout_phase,
                column=self.wcfg["column_index_sunlight_phase_countdown"],
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        track_time = api.read.session.track_time()

        if self.wcfg["enable_track_clock_synchronization"]:
            time_scale = api.read.session.time_scale()
        else:
            time_scale = self.time_scale_override

        if track_time == -1:
            track_time = calc.clock_time(api.read.session.elapsed(), api.read.session.start(), time_scale)

        # Track clock
        if self.wcfg["show_track_clock"]:
            self.update_track_clock(self.bar_track_clock, track_time)

        # Track clock time scale
        if self.wcfg["show_time_scale"]:
            self.update_time_scale(self.bar_time_scale, time_scale)

        # Sunlight phase countdown
        if self.wcfg["show_sunlight_phase_countdown"]:
            sun_phases = minfo.mapping.sunlightPhases

            if sun_phases is None:
                countdown = 0
                next_phase_index = 0
            else:
                phase_index = calc.binary_search_lower_column(sun_phases, track_time, 0, 3) + 1
                if phase_index > 3:
                    phase_index = 0
                next_phase_time, next_phase_index = sun_phases[phase_index]
                if track_time > next_phase_time:
                    next_phase_time += 86400
                countdown = next_phase_time - track_time
                if not self.wcfg["enable_time_scaled_countdown"] and time_scale > 0:
                    countdown /= time_scale

            self.update_countdown(self.bar_countdown, countdown)
            self.update_phase_sign(self.bar_phase_sign, next_phase_index)

    # GUI update methods
    def update_track_clock(self, target, data):
        """Track clock"""
        if target.last != data:
            target.last = data
            target.text = strftime(self.wcfg["track_clock_format"], gmtime(data))
            target.update()

    def update_time_scale(self, target, data):
        """Track clock time scale"""
        if target.last != data:
            target.last = data
            if 0 <= data <= 60:
                text = f"{self.prefix_time_scale}{data}"
            else:
                text = TEXT_NA
            target.text = text
            target.update()

    def update_countdown(self, target, data):
        """Sunlight phase countdown"""
        if target.last != data:
            target.last = data
            target.text = f"-{calc.sec2countdown(abs(data))}"
            target.update()

    def update_phase_sign(self, target, data):
        """Upcoming phase sign"""
        if target.last != data:
            target.last = data
            if data == 0:  # sunrise
                sign_index = 1
                color_index = 1
            elif data == 1:  # sunrise
                sign_index = 1
                color_index = 0
            elif data == 2:  # sec_sunset
                sign_index = 2
                color_index = 0
            elif data == 3:  # midnight
                sign_index = 2
                color_index = 1
            target.text = TEXT_TREND_SIGN[sign_index]
            target.fg = self.bar_style_phase[color_index]
            target.update()
