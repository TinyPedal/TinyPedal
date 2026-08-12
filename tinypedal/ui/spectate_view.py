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
Spectate list view
"""

from __future__ import annotations

import logging

from PySide2.QtCore import QBasicTimer, Slot
from PySide2.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import app_signal, realtime_state
from ..api_control import api
from ..module_control import mctrl
from ..setting import cfg
from ._common import UIScaler

logger = logging.getLogger(__name__)


class SpectateList(QWidget):
    """Spectate list view"""

    def __init__(self, parent):
        super().__init__(parent)
        self._driver_none = "Anonymous"
        self.last_enabled = None
        self.last_driver_name = ""
        self.last_total_vehicles = 0

        # Set update timer
        self._update_timer = QBasicTimer()

        # Label
        self.label_spectating = QLabel("")

        # List box
        self.listbox_spectate = QListWidget(self)
        self.listbox_spectate.setAlternatingRowColors(True)
        self.listbox_spectate.itemDoubleClicked.connect(self.spectate_selected)

        # Button
        self.button_spectate = QPushButton("Spectate")
        self.button_spectate.clicked.connect(self.spectate_selected)

        self.button_refresh = QPushButton("Refresh")
        self.button_refresh.clicked.connect(self.refresh)

        self.button_toggle = QPushButton("")
        self.button_toggle.setCheckable(True)
        self.button_toggle.toggled.connect(self.toggle_spectate)

        layout_button = QHBoxLayout()
        layout_button.addWidget(self.button_spectate)
        layout_button.addWidget(self.button_refresh)
        layout_button.addStretch(1)
        layout_button.addWidget(self.button_toggle)

        # Layout
        layout_main = QVBoxLayout()
        layout_main.addWidget(self.label_spectating)
        layout_main.addWidget(self.listbox_spectate)
        layout_main.addLayout(layout_button)
        margin = UIScaler.pixel(6)
        layout_main.setContentsMargins(margin, margin, margin, margin)
        self.setLayout(layout_main)

    @Slot(bool)  # type: ignore[operator]
    def refresh(self):
        """Refresh spectate list"""
        enabled = cfg.api["enable_player_index_override"]

        if enabled:
            self.update_drivers(selected_slot=cfg.api["player_index"])
        else:
            self.listbox_spectate.clear()
            self.last_total_vehicles = 0
            self.reload_data_module("")

        # Update button state only if changed
        if self.last_enabled != enabled:
            self.last_enabled = enabled
            self.set_enable_state(enabled)

    def timerEvent(self, event):
        """Update when data not paused"""
        if not realtime_state.paused:
            total_vehicles = api.read.vehicle.total_vehicles()
            driver_name = api.read.vehicle.driver_name()
            if not driver_name:
                driver_name = self._driver_none
            if (
                self.last_driver_name != driver_name
                or self.last_total_vehicles != total_vehicles
            ):
                self.last_total_vehicles = total_vehicles
                self.update_drivers(selected_slot=cfg.api["player_index"])
                logger.info("Spectating: driver list updated")

    def reload_data_module(self, driver_name: str):
        """Reload data recording module if driver changed"""
        if self.last_driver_name == driver_name:
            return

        self.last_driver_name = driver_name
        self.label_spectating.setText(f"Spectating: <b>{driver_name}</b>")

        if realtime_state.active:
            for module_name in (
                "module_delta",
                "module_fuel",
                "module_mapping",
                "module_sectors",
                "module_stint",
            ):
                mctrl.reload(module_name)

    def set_enable_state(self, enabled: bool):
        """Set enable state"""
        self.button_toggle.setChecked(enabled)
        self.button_toggle.setText("Enabled" if enabled else "Disabled")
        self.listbox_spectate.setDisabled(not enabled)
        self.button_spectate.setDisabled(not enabled)
        self.button_refresh.setDisabled(not enabled)
        self.label_spectating.setDisabled(not enabled)
        if enabled:
            self._update_timer.start(200, self)
            logger.info("ENABLED: spectate mode")
        else:
            self._update_timer.stop()
            self.label_spectating.setText("Spectating: <b>Disabled</b>")
            logger.info("DISABLED: spectate mode")

    def toggle_spectate(self, checked: bool):
        """Toggle spectate mode"""
        cfg.api["enable_player_index_override"] = checked
        cfg.save()
        api.setup()
        app_signal.refresh.emit(True)

    def spectate_selected(self):
        """Spectate selected player"""
        self.update_drivers(selected_name=self.selected_name())

    def update_drivers(self, selected_slot: int = -1, selected_name: str = ""):
        """Update drivers list"""
        listbox = self.listbox_spectate
        driver_list = []

        for driver_index in range(api.read.vehicle.total_vehicles()):
            driver_name = api.read.vehicle.driver_name(driver_index)
            driver_slot = api.read.vehicle.slot_id(driver_index)
            driver_list.append(driver_name)
            if selected_slot != -1:  # match slot
                if selected_slot == driver_slot:
                    selected_name = driver_name
            elif selected_name:  # match name
                if driver_name == selected_name:
                    selected_slot = driver_slot

        driver_list.sort(key=str.lower)
        listbox.clear()
        listbox.addItem(self._driver_none)
        listbox.addItems(driver_list)

        self.focus_on_selected(selected_name)
        self.save_selected_index(selected_slot)
        self.reload_data_module(self.selected_name())

    def focus_on_selected(self, driver_name: str):
        """Focus on selected driver row"""
        listbox = self.listbox_spectate
        for row_index in range(listbox.count()):
            if driver_name == listbox.item(row_index).text():
                break
        else:  # fallback to 0 if name not found
            row_index = 0
        listbox.setCurrentRow(row_index)

    def selected_name(self) -> str:
        """Selected driver name"""
        selected_item = self.listbox_spectate.currentItem()
        return self._driver_none if selected_item is None else selected_item.text()

    @staticmethod
    def save_selected_index(index: int):
        """Save selected driver index"""
        if cfg.api["player_index"] != index:
            cfg.api["player_index"] = index
            api.setup()
            cfg.save()
