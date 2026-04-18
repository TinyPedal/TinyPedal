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
Traffic Widget
"""

from .. import units
from ..api_control import api
from ..const_common import MAX_SECONDS, TEXT_PLACEHOLDER
from ..formatter import random_color_class, shorten_driver_name
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

        if self.wcfg["show_caption"]:
            font_cap = self.config_font(
                self.wcfg["font_name"],
                self.wcfg["font_size"] * self.wcfg["font_scale_caption"],
                self.wcfg["font_weight"],
            )
            font_cap_m = self.get_font_metrics(font_cap)

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        bar_width = max(self.wcfg["bar_width"], 3)
        style_width = font_m.width * bar_width + bar_padx
        self.lap_width = bar_width - 1
        self.cls_width = bar_width

        # Config units
        self.unit_fuel = units.set_unit_fuel(self.cfg.units["fuel_unit"])

        # Create layout
        layout_slower = self.set_grid_layout()
        layout_leader = self.set_grid_layout()
        layout_faster = self.set_grid_layout()
        layout.addLayout(layout_slower, 0, self.wcfg["display_order_slower"])
        layout.addLayout(layout_leader, 0, self.wcfg["display_order_leader"])
        layout.addLayout(layout_faster, 0, self.wcfg["display_order_faster"])

        if self.wcfg["show_caption"]:
            cap_temps = self.set_rawtext(
                font=font_cap,
                text=self.wcfg["caption_text_slower"],
                fixed_height=font_cap_m.height,
                offset_y=font_cap_m.voffset,
                fg_color=self.wcfg["font_color_caption"],
                bg_color=self.wcfg["background_color_caption"],
                count=3,
            )
            texts = (
                self.wcfg["caption_text_slower"],
                self.wcfg["caption_text_leader"],
                self.wcfg["caption_text_faster"],
            )
            for cap_temp, cap_text in zip(cap_temps, texts):
                cap_temp.text = cap_text
            layout_slower.addWidget(cap_temps[0], 0, 0)
            layout_leader.addWidget(cap_temps[1], 0, 0)
            layout_faster.addWidget(cap_temps[2], 0, 0)

        # Class name
        if self.wcfg["show_class"]:
            self.bar_classes = self.set_rawtext(
                text=TEXT_PLACEHOLDER,
                fixed_width=style_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_class"],
                bg_color=self.wcfg["background_color_class"],
                count=3,
            )
            layout_slower.addWidget(self.bar_classes[0], 1, 0)
            layout_leader.addWidget(self.bar_classes[1], 1, 0)
            layout_faster.addWidget(self.bar_classes[2], 1, 0)

        # Estimated laps
        if self.wcfg["show_estimated_laps"]:
            self.decimals_laps = max(self.wcfg["decimal_places_estimated_laps"], 0)
            self.bar_style_laps = (
                (
                    self.wcfg["font_color_estimated_laps"],
                    self.wcfg["background_color_estimated_laps"],
                ),
                (
                    self.wcfg["font_color_traffic_highlight"],
                    self.wcfg["background_color_traffic_highlight"],
                ),
            )
            self.bar_laps = self.set_rawtext(
                text=TEXT_PLACEHOLDER,
                fixed_width=style_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_estimated_laps"],
                bg_color=self.wcfg["background_color_estimated_laps"],
                count=3,
            )
            layout_slower.addWidget(self.bar_laps[0], 2, 0)
            layout_leader.addWidget(self.bar_laps[1], 2, 0)
            layout_faster.addWidget(self.bar_laps[2], 2, 0)

        # Time interval
        if self.wcfg["show_time_interval"]:
            self.decimals_time = max(self.wcfg["decimal_places_time_interval"], 0)
            self.bar_time = self.set_rawtext(
                text=TEXT_PLACEHOLDER,
                fixed_width=style_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_time_interval"],
                bg_color=self.wcfg["background_color_time_interval"],
                count=3,
            )
            layout_slower.addWidget(self.bar_time[0], 3, 0)
            layout_leader.addWidget(self.bar_time[1], 3, 0)
            layout_faster.addWidget(self.bar_time[2], 3, 0)


    def timerEvent(self, event):
        """Update when vehicle on track"""
        veh_data = minfo.vehicles.dataSet
        player_laptime = api.read.timing.estimated_laptime()

        ahead_overtake_laps = MAX_SECONDS
        ahead_overtake_timegap = 0.0
        ahead_overtake_index = -1

        behind_overtake_laps = MAX_SECONDS
        behind_overtake_timegap = 0.0
        behind_overtake_index = -1

        leader_overtake_laps = 0.0
        leader_overtake_timegap = 0.0
        leader_overtake_index = minfo.vehicles.leaderIndex

        if player_laptime > 0:
            relative_ahead = minfo.relative.relativeAhead
            relative_behind = minfo.relative.relativeBehind
            delta_time_interval_ahead = minfo.relative.relativeDeltaAhead
            delta_time_interval_behind = minfo.relative.relativeDeltaBehind

            # Ahead
            for ahead_timegap, ahead_index in relative_ahead:
                if veh_data[ahead_index].inPit:
                    continue

                avg_delta_timegap = delta_time_interval_ahead[ahead_index][1]

                if avg_delta_timegap > 0:
                    ahead_laps = ahead_timegap / avg_delta_timegap / player_laptime
                else:
                    ahead_laps = 0

                if 0 < ahead_laps < ahead_overtake_laps:
                    ahead_overtake_laps = ahead_laps
                    ahead_overtake_timegap = ahead_timegap
                    ahead_overtake_index = ahead_index

            if ahead_overtake_laps >= MAX_SECONDS:
                ahead_overtake_laps = 0.0

            # Behind
            for behind_timegap, behind_index in relative_behind:
                if veh_data[behind_index].inPit:
                    continue

                avg_delta_timegap = delta_time_interval_behind[behind_index][1]

                if avg_delta_timegap > 0:
                    behind_laps = -behind_timegap / avg_delta_timegap / player_laptime
                else:
                    behind_laps = 0

                if 0 < behind_laps < behind_overtake_laps:
                    behind_overtake_laps = behind_laps
                    behind_overtake_timegap = behind_timegap
                    behind_overtake_index = behind_index

                if behind_index == leader_overtake_index:
                    leader_overtake_laps = behind_laps
                    leader_overtake_timegap = behind_timegap

            if behind_overtake_laps >= MAX_SECONDS:
                behind_overtake_laps = 0.0

        if self.wcfg["show_class"]:
            veh_info = veh_data[ahead_overtake_index]
            self.update_class(self.bar_classes[0], veh_info.vehicleClass, veh_info.driverName)
            veh_info = veh_data[leader_overtake_index]
            self.update_class(self.bar_classes[1], veh_info.vehicleClass, veh_info.driverName)
            veh_info = veh_data[behind_overtake_index]
            self.update_class(self.bar_classes[2], veh_info.vehicleClass, veh_info.driverName)

        if self.wcfg["show_estimated_laps"]:
            plr_lap_progress = 1 - api.read.lap.progress()
            opt_lap_progress = 1 - api.read.lap.progress(ahead_overtake_index)
            self.update_laps(self.bar_laps[0], ahead_overtake_laps, opt_lap_progress)
            self.update_laps(self.bar_laps[1], leader_overtake_laps, plr_lap_progress)
            self.update_laps(self.bar_laps[2], behind_overtake_laps, plr_lap_progress)

        if self.wcfg["show_time_interval"]:
            self.update_time(self.bar_time[0], ahead_overtake_timegap)
            self.update_time(self.bar_time[1], leader_overtake_timegap)
            self.update_time(self.bar_time[2], behind_overtake_timegap)

    # GUI update methods
    def update_laps(self, target, *data):
        """Traffic laps"""
        if target.last != data:
            target.last = data
            laps = data[0]
            if laps > 0:
                text = f"{laps:.{self.decimals_laps}f}"[:self.lap_width].strip(".")
                text = f"{text}L"
            else:
                text = TEXT_PLACEHOLDER
            target.text = text
            if self.wcfg["enable_traffic_highlight_from_current_lap"]:
                target.fg, target.bg = self.bar_style_laps[0 < laps <= data[1]]
            target.update()

    def update_time(self, target, data):
        """Time interval"""
        if target.last != data:
            target.last = data
            if data != 0:
                text = f"{abs(data):.{self.decimals_time}f}"[:self.lap_width].strip(".")
                text = f"{text}s"
            else:
                text = TEXT_PLACEHOLDER
            target.text = text
            target.update()

    def update_class(self, target, *data):
        """Vehicle class"""
        if target.last != data:
            target.last = data
            text, bg_color = self.set_class_style(data[0])
            if self.wcfg["show_driver_name_instead_of_class"]:
                text = data[1]
                if not text:
                    text = TEXT_PLACEHOLDER
                elif self.wcfg["driver_name_shorten"]:
                    text = shorten_driver_name(text)
                if self.wcfg["driver_name_uppercase"]:
                    text = text.upper()
            target.text = text[:self.cls_width]
            target.fg, target.bg = (self.wcfg["font_color_class"], bg_color)
            target.update()

    def set_class_style(self, class_name: str):
        """Compare vehicle class name with user defined dictionary"""
        style = self.cfg.user.classes.get(class_name)
        if style is not None:
            return style["alias"], style["color"]
        if class_name:
            return class_name, random_color_class(class_name)
        return TEXT_PLACEHOLDER, self.wcfg["background_color_class"]
