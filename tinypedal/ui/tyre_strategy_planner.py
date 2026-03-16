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
Tyre strategy planner
"""

from __future__ import annotations

import os

from PySide2.QtCore import QPoint, QStandardPaths, Qt, Signal, Slot
from PySide2.QtGui import QBrush, QFont, QKeySequence, QPainter, QPen
from PySide2.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..const_file import ConfigType, FileFilter
from ..formatter import format_option_name
from ..setting import cfg
from ..userfile.tyre_strategy import (
    DEFAULT_TYRE_SET,
    DEFAULT_TYRE_SETTING,
    HEADER_TYREPLAN,
    TYRE_STRATEGY_FILE_VERSION,
    create_tyre_strategy,
    decode_tyre_name,
    encode_tyre_name,
    export_tyre_strategy_file,
    extract_tyre_key,
    load_tyre_strategy_file,
    save_tyre_strategy_file,
)
from ._common import (
    QVAL_FILENAME,
    BaseEditor,
    CompactButton,
    UIScaler,
    add_vertical_separator,
)
from .config import UserConfig


def set_tyre_strategy_file_path(filename: str = "") -> str:
    """Set file path"""
    filepath = cfg.user.config["tyre_strategy_planner"]["last_file_path"]
    if not filepath or not os.path.exists(filepath):
        filepath = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        if not filepath.endswith("/"):
            filepath += "/"
    return f"{filepath}{filename}"


def save_tyre_strategy_file_path(filepath: str):
    """Save file path"""
    if filepath != cfg.user.config["tyre_strategy_planner"]["last_file_path"]:
        cfg.user.config["tyre_strategy_planner"]["last_file_path"] = filepath
        cfg.save(config_type=ConfigType.CONFIG)


class TyreNameListItem(QListWidgetItem):
    """Tyre name list item with custom sort order"""

    sort_type = 0

    def __init__(self, tyre_name: str):
        super().__init__(tyre_name)
        # Sort reference
        self.compound = decode_tyre_name(tyre_name)
        self.stints = 0

    def __lt__(self, other):
        """Sort"""
        # Sort by number of stints
        if TyreNameListItem.sort_type:
            return self.stints > other.stints
        # Sort by compound type
        return self.compound < other.compound


class TyrePlanTable(QTableWidget):
    """Tyre plan table"""

    refresh = Signal(bool)

    def __init__(self, parent):
        super().__init__(parent)
        self._restrict_allocation = True
        self._wheel_count = 4

    def set_drag_mode(self):
        """Set drag mode based selection"""
        if len(self.selectedIndexes()) > 1:
            self.setDragDropMode(QAbstractItemView.DropOnly)
            return
        # Disable empty drag
        item = self.currentItem()
        if not item or not item.text():
            self.setDragDropMode(QAbstractItemView.DropOnly)
        else:
            self.setDragDropMode(QAbstractItemView.DragDrop)

    def set_allocation(self, checked: bool):
        """Set restrict tyre allocation"""
        self._restrict_allocation = checked

    def dropEvent(self, event):
        """Verify drop location & store a temp item copy"""
        item = self.itemAt(event.pos())
        if not item:
            return
        # Restrict drop inside row & column
        max_row = self.rowCount()
        row_index = item.row()
        column_index = item.column()
        if row_index >= max_row or column_index >= self._wheel_count:
            return
        # Create copy before drop
        temp_item = item.clone()
        super().dropEvent(event)
        # Remove row from invalid drop
        if max_row < self.rowCount():
            self.removeRow(max_row)
            return
        # Verify new item
        tyre_name = item.text()
        if tyre_name:
            if (same_index := self._same_row(tyre_name, row_index, column_index)) != column_index:
                self.setItem(row_index, column_index, temp_item)
                msg_text = (
                    f"<b>{tyre_name}</b> already installed on <b>{HEADER_TYREPLAN[same_index]}</b> wheel.<br><br>"
                    f"Cannot install the same tyre on two wheels at the same time."
                )
                QMessageBox.information(self, "Incorrect Tyre Allocation", msg_text)
            elif self._restrict_allocation and (same_index := self._same_allocation(tyre_name, row_index, column_index)) != column_index:
                self.setItem(row_index, column_index, temp_item)
                msg_text = (
                    f"<b>{tyre_name}</b> already used on <b>{HEADER_TYREPLAN[same_index]}</b> wheel.<br><br>"
                    f"Cannot allocate already used tyre on a different wheel."
                )
                QMessageBox.information(self, "Incorrect Tyre Allocation", msg_text)
            elif not self.cellWidget(row_index, column_index):
                self._add_stats(row_index, column_index)
        else:  # ignore emptry drop
            self.setItem(row_index, column_index, temp_item)
        # Signal update
        self.refresh.emit(True)

    def append_row(self, row_index: int = -1):
        """Add new table row"""
        self._add_row(row_index)
        # Signal update
        self.refresh.emit(True)

    def duplicate_row(self):
        """Duplicate current row (tyre column only)"""
        row_index = self.currentRow()
        column_count = self._wheel_count
        new_row_index = row_index + 1
        self._add_row(new_row_index)

        for column_index in range(column_count):
            item = self.item(row_index, column_index)
            new_item = self.item(new_row_index, column_index)
            if not item:
                continue
            tyre_name = item.text()
            if not tyre_name:
                continue
            new_item.setText(tyre_name)
            self._add_stats(new_row_index, column_index)
        # Signal update
        self.refresh.emit(True)

    def insert_above(self):
        """Insert new row at above or below current row"""
        self._add_row(self.currentRow())
        # Signal update
        self.refresh.emit(True)

    def insert_below(self):
        """Insert new row at above or below current row"""
        self._add_row(self.currentRow() + 1)
        # Signal update
        self.refresh.emit(True)

    def delete_row(self):
        """Delete selected row"""
        selected_rows = set(data.row() for data in self.selectedIndexes())
        for row_index in sorted(selected_rows, reverse=True):
            self.removeRow(row_index)
        # Signal update
        self.refresh.emit(True)

    def remove_items(self):
        """Remove selected items"""
        for item in self.selectedItems():
            row_index = item.row()
            column_index = item.column()
            self._remove_item(row_index, column_index)
        # Signal update
        self.refresh.emit(True)

    def remove_invalid(self, tyre_name_list: tuple[str, ...]):
        """Remove invalid items according to reference item list"""
        row_count = self.rowCount()
        column_count = self._wheel_count
        for row_index in range(row_count):
            for column_index in range(column_count):
                item = self.item(row_index, column_index)
                if not item:
                    continue
                tyre_name = item.text()
                if not tyre_name:
                    continue
                if tyre_name not in tyre_name_list:
                    self._remove_item(row_index, column_index)
        # Signal update
        self.refresh.emit(True)

    def export_to_list(self, column_count: int = 4) -> list[list[str]]:
        """Export data to row[column[tyre_name, ...], ...]"""
        row_list = []
        row_count = self.rowCount()
        for row_index in range(row_count):
            column_list = []
            for column_index in range(column_count):
                item = self.item(row_index, column_index)
                tyre_name = item.text() if item else ""
                column_list.append(tyre_name)
            row_list.append(column_list)
        return row_list

    def load_tyre_plan(self, user_data: list[list[str]]):
        """Load tyre plan data to table"""
        self.setRowCount(0)
        if len(user_data) < 1:
            self._add_row()
            return
        for row_index, row_data in enumerate(user_data):
            self.insertRow(row_index)
            self.setCurrentCell(row_index, 0)
            for column_index in range(self.columnCount()):
                if column_index < self._wheel_count:
                    text = row_data[column_index]
                else:
                    text = ""
                self._add_item(row_index, column_index, text)

    def set_change_time(self, row_index: int, column_index: int, seconds: float):
        """Set tyre change time"""
        item = self.item(row_index, column_index)
        if seconds <= 0:
            text_time = "N/A"
            item.setFlags(Qt.NoItemFlags)
        else:
            text_time = f"{seconds:+.1f}s"
            item.setFlags(Qt.ItemIsEnabled)
        item.setText(text_time)

    def _add_row(self, row_index: int = -1):
        """Add new table row"""
        if row_index < 0:
            row_index = self.rowCount()
        self.insertRow(row_index)
        self.setCurrentCell(row_index, 0)
        for column_index in range(self.columnCount()):
            self._add_item(row_index, column_index, "")

    def _add_item(self, row_index: int, column_index: int, text: str):
        """Add item"""
        flag_tyre = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled
        flag_readonly = Qt.ItemIsEnabled
        item = QTableWidgetItem()
        if column_index < self._wheel_count:
            item.setText(text)
            item.setFlags(flag_tyre)
            if text:
                self._add_stats(row_index, column_index)
        else:
            item.setFlags(flag_readonly)
            item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row_index, column_index, item)

    def _add_stats(self, row_index: int, column_index: int):
        """Add item stats"""
        item_stats = TyrePlanItemTag(None)
        self.setCellWidget(row_index, column_index, item_stats)

    def _remove_item(self, row_index: int, column_index: int):
        """Remove one item from specific cell"""
        item = self.item(row_index, column_index)
        item.setText("")
        self.removeCellWidget(row_index, column_index)

    def _same_allocation(self, target_tyre_name: str, target_row: int, target_column: int) -> int:
        """Check allocation of same tyre"""
        column_index = -1
        row_count = self.rowCount()
        column_count = self._wheel_count
        for row_index in range(row_count):
            for column_index in range(column_count):
                item = self.item(row_index, column_index)
                if not item:
                    continue
                tyre_name = item.text()
                if row_index == target_row and column_index == target_column:
                    continue
                if tyre_name == target_tyre_name:
                    return column_index
        return target_column

    def _same_row(self, target_tyre_name: str, target_row: int, target_column: int) -> int:
        """Check allocation of same tyre on the same row"""
        column_index = -1
        column_count = self._wheel_count
        for column_index in range(column_count):
            item = self.item(target_row, column_index)
            if not item:
                continue
            tyre_name = item.text()
            if column_index == target_column:
                continue
            if tyre_name == target_tyre_name:
                return column_index
        return target_column


class TyreSetList(QListWidget):
    """Tyre set list"""

    def set_drag_mode(self):
        """Set drag mode based on selection"""
        if len(self.selectedIndexes()) > 1:
            self.setDragDropMode(QAbstractItemView.NoDragDrop)
        else:
            self.setDragDropMode(QAbstractItemView.DragOnly)

    def tyre_in_stock(self) -> tuple[str, ...]:
        """List all tyre name in stock"""
        return tuple(self.item(row).text() for row in range(self.count()))

    def load_tyre_stock(self, user_data: list[str]):
        """Load tyre stock to list"""
        self.clear()
        if len(user_data) < 1:
            return
        for row_data in user_data:
            self._add_item(row_data)

    def sort_by_compound(self):
        """Sort by compound type"""
        if self.count() > 1:
            TyreNameListItem.sort_type = 0
            self.sortItems(Qt.SortOrder.AscendingOrder)

    def sort_by_stints(self):
        """Sort by number of stints"""
        if self.count() > 1:
            TyreNameListItem.sort_type = 1
            self.sortItems(Qt.SortOrder.AscendingOrder)

    def add_tyre(self, tyre_key: str):
        """Add tyre"""
        tyre_name = encode_tyre_name(tyre_key, self.tyre_in_stock())
        self._add_item(tyre_name)

    def remove_tyre(self, items: list[QListWidgetItem]):
        """Remove selected tyre items"""
        for item in items:
            self.takeItem(self.row(item))

    def update_uses(self, tyre_name_list: list[str]):
        """Update number of stints for each tyre"""
        for row in range(self.count()):
            item = self.item(row)
            tyre_name = item.text()
            if tyre_name in tyre_name_list:
                count_stints = tyre_name_list.count(tyre_name)
            else:
                count_stints = 0
            item.stints = count_stints
            self.itemWidget(item).set_uses(count_stints)

    def count_stock(self, tyre_set_data: dict) -> int:
        """Count stock tyres"""
        count = 0
        for row in range(self.count()):
            item = self.item(row)
            tyre_name = item.text()
            tyre_key = extract_tyre_key(tyre_name)
            tyre_setting = tyre_set_data.get(tyre_key, DEFAULT_TYRE_SETTING)
            if not tyre_setting["enable_limited_stock"]:
                continue
            count += 1
        return count

    def count_used(self) -> int:
        """Count used tyres"""
        count = 0
        for row in range(self.count()):
            item = self.item(row)
            if item.stints > 0:
                count += 1
        return count

    def _add_item(self, tyre_name: str):
        """Add tyre item"""
        item = TyreNameListItem(tyre_name)
        self.addItem(item)
        label_item = TyreSetItemTag(None)
        self.setItemWidget(item, label_item)


class TyreSetItemTag(QWidget):
    """Tyre set item tag"""

    def __init__(self, parent):
        super().__init__(parent)
        layout_item = QHBoxLayout()
        layout_item.setContentsMargins(0, 0, 0, 0)
        layout_item.setSpacing(0)
        layout_item.addStretch(1)

        self._label_stints = QLabel()
        layout_item.addWidget(self._label_stints)

        self.setLayout(layout_item)
        self.set_uses(0)

    def set_uses(self, stints: int):
        """Set number of stints the tyre used"""
        if stints > 0:
            color = "#996633"
        else:
            color = "#777777"
        self._label_stints.setStyleSheet(f"background:{color}")
        self._label_stints.setText(f"Stints: {stints}")


class TyrePlanItemTag(QWidget):
    """Tyre plan item tag"""

    def __init__(self, parent):
        super().__init__(parent)
        font = self.font()
        font.setWeight(QFont.Bold)
        self.setFont(font)
        self.remaining = 0.0
        self.end = 0.0

    def set_remaining(self, percent: float, wear_per_stint: float):
        """Set remaining tyre tread (fraction)"""
        self.remaining = percent
        self.end = percent - wear_per_stint

    def paintEvent(self, event):
        percent = self.remaining
        end = self.end
        if percent > 0.9:
            color = "#00AA33"
        elif percent > 0.8:
            color = "#33AA00"
        elif percent > 0.7:
            color = "#66AA00"
        elif percent > 0.6:
            color = "#88AA00"
        elif percent > 0.5:
            color = "#AAAA00"
        elif percent > 0.4:
            color = "#AA8800"
        elif percent > 0.3:
            color = "#AA6600"
        elif percent > 0.2:
            color = "#BB3300"
        else:
            color = "#CC0000"
        painter = QPainter(self)
        width = self.width()
        height = self.height()
        painter.fillRect(width * (1 - percent), height * 0.9, width * percent, height, color)
        painter.setPen(QPen(color))
        if end < 0:
            text = "Blowout"
        elif percent < 1:
            text = f"{percent * 100:.0f}-{end:.0%}"
        else:
            text = f"New-{end:.0%}"
        text_align = Qt.AlignRight | Qt.AlignVCenter
        painter.drawText(0, 0, width, height, text_align, text)


class TyreStatusBar(QStatusBar):
    """Tyre usage info status bar"""

    def __init__(self, parent):
        super().__init__(parent)
        self._tyre_stock = QLabel()
        self._tyre_used = QLabel()
        self._stints = QLabel()
        self._pit_stops = QLabel()
        self._changes = QLabel()
        self._change_time = QLabel()

        self.addWidget(self._tyre_stock)
        self.addWidget(add_vertical_separator())
        self.addWidget(self._tyre_used)
        self.addWidget(add_vertical_separator())
        self.addWidget(self._stints)
        self.addWidget(add_vertical_separator())
        self.addWidget(self._pit_stops)
        self.addWidget(add_vertical_separator())
        self.addWidget(self._changes)
        self.addWidget(add_vertical_separator())
        self.addWidget(self._change_time)

    def update_info(self, tyre_used: int, tyre_max: int, tyre_stock: int, stints: int, changes: int, change_time: float):
        """Update tyre usage info"""
        stock_color = "color:#F20;" if tyre_stock > tyre_max else ""
        stock_invalid = " (invalid)" if stock_color else ""
        self._tyre_stock.setStyleSheet(stock_color)
        self._tyre_stock.setText(f"Stock: {tyre_stock} / {tyre_max}{stock_invalid}")
        self._tyre_used.setText(f"Used: {tyre_used}")
        self._stints.setText(f"Stints: {stints}")
        self._pit_stops.setText(f"Pits: {max(stints - 1, 0)}")
        self._changes.setText(f"Changes: {changes}")
        self._change_time.setText(f"Time: {change_time:+.2f}s")


class TyreRulePanel(QFrame):
    """Tyre rule panel"""

    def __init__(self, parent: TyreStrategyPlanner):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(4, 2, 4, 2)
        self.setLayout(layout)
        self.setFrameShape(QFrame.StyledPanel)

        self._max_tyre = QSpinBox()
        self._max_tyre.setRange(0, 999)
        self._max_tyre.setValue(4)
        self._max_tyre.setAlignment(Qt.AlignRight)
        self._max_tyre.valueChanged.connect(parent.update_tyre_status)

        self._tyre_alloc = QCheckBox("Restrict Allocation")
        self._tyre_alloc.setChecked(True)
        self._tyre_alloc.toggled.connect(parent.update_tyre_status)

        self._change_time_1 = self._add_tyre_time_spinbox(1)
        self._change_time_1.valueChanged.connect(parent.update_tyre_wear)

        self._change_time_2 = self._add_tyre_time_spinbox(2)
        self._change_time_2.valueChanged.connect(parent.update_tyre_wear)

        self._change_time_3 = self._add_tyre_time_spinbox(3)
        self._change_time_3.valueChanged.connect(parent.update_tyre_wear)

        self._change_time_4 = self._add_tyre_time_spinbox(4)
        self._change_time_4.valueChanged.connect(parent.update_tyre_wear)

        self._highlight_new = QCheckBox("Highlight New Tyre")
        self._highlight_new.setChecked(True)
        self._highlight_new.toggled.connect(parent.update_tyre_wear)

        layout.addWidget(QLabel("Maximum Tyres"))
        layout.addWidget(self._max_tyre)
        layout.addWidget(add_vertical_separator())
        layout.addWidget(QLabel("Change Time"))
        layout.addWidget(self._change_time_1)
        layout.addWidget(self._change_time_2)
        layout.addWidget(self._change_time_3)
        layout.addWidget(self._change_time_4)
        layout.addWidget(add_vertical_separator())
        layout.addWidget(self._tyre_alloc)
        layout.addWidget(add_vertical_separator())
        layout.addWidget(self._highlight_new)
        layout.addStretch(1)

    def _add_tyre_time_spinbox(self, count: int):
        """Add tyre time spinbox"""
        spinbox = QDoubleSpinBox()
        spinbox.setRange(0, 99)
        spinbox.setDecimals(1)
        spinbox.setSingleStep(0.1)
        spinbox.setAlignment(Qt.AlignRight)
        spinbox.setSuffix(f" s/{count}")
        return spinbox

    def load_tyre_rule(self, user_data: dict):
        """Load tyre rule from user data"""
        self._max_tyre.setValue(user_data["maximum_tyre"])
        self._tyre_alloc.setChecked(user_data["enable_restricted_allocation"])
        self._change_time_1.setValue(user_data["tyre_change_time_1"])
        self._change_time_2.setValue(user_data["tyre_change_time_2"])
        self._change_time_3.setValue(user_data["tyre_change_time_3"])
        self._change_time_4.setValue(user_data["tyre_change_time_4"])

    def export_tyre_rule(self):
        """export tyre rule from user data"""
        return {
            "maximum_tyre": self._max_tyre.value(),
            "enable_restricted_allocation": self._tyre_alloc.isChecked(),
            "tyre_change_time_1": self._change_time_1.value(),
            "tyre_change_time_2": self._change_time_2.value(),
            "tyre_change_time_3": self._change_time_3.value(),
            "tyre_change_time_4": self._change_time_4.value(),
        }

    def max_allowed(self) -> int:
        """Max allowed tyres"""
        return self._max_tyre.value()

    def is_restrict_allocation(self) -> bool:
        """Is restrict tyre allocation"""
        return self._tyre_alloc.isChecked()

    def is_highlight_new(self) -> bool:
        """Is highlight new tyre"""
        return self._highlight_new.isChecked()

    def change_time(self) -> tuple[float, float, float, float, float]:
        """Tyre change time (seconds) list"""
        return (
            0.0,  # no change
            self._change_time_1.value(),
            self._change_time_2.value(),
            self._change_time_3.value(),
            self._change_time_4.value(),
        )


class TyreSetPanel(QFrame):
    """Tyre set panel"""

    def __init__(self, parent: TyreStrategyPlanner, tyre_set_list: TyreSetList):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(UIScaler.size(17))
        self.setLayout(layout)

        # Button top
        self._tyre_selector = QComboBox()

        button_addtyre = CompactButton("Add")
        button_addtyre.clicked.connect(parent.add_tyre_to_set)

        button_config = CompactButton("Config")
        button_config.clicked.connect(parent.open_tyre_config_dialog)

        layout_top = QHBoxLayout()
        layout_top.addWidget(self._tyre_selector)
        layout_top.addWidget(button_addtyre)
        layout_top.addWidget(button_config)

        # Button low
        sort_menu = QMenu(self)

        sort_by_tyre = sort_menu.addAction("Compound Type")
        sort_by_tyre.triggered.connect(tyre_set_list.sort_by_compound)

        sort_by_uses = sort_menu.addAction("Number of Stints")
        sort_by_uses.triggered.connect(tyre_set_list.sort_by_stints)

        button_sort = CompactButton("Sort By", has_menu=True)
        button_sort.setMenu(sort_menu)

        button_remove = CompactButton("Remove")
        button_remove.clicked.connect(parent.remove_tyre_from_set)

        button_clearall = CompactButton("Clear All")
        button_clearall.clicked.connect(parent.remove_all_tyres)

        layout_button = QHBoxLayout()
        layout_button.addWidget(button_sort)
        layout_button.addStretch(1)
        layout_button.addWidget(button_remove)
        layout_button.addWidget(button_clearall)

        layout.addLayout(layout_top)
        layout.addWidget(tyre_set_list)
        layout.addLayout(layout_button)

    def load_tyre_set(self, userdata: dict[str, dict]):
        """Load tyre set"""
        self._tyre_selector.clear()
        self._tyre_selector.addItems(userdata)
        self._tyre_selector.setCurrentIndex(2)

    def selected_tyre(self) -> str:
        """Selected tyre name"""
        return self._tyre_selector.currentText()


class TyrePlanPanel(QFrame):
    """Tyre plan panel"""

    def __init__(self, parent: TyreStrategyPlanner, tyre_plan_table: TyrePlanTable):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(UIScaler.size(60))
        self.setLayout(layout)

        # Filename edit
        self._filename = QLineEdit()
        self._filename.setValidator(QVAL_FILENAME)

        # Button top
        file_menu = QMenu(self)

        new_file = file_menu.addAction("New File")
        new_file.triggered.connect(parent.create_new_file)

        file_menu.addSeparator()

        open_file = file_menu.addAction("Open File")
        open_file.triggered.connect(parent.load_from_file)

        file_menu.addSeparator()

        save_as = file_menu.addAction("Save As...")
        save_as.triggered.connect(parent.saving)

        export_csv = file_menu.addAction("Export As...")
        export_csv.triggered.connect(parent.export_as_csv)

        button_file = CompactButton("File", has_menu=True)
        button_file.setMenu(file_menu)

        button_save = CompactButton("Save As")
        button_save.clicked.connect(parent.saving)

        layout_top = QHBoxLayout()
        layout_top.addWidget(button_file)
        layout_top.addWidget(self._filename, stretch=1)
        layout_top.addWidget(button_save)

        # Button bottom
        button_duplicate = CompactButton("Duplicate Row")
        button_duplicate.clicked.connect(parent.duplicate_row)

        button_addnew = CompactButton("New Row")
        button_addnew.clicked.connect(parent.add_new_row)

        button_insertbelow = CompactButton("Insert Below")
        button_insertbelow.clicked.connect(parent.insert_row_below)

        button_insertabove = CompactButton("Insert Above")
        button_insertabove.clicked.connect(parent.insert_row_above)

        button_delete = CompactButton("Delete Row")
        button_delete.clicked.connect(parent.delete_row)

        button_close = CompactButton("Close")
        button_close.clicked.connect(parent.close)

        layout_button = QHBoxLayout()
        layout_button.addWidget(button_duplicate)
        layout_button.addWidget(button_addnew)
        layout_button.addWidget(button_insertbelow)
        layout_button.addWidget(button_insertabove)
        layout_button.addWidget(button_delete)
        layout_button.addStretch(1)
        layout_button.addWidget(button_close)

        layout.addLayout(layout_top)
        layout.addWidget(tyre_plan_table)
        layout.addLayout(layout_button)

    def set_filename(self, filename: str):
        """Set tyre strategy file name"""
        self._filename.setText(filename)

    def filename(self) -> str:
        """Tyre strategy file name"""
        return self._filename.text()


class TyreStrategyPlanner(BaseEditor):
    """Tyre strategy planner"""

    def __init__(self, parent):
        super().__init__(parent)
        self.set_utility_title("Tyre Strategy Planner")
        self.setMinimumHeight(UIScaler.size(40))

        self.user_data = {}

        # Tyre set list
        tyre_set = TyreSetList(self)
        tyre_set.setAlternatingRowColors(True)
        tyre_set.setSelectionMode(QListWidget.ExtendedSelection)
        tyre_set.itemSelectionChanged.connect(tyre_set.set_drag_mode)

        tyre_set.setContextMenuPolicy(Qt.CustomContextMenu)
        tyre_set.customContextMenuRequested.connect(self.open_context_menu_tyre_list)

        self.tyre_set = tyre_set

        # Tyre plan table
        tyre_plan = TyrePlanTable(self)
        tyre_plan.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tyre_plan.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        tyre_plan.setShowGrid(False)

        tyre_plan.setColumnCount(len(HEADER_TYREPLAN))
        tyre_plan.setHorizontalHeaderLabels(HEADER_TYREPLAN)

        tyre_plan.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        tyre_plan.setColumnWidth(4, UIScaler.size(5))

        tyre_plan.setContextMenuPolicy(Qt.CustomContextMenu)
        tyre_plan.customContextMenuRequested.connect(self.open_context_menu_tyre_table)

        tyre_plan.itemSelectionChanged.connect(tyre_plan.set_drag_mode)
        tyre_plan.refresh.connect(self.update_tyre_wear)

        self.tyre_plan = tyre_plan

        # Set panels
        self.tyre_status_bar = TyreStatusBar(self)
        self.tyre_rule_panel = TyreRulePanel(self)
        self.tyre_set_panel = TyreSetPanel(self, self.tyre_set)
        self.tyre_plan_panel = TyrePlanPanel(self, self.tyre_plan)

        # Set layout
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setHandleWidth(5)
        splitter.addWidget(self.tyre_set_panel)
        splitter.addWidget(self.tyre_plan_panel)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes((self.tyre_set_panel.width(), self.tyre_plan_panel.width()))

        layout_main = QVBoxLayout()
        layout_main.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, 0)
        layout_main.addWidget(self.tyre_rule_panel)
        layout_main.addWidget(splitter, stretch=1)
        layout_main.addWidget(self.tyre_status_bar)
        self.setLayout(layout_main)

        # Shortcut
        self._add_keyboard_shortcut()

        # Init setting & table
        self.create_new_file()

    def _add_keyboard_shortcut(self):
        """Add keyboard shortcut"""
        if os.getenv("PYSIDE_OVERRIDE") == "6":
            from PySide2.QtGui import QShortcut
        else:
            from PySide2.QtWidgets import QShortcut

        delete_key = QShortcut(self)
        delete_key.setKey(QKeySequence(QKeySequence.Delete))
        delete_key.activated.connect(self.remove_tyre_from_table)

    def refresh_table(self):
        """Refresh table"""
        self.tyre_rule_panel.load_tyre_rule(self.user_data["tyre_rule"])
        self.tyre_set_panel.load_tyre_set(self.user_data["tyre_set"])
        self.tyre_set.load_tyre_stock(self.user_data["tyre_stock"])
        self.tyre_plan.load_tyre_plan(self.user_data["tyre_plan"])
        self.update_tyre_wear()

    # File create, load, save, export
    def create_new_file(self):
        """Create new file"""
        if not self.confirm_discard():
            return
        self.tyre_plan_panel.set_filename("Untitled plan")
        self.user_data = create_tyre_strategy()
        self.refresh_table()
        self.set_unmodified()

    def load_from_file(self):
        """Load tyre strategy from file"""
        if not self.confirm_discard():
            return
        filename_full, file_filter = QFileDialog.getOpenFileName(
            self,
            dir=set_tyre_strategy_file_path(),
            filter=FileFilter.TYRESTRATEGY,
        )
        if not filename_full:
            return
        filepath = os.path.dirname(filename_full) + "/"
        filename = os.path.basename(filename_full)
        user_data = load_tyre_strategy_file(
            filepath=filepath,
            filename=filename,
        )
        if user_data is None:
            msg_text = "Cannot open selected file.<br><br>Invalid tyre strategy file."
            QMessageBox.warning(self, "Error", msg_text)
            return
        self.user_data = user_data
        # Update file name
        save_tyre_strategy_file_path(filepath)
        self.tyre_plan_panel.set_filename(os.path.splitext(filename)[0])
        self.refresh_table()
        self.set_unmodified()

    def saving(self):
        """Save tyre strategy file"""
        filename = self.tyre_plan_panel.filename()
        if not filename:
            QMessageBox.warning(self, "Error", "Invalid file name.")
            return
        filename_full, file_filter = QFileDialog.getSaveFileName(
            self,
            dir=set_tyre_strategy_file_path(filename),
            filter=FileFilter.TYRESTRATEGY,
        )
        if not filename_full:  # save canceled
            return
        # Prepare data
        user_data = self.user_data
        user_data["file_version"] = TYRE_STRATEGY_FILE_VERSION
        user_data["tyre_rule"].update(self.tyre_rule_panel.export_tyre_rule())
        user_data["tyre_stock"] = self.tyre_set.tyre_in_stock()
        user_data["tyre_plan"] = self.tyre_plan.export_to_list()
        # Save data
        filepath = os.path.dirname(filename_full) + "/"
        filename = os.path.basename(filename_full)
        save_tyre_strategy_file(
            dict_user=user_data,
            filename=filename,
            filepath=filepath,
        )
        # Update file name
        save_tyre_strategy_file_path(filepath)
        self.tyre_plan_panel.set_filename(os.path.splitext(filename)[0])
        self.set_unmodified()
        msg_text = f"Tyre strategy file saved at:<br><b>{filename_full}</b>"
        QMessageBox.information(self, "Saved", msg_text)

    def export_as_csv(self):
        """Export tyre strategy as spreadsheet (CSV)"""
        filename = self.tyre_plan_panel.filename()
        if not filename:
            QMessageBox.warning(self, "Error", "Invalid file name.")
            return
        filename_full, file_filter = QFileDialog.getSaveFileName(
            self,
            dir=set_tyre_strategy_file_path(filename),
            filter=FileFilter.CSV,
        )
        if not filename_full:  # save canceled
            return
        # Tyre rule
        tyre_rule = self.tyre_rule_panel.export_tyre_rule()
        tyre_rule_data = [
            [format_option_name(name) for name in tyre_rule],
            list(tyre_rule.values()),
        ]
        # Tyre stock list
        tyre_set = self.tyre_set
        tyre_stock_data = [["Tyre Stock", "Stints"]]
        for row in range(tyre_set.count()):
            item = tyre_set.item(row)
            tyre_stock_data.append([item.text(), item.stints])
        # Tyre plan table
        tyre_plan_header = ["Stint"]
        for index, name in enumerate(HEADER_TYREPLAN):
            tyre_plan_header.append(name)
            if index < 4:
                tyre_plan_header.append("Tread (%)")
        tyre_plan = self.tyre_plan
        tyre_plan_data = [tyre_plan_header]
        row_count = tyre_plan.rowCount()
        column_count = tyre_plan.columnCount()
        for row_index in range(row_count):
            column_list = [row_index + 1]
            for column_index in range(column_count):
                item = tyre_plan.item(row_index, column_index)
                if item:
                    tyre_name = item.text()
                else:
                    tyre_name = ""
                column_list.append(tyre_name)
                if column_index < 4:
                    item_tag = tyre_plan.cellWidget(row_index, column_index)
                    if item_tag:
                        tyre_remaining = f"{item_tag.remaining * 100:.2f} - {max(item_tag.end, 0.0) * 100:.2f}"
                    else:
                        tyre_remaining = "0.0"
                    column_list.append(tyre_remaining)
            tyre_plan_data.append(column_list)
        # Save data
        filepath = os.path.dirname(filename_full) + "/"
        filename = os.path.basename(filename_full)
        export_tyre_strategy_file(
            rule_data=tyre_rule_data,
            stock_data=tyre_stock_data,
            plan_data=tyre_plan_data,
            filename=filename,
            filepath=filepath,
        )
        save_tyre_strategy_file_path(filepath)
        msg_text = f"Tyre strategy file exported at:<br><b>{filename_full}</b>"
        QMessageBox.information(self, "Exported", msg_text)

    # Context menu
    def open_context_menu_tyre_list(self, position: QPoint):
        """Open context menu - tyre list"""
        tyre_list = self.tyre_set
        if not tyre_list.itemAt(position):
            return
        menu = QMenu()
        remove_from_set = menu.addAction("Remove Selected")
        selected_action = menu.exec_(tyre_list.mapToGlobal(position))
        if not selected_action:
            return
        if selected_action == remove_from_set:
            self.remove_tyre_from_set()

    def open_context_menu_tyre_table(self, position: QPoint):
        """Open context menu - tyre plan table"""
        table = self.tyre_plan
        if not table.itemAt(position):
            return
        menu = QMenu()
        remove_from_table = menu.addAction("Remove Selected")
        duplicate_row = menu.addAction("Duplicate Row")
        menu.addSeparator()
        insert_above = menu.addAction("Insert Row Above")
        insert_below = menu.addAction("Insert Row Below")
        menu.addSeparator()
        delete_row = menu.addAction("Delete Row")
        position += QPoint(table.verticalHeader().width(), table.horizontalHeader().height())
        selected_action = menu.exec_(table.mapToGlobal(position))
        if not selected_action:
            return
        if selected_action == duplicate_row:
            self.duplicate_row()
        elif selected_action == insert_above:
            self.insert_row_above()
        elif selected_action == insert_below:
            self.insert_row_below()
        elif selected_action == delete_row:
            self.delete_row()
        elif selected_action == remove_from_table:
            self.remove_tyre_from_table()

    # Update tyre table, list, status
    def update_tyre_status(self):
        """Update tyre status info"""
        self.set_modified()
        self.tyre_plan.set_allocation(self.tyre_rule_panel.is_restrict_allocation())
        tyre_used = self.tyre_set.count_used()
        tyre_max = self.tyre_rule_panel.max_allowed()
        tyre_stock = self.tyre_set.count_stock(self.user_data["tyre_set"])
        stints = self.tyre_plan.rowCount()
        # Sum of tyre change time
        total_changes = 0
        total_change_time = 0
        for row_index in range(1, self.tyre_plan.rowCount()):
            item = self.tyre_plan.item(row_index, 4)
            if not item:
                continue
            text = item.text()
            if not text.endswith("s"):
                continue
            total_change_time += float(text.rstrip("s"))
            total_changes += 1
        # Update
        self.tyre_status_bar.update_info(
            tyre_used=tyre_used,
            tyre_max=tyre_max,
            tyre_stock=tyre_stock,
            stints=stints,
            changes=total_changes,
            change_time=total_change_time,
        )

    @Slot(bool)  # type: ignore[operator]
    def update_tyre_wear(self):
        """Update tyre wear"""
        table = self.tyre_plan
        tyre_change_time = self.tyre_rule_panel.change_time()
        is_highlight_new = self.tyre_rule_panel.is_highlight_new()
        tyre_set_data = self.user_data["tyre_set"]
        refer_starting_tread = (
            "front_left_starting_tread",
            "front_right_starting_tread",
            "rear_left_starting_tread",
            "rear_right_starting_tread",
        )
        refer_wear_per_stint = (
            "front_left_wear_per_stint",
            "front_right_wear_per_stint",
            "rear_left_wear_per_stint",
            "rear_right_wear_per_stint",
        )

        tyre_name_list = []
        row_count = table.rowCount()
        column_count = 4
        for row_index in range(row_count):
            count_changed = 0
            for column_index in range(column_count):
                item = table.item(row_index, column_index)
                if not item:
                    continue
                tyre_name = item.text()
                if not tyre_name:
                    continue
                # Count changed tyres
                item_above = table.item(max(row_index - 1, 0), column_index)
                if not item_above or item_above.text() != tyre_name:
                    count_changed += 1
                # Count used tyres
                tyre_name_list.append(tyre_name)
                # Get unique tyre key name
                tyre_key = extract_tyre_key(tyre_name)
                if not tyre_key:
                    continue
                # Calculate wear
                tyre_item = table.cellWidget(row_index, column_index)
                if not tyre_item:
                    continue
                tyre_setting = tyre_set_data.get(tyre_key, DEFAULT_TYRE_SETTING)
                starting_tread = min(tyre_setting[refer_starting_tread[column_index]], 100.0) * 0.01
                wear_per_stint = max(tyre_setting[refer_wear_per_stint[column_index]], 0.0) * 0.01
                count_stints = tyre_name_list.count(tyre_name) - 1
                highlight = (not is_highlight_new or count_stints < 1)
                item.setForeground(Qt.NoBrush if highlight else QBrush(Qt.darkGray))
                tyre_item.set_remaining(starting_tread - wear_per_stint * count_stints, wear_per_stint)
            else:
                # Calculate tyre change time
                table.set_change_time(row_index, column_count, tyre_change_time[count_changed])

        self.tyre_set.update_uses(tyre_name_list)
        self.update_tyre_status()

    # Tyre list actions
    def open_tyre_config_dialog(self):
        """Open tyre config dialog"""
        tyre_name = self.tyre_set_panel.selected_tyre()
        _dialog = UserConfig(
            self,
            key_name=tyre_name,
            preset_name="Tyre Compound",
            config_type="",
            user_setting=self.user_data["tyre_set"],
            default_setting=DEFAULT_TYRE_SET,
            reload_func=self.update_tyre_wear,
        )
        _dialog.open()

    def add_tyre_to_set(self):
        """Add tyre to tyre set list"""
        tyre_key = self.tyre_set_panel.selected_tyre()
        if not tyre_key:
            QMessageBox.warning(self, "Error", "Invalid tyre name.")
            return
        self.tyre_set.add_tyre(tyre_key)
        self.update_tyre_status()

    def remove_tyre_from_set(self):
        """Remove tyre from tyre set list and table"""
        items = self.tyre_set.selectedItems()
        if not items:
            QMessageBox.warning(self, "Error", "No tyre selected.")
            return False
        msg_text = (
            "<b>Remove selected tyre from list?</b><br><br>"
            "Corresponding tyre will be removed from table."
        )
        if self.confirm_operation(message=msg_text):
            self.tyre_set.remove_tyre(items)
            self.tyre_plan.remove_invalid(self.tyre_set.tyre_in_stock())

    def remove_all_tyres(self):
        """Remove all tyres from tyre set list and table"""
        msg_text = (
            "<b>Remove all tyres from list?</b><br><br>"
            "All allocated tyres will be removed from table."
        )
        if self.confirm_operation(message=msg_text):
            self.tyre_set.clear()
            self.tyre_plan.remove_invalid(())

    # Tyre table actions
    def remove_tyre_from_table(self):
        """Remove selected tyres from table"""
        if not self.tyre_plan.hasFocus() or not self.tyre_plan.selectedIndexes():
            return
        if self.confirm_operation(message="<b>Remove selected tyre from table?</b>"):
            self.tyre_plan.remove_items()

    def add_new_row(self):
        """Add new row"""
        self.tyre_plan.append_row()

    def insert_row_above(self):
        """Insert row above"""
        self.tyre_plan.insert_above()

    def insert_row_below(self):
        """Insert row below"""
        self.tyre_plan.insert_below()

    def duplicate_row(self):
        """Duplicate row"""
        if not self.tyre_plan.selectedIndexes():
            QMessageBox.warning(self, "Error", "No data selected.")
            return
        self.tyre_plan.duplicate_row()

    def delete_row(self):
        """Delete row"""
        if not self.tyre_plan.selectedIndexes():
            QMessageBox.warning(self, "Error", "No data selected.")
            return
        if self.confirm_operation(message="<b>Delete selected row?</b>"):
            self.tyre_plan.delete_row()
