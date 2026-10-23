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
Class fields Widget
"""

from .. import api, minfo
from ..formatter import random_color_class
from ..validator import state_timer
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
        self.class_range = min(max(int(self.wcfg["maximum_classes"]), 1), 20)
        self.class_width = max(int(self.wcfg["class_width"]), 1)
        self.count_finished = self.wcfg["enable_finished_vehicles_as_active"]
        self.show_inactive = self.wcfg["show_inactive_count"]
        self.prefix_inactive = self.wcfg["prefix_inactive_count"]
        self.gen_refresh_timer = state_timer(max(self.wcfg["refresh_interval"], 1))

        # Class fields
        text_field = f"{'':<{self.class_width}} 00/00"
        if self.show_inactive:
            text_field += f" {self.prefix_inactive}00"
        self.bars_field = self.set_rawtext(
            text=text_field,
            padding=bar_padx,
            width=font_m.width * len(text_field),
            fixed_height=font_m.height,
            offset_y=font_m.voffset,
            fg_color=self.wcfg["font_color_class_field"],
            bg_color=self.wcfg["background_color_class_field"],
            count=self.class_range,
        )
        for idx, target in enumerate(self.bars_field):
            self.set_primary_orient(target=target, column=idx)
            target.setHidden(idx > 0)  # keep first field visible as placeholder

        # Last data
        self.last_trigger = None
        self.last_fields = ()

    def timerEvent(self, event):
        """Update when vehicle on track"""
        veh_info = minfo.vehicles
        # Only recount if vehicle total or garage state changes, or on refresh timer
        trigger = (veh_info.totalVehicles, veh_info.totalOutPits + veh_info.totalInPits)
        if next(self.gen_refresh_timer) or self.last_trigger != trigger:
            self.last_trigger = trigger
            fields = self.count_class_fields(veh_info)
            if self.last_fields != fields:
                self.last_fields = fields
                self.update_fields(fields)

    # GUI update methods
    def update_fields(self, fields):
        """Class fields"""
        total_fields = len(fields)
        for idx, target in enumerate(self.bars_field):
            if idx >= total_fields:
                target.setHidden(True)
                continue
            class_name, active, total = fields[idx]
            text_class, target.bg = self.set_class_style(class_name)
            text_field = f"{text_class[:self.class_width]:<{self.class_width}} {active:02d}/{total:02d}"
            if self.show_inactive:
                text_field += f" {self.prefix_inactive}{total - active:<2}"
            target.text = text_field
            target.update()
            target.setHidden(False)

    # Additional methods
    def count_class_fields(self, veh_info):
        """Count active and total vehicles per class, sorted by class leader position

        Returns:
            Tuple of (class name, active vehicles, total vehicles).
        """
        class_data = {}  # class name: [best position, active, total]
        for index, data in zip(range(veh_info.totalVehicles), veh_info.dataSet):
            finish_state = api.read.vehicle.finish_state(index)
            is_active = (
                data.inPit != 2  # not in garage
                and finish_state < 2  # not DNF or DQ
                and (self.count_finished or finish_state != 1)
            )
            field = class_data.get(data.vehicleClass)
            if field is None:
                class_data[data.vehicleClass] = [data.positionOverall, is_active, 1]
            else:
                if field[0] > data.positionOverall:
                    field[0] = data.positionOverall
                field[1] += is_active
                field[2] += 1

        return tuple(
            (class_name, active, total)
            for class_name, (_, active, total) in sorted(
                class_data.items(), key=lambda item: item[1][0]
            )
        )

    def set_class_style(self, class_name: str):
        """Compare vehicle class name with user defined dictionary"""
        style = self.cfg.user.classes.get(class_name)
        if style is not None:
            return style["alias"], style["color"]
        if class_name:
            return class_name, random_color_class(class_name)
        return class_name, self.wcfg["background_color_class_field"]
