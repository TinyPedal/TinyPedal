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
Damage stats Widget
"""

from ..api_control import api
from ..const_common import TEXT_NA
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
        self.decimals = max(self.wcfg["decimal_places"], 0)
        self.width_integrity = 3 + self.decimals + (self.decimals > 0)
        bar_width = font_m.width * self.width_integrity + bar_padx

        if self.wcfg["layout"] == 0:
            width_aero = max(
                len(self.wcfg["prefix_aero_integrity"]),
                len(self.wcfg["prefix_body_integrity"]),
                len(self.wcfg["prefix_suspension_integrity"]),
                len(self.wcfg["prefix_tyre_integrity"]),
            )
            width_body = width_aero
            width_susp = width_aero
            width_tyre = width_aero
        else:
            width_aero = len(self.wcfg["prefix_aero_integrity"])
            width_body = len(self.wcfg["prefix_body_integrity"])
            width_susp = len(self.wcfg["prefix_suspension_integrity"])
            width_tyre = len(self.wcfg["prefix_tyre_integrity"])

        # Aero integrity
        if self.wcfg["show_aero_integrity"]:
            layout_aero = self.set_grid_layout()
            self.bar_style_aero = (
                self.wcfg["background_color_aero_integrity"],
                self.wcfg["warning_color_low_aero_integrity"],
            )
            self.bar_aero = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_aero_integrity"],
                bg_color=self.wcfg["background_color_aero_integrity"],
            )
            layout_aero.addWidget(self.bar_aero, 0, 1)
            if self.wcfg["show_integrity_prefix"]:
                bar_aero_prefix = self.set_rawtext(
                    text=self.wcfg["prefix_aero_integrity"],
                    width=font_m.width * width_aero + bar_padx,
                    fixed_height=font_m.height,
                    offset_y=font_m.voffset,
                    fg_color=self.wcfg["font_color_integrity_prefix"],
                    bg_color=self.wcfg["background_color_integrity_prefix"],
                )
                layout_aero.addWidget(bar_aero_prefix, 0, 0)
            self.set_primary_orient(
                target=layout_aero,
                column=self.wcfg["display_order_aero_integrity"],
            )

        # Body integrity
        if self.wcfg["show_body_integrity"]:
            layout_body = self.set_grid_layout()
            self.bar_style_body = (
                self.wcfg["background_color_body_integrity"],
                self.wcfg["warning_color_low_body_integrity"],
            )
            self.bar_body = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_body_integrity"],
                bg_color=self.wcfg["background_color_body_integrity"],
            )
            layout_body.addWidget(self.bar_body, 0, 1)
            if self.wcfg["show_integrity_prefix"]:
                bar_body_prefix = self.set_rawtext(
                    text=self.wcfg["prefix_body_integrity"],
                    width=font_m.width * width_body + bar_padx,
                    fixed_height=font_m.height,
                    offset_y=font_m.voffset,
                    fg_color=self.wcfg["font_color_integrity_prefix"],
                    bg_color=self.wcfg["background_color_integrity_prefix"],
                )
                layout_body.addWidget(bar_body_prefix, 0, 0)
            self.set_primary_orient(
                target=layout_body,
                column=self.wcfg["display_order_body_integrity"],
            )

        # Suspension integrity
        if self.wcfg["show_suspension_integrity"]:
            layout_susp = self.set_grid_layout()
            self.bar_style_susp = (
                self.wcfg["background_color_suspension_integrity"],
                self.wcfg["warning_color_low_suspension_integrity"],
            )
            self.bar_susp = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_suspension_integrity"],
                bg_color=self.wcfg["background_color_suspension_integrity"],
            )
            layout_susp.addWidget(self.bar_susp, 0, 1)
            if self.wcfg["show_integrity_prefix"]:
                bar_susp_prefix = self.set_rawtext(
                    text=self.wcfg["prefix_suspension_integrity"],
                    width=font_m.width * width_susp + bar_padx,
                    fixed_height=font_m.height,
                    offset_y=font_m.voffset,
                    fg_color=self.wcfg["font_color_integrity_prefix"],
                    bg_color=self.wcfg["background_color_integrity_prefix"],
                )
                layout_susp.addWidget(bar_susp_prefix, 0, 0)
            self.set_primary_orient(
                target=layout_susp,
                column=self.wcfg["display_order_suspension_integrity"],
            )

        # Tyre integrity
        if self.wcfg["show_tyre_integrity"]:
            layout_tyre = self.set_grid_layout()
            self.bar_style_tyre = (
                self.wcfg["background_color_tyre_integrity"],
                self.wcfg["warning_color_low_tyre_integrity"],
            )
            self.bar_tyre = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_tyre_integrity"],
                bg_color=self.wcfg["background_color_tyre_integrity"],
            )
            layout_tyre.addWidget(self.bar_tyre, 0, 1)
            if self.wcfg["show_integrity_prefix"]:
                bar_tyre_prefix = self.set_rawtext(
                    text=self.wcfg["prefix_tyre_integrity"],
                    width=font_m.width * width_tyre + bar_padx,
                    fixed_height=font_m.height,
                    offset_y=font_m.voffset,
                    fg_color=self.wcfg["font_color_integrity_prefix"],
                    bg_color=self.wcfg["background_color_integrity_prefix"],
                )
                layout_tyre.addWidget(bar_tyre_prefix, 0, 0)
            self.set_primary_orient(
                target=layout_tyre,
                column=self.wcfg["display_order_tyre_integrity"],
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if self.wcfg["show_aero_integrity"]:
            damage_aero = api.read.vehicle.aero_damage()
            if damage_aero >= 0:
                damage_aero = 1 - damage_aero
            self.update_integrity(self.bar_aero, damage_aero, self.bar_style_aero, self.wcfg["low_aero_integrity_threshold"])

        if self.wcfg["show_body_integrity"]:
            damage_body = 1 - sum(api.read.vehicle.damage_severity()) / 16
            self.update_integrity(self.bar_body, damage_body, self.bar_style_body, self.wcfg["low_body_integrity_threshold"])

        if self.wcfg["show_suspension_integrity"]:
            damage_susp = max(api.read.wheel.suspension_damage())
            if damage_susp >= 0:
                damage_susp = 1 - damage_susp
            else:  # show detached wheel if suspension damage not available
                damage_susp = not any(api.read.wheel.is_detached())
            self.update_integrity(self.bar_susp, damage_susp, self.bar_style_susp, self.wcfg["low_suspension_integrity_threshold"])

        if self.wcfg["show_tyre_integrity"]:
            damage_tyre = min(api.read.tyre.wear())
            self.update_integrity(self.bar_tyre, damage_tyre, self.bar_style_tyre, self.wcfg["low_tyre_integrity_threshold"])

    # GUI update methods
    def update_integrity(self, target, data, style, threshold):
        """Update integrity"""
        if target.last != data:
            target.last = data
            if -1 != data:
                if data < 0:
                    data = 0
                text = f"{data:.{self.decimals}%}"[:self.width_integrity]
                color = style[data <= threshold]
            else:
                text = TEXT_NA
                color = style[0]
            target.text = text
            target.bg = color
            target.update()
