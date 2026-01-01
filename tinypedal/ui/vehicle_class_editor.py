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
Vehicle class editor
"""

import random
import time

from PySide2.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ..api_control import api
from ..const_common import EMPTY_DICT
from ..const_file import ConfigType
from ..formatter import random_color_class
from ..setting import cfg, copy_setting
from ._common import (
    QVAL_COLOR,
    BaseEditor,
    CompactButton,
    DoubleClickEdit,
    UIScaler,
)

HEADER_CLASSES = "Class name","Alias name","Color"


class VehicleClassEditor(BaseEditor):
    """Vehicle class editor"""

    def __init__(self, parent):
        super().__init__(parent)
        self.set_utility_title("Vehicle Class Editor")
        self.setMinimumSize(UIScaler.size(30), UIScaler.size(30))

        self.classes_temp = copy_setting(cfg.user.classes)

        # Set table
        self.table_classes = QTableWidget(self)
        self.table_classes.setColumnCount(len(HEADER_CLASSES))
        self.table_classes.setHorizontalHeaderLabels(HEADER_CLASSES)
        self.table_classes.verticalHeader().setVisible(False)
        self.table_classes.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table_classes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_classes.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table_classes.setColumnWidth(2, UIScaler.size(7))
        self.table_classes.cellChanged.connect(self.set_modified)
        self.refresh_table()
        self.set_unmodified()

        # Set button
        layout_button = self.set_layout_button()

        # Set layout
        layout_main = QVBoxLayout()
        layout_main.addWidget(self.table_classes)
        layout_main.addLayout(layout_button)
        layout_main.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        self.setLayout(layout_main)

    def set_layout_button(self):
        """Set button layout"""
        button_add = CompactButton("Add")
        button_add.clicked.connect(self.add_class)

        button_sort = CompactButton("Sort")
        button_sort.clicked.connect(self.sort_class)

        button_delete = CompactButton("Delete")
        button_delete.clicked.connect(self.delete_class)

        button_reset = CompactButton("Reset")
        button_reset.clicked.connect(self.reset_setting)

        button_apply = CompactButton("Apply")
        button_apply.clicked.connect(self.applying)

        button_save = CompactButton("Save")
        button_save.clicked.connect(self.saving)

        button_close = CompactButton("Close")
        button_close.clicked.connect(self.close)

        layout_button = QHBoxLayout()
        layout_button.addWidget(button_add)
        layout_button.addWidget(button_sort)
        layout_button.addWidget(button_delete)
        layout_button.addWidget(button_reset)
        layout_button.addStretch(1)
        layout_button.addWidget(button_apply)
        layout_button.addWidget(button_save)
        layout_button.addWidget(button_close)
        return layout_button

    def refresh_table(self):
        """Refresh class list"""
        self.table_classes.setRowCount(0)
        row_index = 0
        for class_name, class_data in self.classes_temp.items():
            self.add_vehicle_entry(
                row_index, class_name, class_data["alias"], class_data["color"])
            row_index += 1

    def __add_option_color(self, key):
        """Color string"""
        color_edit = DoubleClickEdit(self, mode="color", init=key)
        color_edit.setMaxLength(9)
        color_edit.setValidator(QVAL_COLOR)
        color_edit.textChanged.connect(self.set_modified)
        color_edit.textChanged.connect(color_edit.preview_color)
        color_edit.setText(key)  # load selected option
        return color_edit

    def add_class(self):
        """Add new class entry"""
        start_index = row_index = self.table_classes.rowCount()
        # Add all missing vehicle class from active session
        veh_total = api.read.vehicle.total_vehicles()
        for index in range(veh_total):
            class_name = api.read.vehicle.class_name(index)
            if not self.is_value_in_table(class_name, self.table_classes):
                self.add_vehicle_entry(
                    row_index, class_name, class_name, random_color_class(class_name))
                row_index += 1
        # Add new class entry
        if start_index == row_index:
            new_class_name = self.new_name_increment("New Class Name", self.table_classes)
            self.add_vehicle_entry(
                row_index, new_class_name, "NAME", random_color_class(str(random.random())))
            self.table_classes.setCurrentCell(row_index, 0)

    def add_vehicle_entry(self, row_index: int, class_name: str, alias_name: str, color: str):
        """Add new class entry to table"""
        self.table_classes.insertRow(row_index)
        self.table_classes.setItem(row_index, 0, QTableWidgetItem(class_name))
        self.table_classes.setItem(row_index, 1, QTableWidgetItem(alias_name))
        self.table_classes.setCellWidget(row_index, 2, self.__add_option_color(color))

    def sort_class(self):
        """Sort class in ascending order"""
        if self.table_classes.rowCount() > 1:
            self.table_classes.sortItems(0)
            self.set_modified()

    def delete_class(self):
        """Delete class entry"""
        selected_rows = set(data.row() for data in self.table_classes.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Error", "No data selected.")
            return

        if not self.confirm_operation(message="<b>Delete selected rows?</b>"):
            return

        for row_index in sorted(selected_rows, reverse=True):
            self.table_classes.removeRow(row_index)
        self.set_modified()

    def reset_setting(self):
        """Reset setting"""
        msg_text = (
            "Reset <b>classes preset</b> to default?<br><br>"
            "Changes are only saved after clicking Apply or Save Button."
        )
        if self.confirm_operation(message=msg_text):
            self.classes_temp = copy_setting(cfg.default.classes)
            self.set_modified()
            self.refresh_table()

    def applying(self):
        """Save & apply"""
        self.save_setting()

    def saving(self):
        """Save & close"""
        self.save_setting()
        self.accept()  # close

    def update_classes_temp(self):
        """Update temporary changes to class temp first"""
        loaded = self.classes_temp.copy()
        self.classes_temp.clear()
        for index in range(self.table_classes.rowCount()):
            class_name = self.table_classes.item(index, 0).text()
            abbr_name = self.table_classes.item(index, 1).text()
            color_string = self.table_classes.cellWidget(index, 2).text()
            self.classes_temp[class_name] = {
                "alias": abbr_name,
                "color": color_string,
                "preset": loaded.get(class_name, EMPTY_DICT).get("preset", ""),
            }

    def save_setting(self):
        """Save setting"""
        self.update_classes_temp()
        cfg.user.classes = copy_setting(self.classes_temp)
        cfg.save(0, cfg_type=ConfigType.CLASSES)
        while cfg.is_saving:  # wait saving finish
            time.sleep(0.01)
        self.reloading()
        self.set_unmodified()
