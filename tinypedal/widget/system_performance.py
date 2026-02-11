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
System performance Widget
"""

import os
from functools import partial

import psutil

from .. import calculation as calc
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

        if self.wcfg["layout"] == 0:
            prefix_just = max(
                len(self.wcfg["prefix_system"]),
                len(self.wcfg["prefix_tinypedal"]),
            )
        else:
            prefix_just = 0

        self.prefix_sys = self.wcfg["prefix_system"].ljust(prefix_just)
        self.prefix_app = self.wcfg["prefix_tinypedal"].ljust(prefix_just)

        # System
        if self.wcfg["show_system_performance"]:
            text_system = f"{self.prefix_sys}0.00% 0.00GB"
            self.bar_system = self.set_rawtext(
                text=text_system,
                width=font_m.width * len(text_system) + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_system"],
                bg_color=self.wcfg["bkg_color_system"],
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_system,
                column=self.wcfg["column_index_system"],
            )

        # APP performance
        if self.wcfg["show_tinypedal_performance"]:
            text_app = f"{self.prefix_app}0.00% 0.00MB"
            self.bar_app = self.set_rawtext(
                text=text_app,
                width=font_m.width * len(text_app) + bar_padx,
                fixed_height=font_m.height,
                offset_y=font_m.voffset,
                fg_color=self.wcfg["font_color_tinypedal"],
                bg_color=self.wcfg["bkg_color_tinypedal"],
                last=0,
            )
            self.set_primary_orient(
                target=self.bar_app,
                column=self.wcfg["column_index_tinypedal"],
            )

        self.calc_ema = partial(
            calc.exp_mov_avg,
            calc.ema_factor(self.wcfg["average_samples"])
        )

        # Last data
        self.app_info = psutil.Process(os.getpid())
        self.cpu_count = os.cpu_count()

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if self.wcfg["show_system_performance"]:
            sys_cpu_ema = self.calc_ema(self.bar_system.last, psutil.cpu_percent())
            self.update_system(self.bar_system, sys_cpu_ema, self.prefix_sys)

        if self.wcfg["show_tinypedal_performance"]:
            app_cpu_ema = self.calc_ema(self.bar_app.last, self.app_info.cpu_percent() / self.cpu_count)
            self.update_app(self.bar_app, app_cpu_ema, self.prefix_app)

    # GUI update methods
    def update_system(self, target, data, prefix):
        """System performance"""
        if target.last != data:
            target.last = data
            memory_used = psutil.virtual_memory().used / 1024 / 1024 / 1024
            cpu = f"{data: >4.2f}"[:4].strip(".")
            mem = f"{memory_used: >4.2f}"[:4].strip(".")
            target.text = f"{prefix}{cpu: >4}%{mem: >5}GB"
            target.update()

    def update_app(self, target, data, prefix):
        """APP performance"""
        if target.last != data:
            target.last = data
            memory_used = self.app_info.memory_full_info().uss / 1024 / 1024
            cpu = f"{data: >4.2f}"[:4].strip(".")
            mem = f"{memory_used: >4.2f}"[:4].strip(".")
            target.text = f"{prefix}{cpu: >4}%{mem: >5}MB"
            target.update()
