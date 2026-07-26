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
Force Widget
"""

from .. import units
from ..const_common import TEXT_NA
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
        bar_width = font_m.width * 6 + bar_padx

        # Config units
        self.unit_weight = units.set_unit_weight(self.cfg.units["weight_unit"])
        self.symbol_weight = units.set_symbol_weight(self.cfg.units["weight_unit"])

        # Longitudinal g-force
        if self.wcfg["show_longitudinal_g_force"]:
            self.bar_gforce_lgt = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_longitudinal_g_force"],
                bg_color=self.wcfg["background_color_longitudinal_g_force"],
            )
            self.set_primary_orient(
                target=self.bar_gforce_lgt,
                column=self.wcfg["display_order_longitudinal_g_force"],
            )

        # Lateral g-force
        if self.wcfg["show_lateral_g_force"]:
            self.bar_gforce_lat = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_lateral_g_force"],
                bg_color=self.wcfg["background_color_lateral_g_force"],
            )
            self.set_primary_orient(
                target=self.bar_gforce_lat,
                column=self.wcfg["display_order_lateral_g_force"],
            )

        # Downforce ratio
        if self.wcfg["show_downforce_ratio"]:
            self.bar_df_ratio = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_downforce_ratio"],
                bg_color=self.wcfg["background_color_downforce_ratio"],
            )
            self.set_primary_orient(
                target=self.bar_df_ratio,
                column=self.wcfg["display_order_downforce_ratio"],
            )

        # Front downforce
        if self.wcfg["show_front_downforce"]:
            self.bar_style_df_front = (
                self.wcfg["background_color_front_downforce"],
                self.wcfg["warning_color_liftforce"],
            )
            self.bar_df_front = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_front_downforce"],
                bg_color=self.bar_style_df_front[0],
            )
            self.set_primary_orient(
                target=self.bar_df_front,
                column=self.wcfg["display_order_front_downforce"],
            )

        # Rear downforce
        if self.wcfg["show_rear_downforce"]:
            self.bar_style_df_rear = (
                self.wcfg["background_color_rear_downforce"],
                self.wcfg["warning_color_liftforce"],
            )
            self.bar_df_rear = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_rear_downforce"],
                bg_color=self.bar_style_df_rear[0],
            )
            self.set_primary_orient(
                target=self.bar_df_rear,
                column=self.wcfg["display_order_rear_downforce"],
            )

        # Estimated static weight
        if self.wcfg["show_estimated_static_weight"]:
            self.bar_weight = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_estimated_static_weight"],
                bg_color=self.wcfg["background_color_estimated_static_weight"],
            )
            self.set_primary_orient(
                target=self.bar_weight,
                column=self.wcfg["display_order_estimated_static_weight"],
            )

        # Acceleration reduction
        if self.wcfg["show_acceleration_reduction"]:
            self.bar_accloss = self.set_rawtext(
                text=TEXT_NA,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_acceleration_reduction"],
                bg_color=self.wcfg["background_color_acceleration_reduction"],
            )
            self.set_primary_orient(
                target=self.bar_accloss,
                column=self.wcfg["display_order_acceleration_reduction"],
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        min_static_weight = minfo.force.minimumStaticWeight
        total_weight = min_static_weight + minfo.fuel.weight

        # Longitudinal g-force
        if self.wcfg["show_longitudinal_g_force"]:
            gf_lgt = round(minfo.force.lgtGForceRaw, 2)
            self.update_gf_lgt(self.bar_gforce_lgt, gf_lgt)

        # Lateral g-force
        if self.wcfg["show_lateral_g_force"]:
            gf_lat = round(minfo.force.latGForceRaw, 2)
            self.update_gf_lat(self.bar_gforce_lat, gf_lat)

        # Downforce ratio
        if self.wcfg["show_downforce_ratio"]:
            df_ratio = round(minfo.force.downForceRatio * 100, 2)
            self.update_df_ratio(self.bar_df_ratio, df_ratio)

        # Front downforce
        if self.wcfg["show_front_downforce"]:
            df_front = round(minfo.force.downForceFront)
            self.update_df_front(self.bar_df_front, df_front)

        # Rear downforce
        if self.wcfg["show_rear_downforce"]:
            df_rear = round(minfo.force.downForceRear)
            self.update_df_rear(self.bar_df_rear, df_rear)

        # Estimated static weight
        if self.wcfg["show_estimated_static_weight"]:
            if self.wcfg["show_minimum_static_weight_without_fuel"]:
                static_weight = min_static_weight
            else:
                static_weight = total_weight
            self.update_static_weight(self.bar_weight, round(static_weight))

        # Acceleration reduction
        if self.wcfg["show_acceleration_reduction"]:
            if total_weight > 0:
                accel_loss = (1 - min_static_weight / total_weight) * 100
            else:
                accel_loss = 0.0
            self.update_acceleration_reduction(self.bar_accloss, accel_loss)

    # GUI update methods
    def update_gf_lgt(self, target, data):
        """Longitudinal g-force"""
        if target.last != data:
            target.last = data
            if data > 0.1:
                sign = "▼"
            elif data < -0.1:
                sign = "▲"
            else:
                sign = "●"
            target.text = f"{sign} {abs(data):.2f}"
            target.update()

    def update_gf_lat(self, target, data):
        """Lateral g-force"""
        if target.last != data:
            target.last = data
            if data > 0.1:
                sign = "◀"
            elif data < -0.1:
                sign = "▶"
            else:
                sign = "●"
            target.text = f"{abs(data):.2f} {sign}"
            target.update()

    def update_df_ratio(self, target, data):
        """Downforce ratio"""
        if target.last != data:
            target.last = data
            text_ratio = f"{data:.2f}"
            target.text = f"{text_ratio:.5}%"
            target.update()

    def update_df_front(self, target, data):
        """Downforce front"""
        if target.last != data:
            target.last = data
            target.text = f"F{abs(data):5.0f}"[:6]
            target.bg = self.bar_style_df_front[data < 0]
            target.update()

    def update_df_rear(self, target, data):
        """Downforce rear"""
        if target.last != data:
            target.last = data
            target.text = f"R{abs(data):5.0f}"[:6]
            target.bg = self.bar_style_df_rear[data < 0]
            target.update()

    def update_static_weight(self, target, data):
        """Estimated static weight"""
        if target.last != data:
            target.last = data
            if data > 1:
                text_weight = f"{self.unit_weight(data):.0f}{self.symbol_weight}"
            else:
                text_weight = TEXT_NA
            target.text = text_weight
            target.update()

    def update_acceleration_reduction(self, target, data):
        """Acceleration reduction"""
        if target.last != data:
            target.last = data
            text_accel = f"{data:.3f}"
            target.text = f"{text_accel:.5}%"
            target.update()
