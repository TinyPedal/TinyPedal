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
Session Widget
"""

from time import strftime

from .. import calculation as calc
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
        font = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size"],
            self.wcfg["font_weight"],
        )
        self.setFont(font)
        font_m = self.get_font_metrics(font)

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        self.session_name_list = (
            self.wcfg["session_text_testday"],
            self.wcfg["session_text_practice"],
            self.wcfg["session_text_qualify"],
            self.wcfg["session_text_warmup"],
            self.wcfg["session_text_race"],
        )

        # Session name
        if self.wcfg["show_session_name"]:
            text_session_name = self.session_name_list[0]
            self.bar_session_name = self.set_rawtext(
                text=text_session_name,
                width=font_m.width * max(map(len, self.session_name_list)) + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_session_name"],
                bg_color=self.wcfg["background_color_session_name"],
            )
            self.set_primary_orient(
                target=self.bar_session_name,
                column=self.wcfg["display_order_session_name"],
            )

        # System clock
        if self.wcfg["show_system_clock"]:
            text_system_clock = strftime(self.wcfg["system_clock_format"])
            self.bar_system_clock = self.set_rawtext(
                text=text_system_clock,
                width=font_m.width * len(text_system_clock) + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_system_clock"],
                bg_color=self.wcfg["background_color_system_clock"],
            )
            self.set_primary_orient(
                target=self.bar_system_clock,
                column=self.wcfg["display_order_system_clock"],
            )

        # Session time
        if self.wcfg["show_session_time"]:
            text_session_time = calc.sec2sessiontime(0)
            self.bar_session_time = self.set_rawtext(
                text=text_session_time,
                width=font_m.width * len(text_session_time) + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_session_time"],
                bg_color=self.wcfg["background_color_session_time"],
            )
            self.set_primary_orient(
                target=self.bar_session_time,
                column=self.wcfg["display_order_session_time"],
            )

        # Estimated remaining laps
        if self.wcfg["show_estimated_laps"]:
            self.prefix_estimated_laps = self.wcfg["prefix_estimated_laps"]
            text_estimated_laps = f"{self.prefix_estimated_laps}-.---"
            self.bar_estimated_laps = self.set_rawtext(
                text=text_estimated_laps,
                width=font_m.width * len(text_estimated_laps) + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_estimated_laps"],
                bg_color=self.wcfg["background_color_estimated_laps"],
            )
            self.set_primary_orient(
                target=self.bar_estimated_laps,
                column=self.wcfg["display_order_estimated_laps"],
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        remaining_time = api.read.session.remaining()

        # Session name
        if self.wcfg["show_session_name"]:
            session_index = api.read.session.session_type()
            self.update_session_name(self.bar_session_name, session_index)

        # System Clock
        if self.wcfg["show_system_clock"]:
            system_time = strftime(self.wcfg["system_clock_format"])
            self.update_system_clock(self.bar_system_clock, system_time)

        # Session time
        if self.wcfg["show_session_time"]:
            if remaining_time <= 0 and minfo.vehicles.finishTimeOffset < 0:
                session_time = remaining_time - minfo.vehicles.finishTimeOffset
                estimated = True
            else:
                session_time = remaining_time
                estimated = False
            self.update_session_time(self.bar_session_time, session_time, estimated)

        # Estimated remaining laps
        if self.wcfg["show_estimated_laps"]:
            if api.read.session.finish_type(minfo.vehicles.finishAsLap):
                laps_left = api.read.lap.remaining()
            else:
                lap_into = api.read.lap.progress()
                est_time = remaining_time - minfo.vehicles.finishTimeOffset
                end_timer_laps_left = calc.end_timer_laps_remain(lap_into, minfo.delta.lapTimePace, est_time)
                laps_left = calc.time_type_laps_remain(calc.ceil(end_timer_laps_left), lap_into)
            self.update_estimated_laps(self.bar_estimated_laps, laps_left)

    # GUI update methods
    def update_session_name(self, target, data):
        """Session name"""
        if target.last != data:
            target.last = data
            target.text = self.session_name_list[data]
            target.update()

    def update_system_clock(self, target, data):
        """System Clock"""
        if target.last != data:
            target.last = data
            target.text = data
            target.update()

    def update_session_time(self, target, data, estimated):
        """Session time"""
        if target.last != data:
            target.last = data
            if data < 0:
                data = 0
            if estimated:
                text = f"~{calc.sec2countdown(data):.7}"
            else:
                text = calc.sec2sessiontime(data)
            target.text = text
            target.update()

    def update_estimated_laps(self, target, data):
        """Estimated remaining laps"""
        if target.last != data:
            target.last = data
            text = f"{data:>5.3f}"[:5]
            target.text = f"{self.prefix_estimated_laps}{text}"
            target.update()
