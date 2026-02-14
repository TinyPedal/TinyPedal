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
        bar_width = font_m.width * 5 + bar_padx

        # Transient max braking rate
        if self.wcfg["show_transient_max_braking_rate"]:
            self.bar_trans_rate = self.set_rawtext(
                text="0.00g",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_transient_max_braking_rate"],
                bg_color=self.wcfg["bkg_color_transient_max_braking_rate"],
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_trans_rate,
                column=self.wcfg["column_index_transient_max_braking_rate"],
            )

        # Max braking rate
        if self.wcfg["show_max_braking_rate"]:
            self.bar_max_rate = self.set_rawtext(
                text="0.00g",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_max_braking_rate"],
                bg_color=self.wcfg["bkg_color_max_braking_rate"],
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_max_rate,
                column=self.wcfg["column_index_max_braking_rate"],
            )

        # Delta braking rate
        if self.wcfg["show_delta_braking_rate"]:
            self.bar_style_delta_rate = (
                self.wcfg["bkg_color_braking_rate_loss"],
                self.wcfg["bkg_color_braking_rate_gain"],
                self.wcfg["bkg_color_delta_braking_rate"],
            )
            self.bar_delta_rate = self.set_rawtext(
                text="+0.00",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_delta_braking_rate"],
                bg_color=self.bar_style_delta_rate[2],
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_delta_rate,
                column=self.wcfg["column_index_delta_braking_rate"],
            )

        # Front wheel lock duration
        if self.wcfg["show_front_wheel_lock_duration"]:
            self.bar_lock_f = self.set_rawtext(
                text="F 0.0",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_front_wheel_lock_duration"],
                bg_color=self.wcfg["bkg_color_front_wheel_lock_duration"],
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_lock_f,
                column=self.wcfg["column_index_front_wheel_lock_duration"],
            )

        # Rear wheel lock duration
        if self.wcfg["show_rear_wheel_lock_duration"]:
            self.bar_lock_r = self.set_rawtext(
                text="R 0.0",
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_rear_wheel_lock_duration"],
                bg_color=self.wcfg["bkg_color_rear_wheel_lock_duration"],
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_lock_r,
                column=self.wcfg["column_index_rear_wheel_lock_duration"],
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

        # Front wheel lock duration
        if self.wcfg["show_front_wheel_lock_duration"]:
            self.update_lock_time_f(self.bar_lock_f, max(minfo.wheels.lockingTime[:2]))

        # Rear wheel lock duration
        if self.wcfg["show_rear_wheel_lock_duration"]:
            self.update_lock_time_r(self.bar_lock_r, max(minfo.wheels.lockingTime[2:]))

    # GUI update methods
    def update_braking_rate(self, target, data):
        """Braking rate (g force)"""
        if target.last != data:
            target.last = data
            target.text = f"{data: >4.2f}g"[:5]
            target.update()

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
            target.text = text[:5]
            target.bg = self.bar_style_delta_rate[data > 0]
            target.update()

    def update_lock_time_f(self, target, data):
        """Front wheel lock duration"""
        if target.last != data:
            target.last = data
            target.text = f"F{data: >4.1f}"[:5]
            target.update()

    def update_lock_time_r(self, target, data):
        """Rear wheel lock duration"""
        if target.last != data:
            target.last = data
            target.text = f"R{data: >4.1f}"[:5]
            target.update()
