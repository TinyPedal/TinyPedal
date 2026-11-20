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

from .. import minfo
from ..constant import DATA
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
        self.class_range = min(max(int(self.wcfg["maximum_classes"]), 2), DATA.MAX_CLASSES)
        self.class_width = max(int(self.wcfg["class_width"]), 0)

        self.prefix_active = self.wcfg["prefix_active_count"]
        self.prefix_total = self.wcfg["prefix_total_count"]
        self.prefix_inactive = self.wcfg["prefix_inactive_count"]

        self.suffix_active = self.wcfg["suffix_active_count"]
        self.suffix_total = self.wcfg["suffix_total_count"]
        self.suffix_inactive = self.wcfg["suffix_inactive_count"]

        # Class fields
        text_field = f"{'CLASS':<{self.class_width}.{self.class_width}}"
        if self.wcfg["show_active_count"]:
            text_field += f"{self.prefix_active}00{self.suffix_active}"
        if self.wcfg["show_total_count"]:
            text_field += f"{self.prefix_total}00{self.suffix_total}"
        if self.wcfg["show_inactive_count"]:
            text_field += f"{self.prefix_inactive}00{self.suffix_inactive}"
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

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if minfo.vehicles.updateClassField:
            minfo.vehicles.updateClassField = False
            self.update_fields()

    # GUI update methods
    def update_fields(self):
        """Class fields"""
        fields = self.count_class_fields()
        total_fields = len(fields)
        for idx, target in enumerate(self.bars_field):
            if idx >= total_fields:
                target.setHidden(True)
                continue
            _, class_name, active, total = fields[idx]
            text_class, target.bg = self.set_class_style(class_name)
            text_field = f"{text_class:<{self.class_width}.{self.class_width}}"
            if self.wcfg["show_active_count"]:
                text_field += f"{self.prefix_active}{active:02d}{self.suffix_active}"
            if self.wcfg["show_total_count"]:
                text_field += f"{self.prefix_total}{total:02d}{self.suffix_total}"
            if self.wcfg["show_inactive_count"]:
                text_field += f"{self.prefix_inactive}{total - active:02d}{self.suffix_inactive}"
            target.text = text_field
            target.update()
            target.setHidden(False)

    # Additional methods
    def count_class_fields(self):
        """Count active and total vehicles per class, sorted by class order

        Returns:
            Tuple of (class name, active vehicles, total vehicles).
        """
        class_data = {}
        for data in minfo.vehicles.activeDataSet:
            class_name = data.vehicleClass
            field = class_data.get(class_name)
            # Add new field
            if field is None:
                class_data[class_name] = [
                    data.classOrder,  # 0 - class order
                    class_name,  # 1 - class name
                    0,  # 2 - active cars
                    0,  # 3 - total cars
                ]
                field = class_data[class_name]
            # Update field
            if data.inPit != 2:  # not in garage (DNF or DQ will end up in garage)
                field[2] += 1
            field[3] += 1

        return tuple(sorted(data for data in class_data.values()))

    def set_class_style(self, class_name: str):
        """Compare vehicle class name with user defined dictionary"""
        style = self.cfg.user.classes.get(class_name)
        if style is not None:
            return style["alias"], style["color"]
        if class_name:
            return class_name, random_color_class(class_name)
        return class_name, self.wcfg["background_color_class_field"]
