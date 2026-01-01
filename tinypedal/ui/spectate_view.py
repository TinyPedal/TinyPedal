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

import logging
from typing import Callable

from PySide2.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..api_control import api
from ..setting import cfg
from ._common import UIScaler

logger = logging.getLogger(__name__)


class SpectateList(QWidget):
    """Spectate list view"""

    def __init__(self, parent, notify_toggle: Callable):
        super().__init__(parent)
        self.notify_toggle = notify_toggle
        self.last_enabled = None

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
        self.button_toggle.setChecked(cfg.api["enable_player_index_override"])
        self.button_toggle.toggled.connect(self.toggle_spectate)
        self.refresh()

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

    def set_button_state(self, enabled: bool):
        """Set button state"""
        self.button_toggle.setChecked(enabled)
        self.button_toggle.setText("Enabled" if enabled else "Disabled")
        self.listbox_spectate.setDisabled(not enabled)
        self.button_spectate.setDisabled(not enabled)
        self.button_refresh.setDisabled(not enabled)
        self.label_spectating.setDisabled(not enabled)
        self.notify_toggle(enabled)
        if enabled:
            logger.info("ENABLED: spectate mode")
        else:
            logger.info("DISABLED: spectate mode")

    def toggle_spectate(self, checked: bool):
        """Toggle spectate mode"""
        cfg.api["enable_player_index_override"] = checked
        cfg.save()
        api.setup()
        self.refresh()

    def refresh(self):
        """Refresh spectate list"""
        enabled = cfg.api["enable_player_index_override"]

        if enabled:
            self.update_drivers("Anonymous", cfg.api["player_index"], False)
        else:
            self.listbox_spectate.clear()
            self.label_spectating.setText("Spectating: <b>Disabled</b>")

        # Update button state only if changed
        if self.last_enabled != enabled:
            self.last_enabled = enabled
            self.set_button_state(enabled)

    def spectate_selected(self):
        """Spectate selected player"""
        self.update_drivers(self.selected_name(), -1, True)

    def update_drivers(self, selected_driver_name: str, selected_index: int, match_name: bool):
        """Update drivers list"""
        listbox = self.listbox_spectate
        driver_list = []

        for driver_index in range(api.read.vehicle.total_vehicles()):
            driver_name = api.read.vehicle.driver_name(driver_index)
            driver_list.append(driver_name)
            if match_name:
                if driver_name == selected_driver_name:
                    selected_index = driver_index
            else:  # match index
                if driver_index == selected_index:
                    selected_driver_name = driver_name

        driver_list.sort(key=str.lower)
        driver_list.insert(0, "Anonymous")
        listbox.clear()
        listbox.addItems(driver_list)

        self.focus_on_selected(selected_driver_name)
        self.save_selected_index(selected_index)

    def focus_on_selected(self, driver_name: str):
        """Focus on selected driver row"""
        listbox = self.listbox_spectate
        for row_index in range(listbox.count()):
            if driver_name == listbox.item(row_index).text():
                break
        else:  # fallback to 0 if name not found
            row_index = 0
        listbox.setCurrentRow(row_index)
        # Make sure selected name valid
        self.label_spectating.setText(f"Spectating: <b>{self.selected_name()}</b>")

    def selected_name(self) -> str:
        """Selected driver name"""
        selected_item = self.listbox_spectate.currentItem()
        return "Anonymous" if selected_item is None else selected_item.text()

    @staticmethod
    def save_selected_index(index: int):
        """Save selected driver index"""
        if cfg.api["player_index"] != index:
            cfg.api["player_index"] = index
            api.setup()
            cfg.save()
