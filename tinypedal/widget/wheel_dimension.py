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
Wheel dimension Widget
"""

from .. import minfo
from ..constant import DATA
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
        bar_width = font_m.width * 6 + bar_padx

        # Front tyre radius
        if self.wcfg["show_front_tyre_radius"]:
            self.bar_radius_front = self.set_rawtext(
                text=DATA.TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_front_tyre_radius"],
                bg_color=self.wcfg["background_color_front_tyre_radius"],
            )
            self.set_primary_orient(
                target=self.bar_radius_front,
                column=self.wcfg["display_order_front_tyre_radius"],
            )

        # Rear tyre radius
        if self.wcfg["show_rear_tyre_radius"]:
            self.bar_radius_rear = self.set_rawtext(
                text=DATA.TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_rear_tyre_radius"],
                bg_color=self.wcfg["background_color_rear_tyre_radius"],
            )
            self.set_primary_orient(
                target=self.bar_radius_rear,
                column=self.wcfg["display_order_rear_tyre_radius"],
            )

        # Front wheel track
        if self.wcfg["show_front_wheel_track"]:
            self.bar_track_front = self.set_rawtext(
                text=DATA.TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_front_wheel_track"],
                bg_color=self.wcfg["background_color_front_wheel_track"],
            )
            self.set_primary_orient(
                target=self.bar_track_front,
                column=self.wcfg["display_order_front_wheel_track"],
            )

        # Rear wheel track
        if self.wcfg["show_rear_wheel_track"]:
            self.bar_track_rear = self.set_rawtext(
                text=DATA.TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_rear_wheel_track"],
                bg_color=self.wcfg["background_color_rear_wheel_track"],
            )
            self.set_primary_orient(
                target=self.bar_track_rear,
                column=self.wcfg["display_order_rear_wheel_track"],
            )

        # Wheelbase
        if self.wcfg["show_wheelbase"]:
            self.bar_wheelbase = self.set_rawtext(
                text=DATA.TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_wheelbase"],
                bg_color=self.wcfg["background_color_wheelbase"],
            )
            self.set_primary_orient(
                target=self.bar_wheelbase,
                column=self.wcfg["display_order_wheelbase"],
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Front tyre radius
        if self.wcfg["show_front_tyre_radius"]:
            radius_front = minfo.wheels.wheelRadiusFront
            self.update_wheel(self.bar_radius_front, radius_front)

        # Rear tyre radius
        if self.wcfg["show_rear_tyre_radius"]:
            radius_rear = minfo.wheels.wheelRadiusRear
            self.update_wheel(self.bar_radius_rear, radius_rear)

        # Front wheel track
        if self.wcfg["show_front_wheel_track"]:
            track_front = minfo.wheels.wheelTrackFront
            self.update_wheel(self.bar_track_front, track_front)

        # Rear wheel track
        if self.wcfg["show_rear_wheel_track"]:
            track_rear = minfo.wheels.wheelTrackRear
            self.update_wheel(self.bar_track_rear, track_rear)

        # Wheelbase
        if self.wcfg["show_wheelbase"]:
            wheelbase = minfo.wheels.wheelbase
            self.update_wheel(self.bar_wheelbase, wheelbase)

    # GUI update methods
    def update_wheel(self, target, data):
        """Wheel dimension"""
        if target.last != data:
            target.last = data
            if data <= 0:
                text = DATA.TEXT_NA
            else:
                text = f"{data:.0f}mm"
            target.text = text
            target.update()
