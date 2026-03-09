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
Display order dialog
"""

from __future__ import annotations

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QAbstractItemView,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from ..formatter import format_option_name
from ._common import BaseDialog, UIScaler


class DisplayOrder(BaseDialog):
    """Adjust display order for widget column or row"""

    def __init__(self, parent, user_orders: dict, default_orders: dict):
        super().__init__(parent)
        self.set_config_title("Display Order", parent.windowTitle().split(" - ")[0])
        self.setMinimumWidth(UIScaler.size(23))
        self.resize(self.size())  # shrink initial size

        self._parent = parent
        self.temp_orders = user_orders
        self.default_orders = default_orders

        # List
        self.list_widget = DisplayOrderList(self, default_orders)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setSpacing(1)
        self.list_widget.refresh(self.temp_orders)

        # Button
        button_reset = QDialogButtonBox(QDialogButtonBox.Reset)
        button_reset.clicked.connect(self._reset_order)

        button_apply = QDialogButtonBox(QDialogButtonBox.Apply)
        button_apply.clicked.connect(self._apply_order)

        button_close = QDialogButtonBox(QDialogButtonBox.Close)
        button_close.clicked.connect(self.reject)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(button_reset)
        bottom_layout.addStretch()
        bottom_layout.addWidget(button_apply)
        bottom_layout.addWidget(button_close)

        # Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.list_widget)
        main_layout.addLayout(bottom_layout)
        main_layout.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        self.setLayout(main_layout)

        # Fit dialog height to list content
        self.list_widget.set_min_height(self.list_widget.count() + 1)

    def showEvent(self, event):
        """Readjust minimum list height when dialog shown"""
        self.list_widget.set_min_height(5)
        super().showEvent(event)

    def _apply_order(self):
        """Apply display order"""
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            key = item.data(Qt.UserRole)
            if key in self.temp_orders:
                self.temp_orders[key] = row + 1

        self._parent.update_display_order(self.temp_orders)
        self._parent.applying()

    def _reset_order(self):
        """Reset display order"""
        msg_text = (
            "Reset <b>Display Order</b> to default?<br><br>"
            "Changes are only saved after clicking Apply Button."
        )
        if self.confirm_operation(title="Reset Options", message=msg_text):
            self.list_widget.refresh(self.default_orders)


class DisplayOrderList(QListWidget):
    """Display order list"""

    def __init__(self, parent, default_orders: dict):
        super().__init__(parent)
        self._default_orders = default_orders

    def focusInEvent(self, event):
        """Validate data against default data in case item missing due to some reasons"""
        if self.count() == len(self._default_orders):
            return
        # Remove invalid or duplicated item
        valid_items = set()
        for row in range(self.count() - 1, -1, -1):
            item = self.item(row)
            key = item.data(Qt.UserRole)
            if key in self._default_orders and key not in valid_items:
                valid_items.add(key)
            else:
                self.takeItem(row)
        # Add missing item
        missing_items = (key for key in self._default_orders if key not in valid_items)
        for key in missing_items:
            self._add_item(key)

    def refresh(self, target_orders: dict):
        """Refresh list"""
        self.clear()
        row = 0
        for key in sorted(target_orders, key=lambda k: target_orders[k]):
            self._add_item(key)
            row += 1
        self.setCurrentRow(0)

    def set_min_height(self, rows: int, min_rows: int = 5):
        """Set minimum list height based on row height"""
        row_height = self.sizeHintForRow(0)
        row_spacing = self.spacing()
        row_count = max(rows, min_rows)
        list_height = (row_height + row_spacing * 2) * row_count + row_spacing * 2
        self.setMinimumHeight(list_height)

    def _add_item(self, key: str):
        """Add display order item"""
        short_key = key.replace("display_order_", "")
        item = QListWidgetItem(format_option_name(short_key))
        item.setTextAlignment(Qt.AlignCenter)
        item.setToolTip("Click & Drag to Reorder Display")
        item.setData(Qt.UserRole, key)
        self.addItem(item)
