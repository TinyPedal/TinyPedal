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
Heatmap editor
"""

import time

from PySide2.QtWidgets import (
    QComboBox,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QTableWidget,
    QVBoxLayout,
)

from ..const_file import ConfigType
from ..setting import cfg, copy_setting
from ._common import (
    QVAL_COLOR,
    QVAL_HEATMAP,
    BaseDialog,
    BaseEditor,
    BatchOffset,
    CompactButton,
    DoubleClickEdit,
    FloatTableItem,
    UIScaler,
)

HEADER_HEATMAP = "Temperature (Celsius)","Color"


class HeatmapEditor(BaseEditor):
    """Heatmap editor"""

    def __init__(self, parent):
        super().__init__(parent)
        self.set_utility_title("Heatmap Editor")
        self.setMinimumHeight(UIScaler.size(30))

        self._verify_enabled = True
        self.heatmap_temp = copy_setting(cfg.user.heatmap)
        self.selected_heatmap_key = next(iter(self.heatmap_temp.keys()))
        self.selected_heatmap_dict = self.heatmap_temp[self.selected_heatmap_key]

        # Preset selector
        self.heatmap_list = QComboBox()
        self.heatmap_list.addItems(self.heatmap_temp.keys())
        self.heatmap_list.currentIndexChanged.connect(self.select_heatmap)

        # Heatmap list box
        self.table_heatmap = QTableWidget(self)
        self.table_heatmap.setColumnCount(len(HEADER_HEATMAP))
        self.table_heatmap.setHorizontalHeaderLabels(HEADER_HEATMAP)
        self.table_heatmap.verticalHeader().setVisible(False)
        self.table_heatmap.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table_heatmap.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_heatmap.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table_heatmap.setColumnWidth(1, UIScaler.size(8))
        self.table_heatmap.cellChanged.connect(self.set_modified)
        self.table_heatmap.cellChanged.connect(self.verify_input)
        self.refresh_table()
        self.set_unmodified()

        # Button
        button_create = CompactButton("New")
        button_create.clicked.connect(self.open_create_dialog)

        button_copy = CompactButton("Copy")
        button_copy.clicked.connect(self.open_copy_dialog)

        button_delete = CompactButton("Delete")
        button_delete.clicked.connect(self.delete_heatmap)

        button_add = CompactButton("Add")
        button_add.clicked.connect(self.add_temperature)

        button_sort = CompactButton("Sort")
        button_sort.clicked.connect(self.sort_temperature)

        button_remove = CompactButton("Remove")
        button_remove.clicked.connect(self.delete_temperature)

        button_offset = CompactButton("Offset")
        button_offset.clicked.connect(self.open_offset_dialog)

        button_reset = CompactButton("Reset")
        button_reset.clicked.connect(self.reset_heatmap)

        button_apply = CompactButton("Apply")
        button_apply.clicked.connect(self.applying)

        button_save = CompactButton("Save")
        button_save.clicked.connect(self.saving)

        button_close = CompactButton("Close")
        button_close.clicked.connect(self.close)

        # Set layout
        layout_main = QVBoxLayout()
        layout_selector = QHBoxLayout()
        layout_button = QHBoxLayout()

        layout_selector.addWidget(self.heatmap_list, stretch=1)
        layout_selector.addWidget(button_create)
        layout_selector.addWidget(button_copy)
        layout_selector.addWidget(button_delete)

        layout_button.addWidget(button_add)
        layout_button.addWidget(button_sort)
        layout_button.addWidget(button_remove)
        layout_button.addWidget(button_offset)
        layout_button.addWidget(button_reset)
        layout_button.addStretch(1)
        layout_button.addWidget(button_apply)
        layout_button.addWidget(button_save)
        layout_button.addWidget(button_close)

        layout_main.addLayout(layout_selector)
        layout_main.addWidget(self.table_heatmap)
        layout_main.addLayout(layout_button)
        layout_main.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        self.setLayout(layout_main)
        self.setMinimumWidth(self.sizeHint().width() + UIScaler.size(2))

    def refresh_table(self):
        """Refresh temperature table"""
        self.table_heatmap.setRowCount(0)
        row_index = 0

        self._verify_enabled = False
        for temperature, color in self.selected_heatmap_dict.items():
            self.add_temperature_entry(row_index, float(temperature), color)
            row_index += 1
        self._verify_enabled = True

    def __add_option_color(self, key):
        """Color string"""
        color_edit = DoubleClickEdit(self, mode="color", init=key)
        color_edit.setMaxLength(9)
        color_edit.setValidator(QVAL_COLOR)
        color_edit.textChanged.connect(self.set_modified)
        color_edit.textChanged.connect(color_edit.preview_color)
        color_edit.setText(key)  # load selected option
        return color_edit

    def add_temperature_entry(self, row_index: int, temperature: float, color: str):
        """Add new temperature entry to table"""
        self.table_heatmap.insertRow(row_index)
        self.table_heatmap.setItem(row_index, 0, FloatTableItem(temperature))
        self.table_heatmap.setCellWidget(row_index, 1, self.__add_option_color(color))

    def open_create_dialog(self):
        """Create heatmap preset"""
        _dialog = CreateHeatmapPreset(self, "Create Heatmap Preset")
        _dialog.open()

    def open_copy_dialog(self):
        """Copy heatmap preset"""
        _dialog = CreateHeatmapPreset(self, "Duplicate Heatmap Preset", "duplicate")
        _dialog.open()

    def open_offset_dialog(self):
        """Open offset dialog"""
        if self.column_selection_count(0) == 0:
            msg_text = (
                "Select <b>one or more values</b> from <b>temperature</b> "
                "column to apply offset."
            )
            QMessageBox.warning(self, "Error", msg_text)
            return

        self.sort_temperature()
        _dialog = BatchOffset(self, self.apply_batch_offset)
        _dialog.config(1, 1, -99999, 99999)
        _dialog.open()

    def column_selection_count(self, column_index: int = 0) -> int:
        """Column selection count"""
        row_count = 0
        for data in self.table_heatmap.selectedIndexes():
            if data.column() == column_index:
                row_count += 1
            else:
                return 0
        return row_count

    def verify_input(self, row_index: int, column_index: int):
        """Verify input value"""
        if self._verify_enabled:
            self.set_modified()
            item = self.table_heatmap.item(row_index, column_index)
            if column_index == 0:
                item.validate()

    def apply_batch_offset(self, offset: int, is_scale_mode: bool):
        """Apply batch offset"""
        self._verify_enabled = False
        for item in self.table_heatmap.selectedItems():
            value = item.value()
            if is_scale_mode:
                value *= offset
            else:
                value += offset
            item.setValue(value)
        self._verify_enabled = True
        self.set_modified()

    def add_temperature(self):
        """Add new temperature"""
        self.sort_temperature()
        row_index = self.table_heatmap.rowCount()
        if row_index > 0:
            temperature = self.table_heatmap.item(row_index - 1, 0).value() + 10
            color = "#FFFFFF"
        else:
            temperature = -273.0
            color = "#4444FF"
        self.add_temperature_entry(row_index, temperature, color)
        self.table_heatmap.setCurrentCell(row_index, 0)

    def delete_temperature(self, row_index: int):
        """Delete temperature entry"""
        selected_rows = set(data.row() for data in self.table_heatmap.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Error", "No data selected.")
            return

        if not self.confirm_operation(message="<b>Delete selected temperature?</b>"):
            return

        for row_index in sorted(selected_rows, reverse=True):
            self.table_heatmap.removeRow(row_index)
        self.set_modified()

    def sort_temperature(self):
        """Sort temperature"""
        if self.table_heatmap.rowCount() > 1:
            self.table_heatmap.sortItems(0)
            self.set_modified()

    def select_heatmap(self):
        """Select heatmap list"""
        # Sort & apply previous preset first
        if self.selected_heatmap_dict:
            self.update_heatmap_temp()
        # Get newly selected preset name
        self.selected_heatmap_key = self.heatmap_list.currentText()
        self.selected_heatmap_dict = self.heatmap_temp[self.selected_heatmap_key]
        self.refresh_table()

    def delete_heatmap(self):
        """Delete heatmap"""
        if self.selected_heatmap_key in cfg.default.heatmap:
            QMessageBox.warning(self, "Error", "Cannot delete built-in heatmap preset.")
            return

        msg_text = (
            f"Delete <b>{self.selected_heatmap_key}</b> preset?<br><br>"
            "Changes are only saved after clicking Apply or Save Button."
        )
        if self.confirm_operation(message=msg_text):
            self.heatmap_temp.pop(self.selected_heatmap_key)  # remove from dict
            self.selected_heatmap_dict.clear()
            self.heatmap_list.removeItem(self.heatmap_list.currentIndex())
            self.set_modified()

    def reset_heatmap(self):
        """Reset heatmap"""
        if cfg.default.heatmap.get(self.selected_heatmap_key) is None:
            msg_text = (
                "Cannot reset selected heatmap preset.<br><br>"
                "Default preset does not exist."
            )
            QMessageBox.warning(self, "Error", msg_text)
            return

        msg_text = (
            f"Reset <b>{self.selected_heatmap_key}</b> preset to default?<br><br>"
            "Changes are only saved after clicking Apply or Save Button."
        )
        if self.confirm_operation(message=msg_text):
            self.selected_heatmap_dict = cfg.default.heatmap[self.selected_heatmap_key].copy()
            self.refresh_table()

    def applying(self):
        """Save & apply"""
        self.save_heatmap()

    def saving(self):
        """Save & close"""
        self.save_heatmap()
        self.accept()  # close

    def update_heatmap_temp(self):
        """Update temporary changes to selected heatmap first"""
        self.sort_temperature()
        self.selected_heatmap_dict.clear()
        for index in range(self.table_heatmap.rowCount()):
            temperature = f"{self.table_heatmap.item(index, 0).value():.1f}"
            color_string = self.table_heatmap.cellWidget(index, 1).text()
            self.selected_heatmap_dict[temperature] = color_string
        # Apply changes to heatmap preset dictionary
        self.heatmap_temp[self.selected_heatmap_key] = self.selected_heatmap_dict

    def save_heatmap(self):
        """Save heatmap"""
        self.update_heatmap_temp()
        cfg.user.heatmap = copy_setting(self.heatmap_temp)
        cfg.save(0, cfg_type=ConfigType.HEATMAP)
        while cfg.is_saving:  # wait saving finish
            time.sleep(0.01)
        self.reloading()
        self.set_unmodified()


class CreateHeatmapPreset(BaseDialog):
    """Create heatmap preset

    Args:
        title: Dialog title string.
        mode: Edit mode, either "duplicate" or "" for new preset.
    """

    def __init__(self, parent, title: str = "", mode: str = ""):
        super().__init__(parent)
        self._parent = parent
        self.edit_mode = mode
        self.setWindowTitle(title)
        self.setMinimumWidth(UIScaler.size(21))

        # Entry box
        self.preset_entry = QLineEdit()
        self.preset_entry.setMaxLength(40)
        self.preset_entry.setPlaceholderText("Enter a new preset name")
        self.preset_entry.setValidator(QVAL_HEATMAP)

        # Button
        button_create = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        button_create.accepted.connect(self.creating)
        button_create.rejected.connect(self.reject)

        # Layout
        layout_main = QVBoxLayout()
        layout_main.addWidget(self.preset_entry)
        layout_main.addWidget(button_create)
        self.setLayout(layout_main)

    def creating(self):
        """Creating new preset"""
        entered_name = self.preset_entry.text()
        if not entered_name:
            QMessageBox.warning(self, "Error", "Invalid preset name.")
        elif entered_name in cfg.user.heatmap:
            QMessageBox.warning(self, "Error", "Preset already exists.")
        else:
            self.__saving(entered_name)

    def __saving(self, entered_name: str):
        """Saving new preset"""
        # Duplicate preset
        if self.edit_mode == "duplicate":
            self._parent.heatmap_temp[entered_name] = self._parent.selected_heatmap_dict.copy()
        # Create new preset
        else:
            self._parent.heatmap_temp[entered_name] = {"-273.0": "#4444FF"}
        self._parent.heatmap_list.addItem(entered_name)
        self._parent.heatmap_list.setCurrentText(entered_name)
        # Close window
        self.accept()
