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
Onboard setting Widget
"""

from ..api_control import api
from ..const_common import TEXT_PLACEHOLDER
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
        bar_width = font_m.width * 1 + bar_padx
        row_caption = 2 * self.wcfg["swap_upper_caption"]

        # ABS
        if self.wcfg["show_abs"]:
            layout_abs = self.set_grid_layout()
            self.bar_style_abs = (
                self.wcfg["background_color_abs"],
                self.wcfg["abs_activation_color"],
            )
            self.bars_abs = self.set_rawtext(
                text=TEXT_PLACEHOLDER,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_abs"],
                bg_color=self.wcfg["background_color_abs"],
            )
            layout_abs.addWidget(self.bars_abs, 1, 0)
            self.set_primary_orient(
                target=layout_abs,
                column=self.wcfg["display_order_abs"],
            )

            if self.wcfg["show_caption"]:
                cap_temp = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_abs"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["background_color_caption"],
                )
                layout_abs.addWidget(cap_temp, row_caption, 0)

        # TC
        if self.wcfg["show_tc"]:
            layout_tc = self.set_grid_layout()
            self.bar_style_tc = (
                self.wcfg["background_color_tc"],
                self.wcfg["tc_activation_color"],
            )
            self.bars_tc = self.set_rawtext(
                text=TEXT_PLACEHOLDER,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_tc"],
                bg_color=self.wcfg["background_color_tc"],
            )
            layout_tc.addWidget(self.bars_tc, 1, 0)
            self.set_primary_orient(
                target=layout_tc,
                column=self.wcfg["display_order_tc"],
            )

            if self.wcfg["show_caption"]:
                cap_temp = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_tc"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["background_color_caption"],
                )
                layout_tc.addWidget(cap_temp, row_caption, 0)

        # TC cut
        if self.wcfg["show_tc_cut"]:
            layout_tc_cut = self.set_grid_layout()
            self.bars_tc_cut = self.set_rawtext(
                text=TEXT_PLACEHOLDER,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_tc_cut"],
                bg_color=self.wcfg["background_color_tc_cut"],
            )
            layout_tc_cut.addWidget(self.bars_tc_cut, 1, 0)
            self.set_primary_orient(
                target=layout_tc_cut,
                column=self.wcfg["display_order_tc_cut"],
            )

            if self.wcfg["show_caption"]:
                cap_temp = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_tc_cut"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["background_color_caption"],
                )
                layout_tc_cut.addWidget(cap_temp, row_caption, 0)

        # TC slip
        if self.wcfg["show_tc_slip"]:
            layout_tc_slip = self.set_grid_layout()
            self.bars_tc_slip = self.set_rawtext(
                text=TEXT_PLACEHOLDER,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_tc_slip"],
                bg_color=self.wcfg["background_color_tc_slip"],
            )
            layout_tc_slip.addWidget(self.bars_tc_slip, 1, 0)
            self.set_primary_orient(
                target=layout_tc_slip,
                column=self.wcfg["display_order_tc_slip"],
            )

            if self.wcfg["show_caption"]:
                cap_temp = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_tc_slip"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["background_color_caption"],
                )
                layout_tc_slip.addWidget(cap_temp, row_caption, 0)

        # Front ARB
        if self.wcfg["show_front_arb"]:
            layout_farb = self.set_grid_layout()
            self.bars_farb = self.set_rawtext(
                text=TEXT_PLACEHOLDER,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_front_arb"],
                bg_color=self.wcfg["background_color_front_arb"],
            )
            layout_farb.addWidget(self.bars_farb, 1, 0)
            self.set_primary_orient(
                target=layout_farb,
                column=self.wcfg["display_order_front_arb"],
            )

            if self.wcfg["show_caption"]:
                cap_temp = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_front_arb"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["background_color_caption"],
                )
                layout_farb.addWidget(cap_temp, row_caption, 0)

        # Rear ARB
        if self.wcfg["show_rear_arb"]:
            layout_rarb = self.set_grid_layout()
            self.bars_rarb = self.set_rawtext(
                text=TEXT_PLACEHOLDER,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_rear_arb"],
                bg_color=self.wcfg["background_color_rear_arb"],
            )
            layout_rarb.addWidget(self.bars_rarb, 1, 0)
            self.set_primary_orient(
                target=layout_rarb,
                column=self.wcfg["display_order_rear_arb"],
            )

            if self.wcfg["show_caption"]:
                cap_temp = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_rear_arb"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["background_color_caption"],
                )
                layout_rarb.addWidget(cap_temp, row_caption, 0)

        # Brake migration
        if self.wcfg["show_brake_migration"]:
            layout_bmig = self.set_grid_layout()
            self.bars_bmig = self.set_rawtext(
                text=TEXT_PLACEHOLDER,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_brake_migration"],
                bg_color=self.wcfg["background_color_brake_migration"],
            )
            layout_bmig.addWidget(self.bars_bmig, 1, 0)
            self.set_primary_orient(
                target=layout_bmig,
                column=self.wcfg["display_order_brake_migration"],
            )

            if self.wcfg["show_caption"]:
                cap_temp = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_brake_migration"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["background_color_caption"],
                )
                layout_bmig.addWidget(cap_temp, row_caption, 0)

        # Motor map
        if self.wcfg["show_motor_map"]:
            layout_mmap = self.set_grid_layout()
            self.bars_mmap = self.set_rawtext(
                text=TEXT_PLACEHOLDER,
                width=bar_width,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_motor_map"],
                bg_color=self.wcfg["background_color_motor_map"],
            )
            layout_mmap.addWidget(self.bars_mmap, 1, 0)
            self.set_primary_orient(
                target=layout_mmap,
                column=self.wcfg["display_order_motor_map"],
            )

            if self.wcfg["show_caption"]:
                cap_temp = self.set_rawtext(
                    font=font_cap,
                    text=self.wcfg["caption_text_motor_map"],
                    fixed_height=font_cap_m.height,
                    offset_y=font_cap_m.voffset,
                    fg_color=self.wcfg["font_color_caption"],
                    bg_color=self.wcfg["background_color_caption"],
                )
                layout_mmap.addWidget(cap_temp, row_caption, 0)

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if self.wcfg["show_abs"]:
            abs_active = api.read.switch.abs_active()
            abs_level = api.read.switch.abs_level()
            self.update_abs(self.bars_abs, abs_level, abs_active)

        if self.wcfg["show_tc"]:
            tc_active = api.read.switch.tc_active()
            tc_level = api.read.switch.tc_level()
            self.update_tc(self.bars_tc, tc_level, tc_active)

        if self.wcfg["show_tc_cut"]:
            tc_cut_level = api.read.switch.tc_cut_level()
            self.update_level(self.bars_tc_cut, tc_cut_level)

        if self.wcfg["show_tc_slip"]:
            tc_slip_level = api.read.switch.tc_slip_level()
            self.update_level(self.bars_tc_slip, tc_slip_level)

        if self.wcfg["show_brake_migration"]:
            brake_migration_level = api.read.switch.brake_migration_level()
            self.update_level(self.bars_bmig, brake_migration_level)

        if self.wcfg["show_motor_map"]:
            motor_map_level = api.read.switch.motor_map_level()
            self.update_level(self.bars_mmap, motor_map_level)

        if self.wcfg["show_front_arb"]:
            front_arb_level = api.read.switch.front_arb_level()
            self.update_level(self.bars_farb, front_arb_level)

        if self.wcfg["show_rear_arb"]:
            rear_arb_level = api.read.switch.rear_arb_level()
            self.update_level(self.bars_rarb, rear_arb_level)

    # GUI update methods
    def update_tc(self, target, *data):
        """TC state"""
        if target.last != data:
            target.last = data
            if data[0] < 0:
                text = TEXT_PLACEHOLDER
            else:
                text = f"{data[0]}"
            target.text = text
            target.bg = self.bar_style_tc[data[1]]
            target.update()

    def update_abs(self, target, *data):
        """ABS state"""
        if target.last != data:
            target.last = data
            if data[0] < 0:
                text = TEXT_PLACEHOLDER
            else:
                text = f"{data[0]}"
            target.text = text
            target.bg = self.bar_style_abs[data[1]]
            target.update()

    def update_level(self, target, data):
        """Level"""
        if target.last != data:
            target.last = data
            if data < 0:
                text = TEXT_PLACEHOLDER
            else:
                text = f"{data}"
            target.text = text
            target.update()
