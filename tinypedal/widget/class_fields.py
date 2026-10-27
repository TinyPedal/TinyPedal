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

from itertools import islice

from .. import minfo
from ..formatter import random_color_class
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
        self.class_range = min(max(int(self.wcfg["maximum_classes"]), 2), 20)
        self.class_width = max(int(self.wcfg["class_width"]), 0)
        self.prefix_active = self.wcfg["prefix_active_count"]
        self.prefix_total = self.wcfg["prefix_total_count"]
        self.prefix_inactive = self.wcfg["prefix_inactive_count"]

        # Class fields
        text_field = f"{'CLASS':<{self.class_width}.{self.class_width}}"
        if self.wcfg["show_active_count"]:
            text_field += f"{self.prefix_active}00"
        if self.wcfg["show_total_count"]:
            text_field += f"{self.prefix_total}00"
        if self.wcfg["show_inactive_count"]:
            text_field += f"{self.prefix_inactive}00"
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
            if idx > 0:
                target.hide()  # keep first field visible as placeholder

        # Last data
        self.post_update()

    def post_update(self):
        self.last_totals = None
        self.last_fields = ()

    def timerEvent(self, event):
        """Update when vehicle on track"""
        veh_info = minfo.vehicles
        totals = (
            # Force refresh when leader completes a lap
            # in case any class overall position changed
            veh_info.dataSet[veh_info.leaderIndex].totalLapCompleted,
            veh_info.totalVehicles,
            veh_info.totalInGarage,
        )
        # Only recount if vehicle total changes
        if self.last_totals != totals:
            self.last_totals = totals
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
            text_field = f"{text_class:<{self.class_width}.{self.class_width}}"
            if self.wcfg["show_active_count"]:
                text_field += f"{self.prefix_active}{active:02d}"
            if self.wcfg["show_total_count"]:
                text_field += f"{self.prefix_total}{total:02d}"
            if self.wcfg["show_inactive_count"]:
                text_field += f"{self.prefix_inactive}{total - active:02d}"
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
        for data in islice(veh_info.dataSet, veh_info.totalVehicles):
            class_name = data.vehicleClass
            position_overall = data.positionOverall
            is_active = data.inPit != 2  # not in garage (DNF or DQ will end up in garage)
            field = class_data.get(class_name)
            if field is None:
                class_data[class_name] = [position_overall, is_active, 1]
            else:
                if field[0] > position_overall:
                    field[0] = position_overall
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
