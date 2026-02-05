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
Battery Widget
"""

from ..module_info import minfo
from ._base import Overlay
from ._common import warning_flash


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
        bar_width = font_m.width * 8 + bar_padx
        self.freeze_duration = min(max(self.wcfg["freeze_duration"], 0), 30)

        # Base style
        self.set_base_style(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # Battery charge
        if self.wcfg["show_battery_charge"]:
            self.bar_style_charge = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_battery_charge"],
                    bg_color=self.wcfg["bkg_color_battery_charge"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_battery_charge"],
                    bg_color=self.wcfg["warning_color_low_battery"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_battery_charge"],
                    bg_color=self.wcfg["warning_color_high_battery"])
            )
            self.bar_charge = self.set_qlabel(
                text="BATTERY",
                style=self.bar_style_charge[0],
                width=bar_width,
            )
            self.set_primary_orient(
                target=self.bar_charge,
                column=self.wcfg["column_index_battery_charge"],
            )

        # Battery drain
        if self.wcfg["show_battery_drain"]:
            bar_style_drain = self.set_qss(
                fg_color=self.wcfg["font_color_battery_drain"],
                bg_color=self.wcfg["bkg_color_battery_drain"]
            )
            self.bar_drain = self.set_qlabel(
                text="B DRAIN",
                style=bar_style_drain,
                width=bar_width,
            )
            self.set_primary_orient(
                target=self.bar_drain,
                column=self.wcfg["column_index_battery_drain"],
            )

        # Battery regen
        if self.wcfg["show_battery_regen"]:
            bar_style_regen = self.set_qss(
                fg_color=self.wcfg["font_color_battery_regen"],
                bg_color=self.wcfg["bkg_color_battery_regen"]
            )
            self.bar_regen = self.set_qlabel(
                text="B REGEN",
                style=bar_style_regen,
                width=bar_width,
            )
            self.set_primary_orient(
                target=self.bar_regen,
                column=self.wcfg["column_index_battery_regen"],
            )

        # Battery charge net change
        if self.wcfg["show_estimated_net_change"]:
            bar_style_net = self.set_qss(
                fg_color=self.wcfg["font_color_estimated_net_change"],
                bg_color=self.wcfg["bkg_color_estimated_net_change"]
            )
            self.bar_net = self.set_qlabel(
                text="B   NET",
                style=bar_style_net,
                width=bar_width,
            )
            self.set_primary_orient(
                target=self.bar_net,
                column=self.wcfg["column_index_estimated_net_change"],
            )

        # Activation timer
        if self.wcfg["show_activation_timer"]:
            bar_style_timer = self.set_qss(
                fg_color=self.wcfg["font_color_activation_timer"],
                bg_color=self.wcfg["bkg_color_activation_timer"]
            )
            self.bar_timer = self.set_qlabel(
                text="B TIMER",
                style=bar_style_timer,
                width=bar_width,
            )
            self.set_primary_orient(
                target=self.bar_timer,
                column=self.wcfg["column_index_activation_timer"],
            )

        if self.wcfg["show_battery_charge_warning_flash"]:
            self.warn_flash = warning_flash(
                self.wcfg["warning_flash_highlight_duration"],
                self.wcfg["warning_flash_interval"],
                self.wcfg["number_of_warning_flashes"],
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        # Battery charge & usage
        if self.wcfg["show_battery_charge"]:
            battery_charge = minfo.hybrid.batteryCharge

            if battery_charge >= self.wcfg["high_battery_threshold"]:
                batt_warning = 2
            elif battery_charge <= self.wcfg["low_battery_threshold"]:
                batt_warning = 1
            else:
                batt_warning = 0

            if self.wcfg["show_battery_charge_warning_flash"]:
                batt_highlight = self.warn_flash.send(batt_warning)
                if batt_highlight:
                    padding = 0.00000001  # add padding for switching state
                else:
                    batt_warning = 0
                    padding = 0
            else:
                padding = 0

            self.update_charge(self.bar_charge, battery_charge + padding, self.bar_style_charge[batt_warning])

        if 0 <= minfo.delta.lapTimeCurrent < self.freeze_duration:
            battery_drain = minfo.hybrid.batteryDrainLast
            battery_regen = minfo.hybrid.batteryRegenLast
        else:
            battery_drain = minfo.hybrid.batteryDrain
            battery_regen = minfo.hybrid.batteryRegen

        if self.wcfg["show_battery_drain"]:
            self.update_drain(self.bar_drain, battery_drain)

        if self.wcfg["show_battery_regen"]:
            self.update_regen(self.bar_regen, battery_regen)

        if self.wcfg["show_estimated_net_change"]:
            net_change = minfo.hybrid.batteryNetChange
            self.update_net(self.bar_net, net_change)

        # Motor activation timer
        if self.wcfg["show_activation_timer"]:
            active_timer = minfo.hybrid.motorActiveTimer
            self.update_timer(self.bar_timer, active_timer)

    # GUI update methods
    def update_charge(self, target, data, color):
        """Battery charge"""
        if target.last != data:
            target.last = data
            target.setText(f"B{data: >7.2f}"[:8])
            target.updateStyle(color)

    def update_drain(self, target, data):
        """Battery drain"""
        if target.last != data:
            target.last = data
            target.setText(f"-{data: >7.2f}"[:8])

    def update_regen(self, target, data):
        """Battery regen"""
        if target.last != data:
            target.last = data
            target.setText(f"+{data: >7.2f}"[:8])

    def update_net(self, target, data):
        """Battery charge net change"""
        if target.last != data:
            target.last = data
            target.setText(f"N{data: >+7.2f}"[:8])

    def update_timer(self, target, data):
        """Motor activation timer"""
        if target.last != data:
            target.last = data
            target.setText(f"{data: >7.2f}s"[:8])
