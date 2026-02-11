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
Instrument Widget
"""

from PySide2.QtCore import Qt
from PySide2.QtGui import QPixmap

from ..api_control import api
from ..const_file import ImageFile
from ..module_info import minfo
from ._base import Overlay
from ._painter import split_pixmap_icon


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout(gap=self.wcfg["bar_gap"])
        self.set_primary_layout(layout=layout)

        # Config variable
        icon_size = max(self.wcfg["icon_size"], 16) // 2 * 2
        self.warning_color = (
            self.wcfg["bkg_color"],  # 0
            self.wcfg["warning_color_stalling"],  # 1
            self.wcfg["warning_color_clutch"],  # 2
            self.wcfg["warning_color_wheel_lock"],  # 3
            self.wcfg["warning_color_wheel_slip"],  # 4
        )

        # Config canvas
        pixmap_icon = QPixmap(ImageFile.INSTRUMENT).scaledToWidth(
            icon_size * 2, mode=Qt.SmoothTransformation)
        # 0 = enabled icon state, 1 = disabled icon state.
        self.pixmap_headlights = create_icon_set(pixmap_icon, icon_size, 0)
        self.pixmap_ignition = create_icon_set(pixmap_icon, icon_size, 1)
        self.pixmap_clutch = create_icon_set(pixmap_icon, icon_size, 2)
        self.pixmap_wlock = create_icon_set(pixmap_icon, icon_size, 3)
        self.pixmap_wslip = create_icon_set(pixmap_icon, icon_size, 4)

        # Headlights
        if self.wcfg["show_headlights"]:
            self.bar_headlights = self.set_rawimage(
                image=self.pixmap_headlights[1],
                fixed_width=icon_size,
                fixed_height=icon_size,
                bg_color=self.warning_color[0],
            )
            self.set_primary_orient(
                target=self.bar_headlights,
                column=self.wcfg["column_index_headlights"],
            )

        # Ignition
        if self.wcfg["show_ignition"]:
            self.bar_ignition = self.set_rawimage(
                image=self.pixmap_ignition[1],
                fixed_width=icon_size,
                fixed_height=icon_size,
                bg_color=self.warning_color[0],
            )
            self.set_primary_orient(
                target=self.bar_ignition,
                column=self.wcfg["column_index_ignition"],
            )

        # Clutch
        if self.wcfg["show_clutch"]:
            self.bar_clutch = self.set_rawimage(
                image=self.pixmap_clutch[1],
                fixed_width=icon_size,
                fixed_height=icon_size,
                bg_color=self.warning_color[0],
            )
            self.set_primary_orient(
                target=self.bar_clutch,
                column=self.wcfg["column_index_clutch"],
            )

        # Lock
        if self.wcfg["show_wheel_lock"]:
            self.bar_wlock = self.set_rawimage(
                image=self.pixmap_wlock[1],
                fixed_width=icon_size,
                fixed_height=icon_size,
                bg_color=self.warning_color[0],
            )
            self.set_primary_orient(
                target=self.bar_wlock,
                column=self.wcfg["column_index_wheel_lock"],
            )

        # Slip
        if self.wcfg["show_wheel_slip"]:
            self.bar_wslip = self.set_rawimage(
                image=self.pixmap_wslip[1],
                fixed_width=icon_size,
                fixed_height=icon_size,
                bg_color=self.warning_color[0],
            )
            self.set_primary_orient(
                target=self.bar_wslip,
                column=self.wcfg["column_index_wheel_slip"],
            )

        # Last data
        self.flicker = False

    def timerEvent(self, event):
        """Update when vehicle on track"""
        self.flicker = not self.flicker

        # Headlights
        if self.wcfg["show_headlights"]:
            headlights = api.read.switch.headlights()
            self.update_headlights(self.bar_headlights, headlights)

        # Ignition
        # 0 ignition & engine off, 1 ignition on & engine off, 2 ignition & engine on
        if self.wcfg["show_ignition"]:
            ignition = api.read.switch.ignition_starter() * (
                1 + (api.read.engine.rpm() > self.wcfg["stalling_rpm_threshold"]))
            self.update_ignition(self.bar_ignition, ignition)

        # Clutch
        # 2+ = auto clutch on, 1 or 3 = clutch activated
        if self.wcfg["show_clutch"]:
            clutch = (api.read.switch.auto_clutch() << 1) + (api.read.inputs.clutch() > 0.01)
            self.update_clutch(self.bar_clutch, clutch)

        # Wheel lock
        if self.wcfg["show_wheel_lock"]:
            wlock = (
                self.flicker and
                api.read.inputs.brake_raw() > 0 and
                min(minfo.wheels.slipRatio) < -self.wcfg["wheel_lock_threshold"]
            )
            self.update_wlock(self.bar_wlock, wlock)

        # Wheel slip
        if self.wcfg["show_wheel_slip"]:
            wslip = (
                self.flicker and
                api.read.inputs.throttle_raw() > 0 and
                max(minfo.wheels.slipRatio) >= self.wcfg["wheel_slip_threshold"]
            )
            self.update_wslip(self.bar_wslip, wslip)

    # GUI update methods
    def update_headlights(self, target, data):
        """Headlights update"""
        if target.last != data:
            target.last = data
            target.image = self.pixmap_headlights[data == 0]
            target.update()

    def update_ignition(self, target, data):
        """Ignition update"""
        if target.last != data:
            target.last = data
            target.image = self.pixmap_ignition[data == 0]
            target.bg = self.warning_color[data == 1]
            target.update()

    def update_clutch(self, target, data):
        """Clutch update"""
        if target.last != data:
            target.last = data
            target.image = self.pixmap_clutch[data < 2]
            target.bg = self.warning_color[data % 2 * 2]
            target.update()

    def update_wlock(self, target, data):
        """Wheel lock update"""
        if target.last != data:
            target.last = data
            target.image = self.pixmap_wlock[data == 0]
            target.bg = self.warning_color[data * 3]
            target.update()

    def update_wslip(self, target, data):
        """Wheel slip update"""
        if target.last != data:
            target.last = data
            target.image = self.pixmap_wslip[data == 0]
            target.bg = self.warning_color[data * 4]
            target.update()


def create_icon_set(pixmap_icon: QPixmap, icon_size: int, v_offset: int):
    """Create icon set"""
    return tuple(
        split_pixmap_icon(pixmap_icon, icon_size, h_offset, v_offset)
        for h_offset in range(2)
    )
