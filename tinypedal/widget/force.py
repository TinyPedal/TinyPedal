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
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        bar_width = font_m.width * 6 + bar_padx

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # G force
        if self.wcfg["show_g_force"]:
            bar_style_gforce_lgt = self.set_qss(
                fg_color=self.wcfg["font_color_g_force"],
                bg_color=self.wcfg["bkg_color_g_force"]
            )
            self.bar_gforce_lgt = self.set_qlabel(
                text=TEXT_NA,
                style=bar_style_gforce_lgt,
                width=bar_width,
            )
            self.set_primary_orient(
                target=self.bar_gforce_lgt,
                column=self.wcfg["column_index_long_gforce"],
            )

            bar_style_gforce_lat = self.set_qss(
                fg_color=self.wcfg["font_color_g_force"],
                bg_color=self.wcfg["bkg_color_g_force"]
            )
            self.bar_gforce_lat = self.set_qlabel(
                text=TEXT_NA,
                style=bar_style_gforce_lat,
                width=bar_width,
            )
            self.set_primary_orient(
                target=self.bar_gforce_lat,
                column=self.wcfg["column_index_lat_gforce"],
            )

        # Downforce ratio
        if self.wcfg["show_downforce_ratio"]:
            bar_style_df_ratio = self.set_qss(
                fg_color=self.wcfg["font_color_downforce_ratio"],
                bg_color=self.wcfg["bkg_color_downforce_ratio"]
            )
            self.bar_df_ratio = self.set_qlabel(
                text=TEXT_NA,
                style=bar_style_df_ratio,
                width=bar_width,
            )
            self.set_primary_orient(
                target=self.bar_df_ratio,
                column=self.wcfg["column_index_downforce_ratio"],
            )

        # Front downforce
        if self.wcfg["show_front_downforce"]:
            self.bar_style_df_front = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_front_downforce"],
                    bg_color=self.wcfg["bkg_color_front_downforce"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_front_downforce"],
                    bg_color=self.wcfg["warning_color_liftforce"])
            )
            self.bar_df_front = self.set_qlabel(
                text=TEXT_NA,
                style=self.bar_style_df_front[0],
                width=bar_width,
            )
            self.set_primary_orient(
                target=self.bar_df_front,
                column=self.wcfg["column_index_front_downforce"],
            )

        # Rear downforce
        if self.wcfg["show_rear_downforce"]:
            self.bar_style_df_rear = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_rear_downforce"],
                    bg_color=self.wcfg["bkg_color_rear_downforce"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_rear_downforce"],
                    bg_color=self.wcfg["warning_color_liftforce"])
            )
            self.bar_df_rear = self.set_qlabel(
                text=TEXT_NA,
                style=self.bar_style_df_rear[0],
                width=bar_width,
            )
            self.set_primary_orient(
                target=self.bar_df_rear,
                column=self.wcfg["column_index_rear_downforce"],
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # G force
        if self.wcfg["show_g_force"]:
            # Longitudinal g-force
            gf_lgt = round(minfo.force.lgtGForceRaw, 2)
            self.update_gf_lgt(self.bar_gforce_lgt, gf_lgt)

            # Lateral g-force
            gf_lat = round(minfo.force.latGForceRaw, 2)
            self.update_gf_lat(self.bar_gforce_lat, gf_lat)

        # Downforce ratio
        if self.wcfg["show_downforce_ratio"]:
            df_ratio = round(minfo.force.downForceRatio, 2)
            self.update_df_ratio(self.bar_df_ratio, df_ratio)

        # Front downforce
        if self.wcfg["show_front_downforce"]:
            df_front = round(minfo.force.downForceFront)
            self.update_df_front(self.bar_df_front, df_front)

        # Rear downforce
        if self.wcfg["show_rear_downforce"]:
            df_rear = round(minfo.force.downForceRear)
            self.update_df_rear(self.bar_df_rear, df_rear)

    # GUI update methods
    def update_gf_lgt(self, target, data):
        """Longitudinal g-force"""
        if target.last != data:
            target.last = data
            target.setText(f"{self.gforce_lgt(data)} {abs(data):.2f}")

    def update_gf_lat(self, target, data):
        """Lateral g-force"""
        if target.last != data:
            target.last = data
            target.setText(f"{abs(data):.2f} {self.gforce_lat(data)}")

    def update_df_ratio(self, target, data):
        """Downforce ratio"""
        if target.last != data:
            target.last = data
            text = f"{data:.2f}"[:5].strip(".")
            target.setText(f"{text}%")

    def update_df_front(self, target, data):
        """Downforce front"""
        if target.last != data:
            target.last = data
            target.setText(f"F{abs(data):5.0f}"[:6])
            target.updateStyle(self.bar_style_df_front[data < 0])

    def update_df_rear(self, target, data):
        """Downforce rear"""
        if target.last != data:
            target.last = data
            target.setText(f"R{abs(data):5.0f}"[:6])
            target.updateStyle(self.bar_style_df_rear[data < 0])

    # Additional methods
    @staticmethod
    def gforce_lgt(g_force):
        """Longitudinal g-force direction symbol"""
        if g_force > 0.1:
            return "▼"
        if g_force < -0.1:
            return "▲"
        return "●"

    @staticmethod
    def gforce_lat(g_force):
        """Lateral g-force direction symbol"""
        if g_force > 0.1:
            return "◀"
        if g_force < -0.1:
            return "▶"
        return "●"
