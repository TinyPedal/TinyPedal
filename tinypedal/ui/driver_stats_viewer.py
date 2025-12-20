#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2025 TinyPedal developers, see contributors.md file
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
Driver stats viewer
"""

from __future__ import annotations

from PySide2.QtCore import QPoint, Qt
from PySide2.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QMenu,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .. import calculation as calc
from ..api_control import api
from ..const_common import MAX_SECONDS, TEXT_NOLAPTIME
from ..formatter import strip_invalid_char
from ..setting import cfg
from ..units import liter_to_gallon, meter_to_kilometer, meter_to_mile
from ..userfile.driver_stats import (
    DriverStats,
    load_stats_json_file,
    save_stats_json_file,
    validate_stats_file,
)
from ._common import (
    BaseEditor,
    CompactButton,
    NumericTableItem,
    UIScaler,
)
from .track_map_viewer import TrackMapViewer


def parse_display_value(key: str, value: int | float) -> str | int | float:
    """Parse stats display value"""
    if DriverStats.is_lap_time(key):
        if 0 < value < MAX_SECONDS:
            return calc.sec2laptime_full(value)
        return TEXT_NOLAPTIME
    if key == "meters":
        if cfg.units["odometer_unit"] == "Kilometer":
            return round(meter_to_kilometer(value), 1)
        if cfg.units["odometer_unit"] == "Mile":
            return round(meter_to_mile(value), 1)
        return int(value)
    if key == "seconds":
        return round(value / 60 / 60, 2)
    if key == "liters":
        if cfg.units["fuel_unit"] == "Gallon":
            value = liter_to_gallon(value)
        return round(value, 2)
    return value


def format_header_key(key: str):
    """Format header key"""
    if key == "pb":
        return "PB"
    if key == "qb":
        return "Qualifying"
    if key == "rb":
        return "Race"
    if key == "meters":
        if cfg.units["odometer_unit"] == "Kilometer":
            return "Km"
        if cfg.units["odometer_unit"] == "Mile":
            return "Miles"
        return "Meters"
    if key == "seconds":
        return "Hours"
    if key == "liters":
        if cfg.units["fuel_unit"] == "Gallon":
            return "Gallons"
        return "Liters"
    if key == "races":
        return "Finishes"
    return key.title()


class DriverStatsViewer(BaseEditor):
    """Driver stats viewer"""

    def __init__(self, parent):
        super().__init__(parent)
        self.set_utility_title("Driver Stats Viewer")
        self.setMinimumSize(UIScaler.size(80), UIScaler.size(30))
        self.resize(UIScaler.size(80), UIScaler.size(50))

        self.stats_temp = {}
        self.selected_stats_key = ""  # get active session key
        self.selected_stats_dict = {}

        # Preset selector
        self.stats_list = QComboBox()
        self.stats_list.currentIndexChanged.connect(self.select_stats)

        # Set table
        self.table_header_key = ["vehicle", *DriverStats.keys()]
        self.table_stats = QTableWidget(self)
        self.table_stats.setColumnCount(len(self.table_header_key))
        self.table_stats.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_stats.setHorizontalHeaderLabels([format_header_key(key) for key in self.table_header_key])
        self.table_stats.verticalHeader().setVisible(False)
        self.table_stats.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table_stats.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for idx in range(1, len(self.table_header_key)):
            self.table_stats.horizontalHeader().setSectionResizeMode(idx, QHeaderView.Fixed)
            self.table_stats.setColumnWidth(idx, UIScaler.size(5 + (idx <= 6)))

        self.table_stats.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_stats.customContextMenuRequested.connect(self.open_context_menu)

        self.reload_stats()
        self.refresh_table()

        # Button
        button_delete = CompactButton("Delete")
        button_delete.clicked.connect(self.delete_stats_key)

        button_reload = CompactButton("Reload")
        button_reload.clicked.connect(self.reload_stats)

        button_viewmap = CompactButton("View Map")
        button_viewmap.clicked.connect(self.open_trackmap)

        button_close = CompactButton("Close")
        button_close.clicked.connect(self.close)

        # Set layout
        layout_main = QVBoxLayout()
        layout_selector = QHBoxLayout()
        layout_button = QHBoxLayout()

        layout_selector.addWidget(button_viewmap)
        layout_selector.addWidget(self.stats_list, stretch=2)
        layout_selector.addWidget(button_delete)

        layout_button.addWidget(button_reload)
        layout_button.addStretch(1)
        layout_button.addWidget(button_close)

        layout_main.addLayout(layout_selector)
        layout_main.addWidget(self.table_stats)
        layout_main.addLayout(layout_button)
        layout_main.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        self.setLayout(layout_main)

    def reload_stats(self):
        """Reload stats data"""
        stats_user = load_stats_json_file(
            filepath=cfg.path.config,
        )
        if stats_user is None:
            return

        self.stats_temp = validate_stats_file(stats_user)

        if self.selected_stats_key:
            last_selected_stats_key = self.selected_stats_key
        else:  # initial load current track name
            last_selected_stats_key = api.read.session.track_name()

        self.stats_list.clear()
        if self.stats_temp:
            self.stats_list.addItems(sorted(self.stats_temp.keys(), key=sort_stats_key))
        self.stats_list.setCurrentText(last_selected_stats_key)

    def refresh_table(self):
        """Refresh stats table"""
        self.table_stats.setSortingEnabled(False)  # must disable before refresh
        self.table_stats.setRowCount(0)

        row_index = 0
        for veh_name, veh_data in self.selected_stats_dict.items():
            self.add_stats_vehicle(row_index, veh_name, veh_data)
            row_index += 1

        self.table_stats.setSortingEnabled(True)
        self.table_stats.sortByColumn(1, Qt.AscendingOrder)  # sort by laptime

    def add_stats_vehicle(self, row_index: int, veh_name: str, veh_data: dict):
        """Add stats vehicle to table"""
        self.table_stats.insertRow(row_index)
        flag_selectable = Qt.ItemIsSelectable | Qt.ItemIsEnabled

        for column_index, header_key in enumerate(self.table_header_key):
            # Vehicle name
            if column_index == 0:
                item = QTableWidgetItem(str(veh_name))
                item.setFlags(flag_selectable)
                self.table_stats.setItem(row_index, column_index, item)
                continue
            # Vehicle stats
            value_raw = veh_data.get(header_key, 0)
            if DriverStats.is_lap_time(header_key) and value_raw <= 0:
                value_raw = MAX_SECONDS  # correct invalid lap time
            item = NumericTableItem(value_raw, str(parse_display_value(header_key, value_raw)))
            item.setFlags(flag_selectable)
            item.setTextAlignment(Qt.AlignCenter)
            self.table_stats.setItem(row_index, column_index, item)

    def select_stats(self):
        """Select stats key"""
        self.selected_stats_key = self.stats_list.currentText()
        if self.selected_stats_key:
            self.selected_stats_dict = self.stats_temp[self.selected_stats_key]
            self.refresh_table()
        else:
            self.table_stats.setRowCount(0)  # clear table if no track data found

    def delete_stats_key(self):
        """Delete stats key"""
        if not self.selected_stats_key:
            QMessageBox.warning(self, "Error", "No data found.")
            return

        msg_text = (
            "Delete all stats from<br>"
            f"<b>{self.selected_stats_key}</b> ?<br><br>"
            "This cannot be undone!"
        )
        if self.confirm_operation(message=msg_text):
            self.stats_temp.pop(self.selected_stats_key, None)  # remove from dict
            save_stats_json_file(
                stats_user=self.stats_temp,
                filepath=cfg.path.config,
            )
            self.reload_stats()

    def remove_vehicle(self):
        """Remove vehicle and stats"""
        selected_rows = list(data.row() for data in self.table_stats.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Error", "No data selected.")
            return

        track_stats = self.stats_temp.get(self.selected_stats_key, None)
        if not isinstance(track_stats, dict):
            QMessageBox.warning(self, "Error", "No data found.")
            return

        selected_vehicle = self.table_stats.item(selected_rows[0], 0).text()
        msg_text = (
            f"Remove all stats from <b>{selected_vehicle}</b>?<br><br>"
            "This cannot be undone!"
        )
        if self.confirm_operation(message=msg_text):
            track_stats.pop(selected_vehicle, None)  # remove from dict
            save_stats_json_file(
                stats_user=self.stats_temp,
                filepath=cfg.path.config,
            )
            self.reload_stats()

    def reset_stat(self, row: int, column: int):
        """Reset stat"""
        selected_vehicle = self.table_stats.item(row, 0).text()
        selected_column = self.table_header_key[column]
        best_laptime = self.table_stats.item(row, column).text()
        msg_text = (
            f"Reset <b>{best_laptime}</b> lap time for <b>{selected_vehicle}</b>?<br><br>"
            "This cannot be undone!"
        )
        if self.confirm_operation(message=msg_text):
            default_value = DriverStats.__dict__[selected_column]
            self.stats_temp[self.selected_stats_key][selected_vehicle][selected_column] = default_value
            save_stats_json_file(
                stats_user=self.stats_temp,
                filepath=cfg.path.config,
            )
            self.reload_stats()

    def open_context_menu(self, position: QPoint):
        """Open context menu"""
        if not self.table_stats.itemAt(position):
            return

        for data in self.table_stats.selectedIndexes():
            item_row = data.row()
            item_column = data.column()
            break

        menu = QMenu()  # no parent for temp menu
        if item_column == 0:
            menu.addAction("Remove Vehicle")
        elif DriverStats.is_lap_time(self.table_header_key[item_column]):
            menu.addAction("Reset Lap Time")
        else:
            return

        position += QPoint(  # position correction from header
            self.table_stats.verticalHeader().width(),
            self.table_stats.horizontalHeader().height(),
        )
        selected_action = menu.exec_(self.table_stats.mapToGlobal(position))
        if not selected_action:
            return
        if selected_action.text() == "Remove Vehicle":
            self.remove_vehicle()
        elif selected_action.text() == "Reset Lap Time":
            self.reset_stat(item_row, item_column)

    def open_trackmap(self):
        """Open trackmap, make sure to strip off invalid char from key name"""
        _dialog = TrackMapViewer(
            self,
            filepath=cfg.path.track_map,
            filename=strip_invalid_char(self.selected_stats_key),
        )
        _dialog.show()


def sort_stats_key(key: str):
    """Sort stats key in lower case"""
    return key.lower()
